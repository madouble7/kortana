import { IncomingMessage, ServerResponse } from 'http';
import { handleMetrics } from './handlers/metrics';

export const router = (req: IncomingMessage, res: ServerResponse): void => {
  if (req.url === '/metrics' && req.method === 'GET') {
    return handleMetrics(req, res);
  }
  res.writeHead(404);
  res.end('Not Found');
};