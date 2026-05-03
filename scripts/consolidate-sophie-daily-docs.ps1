param(
  [string]$TargetRoot = "C:\Users\user\Desktop\蘇菲每日文檔"
)

$ErrorActionPreference = "Stop"

$sources = @(
  @{ Name = "sophie-agent-content"; Path = "C:\Users\user\sophie-agent\content" },
  @{ Name = "sophie-agent-claude-docs"; Path = "C:\Users\user\sophie-agent\克勞德文檔" },
  @{ Name = "desktop-sophie-daily"; Path = "C:\Users\user\Desktop\Sophie\outputs\daily" },
  @{ Name = "desktop-sophie-traffic"; Path = "C:\Users\user\Desktop\Sophie\outputs\traffic_maps" },
  @{ Name = "desktop-lida-deliverables"; Path = "C:\Users\user\Desktop\麗得行銷\deliverables" },
  @{ Name = "desktop-lida-extracted"; Path = "C:\Users\user\Desktop\麗得行銷\extracted" },
  @{ Name = "website-docs"; Path = "C:\Users\user\Desktop\網站架設\docs" },
  @{ Name = "website-archive-beehiiv"; Path = "C:\Users\user\Desktop\網站架設\_archive_beehiiv_20260503" },
  @{ Name = "daily-report"; Path = "C:\Users\user\Desktop\sophie-daily-report" },
  @{ Name = "aesthetic-workflows-output"; Path = "C:\Users\user\Desktop\sophie-aesthetic-workflows" },
  @{ Name = "medical-automation-output"; Path = "C:\Users\user\Desktop\醫美自動化工作流" }
)

$extensions = @(".md", ".txt", ".html", ".json")
$ignorePathParts = @(
  "\node_modules\",
  "\browser-data",
  "\.git\",
  "\dist\",
  "\build\",
  "\cache\",
  "\.cache\"
)

$contentNamePattern = "(sophie|蘇菲|菲菲|方格子|vocus|fanggezi|line|threads|ig|instagram|linkedin|tiktok|fb|醫美|美容|整形|電波|音波|肉毒|玻尿酸|水光|線雕|瘦瘦針|外泌體|膠原|再生|療程|發文|貼文|文案|腳本|brief|索引|長文|主文|deliverable|report|dashboard|signals)"

function Get-DateFromText([string]$text) {
  $patterns = @(
    "(20\d{2})[-_./](0[1-9]|1[0-2])[-_./]([0-3]\d)",
    "(20\d{2})(0[1-9]|1[0-2])([0-3]\d)"
  )
  foreach ($pattern in $patterns) {
    $match = [regex]::Match($text, $pattern)
    if ($match.Success) {
      return "{0}-{1}-{2}" -f $match.Groups[1].Value, $match.Groups[2].Value, $match.Groups[3].Value
    }
  }
  return $null
}

function Get-SafeName([string]$name) {
  $safe = $name -replace '[<>:"/\\|?*\x00-\x1F]', '-'
  $safe = $safe -replace '\s+', ' '
  $safe = $safe.Trim()
  if ($safe.Length -gt 160) {
    $ext = [IO.Path]::GetExtension($safe)
    $base = [IO.Path]::GetFileNameWithoutExtension($safe)
    $safe = $base.Substring(0, [Math]::Min(140, $base.Length)) + $ext
  }
  return $safe
}

