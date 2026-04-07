/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { API_BASE, API_KEY } from './config';
import { withRetry } from '../lib/geminiRetry';
import { GoogleGenAI, Modality, ThinkingLevel } from "@google/genai";
import { KORTANA_SYSTEM_INSTRUCTION } from '../constants';
import { db, auth } from '../firebase';
import { 
  collection, 
  addDoc, 
  getDocs, 
  deleteDoc, 
  doc, 
  query, 
  orderBy, 
  limit, 
  serverTimestamp,
  Timestamp
} from 'firebase/firestore';
import type { 
  ChatTextResponse, 
  ChatAudioResponse, 
  StartSessionResp, 
  Snapshot, 
  RagUploadResult, 
  RagQueryResponse, 
  BuilderPlan, 
  OcrResponse, 
  ImageGenerateResponse, 
  RcloneStatus, 
  VideoOperation, 
  ImageEditResponse, 
  CodeSnippetResponse, 
  WebSearchResponse, 
  StripeCheckoutSessionResponse, 
  AutonomyHeartbeat, 
  Agent, 
  Ritual, 
  Task, 
  GeminiModel, 
  ImageAspectRatio, 
  VideoAspectRatio, 
  VideoResolution, 
  SearchGroundingResponse, 
  MapsGroundingResponse, 
  TextToSpeechResponse, 
  ImageAnalysisResponse, 
  VideoAnalysisResponse, 
  GroundingSource, 
  LiveServerMessage 
} from '../types'; 

/**
 * Helper to get a fresh instance of GoogleGenAI.
 * Always use process.env.GEMINI_API_KEY as the primary source.
 */
export function getAI() {
  // Priority: process.env.GEMINI_API_KEY (platform) > process.env.API_KEY (from dialog) > config.ts
  const apiKey = (typeof process !== 'undefined' ? (process.env.GEMINI_API_KEY || process.env.API_KEY) : '') || API_KEY;
  if (!apiKey) {
    throw new Error("CRITICAL: No API Key found for Gemini. Please configure your API key in the settings.");
  }
  return new GoogleGenAI({ apiKey });
}

const MODEL_MAP: Record<string, string> = {
  'gemini-2.5-flash': 'gemini-2.5-flash-preview-tts',
  'gemini-3.1-flash-lite-preview': 'gemini-3.1-flash-lite-preview',
};

function getModelName(model: GeminiModel): string {
  return MODEL_MAP[model] || 'gemini-flash-latest';
}

const DEFAULT_TIMEOUT = 15000;

async function fetchWithTimeout(url: string, init: RequestInit = {}, ms = DEFAULT_TIMEOUT): Promise<Response> {
  const ctl = new AbortController();
  const id = setTimeout(() => ctl.abort(), ms);
  try {
    const res = await fetch(url, { ...init, signal: ctl.signal });
    return res;
  } finally {
    clearTimeout(id);
  }
}

export async function apiJson<T>(url: string, init: RequestInit = {}, retries = 2): Promise<T> {
  let attempt = 0;
  let backoff = 500;
  while (true) {
    try {
      const res = await fetchWithTimeout(url, init);
      if (res.status === 429 && attempt < retries) {
        await new Promise(r => setTimeout(r, backoff));
        attempt++; backoff *= 2; continue;
      }
      if (!res.ok) throw new Error(`http ${res.status}`);
      return (await res.json()) as T;
    } catch (e) {
      if (attempt++ >= retries) throw e;
      await new Promise(r => setTimeout(r, backoff));
      backoff *= 2;
    }
  }
}

function withKey(init: RequestInit = {}): RequestInit {
  const h = new Headers(init.headers || {});
  if (API_KEY) h.set('x-api-key', API_KEY);
  return { ...init, headers: h };
}

// Base path for general backend API endpoints
const B = (path: string) => `${API_BASE}${path}`;

