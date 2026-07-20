param(
  [switch]$SkipFrontendExport,
  [switch]$SkipZip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Windows PowerShell does not always load the base archive types as a dependency
# of FileSystem, so load both assemblies before using ZipArchiveMode.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceDir = Join-Path $repoRoot "workspace"
$frontendDir = Join-Path $repoRoot "frontend"
$backendDir = Join-Path $repoRoot "backend"
$runtimeDir = Join-Path $workspaceDir "runtime"
$backendFrontendDist = Join-Path $backendDir "frontend_dist"
$releaseDir = Join-Path $workspaceDir "release"
$portableDir = Join-Path $releaseDir "AsteriaAnalyst-portable"
$portableRuntimeRoot = Join-Path $portableDir "runtime"
$zipPath = Join-Path $releaseDir "AsteriaAnalyst-portable.zip"
$buildStamp = Get-Date -Format "yyyyMMddHHmmss"
$portableBuildDir = Join-Path $releaseDir "AsteriaAnalyst-portable.build-$buildStamp"
$portableBuildRuntimeRoot = Join-Path $portableBuildDir "runtime"
$portableBackupDir = Join-Path $releaseDir "AsteriaAnalyst-portable.previous-$buildStamp"
$portableRunnerPath = Join-Path $portableDir "backend\\run_desktop.py"
$portableGuideSource = Join-Path $repoRoot "docs\\portable-user-guide.zh-CN.md"
$sourceVenvPython = Join-Path $backendDir ".venv\\Scripts\\python.exe"
$sourceVenvConfig = Join-Path $backendDir ".venv\\pyvenv.cfg"
$sourceVenvSitePackages = Join-Path $backendDir ".venv\\Lib\\site-packages"

function Copy-Tree {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination,
    [string[]]$ExcludedDirectories = @()
  )

  if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source directory not found: $Source"
  }

  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  $robocopyArgs = @(
    $Source,
    $Destination,
    "/MIR",
    "/R:2",
    "/W:1",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NP",
    "/XJ"
  )

  $excludedPaths = @("__pycache__") + @($ExcludedDirectories | Where-Object { $_ })
  if ($excludedPaths.Count) {
    $robocopyArgs += "/XD"
    $robocopyArgs += $excludedPaths
  }

  & robocopy @robocopyArgs | Out-Null
  if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed while copying $Source to $Destination (exit code $LASTEXITCODE)."
  }
}

function New-ZipArchive {
  param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory,
    [Parameter(Mandatory = $true)][string]$DestinationPath
  )

  if (-not (Test-Path -LiteralPath $SourceDirectory)) {
    throw "Source directory not found for zip archive: $SourceDirectory"
  }

  if (Test-Path -LiteralPath $DestinationPath) {
    Remove-Item -LiteralPath $DestinationPath -Force
  }

  $sourceRoot = (Resolve-Path -LiteralPath $SourceDirectory).ProviderPath
  $sourceRootPrefix = "$($sourceRoot.TrimEnd('\'))\"
  $archive = [System.IO.Compression.ZipFile]::Open(
    $DestinationPath,
    [System.IO.Compression.ZipArchiveMode]::Create
  )

  try {
    Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force -File | ForEach-Object {
      $relativePath = $_.FullName.Substring($sourceRootPrefix.Length).Replace('\', '/')
      if ($relativePath -match '^backend/.*\.(?:log|tmp|lock)$') {
        return
      }

      [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive,
        $_.FullName,
        $relativePath,
        [System.IO.Compression.CompressionLevel]::Optimal
      ) | Out-Null
    }
  } catch {
    $archive.Dispose()
    if (Test-Path -LiteralPath $DestinationPath) {
      Remove-Item -LiteralPath $DestinationPath -Force -ErrorAction SilentlyContinue
    }
    throw
  }

  $archive.Dispose()
}

