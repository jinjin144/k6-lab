param([string[]]$Only)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$k6Executable = 'C:/Program Files/k6/k6.exe'
$env:K6_WEB_DASHBOARD_OPEN = 'false'
$runs = @(
  @{Name='0.1'; Script='01-first-test.js'; Extra=@()},
  @{Name='0.2'; Script='01-first-test.js'; Extra=@('--vus','5','--duration','20s')},
  @{Name='0.3'; Script='01-first-test.js'; Extra=@('--vus','5','--iterations','20')},
  @{Name='0.4'; Script='04-pizza-api.js'; Extra=@()},
  @{Name='0.5'; Script='05-no-token.js'; Extra=@()},
  @{Name='0.6-normal'; Script='06-thresholds.js'; Extra=@()},
  @{Name='0.6-strict'; Script='06-thresholds.js'; Extra=@('-e','P95=300')},
  @{Name='0.7-normal'; Script='07-requirement.js'; Extra=@()},
  @{Name='0.7-strict'; Script='07-requirement.js'; Extra=@('-e','P95=1')},
  @{Name='0.8-buggy'; Script='08-bug-hunt.js'; Extra=@('--vus','5','--duration','20s','-e','BUGGY=1')},
  @{Name='explore'; Script='explore.js'; Extra=@()},
  @{Name='0.8-fixed'; Script='08-bug-hunt.js'; Extra=@('--vus','5','--duration','20s')},
  @{Name='a1-smoke'; Script='a1-smoke.js'; Extra=@()},
  @{Name='a2-average'; Script='a2-average.js'; Extra=@()},
  @{Name='a3-stress'; Script='a3-stress.js'; Extra=@()},
  @{Name='a4-spike'; Script='a4-spike.js'; Extra=@()},
  @{Name='a5-soak'; Script='a5-soak.js'; Extra=@()}
)
$records = @()
if ($Only -and (Test-Path reports/raw/runs.json)) {
  $records = @(Get-Content reports/raw/runs.json -Raw | ConvertFrom-Json | Where-Object { $_.name -notin $Only })
}
foreach ($run in $runs) {
  if ($Only -and $run.Name -notin $Only) { continue }
  Write-Output "START $($run.Name)"
  $runArgs = @('run','--no-color','--quiet','--summary-trend-stats','avg,min,med,max,p(90),p(95),p(99)', '--summary-export',"reports/raw/$($run.Name)-summary.json")
  if ($run.Name -match '^a[2-5]-') {
    $runArgs += @('--out',"web-dashboard=export=reports/$($run.Name).html",'--out',"json=reports/raw/$($run.Name)-metrics.json.gz")
  }
  $runArgs += $run.Extra
  $runArgs += $run.Script
  $started = [DateTimeOffset]::Now.ToString('o')
  & $k6Executable @runArgs *> "reports/raw/$($run.Name).log"
  $exitCode = $LASTEXITCODE
  $records += @{name=$run.Name; started=$started; ended=[DateTimeOffset]::Now.ToString('o'); exitCode=$exitCode; arguments=$runArgs}
  ConvertTo-Json -Depth 8 -InputObject @($records) | Set-Content reports/raw/runs.json -Encoding utf8
  Write-Output "DONE $($run.Name) exit=$exitCode"
  if ($exitCode -ne 0 -and $exitCode -ne 99) { throw "Run failed: $($run.Name); see log" }
  if ($run.Name -eq 'a1-smoke' -and $exitCode -ne 0) { throw 'Smoke failed; stop before larger tests.' }
}
