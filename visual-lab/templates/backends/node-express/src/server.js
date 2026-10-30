import { app } from './app.js';

const port = Number(process.env.PORT || __API_PORT__);
app.listen(port, '0.0.0.0', () => console.log(`API listening on :${port}`));
