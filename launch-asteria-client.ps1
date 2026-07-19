param(
    [ValidateRange(1, 65535)]
    [int]$BackendPort = 8000,
    [ValidateRange(1, 65535)]
    [int]$FrontendPort = 3000,
    [string]$RoutePath = "/analysis",
    [switch]$NoBrowser
)

$launcher = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "start-asteria.ps1"
& $launcher @PSBoundParameters
exit $LASTEXITCODE
