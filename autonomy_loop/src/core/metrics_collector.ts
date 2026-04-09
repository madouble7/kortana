import * as os from 'os';

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_io: number;
  network_io: number;
  active_task_count: number;
}

export const collectMetrics = (): SystemMetrics => {
  const cpus = os.cpus();
  const load = os.loadavg()[0];
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  
  return {
    cpu_usage: load,
    memory_usage: ((totalMem - freeMem) / totalMem) * 100,
    disk_io: 0,
    network_io: 0,
    active_task_count: 0
  };
};

export const formatPrometheus = (metrics: SystemMetrics): string => {
  return [
    `# HELP system_cpu_usage_ratio Current CPU load average`,
    `# TYPE system_cpu_usage_ratio gauge`,
    `system_cpu_usage_ratio ${metrics.cpu_usage.toFixed(2)}`,
    `# HELP system_memory_usage_percent Percentage of memory in use`,
    `# TYPE system_memory_usage_percent gauge`,
    `system_memory_usage_percent ${metrics.memory_usage.toFixed(2)}`,
    `# HELP system_active_tasks_count Number of active tasks`,
    `# TYPE system_active_tasks_count gauge`,
    `system_active_tasks_count ${metrics.active_task_count}`
  ].join('\n');
};