export async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  let attempt = 0;
  let backoff = 2000; // Start with 2s
  while (true) {
    try {
      return await fn();
    } catch (e: any) {
      const errorMsg = e.toString();
      if ((errorMsg.includes('429') || errorMsg.includes('RESOURCE_EXHAUSTED')) && attempt < retries) {
        await new Promise(r => setTimeout(r, backoff));
        attempt++;
        backoff *= 2;
        continue;
      }
      throw e;
    }
  }
}
