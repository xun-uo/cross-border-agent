# 用 PowerShell 直连 GitHub API 推送（Python urllib 在这台机器上被间歇阻断）
# 改版 2026-11-04：走 Git Data API，只上传内容变化的文件。
#   旧版：156 个文件 x (GET sha + PUT 内容) = 312 次串行请求、153 个 commit，实测 519 秒。
#   新版：1 次取远端 tree + 每个变化文件 1 次 blob + 1 次 tree + 1 次 commit + 1 次 refs，
#         改 1 个文件约 4 次请求、几秒；没有变化直接跳过。
# 用法：push_ps1.ps1              正常推送
#       push_ps1.ps1 -DryRun      只列出哪些文件变化了，不推
param(
    [switch]$DryRun,
    [string]$Message = ''
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root   = 'D:\跨境智服'
$token  = (Get-Content "$root\gh_token.txt" -Raw).Trim()
$repo   = 'xun-uo/cross-border-agent'
$branch = 'main'
$api    = 'https://api.github.com'

$headers = @{
    Authorization = "Bearer $token"
    Accept        = 'application/vnd.github+json'
    'User-Agent'  = 'dsh-push'
}

$sw = [System.Diagnostics.Stopwatch]::StartNew()

function Send-GitHub {
    param([string]$Uri, [string]$Method = 'GET', $Body = $null)
    $p = @{ Uri = $Uri; Headers = $headers; Method = $Method; TimeoutSec = 90 }
    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 12 -Compress
        $p.Body = [System.Text.Encoding]::UTF8.GetBytes($json)
        $p.ContentType = 'application/json; charset=utf-8'
    }
    # 本机到 api.github.com 的连接时好时坏（实测首次连接可能 16 秒或直接失败，热了之后约 100ms），
    # 传输层失败重试 3 次；HTTP 4xx 是真错，不重试。
    for ($try = 1; $try -le 4; $try++) {
        try {
            return Invoke-RestMethod @p
        } catch {
            $code = $null
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $code = [int]$_.Exception.Response.StatusCode
            }
            if ($code -ge 400 -and $code -lt 500) { throw }
            if ($try -eq 4) { throw }
            Write-Output "  [重试 $try/3] 网络连接失败，$try 秒后重来"
            Start-Sleep -Seconds $try
        }
    }
}

# 本地文件 -> git blob sha1（"blob <len>\0" + 内容）
function Get-BlobSha {
    param([System.IO.FileInfo]$File)
    $sha = [System.Security.Cryptography.SHA1]::Create()
    try {
        $len  = $File.Length
        $head = [System.Text.Encoding]::ASCII.GetBytes("blob $len`0")
        $fs   = [System.IO.File]::OpenRead($File.FullName)
        try {
            $sha.TransformBlock($head, 0, $head.Length, $null, 0) | Out-Null
            $buf = New-Object byte[] 65536
            while (($n = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
                $sha.TransformBlock($buf, 0, $n, $null, 0) | Out-Null
            }
            $sha.TransformFinalBlock($buf, 0, 0) | Out-Null
        } finally { $fs.Dispose() }
        ([BitConverter]::ToString($sha.Hash) -replace '-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

# ---- 1. 挑出要同步的文件（过滤规则与旧版一致）----
$skipDirs  = @('.venv', '__pycache__', '.git', 'out', 'node_modules')
$skipFiles = @('apikey.txt', 'gh_token.txt', '.env', '_usage.json', 'rules_runtime.json', 'judge_log.jsonl')
$exts = @('.py', '.json', '.md', '.ps1', '.cmd', '.txt', '.yml', '.yaml', '.toml', '.cfg', '.ini')

$files = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($root.Length + 1)
    $parts = $rel -split '\\'
    $bad = $false
    foreach ($p in $parts[0..([Math]::Max(0, $parts.Count - 2))]) {
        if ($skipDirs -contains $p) { $bad = $true }
    }
    (-not $bad) -and ($skipFiles -notcontains $_.Name) -and ($exts -contains $_.Extension.ToLower()) -and
    ($rel -notlike 'data\rule_versions\*')
}
Write-Output "本地上传范围内文件: $($files.Count)"

# ---- 2. 取远端当前 commit / tree（递归一次拿全）----
$ref = Send-GitHub "$api/repos/$repo/git/ref/heads/$branch"
$headCommit = $ref.object.sha
$commitObj  = Send-GitHub "$api/repos/$repo/git/commits/$headCommit"
$baseTree   = $commitObj.tree.sha
$treeObj    = Send-GitHub "$api/repos/$repo/git/trees/$baseTree`?recursive=1"

$remote = @{}
foreach ($e in $treeObj.tree) {
    if ($e.type -eq 'blob') { $remote[$e.path] = $e.sha }
}
Write-Output "远端文件: $($remote.Count)  当前 commit: $($headCommit.Substring(0,7))"

# ---- 3. 逐个比对，只留变化 ----
$changed = New-Object System.Collections.ArrayList
foreach ($f in $files) {
    $rel = ($f.FullName.Substring($root.Length + 1) -replace '\\', '/')
    $sha = Get-BlobSha -File $f
    $old = $remote[$rel]
    if ($old -ne $sha) {
        $kind = if ($null -eq $old) { '新增' } else { '修改' }
        [void]$changed.Add([pscustomobject]@{ Path = $rel; File = $f; Sha = $sha; Kind = $kind })
    }
}

"变化文件: $($changed.Count) / $($files.Count)   比对耗时 $([int]$sw.Elapsed.TotalSeconds)s"
foreach ($c in $changed) { Write-Output "  $($c.Kind)  $($c.Path)" }

if ($changed.Count -eq 0) {
    Write-Output "没有变化，什么都不用传。"
    return
}
if ($DryRun) {
    Write-Output "[DryRun] 只列清单，未推送。"
    return
}

# ---- 4. 只给变化的文件建 blob ----
$entries = New-Object System.Collections.ArrayList
$i = 0
foreach ($c in $changed) {
    $i++
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($c.File.FullName))
    $blob = Send-GitHub "$api/repos/$repo/git/blobs" -Method POST -Body @{ content = $b64; encoding = 'base64' }
    [void]$entries.Add(@{ path = $c.Path; mode = '100644'; type = 'blob'; sha = $blob.sha })
    Write-Output "  blob $i/$($changed.Count)  $($c.Path)"
}

# ---- 5. 建 tree（base_tree 继承未变的部分）----
$newTree = Send-GitHub "$api/repos/$repo/git/trees" -Method POST -Body @{ base_tree = $baseTree; tree = $entries }

# ---- 6. 建 commit + 移动分支 ----
if (-not $Message) {
    $Message = if ($changed.Count -le 3) {
        "update: " + (($changed | ForEach-Object { $_.Path }) -join ', ')
    } else {
        "update: $($changed.Count) files"
    }
}
$newCommit = Send-GitHub "$api/repos/$repo/git/commits" -Method POST -Body @{
    message = $Message
    tree    = $newTree.sha
    parents = @($headCommit)
}
Send-GitHub "$api/repos/$repo/git/refs/heads/$branch" -Method PATCH -Body @{ sha = $newCommit.sha; force = $false } | Out-Null

$sw.Stop()
Write-Output ("uploaded={0} failed=0  新 commit {1}  总耗时 {2:N1}s" -f $changed.Count, $newCommit.sha.Substring(0, 7), $sw.Elapsed.TotalSeconds)