function Get-PortableProcessIds {
  $portablePythonPaths = @(
    (Join-Path $portableRuntimeRoot "python\\python.exe"),
    (Join-Path $portableRuntimeRoot "python\\pythonw.exe"),
    (Join-Path $portableDir "backend\\.venv\\Scripts\\python.exe"),
    (Join-Path $portableDir "backend\\.venv\\Scripts\\pythonw.exe")
  ) | ForEach-Object { $_.ToLowerInvariant() }
  $processIds = @()
  $escapedRunner = $null

  if (Test-Path -LiteralPath $portableRunnerPath) {
    $escapedRunner = [regex]::Escape($portableRunnerPath)
  }

  $runtimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      ($_.ExecutablePath -and $portablePythonPaths -contains $_.ExecutablePath.ToLowerInvariant()) -or
      ($escapedRunner -and [string]$_.CommandLine -match $escapedRunner)
    })
  if ($runtimeProcesses.Count) {
    $processIds += $runtimeProcesses.ProcessId
  }

  try {
    $listenerPids = @(Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction Stop |
      Select-Object -ExpandProperty OwningProcess -Unique)
    if ($listenerPids.Count) {
      $listenerProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
          $listenerPids -contains $_.ProcessId -and (
            ($_.ExecutablePath -and $portablePythonPaths -contains $_.ExecutablePath.ToLowerInvariant()) -or
            ($escapedRunner -and [string]$_.CommandLine -match $escapedRunner)
          )
        })
      if ($listenerProcesses.Count) {
        $processIds += $listenerProcesses.ProcessId
      }
    }
  } catch {
  }

  return @($processIds | Sort-Object -Unique -Descending)
}

function Stop-PortableProcesses {
  $processIds = @(Get-PortableProcessIds)
  if (-not $processIds.Count) {
    return
  }

  Write-Host "==> Stopping portable processes: $($processIds -join ', ')"
  foreach ($processId in $processIds) {
    try {
      Stop-Process -Id $processId -Force -ErrorAction Stop
    } catch {
    }
  }

  $deadline = (Get-Date).AddSeconds(20)
  while ((Get-Date) -lt $deadline) {
    $stillRunning = @(
      $processIds | Where-Object {
        Get-Process -Id $_ -ErrorAction SilentlyContinue
      }
    )

    $portBusy = $false
    try {
      $portBusy = [bool](Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction Stop | Select-Object -First 1)
    } catch {
      $portBusy = $false
    }

    if (-not $stillRunning.Count -and -not $portBusy) {
      return
    }

    Start-Sleep -Milliseconds 500
  }

  Start-Sleep -Seconds 2
}

function Remove-PortableDirectory {
  if (-not (Test-Path -LiteralPath $portableDir)) {
    return
  }

  $deadline = (Get-Date).AddSeconds(30)
  while ($true) {
    Stop-PortableProcesses

    try {
      Remove-Item -LiteralPath $portableDir -Recurse -Force -ErrorAction Stop
      return
    } catch {
      if (-not (Test-Path -LiteralPath $portableDir)) {
        return
      }

      $backendDirPath = Join-Path $portableDir "backend"
      if (Test-Path -LiteralPath $backendDirPath) {
        Get-ChildItem -LiteralPath $backendDirPath -File -ErrorAction SilentlyContinue |
          Where-Object { $_.Extension -in @(".log", ".tmp", ".lock") } |
          ForEach-Object {
            try {
              Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop
            } catch {
            }
          }
      }

      if ((Get-Date) -ge $deadline) {
        throw
      }

      Start-Sleep -Milliseconds 750
    }
  }
}

function Resolve-BasePythonHome {
  if (Test-Path -LiteralPath $sourceVenvConfig) {
    $homeLine = Get-Content -LiteralPath $sourceVenvConfig |
      Where-Object { $_ -match '^home\s*=' } |
      Select-Object -First 1
    if ($homeLine) {
      $sourceHome = ($homeLine -split '=', 2)[1].Trim()
      if (Test-Path -LiteralPath (Join-Path $sourceHome "python.exe")) {
        return $sourceHome
      }
    }
  }

  if (Test-Path -LiteralPath $sourceVenvPython) {
    $basePrefix = (& $sourceVenvPython -c "import sys; print(sys.base_prefix)")
    if ($LASTEXITCODE -eq 0) {
      $sourceHome = ($basePrefix | Select-Object -First 1).Trim()
      if ($sourceHome -and (Test-Path -LiteralPath (Join-Path $sourceHome "python.exe"))) {
        return $sourceHome
      }
    }
  }

  throw "Unable to resolve the base Python installation for portable packaging."
}

