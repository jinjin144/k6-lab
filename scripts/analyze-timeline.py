"""Summarize actual timestamped K6 samples; no extra requests are sent."""
import gzip
import json
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
runs = {r['name']:r for r in json.loads((root/'reports/raw/runs.json').read_text(encoding='utf-8-sig'))}
def percentile(values, fraction):
    values = sorted(values)
    x = (len(values)-1)*fraction
    lo = int(x)
    return values[lo]+(values[min(lo+1,len(values)-1)]-values[lo])*(x-lo)

output = {}
for name in ('a4-spike','a5-soak'):
    source = root/f'reports/raw/{name}-metrics.json.gz'
    if not source.exists() or name not in runs:
        continue
    start = datetime.fromisoformat(runs[name]['started'])
    windows = [(0,30),(35,65),(70,100),(100,130)] if name=='a4-spike' else [(30,150),(510,630)]
    buckets = [{'start_s':a,'end_s':b,'durations':[],'failed':[]} for a,b in windows]
    with gzip.open(source,'rt',encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line)
            if event.get('type')!='Point' or event.get('metric') not in ('http_req_duration','http_req_failed'):
                continue
            data = event['data']
            elapsed = (datetime.fromisoformat(data['time'].replace('Z','+00:00'))-start).total_seconds()
            for bucket in buckets:
                if bucket['start_s']<=elapsed<bucket['end_s']:
                    bucket['durations' if event['metric']=='http_req_duration' else 'failed'].append(data['value'])
    for bucket in buckets:
        values = bucket.pop('durations')
        failures = bucket.pop('failed')
        bucket['requests'] = len(values)
        bucket['p95_ms'] = percentile(values,.95) if values else None
        bucket['failed_rate'] = sum(failures)/len(failures) if failures else None
    output[name] = buckets
(root/'reports/raw/timeline-analysis.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
