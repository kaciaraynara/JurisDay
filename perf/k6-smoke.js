import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuração
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const JWT = __ENV.JWT || ''; // opcional: token real para rotas protegidas

// Smoke: baixa carga, só para validar uptime/latência básica.
export const options = {
  vus: 5,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(90)<800', 'p(99)<1500'],
    http_req_failed: ['rate<0.02'],
  },
};

// Endpoints públicos para checar tempo de resposta
const targets = [
  { name: 'root', path: '/' },
  { name: 'docs', path: '/docs' },
  { name: 'login_page', path: '/static/login.html' },
  { name: 'signup_page', path: '/static/signup.html' },
];

export default function () {
  targets.forEach(t => {
    const res = http.get(`${BASE_URL}${t.path}`);
    check(res, {
      [`${t.name} status 200`]: r => r.status === 200,
      [`${t.name} < 800ms`]: r => r.timings.duration < 800,
    });
  });

  // Opcional: rota protegida com JWT (se fornecido)
  if (JWT) {
    const res = http.get(`${BASE_URL}/monitorar/status`, {
      headers: { Authorization: `Bearer ${JWT}` },
    });
    check(res, { 'monitorar/status 200/401': r => [200, 401].includes(r.status) });
  }

  sleep(1);
}
