import express from 'express';
import fetch from 'node-fetch';

const app = express();
const PORT = process.env.PORT || 5174;
const UA = process.env.KORTANA_UA || 'kortana/1.0 (+https://example.com)';

app.get('/proxy', async (req, res) => {
  const url = req.query.url;
  if (!url) return res.status(400).send('Missing url');
  try {
    const upstream = await fetch(String(url), {headers: {'User-Agent': UA}});
    res.status(upstream.status);
    upstream.headers.forEach((v, k) => res.setHeader(k, v));
    const buffer = await upstream.arrayBuffer();
    res.send(Buffer.from(buffer));
  } catch (e) {
    res.status(500).send(String(e));
  }
});

app.listen(PORT, () => console.log(`Proxy listening on ${PORT}`));