function Get-RelativePathSafe([string]$base, [string]$full) {
  try {
    return [IO.Path]::GetRelativePath($base, $full)
  } catch {
    return $full.Replace($base, "").TrimStart("\")
  }
}

function Test-UsefulContentFile($file) {
  $ext = [IO.Path]::GetExtension($file.FullName).ToLowerInvariant()
  if ($extensions -notcontains $ext) { return $false }
  foreach ($part in $ignorePathParts) {
    if ($file.FullName -like "*$part*") { return $false }
  }
  if ($file.FullName -like "$TargetRoot*") { return $false }
  if ($file.Name -match "^(package-lock|package|metadata|browsers|deviceDescriptorsSource|ThirdPartyNotices|README|LICENSE|SECURITY|tsconfig)\.") { return $false }
  if ($file.FullName -match $contentNamePattern) { return $true }
  return $false
}

$targetResolvedParent = Split-Path $TargetRoot -Parent
if (-not (Test-Path $targetResolvedParent)) {
  throw "Target parent does not exist: $targetResolvedParent"
}
if (-not ($TargetRoot -like "C:\Users\user\Desktop\蘇菲每日文檔*")) {
  throw "Refusing unexpected target root: $TargetRoot"
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
$indexDir = Join-Path $TargetRoot "_index"
New-Item -ItemType Directory -Force -Path $indexDir | Out-Null

$records = New-Object System.Collections.Generic.List[object]
$copied = 0
$skipped = 0

foreach ($source in $sources) {
  if (-not (Test-Path $source.Path)) { continue }
  $files = Get-ChildItem -LiteralPath $source.Path -Recurse -File -ErrorAction SilentlyContinue
  foreach ($file in $files) {
    if (-not (Test-UsefulContentFile $file)) {
      $skipped += 1
      continue
    }

    $date = Get-DateFromText "$($file.FullName)"
    if (-not $date) {
      $date = $file.LastWriteTime.ToString("yyyy-MM-dd")
    }

    $dayDir = Join-Path $TargetRoot $date
    $materialDir = Join-Path $dayDir "素材"
    New-Item -ItemType Directory -Force -Path $materialDir | Out-Null

    $relative = Get-RelativePathSafe $source.Path $file.FullName
    $flat = Get-SafeName ("{0}__{1}" -f $source.Name, ($relative -replace '[\\/]+', '__'))
    $dest = Join-Path $materialDir $flat

    $i = 2
    while ((Test-Path $dest) -and ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash)) {
      $base = [IO.Path]::GetFileNameWithoutExtension($flat)
      $ext = [IO.Path]::GetExtension($flat)
      $dest = Join-Path $materialDir ("{0}-{1}{2}" -f $base, $i, $ext)
      $i += 1
    }

    Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    $copied += 1

    $records.Add([pscustomobject]@{
      Date = $date
      SourceGroup = $source.Name
      SourcePath = $file.FullName
      ArchivedPath = $dest
      Name = $file.Name
      LastWriteTime = $file.LastWriteTime
      SizeKB = [Math]::Round($file.Length / 1KB, 1)
    })
  }
}

$byDate = $records | Sort-Object Date, SourceGroup, Name | Group-Object Date
foreach ($group in $byDate) {
  $dayDir = Join-Path $TargetRoot $group.Name
  $dayIndex = Join-Path $dayDir "_當日索引.md"
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add("# $($group.Name) 蘇菲發文素材索引")
  $lines.Add("")
  $lines.Add("本索引由 `scripts/consolidate-sophie-daily-docs.ps1` 產生。素材為複製歸檔，原檔未刪除。")
  $lines.Add("")
  foreach ($record in ($group.Group | Sort-Object SourceGroup, Name)) {
    $relativeArchive = Get-RelativePathSafe $dayDir $record.ArchivedPath
    $lines.Add("- [$($record.Name)]($relativeArchive)  ")
    $lines.Add("  來源：``$($record.SourcePath)``  ")
    $lines.Add("  類別：$($record.SourceGroup)；大小：$($record.SizeKB) KB")
  }
  Set-Content -LiteralPath $dayIndex -Value ($lines -join "`r`n") -Encoding UTF8
}

$masterIndex = Join-Path $indexDir "總索引.md"
$master = New-Object System.Collections.Generic.List[string]
$master.Add("# 蘇菲每日文檔總索引")
$master.Add("")
$master.Add("最後整理時間：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$master.Add("")
$master.Add("歸檔根目錄：``$TargetRoot``")
$master.Add("")
$master.Add("共歸檔 $copied 個內容檔；略過 $skipped 個非發文內容或系統檔。")
$master.Add("")
foreach ($group in $byDate) {
  $master.Add("## $($group.Name)")
  $master.Add("")
  $master.Add("- 當日索引：[$($group.Name)\\_當日索引.md](../$($group.Name)/_當日索引.md)")
  $master.Add("- 檔案數：$($group.Count)")
  foreach ($record in ($group.Group | Sort-Object SourceGroup, Name | Select-Object -First 20)) {
    $relativeArchive = Get-RelativePathSafe $TargetRoot $record.ArchivedPath
    $master.Add("  - [$($record.Name)](../$relativeArchive) - $($record.SourceGroup)")
  }
  if ($group.Count -gt 20) {
    $master.Add("  - ...另有 $($group.Count - 20) 個檔案，請看當日索引")
  }
  $master.Add("")
}
Set-Content -LiteralPath $masterIndex -Value ($master -join "`r`n") -Encoding UTF8

$csvPath = Join-Path $indexDir "inventory.csv"
$records | Sort-Object Date, SourceGroup, Name | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

[pscustomobject]@{
  TargetRoot = $TargetRoot
  Copied = $copied
  Skipped = $skipped
  MasterIndex = $masterIndex
  InventoryCsv = $csvPath
}