// Backend Health Status
export async function getHealthStatus(): Promise<{ status: string; backend: string; time?: number }> {
    return apiJson(B('/health'));
}

export async function chatProStream(
  message: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const ai = getAI();
  await withRetry(async () => {
    const response = await ai.models.generateContentStream({
      model: "gemini-3.1-flash-lite-preview",
      contents: message,
      config: {
        systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
      }
    });

    for await (const chunk of response) {
      onChunk(chunk.text || '');
    }
  });
}

export async function chatFastStream(
  message: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const ai = getAI();
  await withRetry(async () => {
    const response = await ai.models.generateContentStream({
      model: "gemini-3.1-flash-lite-preview",
      contents: message,
      config: {
        systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
      }
    });

    for await (const chunk of response) {
      onChunk(chunk.text || '');
    }
  });
}

export async function chatWithSearchStream(
  message: string,
  onChunk: (chunk: string) => void,
  onMetadata?: (metadata: any) => void
): Promise<void> {
  const ai = getAI();
  await withRetry(async () => {
    const response = await ai.models.generateContentStream({
      model: "gemini-3.1-flash-lite-preview",
      contents: message,
      config: {
        systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
        tools: [{ googleSearch: {} }],
      }
    });

    for await (const chunk of response) {
      if (chunk.text) onChunk(chunk.text);
      if (onMetadata && chunk.candidates?.[0]?.groundingMetadata) {
        onMetadata(chunk.candidates[0].groundingMetadata);
      }
    }
  });
}

export async function chatPro(message: string): Promise<ChatTextResponse> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-preview",
    contents: message,
    config: {
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
    }
  }));

  return {
    reply: response.text || '',
    used_rag: false
  };
}

export async function chatFast(message: string): Promise<ChatTextResponse> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-preview",
    contents: message,
    config: {
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
    }
  }));

  return {
    reply: response.text || '',
    used_rag: false
  };
}

export async function chatWithSearch(message: string): Promise<SearchGroundingResponse> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-preview",
    contents: message,
    config: {
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
      tools: [{ googleSearch: {} }],
    }
  }));

  const sources: GroundingSource[] = (response.candidates?.[0]?.groundingMetadata?.groundingChunks || []).map((chunk: any) => ({
    title: chunk.web?.title || 'Source',
    uri: chunk.web?.uri || ''
  }));

  return {
    reply: response.text || '',
    sources
  };
}

export async function chatText(message: string): Promise<ChatTextResponse> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-preview",
    contents: message,
    config: {
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
    }
  }));

  return {
    reply: response.text || '',
    used_rag: false
  };
}

export async function chatTextStream(
  message: string,
  useRag: boolean,
  model: GeminiModel,
  useThinkingMode: boolean,
  onData: (chunk: string) => void
): Promise<{ used_rag: boolean }> {
  const ai = getAI();
  const modelName = getModelName(model);
  
  await withRetry(async () => {
    const response = await ai.models.generateContentStream({
      model: modelName,
      contents: message,
      config: {
        systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
        ...(useThinkingMode && modelName.includes('gemini-3') ? { thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH } } : {}),
      },
    });

    for await (const chunk of response) {
      if (chunk.text) {
        onData(chunk.text);
      }
    }
  });

  return { used_rag: false };
}

