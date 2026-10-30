from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
def write(name, text):
    (root / name).write_text(text.strip() + '\n', encoding='utf-8')

common = """import http from 'k6/http';
import { check, sleep } from 'k6';
const BASE_URL = 'https://quickpizza.grafana.com';
const PARAMS = { headers: {
  'Content-Type': 'application/json',
  Authorization: 'token abcdef0123456789',
} };
"""
pizza = """export default function () {
  const res = http.post(`${BASE_URL}/api/pizza`, JSON.stringify({ mustBeVegetarian: true }), PARAMS);
  check(res, {
    'status is 200': r => r.status === 200,
    'pizza has a name': r => r.json('pizza.name') !== undefined,
    'every ingredient is vegetarian': r => r.json('pizza.ingredients').every(i => i.vegetarian === true),
  });
  sleep(1);
}
"""
write('01-first-test.js', """import http from 'k6/http';
import { check, sleep } from 'k6';
export default function () {
  const res = http.get('https://quickpizza.grafana.com/');
  check(res, { 'status is 200': r => r.status === 200 });
  sleep(1);
}
""")
write('04-pizza-api.js', common + pizza)
write('05-no-token.js', """import http from 'k6/http';
import { check, sleep } from 'k6';
export default function () {
  const res = http.post('https://quickpizza.grafana.com/api/pizza', JSON.stringify({ mustBeVegetarian: true }), {
    headers: { 'Content-Type': 'application/json' },
    responseCallback: http.expectedStatuses(401),
  });
  check(res, { 'request without a token is refused': r => r.status === 401 });
  sleep(1);
}
""")
write('06-thresholds.js', common + """const P95 = __ENV.P95 || 1500;
export const options = { vus: 3, duration: '30s', thresholds: {
  http_req_failed: ['rate<0.01'],
  http_req_duration: [`p(95)<${P95}`],
  checks: ['rate>0.99'],
} };
""" + pizza)
write('07-requirement.js', common + """// P95=1 changes only the p(95) requirement for the intentional failing run.
const P95 = __ENV.P95 || 1000;
export const options = { vus: 3, duration: '30s', thresholds: {
  http_req_failed: ['rate<0.01'],
  http_req_duration: [`p(95)<${P95}`, 'p(99)<1500'],
} };
""" + pizza)
write('08-bug-hunt.js', common + """// BUGGY=1 reproduces the original request; the default uses exact API names.
export default function () {
  const body = JSON.stringify({
    excludedIngredients: [__ENV.BUGGY === '1' ? 'pepperoni' : 'Pepperoni'],
    excludedTools: [__ENV.BUGGY === '1' ? 'knife' : 'Knife'],
  });
  const res = http.post(`${BASE_URL}/api/pizza`, body, PARAMS);
  check(res, {
    'status is 200': r => r.status === 200,
    'no pepperoni': r => !r.json('pizza.ingredients').some(i => i.name === 'Pepperoni'),
    'no knife needed': r => r.json('pizza.tool') !== 'Knife',
  });
  sleep(1);
}
""")
write('explore.js', common + """export default function () {
  console.log(http.get(`${BASE_URL}/api/ingredients/topping`, PARAMS).body);
  console.log(http.get(`${BASE_URL}/api/tools`, PARAMS).body);
}
""")
write('journey.js', common.replace('check, sleep', 'check, group, sleep') + """export function journey() {
  group('home', () => {
    const res = http.get(`${BASE_URL}/`);
    check(res, { 'home page is 200': r => r.status === 200 });
  });
  sleep(1 + Math.random() * 2);
  group('quotes', () => {
    const res = http.get(`${BASE_URL}/api/quotes`);
    check(res, { 'quotes are listed': r => r.status === 200 && r.json('quotes').length > 0 });
  });
  sleep(1);
  group('recommendation', () => {
    const res = http.post(`${BASE_URL}/api/pizza`, JSON.stringify({ mustBeVegetarian: true }), PARAMS);
    check(res, {
      'recommendation is 200': r => r.status === 200,
      'pizza has a name': r => r.json('pizza.name') !== undefined,
    });
  });
  sleep(1 + Math.random() * 2);
}
""")
thresholds = {'checks': ['rate>0.99'], 'http_req_failed': ['rate<0.01']}
timed = dict(thresholds, **{'http_req_duration{group:::home}':['p(95)<1000'], 'http_req_duration{group:::recommendation}':['p(95)<1500']})
configs = {
 'a1-smoke': dict(vus=1, duration='30s', thresholds=thresholds),
 'a2-average': dict(stages=[{'duration':d,'target':v} for d,v in [('30s',3),('2m',3),('30s',0)]], thresholds=timed),
 'a3-stress': dict(stages=[{'duration':d,'target':v} for d,v in [('30s',5),('2m',5),('30s',0)]], thresholds=timed),
 'a4-spike': dict(stages=[{'duration':d,'target':v} for d,v in [('30s',1),('5s',5),('30s',5),('5s',1),('1m',1),('10s',0)]], thresholds=timed),
 'a5-soak': dict(stages=[{'duration':d,'target':v} for d,v in [('30s',2),('10m',2),('30s',0)]], thresholds=timed),
}
for name, options in configs.items():
    write(name+'.js', "import { journey } from './journey.js';\nexport const options = " + json.dumps(options, indent=2) + ";\nexport default function () { journey(); }")
