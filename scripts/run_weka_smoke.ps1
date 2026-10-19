$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    & "$projectRoot/.venv/Scripts/python.exe" -m faersight.cli weka-smoke `
        --jar "$projectRoot/.tools/weka/weka-stable-3.8.6.jar"
    if ($LASTEXITCODE -ne 0) { throw 'WEKA smoke test failed' }
} finally {
    Pop-Location
}