export async function chatAudio(file: File): Promise<ChatAudioResponse> {
  const ai = getAI();
  const model = 'gemini-flash-latest';
  
  // Convert file to base64
  const reader = new FileReader();
  const base64Promise = new Promise<string>((resolve, reject) => {
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
  reader.readAsDataURL(file);
  const base64 = await base64Promise;

  const response = await ai.models.generateContent({
    model,
    contents: [
      {
        inlineData: {
          data: base64,
          mimeType: file.type,
        },
      },
      {
        text: "Please transcribe this audio, provide a summary, and a helpful reply.",
      },
    ],
    config: {
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
    }
  });

  const text = response.text || '';
  // The app expects a specific format: transcript, summary, reply
  // We'll do a simple split or just return the text as the reply
  return {
    transcript: "[Transcription not explicitly separated by SDK]",
    summary: "[Summary not explicitly separated by SDK]",
    reply: text
  };
}

export async function startSession(): Promise<StartSessionResp> {
  const res = await fetch(B('/session/start'), withKey({ method: 'POST' }));
  if (!res.ok) throw new Error(`session/start ${res.status}`);
  return res.json();
}

export async function ingestChunk(session_id: string, keys: string[]): Promise<{ accepted: number }> {
  const res = await fetch(B('/session/ingest'), withKey({
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ session_id, chunks: keys })
  }));
  if (!res.ok) throw new Error(`session/ingest ${res.status}`);
  return res.json();
}

export async function getSessionSnapshot(session_id: string): Promise<Snapshot> {
  const res = await fetch(B(`/session/${session_id}/snapshot`), withKey());
  if (!res.ok) {
    if (res.status === 401) throw new Error('missing or invalid api key.');
    throw new Error(`session/snapshot ${res.status}`);
  }
  return res.json();
}

export async function scanDocument(file: File): Promise<OcrResponse> {
  const form = new FormData();
  form.set('file', file);
  const res = await fetch(B('/ocr/handwriting'), withKey({ method: 'POST', body: form }));
  if (!res.ok) throw new Error(`ocr/handwriting ${res.status}`);
  return res.json();
}

// presigned POST upload (s3)
export async function uploadPresigned(file: File, presign: any): Promise<string> {
  const fd = new FormData();
  const keyTemplate = (presign.fields?.key as string) || '';
  const finalKey = keyTemplate.replace('${filename}', file.name);

  Object.entries(presign.fields || {}).forEach(([k, v]) => {
    // Substitute the key with the final filename before appending
    if (k === 'key') {
      fd.append(k, finalKey);
    } else {
      fd.append(String(k), String(v));
    }
  });

  fd.append('file', file);
  const res = await fetch(presign.url, { method: 'POST', body: fd });
  if (!res.ok) throw new Error('upload failed');
  
  // Return the final key that was used for the upload
  return finalKey;
}

// Knowledge Base functions (RAG v2)
export async function ragUploadDocument(file: File, namespace: string = 'default'): Promise<RagUploadResult> {
    const form = new FormData();
    form.set('file', file);
    form.set('namespace', namespace);
    const res = await fetch(B('/rag/documents/upload'), withKey({
        method: 'POST',
        body: form
    }));
    if (!res.ok) throw new Error(`rag/documents/upload POST ${res.status}`);
    return res.json();
}

export async function ragQuery(query: string, namespace: string = 'default', topK: number = 5): Promise<RagQueryResponse> {
    // For this autonomous agent, we'll prioritize searching local memories first
    const memories = await getMemories();
    const matches = memories
      .filter(m => m.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, topK)
      .map((m, index) => ({
        id: m.id,
        text: m.content,
        score: 1.0,
        metadata: { 
          document_id: 'local_memory',
          filename: 'local_memory', 
          chunk_id: index,
          uploaded_at: new Date(m.timestamp).getTime() 
        }
      }));

    if (matches.length > 0) {
      return {
        answer: `I found some relevant information in my local memory about "${query}".`,
        matches
      };
    }

    // Fallback to empty response if local memory has nothing
    return {
      answer: `I couldn't find any relevant information in my local memory about "${query}".`,
      matches: []
    };
}

/**
 * Summarizes a conversation and saves it to memory.
 */
export async function saveConversationSummary(transcript: string): Promise<void> {
  if (!transcript.trim()) return;

  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: 'gemini-3.1-flash-lite-preview',
    contents: `Summarize the following conversation into a concise "memory" that can be used for future context. Focus on key facts, user preferences, and important decisions. Keep it under 200 words.\n\nTranscript:\n${transcript}`,
  }));

  const summary = response.text;
  if (summary) {
    await saveMemory(`[Conversation Summary ${new Date().toLocaleDateString()}]: ${summary}`);
  }
}

