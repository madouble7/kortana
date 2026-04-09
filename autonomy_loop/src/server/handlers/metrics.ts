import { IncomingMessage, ServerResponse } from 'http';
import { collectMetrics, formatPrometheus } from '../../core/metrics_collector';

export const handleMetrics = (req: IncomingMessage, res: ServerResponse): void => {
  try {
    const metrics = collectMetrics();
    const formatted = formatPrometheus(metrics);
    res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4' });
    res.end(formatted);
  } catch (err) {
    res.writeHead(500);
    res.end('Internal Server Error');
  }
};