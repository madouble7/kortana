const http = require('http');
const https = require('https');
const url = require('url');
// Using built-in fetch in Node 22

const PORT = process.env.PORT || 3002;
const UA = process.env.KORTANA_UA || 'kortana/1.0 (+https://example.com)';

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);

  if (parsedUrl.pathname === '/proxy' && req.method === 'GET') {
    const targetUrl = parsedUrl.query.url;
    if (!targetUrl) {
      res.writeHead(400, { 'Content-Type': 'text/plain' });
      res.end('Missing url parameter');
      return;
    }

    try {
      const upstream = await fetch(String(targetUrl), {
        headers: { 'User-Agent': UA }
      });

      res.writeHead(upstream.status, Object.fromEntries(upstream.headers.entries()));
      const buffer = await upstream.arrayBuffer();
      res.end(Buffer.from(buffer));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end(String(e));
    }
  } else if (parsedUrl.pathname === '/proxy/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', ts: Date.now(), port: PORT }));
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  }
});

server.listen(PORT, () => console.log(`Proxy listening on ${PORT}`));