function Build-PortablePythonRuntime {
  param(
    [Parameter(Mandatory = $true)][string]$BackendPortableDir,
    [Parameter(Mandatory = $true)][string]$PortableRuntimeDir
  )

  $portablePythonDir = Join-Path $PortableRuntimeDir "python"
  $portablePython = Join-Path $portablePythonDir "python.exe"
  $portableSitePackages = Join-Path $portablePythonDir "Lib\\site-packages"
  $sourcePythonHome = Resolve-BasePythonHome

  Write-Host "==> Bundling portable Python runtime"
  Copy-Tree -Source $sourcePythonHome -Destination $portablePythonDir -ExcludedDirectories @("site-packages")

  if (-not (Test-Path -LiteralPath $portablePython)) {
    throw "Portable Python runtime was not created: $portablePython"
  }

  if (-not (Test-Path -LiteralPath (Join-Path $portablePythonDir "Lib\\encodings"))) {
    throw "Portable Python runtime is incomplete: stdlib encodings were not copied."
  }

  if (-not (Test-Path -LiteralPath $sourceVenvSitePackages)) {
    throw "Project virtualenv site-packages were not found: $sourceVenvSitePackages"
  }

  if (Test-Path -LiteralPath $portableSitePackages) {
    Remove-Item -LiteralPath $portableSitePackages -Recurse -Force
  }

  Write-Host "==> Copying backend Python packages from project virtualenv"
  Copy-Tree -Source $sourceVenvSitePackages -Destination $portableSitePackages

  Push-Location $BackendPortableDir
  try {
    & $portablePython -c "import app.main, encodings, fastapi, uvicorn, duckdb, pandas, openpyxl, statsmodels, sklearn, seaborn, matplotlib, docx, pypdf, reportlab, requests"
    if ($LASTEXITCODE -ne 0) {
      throw "Portable Python runtime validation failed after copying project dependencies."
    }
  } finally {
    Pop-Location
  }
}

if (-not $SkipFrontendExport) {
  Write-Host "==> Exporting frontend"
  $previousSameOriginApi = [Environment]::GetEnvironmentVariable("NEXT_PUBLIC_API_SAME_ORIGIN", "Process")
  $previousApiBaseUrl = [Environment]::GetEnvironmentVariable("NEXT_PUBLIC_API_BASE_URL", "Process")
  $env:NEXT_PUBLIC_API_SAME_ORIGIN = "1"
  Remove-Item Env:NEXT_PUBLIC_API_BASE_URL -ErrorAction SilentlyContinue
  Push-Location $frontendDir
  try {
    npm run build:export
    if ($LASTEXITCODE -ne 0) {
      throw "Frontend export failed."
    }
  } finally {
    Pop-Location
    if ($null -eq $previousSameOriginApi) {
      Remove-Item Env:NEXT_PUBLIC_API_SAME_ORIGIN -ErrorAction SilentlyContinue
    } else {
      $env:NEXT_PUBLIC_API_SAME_ORIGIN = $previousSameOriginApi
    }
    if ($null -eq $previousApiBaseUrl) {
      Remove-Item Env:NEXT_PUBLIC_API_BASE_URL -ErrorAction SilentlyContinue
    } else {
      $env:NEXT_PUBLIC_API_BASE_URL = $previousApiBaseUrl
    }
  }

  if (Test-Path $backendFrontendDist) {
    Remove-Item -LiteralPath $backendFrontendDist -Recurse -Force
  }
  Copy-Tree -Source (Join-Path $frontendDir "out") -Destination $backendFrontendDist
  if (-not (Test-Path -LiteralPath (Join-Path $backendFrontendDist "analysis.html"))) {
    throw "Frontend export is missing analysis.html."
  }
  # A static export cannot be served by `next start`; force the source launcher
  # to build its server bundle again on its next use.
  Remove-Item -LiteralPath (Join-Path $frontendDir ".next\.asteria-api-base-url") -Force -ErrorAction SilentlyContinue
} elseif (-not (Test-Path -LiteralPath $backendFrontendDist)) {
  throw "SkipFrontendExport was specified but backend frontend_dist does not exist: $backendFrontendDist"
} else {
  Write-Host "==> Reusing existing frontend export"
}