/**
 * Fetches weather data for a given location.
 * Uses Nominatim for geocoding and Open-Meteo for weather.
 */
export async function getWeather(location: string): Promise<string> {
    try {
        // 1. Geocode location to lat/lon using Nominatim directly
        const geoUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location)}&format=jsonv2&limit=1`;
        const geoRes = await fetch(geoUrl, {
            headers: {
                'User-Agent': 'KortanaApp/1.0 (MADouble7@gmail.com)'
            }
        });
        if (!geoRes.ok) throw new Error(`Geocoding failed: ${geoRes.status}`);
        const geoData = await geoRes.json();
        
        if (!geoData || geoData.length === 0) {
            return `Location '${location}' not found.`;
        }
        const { lat, lon, display_name } = geoData[0];

        // 2. Get weather from Open-Meteo directly
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&hourly=temperature_2m&timezone=auto`;
        const weatherRes = await fetch(weatherUrl);
        if (!weatherRes.ok) throw new Error(`Weather fetch failed: ${weatherRes.status}`);
        const weatherData = await weatherRes.json();
        
        const temp = weatherData.current.temperature_2m;
        return `Current weather in ${display_name}: ${temp}°C.`;
    } catch (e) {
        console.error("Weather recall failed:", e);
        return "Failed to retrieve weather data.";
    }
}

// Builder Agent functions
export async function builderPlan(goal: string): Promise<BuilderPlan> {
  const body = new URLSearchParams(); body.set('goal', goal);
  const res = await fetch(B('/builder/plan'), withKey({ method: 'POST', body }));
  if (!res.ok) throw new Error(`builder/plan ${res.status}`);
  return res.json();
}

export async function builderActStream(plan: BuilderPlan, onData: (data: string) => void): Promise<void> {
  const body = new URLSearchParams();
  body.set('goal', plan.goal);
  body.set('approve', 'true'); // Automatically approve for this simple UI

  const res = await fetch(B('/builder/apply'), withKey({ method: 'POST', body }));
  if (!res.ok || !res.body) throw new Error(`builder/apply ${res.status}`);
  
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    let lineEndIndex;
    while ((lineEndIndex = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, lineEndIndex).trim();
      buffer = buffer.slice(lineEndIndex + 1);

      if (line.startsWith('data: ')) {
        const dataContent = line.substring(6).trim();
        if (dataContent) {
          onData(dataContent);
        }
      }
    }
  }

  // Process any remaining data in the buffer
  if (buffer.startsWith('data: ')) {
    const dataContent = buffer.substring(6).trim();
    if (dataContent) {
      onData(dataContent);
    }
  }
}

// Image Generation
export async function generateImage(prompt: string, aspectRatio: ImageAspectRatio = '1:1'): Promise<ImageGenerateResponse> {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: [{ text: prompt }],
    config: {
      imageConfig: {
        aspectRatio: aspectRatio as any,
      },
    },
  });

  let imageBase64 = '';
  for (const part of response.candidates?.[0]?.content?.parts || []) {
    if (part.inlineData) {
      imageBase64 = part.inlineData.data || '';
      break;
    }
  }

  if (!imageBase64) throw new Error('No image generated');

  return {
    image_base64: imageBase64,
    model: 'gemini-2.5-flash-image',
    prompt_hash: prompt.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0).toString(),
    cached: false
  };
}

// Image Editing
export async function editImage(prompt: string, image: { base64: string; mimeType: string }): Promise<ImageEditResponse> {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: [
      {
        inlineData: {
          data: image.base64,
          mimeType: image.mimeType,
        },
      },
      { text: prompt },
    ],
  });

  let imageBase64 = '';
  for (const part of response.candidates?.[0]?.content?.parts || []) {
    if (part.inlineData) {
      imageBase64 = part.inlineData.data || '';
      break;
    }
  }

  if (!imageBase64) throw new Error('No image generated');

  return {
    image_base64: imageBase64,
    text: response.text || null
  };
}

