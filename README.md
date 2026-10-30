# K6 lab

ITDS362 — Performance Testing with Grafana K6, lab version 2.0.

Target: https://quickpizza.grafana.com. Tests run sequentially, never exceeding
5 virtual users. Only the prescribed 2-user soak test exceeds 3 minutes.

## Run

Requires K6 (tested here with v2.3.0). From this repository:

```powershell
k6 run 01-first-test.js
k6 run --vus 5 --duration 20s 01-first-test.js
k6 run --vus 5 --iterations 20 01-first-test.js
k6 run 04-pizza-api.js
k6 run 05-no-token.js
k6 run 06-thresholds.js
k6 run -e P95=300 06-thresholds.js
k6 run 07-requirement.js
k6 run -e P95=1 07-requirement.js
k6 run --vus 5 --duration 20s -e BUGGY=1 08-bug-hunt.js
k6 run explore.js
k6 run --vus 5 --duration 20s 08-bug-hunt.js
k6 run a1-smoke.js
k6 run --out web-dashboard=export=reports/a2-average.html a2-average.js
k6 run --out web-dashboard=export=reports/a3-stress.html a3-stress.js
k6 run --out web-dashboard=export=reports/a4-spike.html a4-spike.js
k6 run --out web-dashboard=export=reports/a5-soak.html a5-soak.js
```

`$LASTEXITCODE` shows the preceding K6 exit code in PowerShell. A failed
threshold returns 99; failed checks alone do not fail a test without a threshold.
The `P95=1` run intentionally changes the requirement to force a failure.

`08-bug-hunt.js` defaults to the fixed request. `BUGGY=1` reproduces the
original case mismatch. Public practice token is supplied by the lab.

## Results and evidence

- `RESULTS.md`: measured results and reflections.
- `reports/*.html`: standalone dashboards for A2–A5 (open locally in a browser).
- `reports/raw/*.log`: console summaries and API exploration.
- `reports/raw/*-summary.json`: machine-readable summaries.
- `reports/raw/*-metrics.json.gz`: timestamped metrics for spike/soak analysis.
- `reports/raw/runs.json`: actual timestamps, commands and exit codes.

`scripts/run-lab.ps1` runs all steps sequentially on this Windows machine,
using `C:/Program Files/k6/k6.exe`. It saves evidence and stops on execution
errors or a failed smoke test. Do not run another load test concurrently.

No commit or push is performed by any helper script.
