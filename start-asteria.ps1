param(
    [ValidateRange(1, 65535)]
    [int]$BackendPort = 8000,
    [ValidateRange(1, 65535)]
    [int]$FrontendPort = 3000,
    [string]$RoutePath = "/analysis",
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if ($BackendPort -eq $FrontendPort) {
    throw "BackendPort and FrontendPort must be different."
}

if ([string]::IsNullOrWhiteSpace($RoutePath)) {
    $RoutePath = "/analysis"
}
if (-not $RoutePath.StartsWith("/")) {
    $RoutePath = "/$RoutePath"
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$logDir = Join-Path $repoRoot "logs\launcher"
$venvDir = Join-Path $backendDir ".venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$requirementsPath = Join-Path $backendDir "requirements.txt"
$packageJsonPath = Join-Path $frontendDir "package.json"
$packageLockPath = Join-Path $frontendDir "package-lock.json"
$nextCli = Join-Path $frontendDir "node_modules\next\dist\bin\next"
$buildIdPath = Join-Path $frontendDir ".next\BUILD_ID"
$frontendApiBaseMarkerPath = Join-Path $frontendDir ".next\.asteria-api-base-url"
$script:FrontendBuildMarker = ""
$script:UseDevelopmentFrontend = $false

$backendPortWasSpecified = $PSBoundParameters.ContainsKey("BackendPort")
$frontendPortWasSpecified = $PSBoundParameters.ContainsKey("FrontendPort")

function Resolve-Tool {
    param([string[]]$Names)

    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }

    return $null
}

function Get-PythonVersion {
    param([string]$Command, [string[]]$Arguments = @())

    try {
        $output = @(& $Command @($Arguments + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")) 2>$null)
        if ($LASTEXITCODE -ne 0 -or -not $output.Count) {
            return $null
        }
        return [version]([string]$output[0]).Trim()
    } catch {
        return $null
    }
}

function Resolve-SystemPython {
    $candidates = @(
        [pscustomobject]@{ Command = "py.exe"; Arguments = @("-3") },
        [pscustomobject]@{ Command = "python.exe"; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }
        $version = Get-PythonVersion -Command $candidate.Command -Arguments $candidate.Arguments
        if ($version -and $version -ge [version]"3.11") {
            return $candidate
        }
    }

    return $null
}

function Get-NodeVersion {
    param([string]$Node)

    try {
        $output = @(& $Node "--version" 2>$null)
        if ($LASTEXITCODE -ne 0 -or -not $output.Count) {
            return $null
        }
        return [version](([string]$output[0]).Trim().TrimStart("v"))
    } catch {
        return $null
    }
}

function Import-LocalEnvironment {
    $envFile = Join-Path $repoRoot ".env"
    if (-not (Test-Path -LiteralPath $envFile)) {
        return
    }

    foreach ($rawLine in Get-Content -LiteralPath $envFile) {
        $line = [string]$rawLine
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#")) {
            continue
        }
        $match = [regex]::Match($line, "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
        if (-not $match.Success) {
            continue
        }
        $name = $match.Groups[1].Value
        $value = $match.Groups[2].Value.Trim()
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Test-PortListening {
    param([int]$Port)

    try {
        return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1)
    } catch {
        return $false
    }
}

function Get-ListeningProcessDetails {
    param([int]$Port)

    try {
        $processIds = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique)
        if (-not $processIds.Count) {
            return @()
        }
        return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessId -in $processIds } |
            Select-Object ProcessId, ParentProcessId, CommandLine)
    } catch {
        return @()
    }
}

function Test-ManagedListener {
    param(
        [object[]]$Details,
        [string[]]$ExpectedCommandPatterns
    )

    $items = @($Details | Where-Object { $_ })
    if (-not $items.Count) {
        return $false
    }

    foreach ($item in $items) {
        $commandLine = [string]$item.CommandLine
        if (-not $commandLine) {
            return $false
        }
        $matchesExpected = $false
        foreach ($pattern in $ExpectedCommandPatterns) {
            if ($pattern -and $commandLine -match $pattern) {
                $matchesExpected = $true
                break
            }
        }
        if (-not $matchesExpected) {
            return $false
        }
    }

    return $true
}

function Get-ProcessTreeIds {
    param([int[]]$RootProcessIds)

    $roots = @($RootProcessIds | Where-Object { $_ } | Select-Object -Unique)
    if (-not $roots.Count) {
        return @()
    }

    $allProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    $pending = [System.Collections.Generic.Queue[int]]::new()
    $seen = [System.Collections.Generic.HashSet[int]]::new()
    $result = New-Object System.Collections.Generic.List[int]
    foreach ($root in $roots) {
        $pending.Enqueue([int]$root)
    }

    while ($pending.Count -gt 0) {
        $current = $pending.Dequeue()
        if (-not $seen.Add($current)) {
            continue
        }
        $result.Add($current)
        foreach ($child in $allProcesses | Where-Object { $_.ParentProcessId -eq $current }) {
            $pending.Enqueue([int]$child.ProcessId)
        }
    }

    return @($result | Sort-Object -Descending)
}

function Stop-ManagedListener {
    param([object[]]$Details)

    $rootIds = @($Details | Where-Object { $_.ProcessId } | Select-Object -ExpandProperty ProcessId -Unique)
    foreach ($processId in Get-ProcessTreeIds -RootProcessIds $rootIds) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-LaunchPort {
    param(
        [string]$Name,
        [int]$PreferredPort,
        [bool]$WasSpecified,
        [string[]]$ExpectedCommandPatterns
    )

    if (-not (Test-PortListening -Port $PreferredPort)) {
        return $PreferredPort
    }

    $details = Get-ListeningProcessDetails -Port $PreferredPort
    if (Test-ManagedListener -Details $details -ExpectedCommandPatterns $ExpectedCommandPatterns) {
        return $PreferredPort
    }

    if ($WasSpecified) {
        $detailText = ($details | ForEach-Object { "PID $($_.ProcessId): $($_.CommandLine)" }) -join "`n"
        throw "$Name port $PreferredPort is used by another process. Choose a different port or close it.`n$detailText"
    }

    for ($offset = 1; $offset -le 30; $offset++) {
        $candidate = $PreferredPort + $offset
        if ($candidate -le 65535 -and -not (Test-PortListening -Port $candidate)) {
            Write-Host "$Name port $PreferredPort is busy; using $candidate instead." -ForegroundColor Yellow
            return $candidate
        }
    }

    throw "Could not find a free $Name port near $PreferredPort."
}

function Wait-HttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 90,
        [int]$RequestTimeoutSeconds = 15,
        [string]$ExpectedContent = ""
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $RequestTimeoutSeconds
            $isSuccess = $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
            $hasExpectedContent = -not $ExpectedContent -or ([string]$response.Content).Contains($ExpectedContent)
            if ($isSuccess -and $hasExpectedContent) {
                return $true
            }
            $lastError = "HTTP $($response.StatusCode)"
        } catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 1
    }

    if ($lastError) {
        Write-Host "Last readiness error for ${Url}: $lastError" -ForegroundColor DarkYellow
    }
    return $false
}

