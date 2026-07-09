$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$EnvFile = Join-Path $RootDir ".env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { return }
        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($key -and -not (Get-Item -Path "env:$key" -ErrorAction SilentlyContinue)) {
            Set-Item -Path "env:$key" -Value $value
        }
    }
}

Set-Location $ScriptDir
if (-not (Test-Path "node_modules/@modelcontextprotocol/sdk")) {
    npm install --no-fund --no-audit
}

if (-not $env:HUBSPOT_PAGES_PYTHON) {
    $env:HUBSPOT_PAGES_PYTHON = "py -3"
}

& node (Join-Path $ScriptDir "hubspot-pages-mcp.mjs")
