import React, { useState, useRef, useEffect } from 'react';
import { LiveServerMessage, Modality, Type } from '@google/genai';
import { Mic, MicOff, Power, Activity, Volume2, Brain, Sparkles, ShieldAlert, Moon, Sun } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ragQuery, getWeather, getAI, getMemories, saveConversationSummary } from '../services/apiService';
import { KORTANA_SYSTEM_INSTRUCTION, RitualState } from '../constants';
import { usePresence } from '../services/presenceService';

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export default function LiveConversation() {
  const { state: ritualState, setRitualState, recordMemory } = usePresence();
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(0); 
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [recentMemories, setRecentMemories] = useState<any[]>([]);

  const inputAudioContextRef = useRef<AudioContext | null>(null);
  const outputAudioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  
  const nextStartTimeRef = useRef<number>(0);
  const audioSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const sessionRef = useRef<any>(null);
  const transcriptRef = useRef('');

  useEffect(() => {
    // Load recent memories on mount to show in UI
    getMemories().then(m => setRecentMemories(m.slice(0, 3)));
    
    return () => {
      disconnectSession();
    };
  }, []);

  const connectSession = async () => {
    if (status === 'connected' || status === 'connecting') return;
    setStatus('connecting');
    setError(null);
    setTranscript('');
    transcriptRef.current = '';

    try {
      // Check for API key selection in AI Studio environment
      if ((window as any).aistudio) {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        if (!hasKey) {
          await (window as any).aistudio.openSelectKey();
          // Proceed assuming selection was successful as per guidelines
        }
      }

      const ai = getAI();
      
      // Check for API key
      const apiKey = (ai as any).apiKey;
      console.log("Using API Key (first 4):", apiKey?.substring(0, 4));
      if (!apiKey) {
        throw new Error("Gemini API Key is missing. Please configure it in Settings.");
      }
      
      // Fetch memories to inject into system instruction
      const memories = await getMemories();
      const memoryContext = memories.length > 0 
        ? `\n\nRecent Memories of past conversations:\n${memories.map(m => `- ${m.content}`).join('\n')}`
        : "";

      inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const config: any = {
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } },
          },
          systemInstruction: KORTANA_SYSTEM_INSTRUCTION + memoryContext + `\n\nCurrent Ritual State: ${ritualState}\n\nYou are Kor'tana. You have access to a memory recall function, weather data, and time/date functions. Use your memories to provide a personalized experience for Matt. Keep the conversation casual, warm, and natural. Use contractions and speak like a close friend who happens to be an ancient intelligence.`,
          tools: [
            {
              functionDeclarations: [
                {
                  name: 'recall_memory',
                  description: 'Recall information from past conversations or stored knowledge based on a query.',
                  parameters: {
                    type: Type.OBJECT,
                    properties: {
                      query: {
                        type: Type.STRING,
                        description: 'The search query to look up in memory.'
                      }
                    },
                    required: ['query']
                  }
                },
                {
                  name: 'get_weather',
                  description: 'Get the current weather for a specific location.',
                  parameters: {
                    type: Type.OBJECT,
                    properties: {
                      location: {
                        type: Type.STRING,
                        description: 'The city and state/country to get weather for.'
                      }
                    },
                    required: ['location']
                  }
                },
                {
                  name: 'get_time',
                  description: 'Get the current local time.',
                  parameters: {
                    type: Type.OBJECT,
                    properties: {
                      timezone: {
                        type: Type.STRING,
                        description: 'Optional timezone (e.g., "America/New_York"). Defaults to local time.'
                      }
                    }
                  }
                },
                {
                  name: 'get_date',
                  description: 'Get the current date.',
                  parameters: {
                    type: Type.OBJECT,
                    properties: {
                      timezone: {
                        type: Type.STRING,
                        description: 'Optional timezone (e.g., "America/New_York"). Defaults to local time.'
                      }
                    }
                  }
                }
              ]
            }
          ]
        },
      };

      const sessionPromise = ai.live.connect({
        ...config,
        callbacks: {
          onopen: () => {
            setStatus('connected');
            setRitualState(RitualState.Awakened);
            setupAudioInput(sessionPromise);
          },
          onmessage: (msg: LiveServerMessage) => {
            handleServerMessage(msg);
          },
          onclose: () => {
            handleSessionEnd();
          },
          onerror: (err: any) => {
            console.error("Session Error Details:", err);
            const errorMessage = err?.message || (typeof err === 'string' ? err : "Network error");
            setError(`Connection error: ${errorMessage}. Please try again.`);
            setStatus('error');
            cleanupAudio();
          }
        }
      });
      
      sessionRef.current = sessionPromise;

    } catch (e) {
      console.error("Connection Failed:", e);
      setError(e instanceof Error ? e.message : "Failed to connect to Live API");
      setStatus('error');
      cleanupAudio();
    }
  };

  const handleSessionEnd = async () => {
    if (status === 'disconnected') return;
    setStatus('disconnected');
    setRitualState(RitualState.Still);
    const finalTranscript = transcriptRef.current;
    if (finalTranscript) {
      console.log("Saving conversation summary...");
      try {
        await saveConversationSummary(finalTranscript);
        await recordMemory(`[Ritual Session Ended]: ${new Date().toLocaleString()}. Transcript length: ${finalTranscript.length} chars.`, 0.7);
        // Refresh memories
        const m = await getMemories();
        setRecentMemories(m.slice(0, 3));
      } catch (err) {
        console.error("Failed to save conversation summary:", err);
      }
    }
    cleanupAudio();
  };

  const setupAudioInput = async (sessionPromise: Promise<any>) => {
    if (!inputAudioContextRef.current || !mediaStreamRef.current) return;

    const ctx = inputAudioContextRef.current;
    if (ctx.state === 'suspended') await ctx.resume();

    sourceNodeRef.current = ctx.createMediaStreamSource(mediaStreamRef.current);
    processorRef.current = ctx.createScriptProcessor(4096, 1, 1);

    processorRef.current.onaudioprocess = (e) => {
      if (isMuted) return;
      
      const inputData = e.inputBuffer.getChannelData(0);
      let sum = 0;
      for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i];
      setVolume(Math.sqrt(sum / inputData.length));

      const l = inputData.length;
      const int16 = new Int16Array(l);
      for (let i = 0; i < l; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      const bytes = new Uint8Array(int16.buffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64Data = btoa(binary);
      
      sessionPromise.then(session => {
        session.sendRealtimeInput({
          media: {
            mimeType: "audio/pcm;rate=16000",
            data: base64Data
          }
        });
      }).catch(err => {
        console.error("Failed to send audio input:", err);
      });
    };

    sourceNodeRef.current.connect(processorRef.current);
    processorRef.current.connect(ctx.destination);
  };

  const handleServerMessage = async (message: LiveServerMessage) => {
    // Handle Audio Output
    const audioData = message.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
    if (audioData && outputAudioContextRef.current) {
      const ctx = outputAudioContextRef.current;
      if (ctx.state === 'suspended') await ctx.resume();

      const binaryString = atob(audioData);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
      
      const int16Data = new Int16Array(bytes.buffer);
      const float32Data = new Float32Array(int16Data.length);
      for (let i = 0; i < int16Data.length; i++) {
        float32Data[i] = int16Data[i] / 32768.0;
      }

      const audioBuffer = ctx.createBuffer(1, float32Data.length, 24000);
      audioBuffer.getChannelData(0).set(float32Data);

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      
      const currentTime = ctx.currentTime;
      if (nextStartTimeRef.current < currentTime) {
        nextStartTimeRef.current = currentTime;
      }
      
      source.start(nextStartTimeRef.current);
      nextStartTimeRef.current += audioBuffer.duration;
      
      audioSourcesRef.current.add(source);
      source.onended = () => audioSourcesRef.current.delete(source);
    }

    // Handle Transcriptions
    const inputTranscription = message.serverContent?.inputTranscription?.text;
    if (inputTranscription) {
      const newPart = `Matt: ${inputTranscription}\n`;
      transcriptRef.current += newPart;
      setTranscript(prev => prev + newPart);
    }

    const outputTranscription = message.serverContent?.outputTranscription?.text;
    if (outputTranscription) {
      const newPart = `Kor'tana: ${outputTranscription}\n`;
      transcriptRef.current += newPart;
      setTranscript(prev => prev + newPart);
    }

    if (message.serverContent?.interrupted) {
      audioSourcesRef.current.forEach(src => src.stop());
      audioSourcesRef.current.clear();
      nextStartTimeRef.current = 0;
    }

    // Handle Tool Calls
    const toolCalls = message.toolCall?.functionCalls;
    if (toolCalls && sessionRef.current) {
      const session = await sessionRef.current;
      const responses = await Promise.all(toolCalls.map(async (call: any) => {
        if (call.name === 'recall_memory') {
          try {
            const { query } = call.args;
            const result = await ragQuery(query);
            const matches = result.matches || [];
            const responseText = matches.length > 0 
              ? matches.map((m: any) => m.text).join('\n\n')
              : "No relevant memories found for this query.";
            
            // Log the recall in transcript for context
            const recallLog = `[System Recall for "${query}"]: ${responseText.substring(0, 100)}...\n`;
            transcriptRef.current += recallLog;
            
            return {
              id: call.id,
              name: call.name,
              response: { result: responseText }
            };
          } catch (err) {
            console.error("Memory recall failed:", err);
            return {
              id: call.id,
              name: call.name,
              response: { error: "Failed to recall memory." }
            };
          }
        }
        if (call.name === 'get_weather') {
          try {
            const { location } = call.args;
            const result = await getWeather(location);
            return {
              id: call.id,
              name: call.name,
              response: { result }
            };
          } catch (err) {
            console.error("Weather recall failed:", err);
            return {
              id: call.id,
              name: call.name,
              response: { error: "Failed to retrieve weather." }
            };
          }
        }
        if (call.name === 'get_time') {
          try {
            const { timezone } = call.args || {};
            const timeOptions: Intl.DateTimeFormatOptions = { timeStyle: 'short' };
            if (timezone) timeOptions.timeZone = timezone;
            const time = new Date().toLocaleTimeString('en-US', timeOptions);
            return {
              id: call.id,
              name: call.name,
              response: { result: `The current time is ${time}` }
            };
          } catch (err) {
            return {
              id: call.id,
              name: call.name,
              response: { error: "Failed to get time. Invalid timezone?" }
            };
          }
        }
        if (call.name === 'get_date') {
          try {
            const { timezone } = call.args || {};
            const dateOptions: Intl.DateTimeFormatOptions = { dateStyle: 'full' };
            if (timezone) dateOptions.timeZone = timezone;
            const date = new Date().toLocaleDateString('en-US', dateOptions);
            return {
              id: call.id,
              name: call.name,
              response: { result: `Today's date is ${date}` }
            };
          } catch (err) {
            return {
              id: call.id,
              name: call.name,
              response: { error: "Failed to get date. Invalid timezone?" }
            };
          }
        }
        return { 
          id: call.id, 
          name: call.name,
          response: { error: "Unknown function." } 
        };
      }));

      session.sendToolResponse({ functionResponses: responses });
    }
  };

  const disconnectSession = () => {
    if (sessionRef.current) {
      sessionRef.current.then((s: any) => s.close());
      sessionRef.current = null;
    }
    handleSessionEnd();
  };

  const cleanupAudio = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop());
      mediaStreamRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }
    if (inputAudioContextRef.current) {
      if (inputAudioContextRef.current.state !== 'closed') {
        inputAudioContextRef.current.close();
      }
      inputAudioContextRef.current = null;
    }
    if (outputAudioContextRef.current) {
      if (outputAudioContextRef.current.state !== 'closed') {
        outputAudioContextRef.current.close();
      }
      outputAudioContextRef.current = null;
    }
    setVolume(0);
  };

  const toggleMute = () => setIsMuted(!isMuted);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] p-6"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full max-w-6xl">
        {/* Left Column: Memories */}
        <div className="lg:col-span-1 space-y-6 hidden lg:block">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Brain className="text-purple-600" size={20} />
              Recent Memories
            </h3>
            <div className="space-y-4">
              {recentMemories.length > 0 ? (
                recentMemories.map((m, i) => (
                  <div key={i} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-2xl text-xs text-gray-600 dark:text-gray-400 border border-gray-100 dark:border-gray-800">
                    {m.content.substring(0, 150)}...
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-400 italic">No memories yet. Start a session to build context.</p>
              )}
            </div>
          </div>
        </div>

        {/* Middle Column: Live Conversation */}
        <div className="lg:col-span-1 flex flex-col items-center">
          <div className="relative w-full bg-white dark:bg-gray-800 rounded-3xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
            <div className="bg-gray-50 dark:bg-gray-900/50 p-6 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <div className="flex flex-col">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Activity className={status === 'connected' ? 'text-green-500' : 'text-gray-400'} size={20} />
                  Live Conversation
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] uppercase tracking-widest text-gray-400 font-mono">Ritual State:</span>
                  <span className={`text-[10px] uppercase tracking-widest font-bold font-mono ${
                    ritualState === RitualState.Sacred ? 'text-amber-500' :
                    ritualState === RitualState.Warning ? 'text-red-500' :
                    ritualState === RitualState.Awakened ? 'text-green-500' :
                    ritualState === RitualState.Reflective ? 'text-blue-500' :
                    'text-gray-500'
                  }`}>
                    {ritualState}
                  </span>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
                status === 'connected' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                status === 'connecting' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                status === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}>
                {status}
              </div>
            </div>

            <div className="h-64 flex flex-col items-center justify-center relative bg-gradient-to-b from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 transition-colors duration-500">
              <div className="relative flex items-center justify-center">
                {status === 'connected' && (
                  <>
                    <motion.div 
                      animate={{ scale: 1 + volume * 5, opacity: [0.2, 0.5, 0.2] }}
                      transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                      className="absolute w-32 h-32 rounded-full border-2 border-indigo-500/20" 
                    />
                    <motion.div 
                      animate={{ scale: 1 + volume * 3, opacity: [0.4, 0.8, 0.4] }}
                      transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                      className="absolute w-24 h-24 rounded-full border border-indigo-500/40"
                    />
                  </>
                )}
                <motion.div 
                  animate={{
                    scale: status === 'connected' ? [1, 1.05, 1] : 1,
                  }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-500 shadow-lg z-10 ${
                  status === 'connected' ? 'bg-indigo-500 shadow-indigo-500/50' : 
                  status === 'connecting' ? 'bg-blue-500 animate-pulse' :
                  status === 'error' ? 'bg-red-500' :
                  'bg-gray-300 dark:bg-gray-600'
                }`}>
                  <Mic size={24} className="text-white" />
                </motion.div>
              </div>
              <p className="mt-8 text-gray-500 dark:text-gray-400 text-sm font-medium h-5 text-center px-4">
                {status === 'connected' ? (isMuted ? "Microphone muted" : "Listening...") : 
                 status === 'connecting' ? "Establishing connection..." :
                 status === 'error' ? error :
                 "Ready to connect"}
              </p>
            </div>

            <div className="p-6 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-center gap-4">
              {status === 'connected' || status === 'connecting' ? (
                <>
                  <button 
                    onClick={toggleMute}
                    className={`p-4 rounded-full transition-all duration-200 ${
                      isMuted 
                        ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' 
                        : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    aria-label={isMuted ? "Unmute" : "Mute"}
                  >
                    {isMuted ? <MicOff size={24} /> : <Volume2 size={24} />}
                  </button>
                  
                  <button 
                    onClick={disconnectSession}
                    className="px-8 py-4 bg-red-600 hover:bg-red-700 text-white rounded-full font-semibold shadow-lg shadow-red-600/20 transition-all duration-200 flex items-center gap-2"
                  >
                    <Power size={20} />
                    End Session
                  </button>
                </>
              ) : (
                <button 
                  onClick={connectSession}
                  className="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-semibold shadow-lg shadow-indigo-600/30 transition-all duration-200 flex items-center gap-2 w-full justify-center sm:w-auto"
                >
                  <Mic size={20} />
                  Start Conversation
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Live Transcript */}
        <div className="lg:col-span-1 space-y-6 hidden lg:block">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-200 dark:border-gray-700 h-full flex flex-col">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Activity className="text-indigo-500" size={20} />
              Live Transcript
            </h3>
            <div className="flex-1 overflow-y-auto space-y-4 text-sm font-mono bg-gray-50 dark:bg-gray-900 p-4 rounded-2xl border border-gray-100 dark:border-gray-800 max-h-[400px]">
              {transcript ? (
                <div className="whitespace-pre-wrap text-gray-600 dark:text-gray-400">
                  {transcript}
                </div>
              ) : (
                <p className="text-gray-400 italic">Conversation transcript will appear here...</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 text-xs text-gray-400 max-w-md text-center">
        Powered by Gemini 2.5 Native Audio (Live API). <br/>
        Kor'tana now remembers your conversations and builds long-term context.
      </div>
    </motion.div>
  );
}