function Test-BackendRuntime {
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        return $false
    }

    try {
        & $pythonExe -c "import sys, fastapi, pandas, uvicorn; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Ensure-BackendRuntime {
    if (-not (Test-Path -LiteralPath $requirementsPath)) {
        throw "Backend requirements file not found: $requirementsPath"
    }
    if (Test-BackendRuntime) {
        return
    }

    if (-not (Test-Path -LiteralPath $pythonExe)) {
        $bootstrap = Resolve-SystemPython
        if (-not $bootstrap) {
            throw "Python 3.11+ was not found. Install Python 3.11+ and run start-asteria.cmd again."
        }
        Write-Host "Creating backend virtual environment..." -ForegroundColor Yellow
        & $bootstrap.Command @($bootstrap.Arguments + @("-m", "venv", $venvDir))
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pythonExe)) {
            throw "Failed to create the backend virtual environment at $venvDir"
        }
    } else {
        $venvVersion = Get-PythonVersion -Command $pythonExe
        if (-not $venvVersion -or $venvVersion -lt [version]"3.11") {
            throw "The existing backend .venv does not use Python 3.11+. Remove $venvDir and run start-asteria.cmd again."
        }
        Write-Host "Repairing backend dependencies..." -ForegroundColor Yellow
    }

    & $pythonExe -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update pip in $venvDir"
    }
    & $pythonExe -m pip install --disable-pip-version-check -r $requirementsPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-BackendRuntime)) {
        throw "Failed to install backend requirements."
    }
}