if (Test-Path $portableBuildDir) {
  Remove-Item -LiteralPath $portableBuildDir -Recurse -Force
}
if (Test-Path $portableBackupDir) {
  Remove-Item -LiteralPath $portableBackupDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $portableBuildDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $portableBuildDir "backend") | Out-Null
New-Item -ItemType Directory -Force -Path $portableBuildRuntimeRoot | Out-Null

Write-Host "==> Assembling portable package"
Copy-Tree -Source (Join-Path $backendDir "app") -Destination (Join-Path $portableBuildDir "backend\\app")
Copy-Tree -Source $backendFrontendDist -Destination (Join-Path $portableBuildDir "backend\\frontend_dist")
Copy-Item -LiteralPath (Join-Path $backendDir "run_desktop.py") -Destination (Join-Path $portableBuildDir "backend\\run_desktop.py") -Force
Copy-Item -LiteralPath (Join-Path $backendDir "requirements.txt") -Destination (Join-Path $portableBuildDir "backend\\requirements.txt") -Force
if (Test-Path $runtimeDir) {
  Copy-Tree -Source $runtimeDir -Destination $portableBuildRuntimeRoot
}
Build-PortablePythonRuntime -BackendPortableDir (Join-Path $portableBuildDir "backend") -PortableRuntimeDir $portableBuildRuntimeRoot

$startBat = @'
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-asteria.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
'@
Set-Content -LiteralPath (Join-Path $portableBuildDir "start-asteria.bat") -Value $startBat -Encoding ASCII

$startPs1 = @'
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$runtimeDir = Join-Path $scriptDir "runtime"
$python = Join-Path $runtimeDir "python\python.exe"
$pythonw = Join-Path $runtimeDir "python\pythonw.exe"
$runner = Join-Path $backendDir "run_desktop.py"
$preferredPort = 8787
$stdoutLog = Join-Path $backendDir "desktop-start.out.log"
$stderrLog = Join-Path $backendDir "desktop-start.err.log"

if (-not (Test-Path -LiteralPath $runner)) {
    throw "Asteria backend runner not found: $runner"
}

if (Test-Path -LiteralPath $python) {
    $launcher = $python
} elseif (Test-Path -LiteralPath $pythonw) {
    $launcher = $pythonw
} else {
    throw "Asteria Python runtime not found."
}

function Test-AsteriaHealth {
    param([Parameter(Mandatory = $true)][string]$HealthUrl)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 3
        return $response.Content -like '*"status":"ok"*'
    } catch {
        return $false
    }
}

function Wait-AsteriaHealth {
    param(
        [Parameter(Mandatory = $true)][string]$HealthUrl,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-AsteriaHealth -HealthUrl $HealthUrl) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return $false
}

function Test-PortAvailable {
    param([Parameter(Mandatory = $true)][int]$Port)

    try {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -eq $listener
    } catch {
        return $true
    }
}

function Resolve-AvailablePort {
    param([int]$PreferredPort = 8787)

    foreach ($candidatePort in $PreferredPort..($PreferredPort + 30)) {
        if (Test-PortAvailable -Port $candidatePort) {
            return $candidatePort
        }
    }

    throw "No available local port was found between $PreferredPort and $($PreferredPort + 30)."
}

function Get-ManagedPortableProcesses {
    $escapedRunner = [regex]::Escape($runner)
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { [string]$_.CommandLine -match $escapedRunner } |
        Sort-Object ProcessId -Descending)
}

function Stop-ManagedPortableProcesses {
    $processes = @(Get-ManagedPortableProcesses)
    if (-not $processes.Count) {
        return
    }

    Write-Host "Stopping stale Asteria portable process(es): $($processes.ProcessId -join ', ')" -ForegroundColor Yellow
    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } catch {
        }
    }

    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        if (-not (@(Get-ManagedPortableProcesses).Count)) {
            return
        }
        Start-Sleep -Milliseconds 500
    }
}

function Get-ManagedPortablePort {
    $processIds = @(Get-ManagedPortableProcesses | Select-Object -ExpandProperty ProcessId)
    if (-not $processIds.Count) {
        return $null
    }

    try {
        $listener = Get-NetTCPConnection -State Listen -ErrorAction Stop |
            Where-Object { $processIds -contains $_.OwningProcess } |
            Sort-Object LocalPort |
            Select-Object -First 1
        if ($listener) {
            return [int]$listener.LocalPort
        }
    } catch {
    }

    return $null
}

