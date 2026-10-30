# 用 PowerShell 直连 GitHub API 推送（Python urllib 在这台机器上被间歇阻断）
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root  = 'D:\跨境智服'
$token = (Get-Content "$root\gh_token.txt" -Raw).Trim()
$repo  = 'xun-uo/cross-border-agent'
$api   = 'https://api.github.com'
$headers = @{
    Authorization = "Bearer $token"
    Accept        = 'application/vnd.github+json'
    'User-Agent'  = 'dsh-push'
}

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

Write-Output "files to upload: $($files.Count)"
$ok = 0; $fail = 0
foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length + 1) -replace '\\', '/'
    $enc = ($rel -split '/' | ForEach-Object { [uri]::EscapeDataString($_) }) -join '/'
    $content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.FullName))

    $sha = $null
    try {
        $info = Invoke-RestMethod -Uri "$api/repos/$repo/contents/$enc" -Headers $headers -TimeoutSec 60
        $sha = $info.sha
    } catch { }

    $body = @{ message = "update: $rel"; content = $content; branch = 'main' }
    if ($sha) { $body.sha = $sha }
    $json = $body | ConvertTo-Json -Compress

    $done = $false
    for ($try = 1; $try -le 3; $try++) {
        try {
            Invoke-RestMethod -Uri "$api/repos/$repo/contents/$enc" -Method Put -Headers $headers -Body $json -ContentType 'application/json' -TimeoutSec 90 | Out-Null
            $done = $true; break
        } catch {
            Start-Sleep -Seconds (2 * $try)
        }
    }
    if ($done) { $ok++; Write-Output "  OK   $rel" } else { $fail++; Write-Output "  FAIL $rel" }
}

Write-Output "uploaded=$ok failed=$fail"