// Image Analysis
export async function analyzeImage(image: { base64: string; mimeType: string }, prompt: string): Promise<ImageAnalysisResponse> {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-flash-latest',
    contents: [
      {
        inlineData: {
          data: image.base64,
          mimeType: image.mimeType,
        },
      },
      { text: prompt },
    ],
  });

  return {
    analysis: response.text || ''
  };
}

// Rclone Sync functions
export async function triggerRcloneSync(dryRun: boolean = false): Promise<{ status: string }> {
    const res = await fetch(B('/ops/rclone/sync'), withKey({
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ dry_run: dryRun })
    }));
    if (!res.ok) throw new Error(`ops/rclone/sync ${res.status}`);
    return res.json();
}

export async function getRcloneSyncStatus(): Promise<RcloneStatus> {
    const res = await fetch(B('/ops/rclone/status'), withKey());
    if (!res.ok) throw new Error(`ops/rclone/status ${res.status}`);
    return res.json();
}

// Video Generation
export async function generateVideo(prompt: string, image: { base64: string; mimeType: string } | null, aspectRatio: VideoAspectRatio, resolution: VideoResolution): Promise<VideoOperation> {
  const ai = getAI();
  let operation = await ai.models.generateVideos({
    model: 'veo-3.1-fast-generate-preview',
    prompt: prompt,
    ...(image ? {
      image: {
        imageBytes: image.base64,
        mimeType: image.mimeType,
      }
    } : {}),
    config: {
      numberOfVideos: 1,
      resolution: resolution === '1080p' ? '1080p' : '720p',
      aspectRatio: aspectRatio === '16:9' ? '16:9' : '9:16'
    }
  });

  return {
    name: operation.name || '',
    done: operation.done || false,
    response: operation.response as any
  };
}

export async function getVideosOperation(operationName: string): Promise<VideoOperation> {
    const ai = getAI();
    const operation = await ai.operations.getVideosOperation({ operation: { name: operationName } as any });
    return {
        name: operation.name || '',
        done: operation.done || false,
        response: operation.response as any
    };
}

// Video Analysis
export async function analyzeVideo(file: File, prompt: string): Promise<VideoAnalysisResponse> {
  const ai = getAI();
  // Convert file to base64
  const reader = new FileReader();
  const base64Promise = new Promise<string>((resolve, reject) => {
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
  reader.readAsDataURL(file);
  const base64 = await base64Promise;

  const response = await ai.models.generateContent({
    model: 'gemini-flash-latest',
    contents: [
      {
        inlineData: {
          data: base64,
          mimeType: file.type,
        },
      },
      { text: prompt },
    ],
  });

  return {
    analysis: response.text || ''
  };
}


// Code Snippet Generation (Non-Vertex AI related)
export async function generateCodeSnippet(prompt: string): Promise<CodeSnippetResponse> {
  const res = await fetch(B('/code/generate'), withKey({
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ prompt })
  }));
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`code/generate ${res.status}: ${errorText}`);
  }
  return res.json();
}

// Web Search (Non-Vertex AI related, using existing proxy for general web search)
export async function chatWebSearch(query: string): Promise<WebSearchResponse> {
  const res = await fetch(B('/chat-web-search'), withKey({
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query })
  }));
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`chat-web-search ${res.status}: ${errorText}`);
  }
  return res.json();
}

// Search Grounding
export async function searchGrounding(query: string): Promise<SearchGroundingResponse> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: 'gemini-3.1-flash-lite-preview',
    contents: query,
    config: {
      tools: [{ googleSearch: {} }],
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
    },
  }));

  const sources: GroundingSource[] = (response.candidates?.[0]?.groundingMetadata?.groundingChunks || []).map((chunk: any) => ({
    title: chunk.web?.title || 'Source',
    uri: chunk.web?.uri || ''
  }));

  return {
    reply: response.text || '',
    sources
  };
}