function Ensure-FrontendDependencies {
    if (-not (Test-Path -LiteralPath $packageJsonPath)) {
        throw "Frontend package.json not found: $packageJsonPath"
    }
    if (-not $script:NodeExe) {
        throw "Node.js 20.9+ was not found. Install Node.js 20.9+ and run start-asteria.cmd again."
    }
    if (-not $script:NpmCmd) {
        throw "npm was not found. Reinstall Node.js 20.9+ and run start-asteria.cmd again."
    }

    $nodeVersion = Get-NodeVersion -Node $script:NodeExe
    if (-not $nodeVersion -or $nodeVersion -lt [version]"20.9.0") {
        throw "Node.js 20.9+ is required. Detected: $nodeVersion"
    }

    $nodeModulesDir = Join-Path $frontendDir "node_modules"
    $installedLock = Join-Path $nodeModulesDir ".package-lock.json"
    $needsInstall = -not (Test-Path -LiteralPath $nextCli)
    if (-not $needsInstall -and (Test-Path -LiteralPath $packageLockPath)) {
        $needsInstall = -not (Test-Path -LiteralPath $installedLock) -or
            ((Get-Item -LiteralPath $packageLockPath).LastWriteTimeUtc -gt (Get-Item -LiteralPath $installedLock).LastWriteTimeUtc)
    }
    if (-not $needsInstall) {
        return
    }

    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try {
        if (Test-Path -LiteralPath $packageLockPath) {
            & $script:NpmCmd ci --no-audit --no-fund
        } else {
            & $script:NpmCmd install --no-audit --no-fund
        }
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $nextCli)) {
            throw "Frontend dependency installation failed."
        }
    } finally {
        Pop-Location
    }
}

