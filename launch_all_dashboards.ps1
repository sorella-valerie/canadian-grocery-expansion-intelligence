$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$apps = @(
    @{ Path = "projects\01_canada_affordability_opportunity"; Port = 8511 },
    @{ Path = "projects\02_canadian_healthcare_access"; Port = 8512 },
    @{ Path = "projects\03_newcomer_settlement"; Port = 8513 },
    @{ Path = "projects\04_food_affordability_monitor"; Port = 8514 },
    @{ Path = "projects\05_nonprofit_sustainability"; Port = 8515 },
    @{ Path = "projects\06_global_cost_opportunity"; Port = 8516 }
)

foreach ($app in $apps) {
    $appDirectory = Join-Path $workspace $app.Path
    $alreadyRunning = Get-NetTCPConnection -LocalPort $app.Port -State Listen -ErrorAction SilentlyContinue
    if (-not $alreadyRunning) {
        Start-Process -FilePath python -ArgumentList "-m", "streamlit", "run", "streamlit_app.py", "--server.port=$($app.Port)", "--server.headless=true" -WorkingDirectory $appDirectory -WindowStyle Hidden
    }
}

$hubRunning = Get-NetTCPConnection -LocalPort 8509 -State Listen -ErrorAction SilentlyContinue
if (-not $hubRunning) {
    Start-Process -FilePath python -ArgumentList "-m", "streamlit", "run", "portfolio_hub.py", "--server.port=8509", "--server.headless=true" -WorkingDirectory $workspace -WindowStyle Hidden
}

Start-Process "http://localhost:8509"