// Maps Grounding
export async function mapsGrounding(query: string, latitude?: number, longitude?: number): Promise<MapsGroundingResponse> {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: query,
    config: {
      tools: [{ googleMaps: {} }],
      systemInstruction: KORTANA_SYSTEM_INSTRUCTION,
      ...(latitude && longitude ? {
        toolConfig: {
          retrievalConfig: {
            latLng: {
              latitude,
              longitude
            }
          }
        }
      } : {})
    },
  });

  const sources: GroundingSource[] = (response.candidates?.[0]?.groundingMetadata?.groundingChunks || []).map((chunk: any) => ({
    title: chunk.maps?.title || 'Place',
    uri: chunk.maps?.uri || ''
  }));

  return {
    reply: response.text || '',
    sources
  };
}

// Text-to-Speech
export async function textToSpeech(text: string): Promise<TextToSpeechResponse> {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: {
        voiceConfig: {
          prebuiltVoiceConfig: { voiceName: 'Kore' },
        },
      },
    },
  });

  const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) throw new Error('No audio generated');

  return {
    audio_base64: base64Audio,
    mime_type: 'audio/mpeg'
  };
}


// Stripe Integration (Non-Vertex AI related)
export async function createCheckoutSession(): Promise<StripeCheckoutSessionResponse> {
  const res = await fetch(B('/stripe/checkout-session'), withKey({ method: 'POST', body: JSON.stringify({}) }));
  if (!res.ok) throw new Error(`stripe/checkout-session ${res.status}`);
  return res.json();
}

// Autonomy Telemetry (Non-Vertex AI related)
export async function getAutonomyHeartbeat(): Promise<AutonomyHeartbeat> {
    const res = await fetch(B('/autonomy/heartbeat'), withKey());
    if (!res.ok) throw new Error(`autonomy/heartbeat ${res.status}`);
    return res.json();
}

// --- Constellation Dashboard --- (Non-Vertex AI related)
export async function getConstellationAgents(): Promise<Agent[]> {
    return apiJson<Agent[]>(B('/constellation/agents'));
}

export async function getConstellationRituals(): Promise<Ritual[]> {
    return apiJson<Ritual[]>(B('/constellation/rituals'));
}

// --- Task Management (Non-Vertex AI related) ---
export async function getTasks(): Promise<Task[]> {
    const res = await fetch(B('/tasks'), withKey());
    if (!res.ok) throw new Error(`tasks GET ${res.status}`);
    return res.json();
}

export async function claimTask(taskId: string): Promise<{ status: string; task_id: string; assigned_to: string }> {
    const res = await fetch(B(`/tasks/${taskId}/claim`), withKey({ method: 'POST' }));
    if (!res.ok) throw new Error(`tasks/${taskId}/claim POST ${res.status}`);
    return res.json();
}

