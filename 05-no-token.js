import http from 'k6/http';
import { check, sleep } from 'k6';
export default function () {
  const res = http.post('https://quickpizza.grafana.com/api/pizza', JSON.stringify({ mustBeVegetarian: true }), {
    headers: { 'Content-Type': 'application/json' },
    responseCallback: http.expectedStatuses(401),
  });
  check(res, { 'request without a token is refused': r => r.status === 401 });
  sleep(1);
}
