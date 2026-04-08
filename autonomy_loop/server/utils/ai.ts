import { GoogleGenAI } from "@google/genai";

/**
 * Executes an AI operation with exponential backoff retry logic.
 * Specifically handles 429 (Resource Exhausted) errors.
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 2000
): Promise<T> {
  let lastError: any;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;
      const isQuotaError = error?.message?.includes('429') || error?.status === 'RESOURCE_EXHAUSTED';
      const isUnavailableError = error?.status === 'UNAVAILABLE' || error?.code === 503;
      
      if ((isQuotaError || isUnavailableError) && i < maxRetries - 1) {
        const delay = initialDelay * Math.pow(2, i);
        console.warn(`[AI Retry] AI error (status: ${error?.status || error?.code}). Retrying in ${delay}ms (attempt ${i + 1}/${maxRetries})...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw lastError;
}
