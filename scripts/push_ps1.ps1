# 用 PowerShell 直连 GitHub API 推送（Python urllib 在这台机器上被间歇阻断）
# 改版 2026-11-04：走 Git Data API。
#   - 只上传内容变化的文件（旧版 156 个文件 x GET+PUT = 312 次请求、153 个 commit，实测 519 秒）
#   - 本地删掉的文件在远端一起删（旧版只会加和改，删不掉——导致「本地删了线上还在」，比如
#     .streamlit/config.toml 删了线上一直留着，把右上角 ⋮ 菜单里的主题切换藏了半个多月）
#   实测：改 1 个文件 11 秒；无变化 3 秒。
# 用法：push_ps1.ps1              正常推送
#       push_ps1.ps1 -DryRun      只列出变化/删除，不推
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

# .devcontainer 是 Streamlit Cloud 那边建的文件，本地没有；不放进同步范围，免得被「远端删除」误删
$skipDirs  = @('.venv', '__pycache__', '.git', 'out', 'node_modules', '.devcontainer')
$skipFiles = @('apikey.txt', 'gh_token.txt', '.env', '_usage.json', 'rules_runtime.json', 'judge_log.jsonl')
$exts = @('.py', '.json', '.md', '.ps1', '.cmd', '.txt', '.yml', '.yaml', '.toml', '.cfg', '.ini')

# 仓库相对路径（正斜杠）是否在同步范围内。本地枚举和远端删除判断共用这一套规则。
function Test-InScope {
    param([string]$Rel)
    $parts = $Rel -split '/'
    foreach ($p in $parts[0..([Math]::Max(0, $parts.Count - 2))]) {
        if ($skipDirs -contains $p) { return $false }
    }
    $name = $parts[-1]
    if ($skipFiles -contains $name) { return $false }
    $ext = [System.IO.Path]::GetExtension($name).ToLowerInvariant()
    if ($exts -notcontains $ext) { return $false }
    if ($Rel -like 'data/rule_versions/*') { return $false }
    return $true
}

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

# ---- 1. 挑出本地要同步的文件 ----
$files = @()
foreach ($f in (Get-ChildItem -Path $root -Recurse -File)) {
    $rel = ($f.FullName.Substring($root.Length + 1) -replace '\\', '/')
    if (Test-InScope -Rel $rel) { $files += $f }
}
Write-Output "本地同步范围内文件: $($files.Count)"

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

# ---- 3. 比对：变化的要传，本地没了的要删 ----
$changed = New-Object System.Collections.ArrayList
$localPaths = @{}
foreach ($f in $files) {
    $rel = ($f.FullName.Substring($root.Length + 1) -replace '\\', '/')
    $localPaths[$rel] = $true
    $sha = Get-BlobSha -File $f
    $old = $remote[$rel]
    if ($old -ne $sha) {
        $kind = if ($null -eq $old) { '新增' } else { '修改' }
        [void]$changed.Add([pscustomobject]@{ Path = $rel; File = $f; Sha = $sha; Kind = $kind })
    }
}

$deleted = New-Object System.Collections.ArrayList
foreach ($rp in @($remote.Keys)) {
    if ($localPaths.ContainsKey($rp)) { continue }
    if (-not (Test-InScope -Rel $rp)) { continue }
    [void]$deleted.Add($rp)
}

"上传: $($changed.Count)  删除: $($deleted.Count)   比对耗时 $([int]$sw.Elapsed.TotalSeconds)s"
foreach ($c in $changed) { Write-Output "  $($c.Kind)  $($c.Path)" }
foreach ($d in $deleted) { Write-Output "  删除  $d" }

if ($changed.Count -eq 0 -and $deleted.Count -eq 0) {
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
# 删除：tree 里把 sha 置 null
foreach ($d in $deleted) {
    [void]$entries.Add(@{ path = $d; mode = '100644'; type = 'blob'; sha = $null })
}

# ---- 5. 建 tree（base_tree 继承未变的部分）----
$newTree = Send-GitHub "$api/repos/$repo/git/trees" -Method POST -Body @{ base_tree = $baseTree; tree = $entries }

# ---- 6. 建 commit + 移动分支 ----
if (-not $Message) {
    $bits = @()
    if ($changed.Count -gt 0) {
        if ($changed.Count -le 3) { $bits += (($changed | ForEach-Object { $_.Path }) -join ', ') }
        else { $bits += "$($changed.Count) files changed" }
    }
    if ($deleted.Count -gt 0) {
        if ($deleted.Count -le 3) { $bits += 'rm ' + ($deleted -join ', ') }
        else { $bits += "$($deleted.Count) files removed" }
    }
    $Message = "update: " + ($bits -join '; ')
}
$newCommit = Send-GitHub "$api/repos/$repo/git/commits" -Method POST -Body @{
    message = $Message
    tree    = $newTree.sha
    parents = @($headCommit)
}
Send-GitHub "$api/repos/$repo/git/refs/heads/$branch" -Method PATCH -Body @{ sha = $newCommit.sha; force = $false } | Out-Null

$sw.Stop()
Write-Output ("uploaded={0} deleted={1} failed=0  新 commit {2}  总耗时 {3:N1}s" -f $changed.Count, $deleted.Count, $newCommit.sha.Substring(0, 7), $sw.Elapsed.TotalSeconds)