$env:ASTERIA_DATA_DIR = Join-Path $env:APPDATA "AsteriaAnalyst"
$env:ASTERIA_LAUNCH_PATH = "/analysis"
$env:ASTERIA_OPEN_BROWSER = "0"
if (Test-Path -LiteralPath (Join-Path $scriptDir "runtime\R-4.5.3\bin\Rscript.exe")) {
    $env:ASTERIA_RSCRIPT_PATH = Join-Path $scriptDir "runtime\R-4.5.3\bin\Rscript.exe"
}

$existingPort = Get-ManagedPortablePort
$port = if ($existingPort) { $existingPort } else { Resolve-AvailablePort -PreferredPort $preferredPort }
$healthUrl = "http://127.0.0.1:$port/health"
$appUrl = "http://127.0.0.1:$port/analysis"
$env:ASTERIA_PORT = [string]$port

if (Test-AsteriaHealth -HealthUrl $healthUrl) {
    Start-Process $appUrl
    exit 0
}

if ((@(Get-ManagedPortableProcesses)).Count) {
    if (Wait-AsteriaHealth -HealthUrl $healthUrl -TimeoutSeconds 20) {
        Start-Process $appUrl
        exit 0
    }

    Stop-ManagedPortableProcesses
    $port = Resolve-AvailablePort -PreferredPort $preferredPort
    $healthUrl = "http://127.0.0.1:$port/health"
    $appUrl = "http://127.0.0.1:$port/analysis"
    $env:ASTERIA_PORT = [string]$port
}

Remove-Item -LiteralPath $stdoutLog, $stderrLog -ErrorAction SilentlyContinue
# Start-Process flattens argument arrays, so the script path must carry its
# own quotes when the portable folder is extracted under a path with spaces.
Start-Process -FilePath $launcher `
    -ArgumentList ('"{0}"' -f $runner) `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden | Out-Null

if (-not (Wait-AsteriaHealth -HealthUrl $healthUrl -TimeoutSeconds 60)) {
    Write-Host "Asteria Analyst startup timed out. Check logs:" -ForegroundColor Red
    Write-Host "  $stdoutLog"
    Write-Host "  $stderrLog"
    exit 1
}

Start-Process $appUrl
'@
Set-Content -LiteralPath (Join-Path $portableBuildDir "start-asteria.ps1") -Value $startPs1 -Encoding UTF8

$guide = @'
Asteria Analyst Portable

1. Double-click start-asteria.bat
2. Your browser will open the local analysis workspace automatically
3. Basic spreadsheet analysis works locally without an API key
4. Configure an API key, model, and relay/Base URL only before using AI-assisted report features
5. If runtime\R-4.5.3 exists, Rscript will default to the bundled runtime automatically
6. Upload Excel/CSV files and start analyzing
7. Read 使用指南.zh-CN.md for the complete Chinese offline guide

All user data and runtime settings are stored under:
%APPDATA%\AsteriaAnalyst
'@
Set-Content -LiteralPath (Join-Path $portableBuildDir "USER-GUIDE.txt") -Value $guide -Encoding UTF8

if (-not (Test-Path -LiteralPath $portableGuideSource)) {
  throw "Portable Chinese guide not found: $portableGuideSource"
}
Copy-Item -LiteralPath $portableGuideSource -Destination (Join-Path $portableBuildDir "使用指南.zh-CN.md") -Force

Write-Host "==> Publishing portable package"
Stop-PortableProcesses
if (Test-Path $portableDir) {
  Move-Item -LiteralPath $portableDir -Destination $portableBackupDir
}
Move-Item -LiteralPath $portableBuildDir -Destination $portableDir
if (Test-Path $portableBackupDir) {
  Remove-Item -LiteralPath $portableBackupDir -Recurse -Force
}

if ($SkipZip) {
  Write-Host "Portable package ready:"
  Write-Host "  Folder: $portableDir"
  Write-Host "  Zip:    skipped"
} else {
  if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
  }

  Write-Host "==> Creating zip archive"
  New-ZipArchive -SourceDirectory $portableDir -DestinationPath $zipPath

  Write-Host "Portable package ready:"
  Write-Host "  Folder: $portableDir"
  Write-Host "  Zip:    $zipPath"
}
