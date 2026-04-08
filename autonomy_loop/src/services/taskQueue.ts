import { validateTaskUniqueness } from '../middleware/deduplicationFilter';

interface Task {
  id: string;
  description: string;
  fingerprint: string;
}

class TaskQueue {
  private tasks: Task[] = [];

  public addTask(task: Task): boolean {
    if (!validateTaskUniqueness(this.tasks, task.fingerprint)) {
      return false;
    }
    this.tasks.push(task);
    return true;
  }

  public getTasks(): Task[] {
    return this.tasks;
  }
}

export const taskQueue = new TaskQueue();