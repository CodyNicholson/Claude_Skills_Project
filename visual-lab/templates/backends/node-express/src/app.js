// __LAB_NAME__ API. One endpoint per feature under /api/demos/*, each returning a DemoResult.
import express from 'express';
import { Demo } from './lab.js';

export const app = express();
app.use(express.json({ limit: '256kb' }));

app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

app.post('/api/demos/hello', async (req, res) => {
  const message = String(req.query.message ?? 'hello').slice(0, 200);
  const d = new Demo('hello');
  if (req.query.mistake === 'true') {
    // A pitfall demo: do it the wrong way for real, show the genuine error, then the fix
    const { error } = await d.attempt(`JSON.parse(${JSON.stringify(message)})  // wrong: text is not JSON`, () => JSON.parse(message));
    d.check('The wrong way fails with the error the page describes', error !== null, error);
    d.data.error = error;
  }
  // Replace with a real call into __TOOL__
  const reply = message.toUpperCase();
  d.command(`toUpperCase(${JSON.stringify(message)})`);
  d.check('Reply is the upper-cased message', reply === message.toUpperCase(), reply);
  Object.assign(d.data, { message, reply });
  res.json(d.result());
});

// Every demo is listed here so the test suite can run them all, like the UI's "Run all demos"
export const DEMO_ROUTES = [['POST', '/api/demos/hello']];

app.use((err, req, res, next) => {
  res.status(500).json({ error: err.message });
});