function Get-FrontendBuildInputs {
    $inputs = @($packageJsonPath, $packageLockPath, (Join-Path $frontendDir "next.config.ts"), (Join-Path $frontendDir "postcss.config.mjs"))
    foreach ($directory in @((Join-Path $frontendDir "src"), (Join-Path $frontendDir "public"))) {
        if (Test-Path -LiteralPath $directory) {
            $inputs += @(Get-ChildItem -LiteralPath $directory -Recurse -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
        }
    }
    return @($inputs | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
}

function Stop-ProcessTree {
    param([int]$RootProcessId)

    foreach ($processId in Get-ProcessTreeIds -RootProcessIds @($RootProcessId)) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-FrontendBuild {
    $needsBuild = -not (Test-Path -LiteralPath $buildIdPath)
    if (-not $needsBuild) {
        $recordedBuildMarker = if (Test-Path -LiteralPath $frontendApiBaseMarkerPath) {
            (Get-Content -LiteralPath $frontendApiBaseMarkerPath -Raw).Trim()
        } else {
            ""
        }
        if ($recordedBuildMarker -ne $script:FrontendBuildMarker) {
            $needsBuild = $true
        }
    }
    if (-not $needsBuild) {
        $buildTime = (Get-Item -LiteralPath $buildIdPath).LastWriteTimeUtc
        foreach ($input in Get-FrontendBuildInputs) {
            if ((Get-Item -LiteralPath $input).LastWriteTimeUtc -gt $buildTime) {
                $needsBuild = $true
                break
            }
        }
    }

    if (-not $needsBuild) {
        $script:UseDevelopmentFrontend = $false
        Write-Host "Frontend production build is up to date." -ForegroundColor DarkGray
        return
    }

    Write-Host "Building the frontend production bundle..." -ForegroundColor Yellow
    $buildOut = Join-Path $logDir "frontend-build.out.log"
    $buildErr = Join-Path $logDir "frontend-build.err.log"
    Remove-Item -LiteralPath $buildIdPath -Force -ErrorAction SilentlyContinue
    $buildProcess = Start-Process -FilePath $script:NpmCmd `
        -ArgumentList "run", "build" `
        -WorkingDirectory $frontendDir `
        -RedirectStandardOutput $buildOut `
        -RedirectStandardError $buildErr `
        -WindowStyle Hidden `
        -PassThru

    $buildCompleted = $buildProcess.WaitForExit(600000)
    if (-not $buildCompleted -or -not $buildProcess.HasExited) {
        Stop-ProcessTree -RootProcessId $buildProcess.Id
        Write-Host "Production build timed out; using the actual Next.js development server." -ForegroundColor Yellow
        $script:UseDevelopmentFrontend = $true
        return
    }
    if (-not (Test-Path -LiteralPath $buildIdPath)) {
        Write-Host "Production build failed; using the actual Next.js development server." -ForegroundColor Yellow
        $script:UseDevelopmentFrontend = $true
        return
    }

    $script:UseDevelopmentFrontend = $false
    Set-Content -LiteralPath $frontendApiBaseMarkerPath -Value $script:FrontendBuildMarker -Encoding ASCII
}

function Ensure-Service {
    param(
        [string]$Name,
        [int]$Port,
        [string]$HealthUrl,
        [string]$ExpectedContent,
        [string[]]$ExpectedCommandPatterns,
        [int]$TimeoutSeconds,
        [scriptblock]$Starter
    )

    if (Test-PortListening -Port $Port) {
        $details = Get-ListeningProcessDetails -Port $Port
        if (-not (Test-ManagedListener -Details $details -ExpectedCommandPatterns $ExpectedCommandPatterns)) {
            $detailText = ($details | ForEach-Object { "PID $($_.ProcessId): $($_.CommandLine)" }) -join "`n"
            throw "$Name port $Port is in use by an unrelated process. The launcher will not stop it.`n$detailText"
        }
        if (Wait-HttpReady -Url $HealthUrl -TimeoutSeconds 10 -ExpectedContent $ExpectedContent) {
            Write-Host "$Name is already running and verified." -ForegroundColor DarkGray
            return $null
        }

        Write-Host "Restarting an unhealthy $Name..." -ForegroundColor Yellow
        Stop-ManagedListener -Details $details
        Start-Sleep -Seconds 1
    }

    $process = & $Starter
    if (-not (Wait-HttpReady -Url $HealthUrl -TimeoutSeconds $TimeoutSeconds -ExpectedContent $ExpectedContent)) {
        throw "$Name did not become ready at $HealthUrl. Check $logDir for startup logs."
    }
    return $process
}

if (-not (Test-Path -LiteralPath $backendDir) -or -not (Test-Path -LiteralPath $frontendDir)) {
    throw "This launcher must be run from the Asteria repository root."
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
Import-LocalEnvironment

$script:NodeExe = Resolve-Tool @("node.exe")
$script:NpmCmd = Resolve-Tool @("npm.cmd", "npm")

$backendPatterns = @("uvicorn.+app\.main:app")
$frontendPatterns = @([regex]::Escape($frontendDir), "next\\dist\\bin\\next")
$backendPort = Resolve-LaunchPort -Name "Backend" -PreferredPort $BackendPort -WasSpecified $backendPortWasSpecified -ExpectedCommandPatterns $backendPatterns
$frontendPort = Resolve-LaunchPort -Name "Frontend" -PreferredPort $FrontendPort -WasSpecified $frontendPortWasSpecified -ExpectedCommandPatterns $frontendPatterns

if ($backendPort -eq $frontendPort) {
    throw "Backend and frontend resolved to the same port. Choose explicit distinct ports."
}

$backendHealthUrl = "http://127.0.0.1:$backendPort/health"
$targetUrl = "http://127.0.0.1:$frontendPort$RoutePath"
$frontendHealthUrl = "http://127.0.0.1:$frontendPort/analysis"
$backendOut = Join-Path $logDir "backend-$backendPort.out.log"
$backendErr = Join-Path $logDir "backend-$backendPort.err.log"
$frontendOut = Join-Path $logDir "frontend-$frontendPort.out.log"
$frontendErr = Join-Path $logDir "frontend-$frontendPort.err.log"

# Make the browser bundle talk to the paired backend, including when fallback ports were selected.
$script:FrontendApiBaseUrl = "http://127.0.0.1:$backendPort"
$script:FrontendBuildMarker = "server|$script:FrontendApiBaseUrl"
$env:NEXT_PUBLIC_API_BASE_URL = $script:FrontendApiBaseUrl
$env:NEXT_PUBLIC_API_SAME_ORIGIN = ""

Ensure-BackendRuntime
Ensure-FrontendDependencies
Ensure-FrontendBuild

Write-Host "Starting Asteria..." -ForegroundColor Cyan
Write-Host "Backend:  $backendHealthUrl" -ForegroundColor DarkGray
Write-Host "Frontend: $targetUrl" -ForegroundColor DarkGray

$backendProc = Ensure-Service -Name "Backend API" -Port $backendPort -HealthUrl $backendHealthUrl -ExpectedContent '"status":"ok"' -ExpectedCommandPatterns $backendPatterns -TimeoutSeconds 90 -Starter {
    Start-Process -FilePath $pythonExe `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$backendPort" `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr `
        -WindowStyle Hidden `
        -PassThru
}

$frontendProc = Ensure-Service -Name "Frontend UI" -Port $frontendPort -HealthUrl $frontendHealthUrl -ExpectedContent "Asteria" -ExpectedCommandPatterns $frontendPatterns -TimeoutSeconds 420 -Starter {
    if ($script:UseDevelopmentFrontend) {
        return Start-Process -FilePath $script:NodeExe `
            -ArgumentList $nextCli, "dev", "--webpack", "--hostname", "127.0.0.1", "--port", "$frontendPort" `
            -WorkingDirectory $frontendDir `
            -RedirectStandardOutput $frontendOut `
            -RedirectStandardError $frontendErr `
            -WindowStyle Hidden `
            -PassThru
    }

    return Start-Process -FilePath $script:NodeExe `
        -ArgumentList $nextCli, "start", "--hostname", "127.0.0.1", "--port", "$frontendPort" `
        -WorkingDirectory $frontendDir `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr `
        -WindowStyle Hidden `
        -PassThru
}

if (-not (Wait-HttpReady -Url $targetUrl -TimeoutSeconds 90 -ExpectedContent "Asteria")) {
    throw "Asteria target page did not become ready: $targetUrl"
}

if (-not $NoBrowser) {
    Start-Process $targetUrl
}

Write-Host ""
Write-Host "Asteria is ready." -ForegroundColor Green
Write-Host "Open: $targetUrl"
Write-Host "Logs: $logDir"
if ($backendProc) {
    Write-Host "Backend PID: $($backendProc.Id)"
}
if ($frontendProc) {
    Write-Host "Frontend PID: $($frontendProc.Id)"
}