// --- WebSocket Service for Constellation (Non-Vertex AI related) ---
type MessageCallback = (data: any) => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private subscribers: MessageCallback[] = [];
  private url: string;
  private reconnectAttempts = 0;
  private shouldReconnect = true;

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}${API_BASE}/ws/constellation`;
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }
    this.shouldReconnect = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('Constellation WebSocket connected.');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.subscribers.forEach(callback => callback(data));
      } catch (e) {
        console.error('Failed to parse WebSocket message:', event.data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Constellation WebSocket disconnected.');
      if (this.shouldReconnect) {
        const timeout = Math.min(30000, (2 ** this.reconnectAttempts) * 1000);
        setTimeout(() => this.connect(), timeout);
        this.reconnectAttempts++;
      }
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(callback: MessageCallback): () => void {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }
}

export const constellationSocket = new WebSocketManager();

// GitHub Issue Analysis
export async function analyzeGitHubIssue(url: string): Promise<any> {
  const ai = getAI();
  const response = await withRetry(async () => await ai.models.generateContent({
    model: 'gemini-3.1-flash-lite-preview',
    contents: `Analyze this GitHub issue: ${url}. Provide a JSON response with: title, repo, author, state, comments_count, sentiment, complexity, priority, summary, suggestions.`,
    config: {
      responseMimeType: 'application/json',
    }
  }));

  try {
    return JSON.parse(response.text || '{}');
  } catch (e) {
    console.error('Failed to parse GitHub analysis:', e);
    return { title: 'Analysis Failed', summary: response.text };
  }
}

// System Status
export async function getSystemStatus(): Promise<any> {
  // Mocking system status for now
  return {
    status: 'healthy',
    cpu_usage: `${Math.floor(Math.random() * 30 + 5)}%`,
    memory_usage: `${Math.floor(Math.random() * 40 + 20)}%`,
    latency: `${Math.floor(Math.random() * 50 + 10)}ms`,
    resonance: 0.99 + (Math.random() * 0.009),
    timestamp: new Date().toISOString()
  };
}

// Memory Management (Firestore)
export async function getMemories(): Promise<any[]> {
  const user = auth.currentUser;
  if (!user) return [];

  try {
    const q = query(
      collection(db, `users/${user.uid}/memories`),
      orderBy('timestamp', 'desc'),
      limit(50)
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp: (doc.data().timestamp as Timestamp)?.toDate().toISOString() || new Date().toISOString()
    }));
  } catch (e) {
    console.error('Error fetching memories:', e);
    return [];
  }
}

export async function saveMemory(content: string): Promise<void> {
  const user = auth.currentUser;
  if (!user) return;

  try {
    await addDoc(collection(db, `users/${user.uid}/memories`), {
      uid: user.uid,
      content,
      timestamp: serverTimestamp()
    });
  } catch (e) {
    console.error('Error saving memory:', e);
  }
}

export async function deleteMemory(id: string): Promise<void> {
  const user = auth.currentUser;
  if (!user) return;

  try {
    await deleteDoc(doc(db, `users/${user.uid}/memories`, id));
  } catch (e) {
    console.error('Error deleting memory:', e);
  }
}
type GeminiLiveConnectCallbacks = {
    onopen: () => void;
    onmessage: (message: LiveServerMessage) => void | Promise<void>;
    onerror: (e: ErrorEvent) => void;
    onclose: (e: CloseEvent) => void;
};

// Replicates the @google/genai LiveSession interface for frontend compatibility
export interface GeminiLiveSession {
    sendRealtimeInput: (input: { media: { data: string; mimeType: string } }) => void;
    close: () => void;
}

export async function geminiLiveConnect(
  callbacks: GeminiLiveConnectCallbacks,
  config: { systemInstruction?: string; speechConfig?: { voiceConfig: { prebuiltVoiceConfig: { voiceName: string } } }; inputAudioTranscription?: {}; outputAudioTranscription?: {}; },
): Promise<GeminiLiveSession> {
    const ai = getAI();
    const sessionPromise = ai.live.connect({
        model: "gemini-2.5-flash-native-audio-preview-09-2025",
        callbacks: {
            onopen: callbacks.onopen,
            onmessage: (message) => callbacks.onmessage(message as any),
            onerror: (e) => callbacks.onerror(new ErrorEvent('error', { error: e })),
            onclose: (e) => callbacks.onclose(e as any),
        },
        config: {
            responseModalities: [Modality.AUDIO],
            speechConfig: config.speechConfig as any,
            systemInstruction: config.systemInstruction,
        },
    });

    const session = await sessionPromise;

    return {
        sendRealtimeInput: (input) => {
            session.sendRealtimeInput(input);
        },
        close: () => {
            session.close();
        },
    };
}
