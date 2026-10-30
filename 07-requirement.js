import http from 'k6/http';
import { check, sleep } from 'k6';
const BASE_URL = 'https://quickpizza.grafana.com';
const PARAMS = { headers: {
  'Content-Type': 'application/json',
  Authorization: 'token abcdef0123456789',
} };
// P95=1 changes only the p(95) requirement for the intentional failing run.
const P95 = __ENV.P95 || 1000;
export const options = { vus: 3, duration: '30s', thresholds: {
  http_req_failed: ['rate<0.01'],
  http_req_duration: [`p(95)<${P95}`, 'p(99)<1500'],
} };
export default function () {
  const res = http.post(`${BASE_URL}/api/pizza`, JSON.stringify({ mustBeVegetarian: true }), PARAMS);
  check(res, {
    'status is 200': r => r.status === 200,
    'pizza has a name': r => r.json('pizza.name') !== undefined,
    'every ingredient is vegetarian': r => r.json('pizza.ingredients').every(i => i.vegetarian === true),
  });
  sleep(1);
}
