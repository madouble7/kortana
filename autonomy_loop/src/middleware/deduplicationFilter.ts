interface Task {
  fingerprint: string;
}

export const validateTaskUniqueness = (existingTasks: Task[], newFingerprint: string): boolean => {
  const isDuplicate = existingTasks.some((task) => task.fingerprint === newFingerprint);
  return !isDuplicate;
};