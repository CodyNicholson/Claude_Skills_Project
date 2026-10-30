import { test } from 'node:test';
import assert from 'node:assert/strict';
import { app, DEMO_ROUTES } from '../src/app.js';

const server = app.listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
test.after(() => server.close());

test('health', async () => {
  const body = await (await fetch(`${base}/api/health`)).json();
  assert.equal(body.status, 'ok');
});

test('every demo passes its own checks', async () => {
  for (const [method, path] of DEMO_ROUTES) {
    const body = await (await fetch(`${base}${path}`, { method })).json();
    assert.ok(body.checks.length > 0, path);
    assert.deepEqual(body.checks.filter((c) => !c.passed), [], path);
  }
});

test('pitfall mode shows the real error', async () => {
  const body = await (await fetch(`${base}/api/demos/hello?mistake=true`, { method: 'POST' })).json();
  assert.ok(body.data.error);
  assert.deepEqual(body.checks.filter((c) => !c.passed), []);
});
