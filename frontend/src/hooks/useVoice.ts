/**
 * useVoice — hook for browser-based voice input (Web Speech API) and
 * audio playback (edge-tts via backend).
 *
 * Provides a seamless text ↔ voice loop:
 *   mic → Web Speech API transcription → text
 *   text → backend /api/voice/speak → audio playback
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

// Extend Window for the vendor-prefixed SpeechRecognition
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

type SpeechRecognitionErrorEvent = Event & { error: string };

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

function getSpeechRecognition(): SpeechRecognitionConstructor | null {
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ??
    w.webkitSpeechRecognition ??
    null) as SpeechRecognitionConstructor | null;
}

// Sentence boundary regex — split on sentence-ending punctuation followed by
// whitespace (or newline). Handles ellipses (... or …), ?, !, and regular periods.
// Must be followed by space/newline to avoid splitting mid-abbreviation or mid-ellipsis.
const SENTENCE_RE = /(?:\.{2,}|[.?!…])\s/;

export interface UseVoiceReturn {
  /** Whether voice mode is enabled (mic + auto-play) */
  voiceEnabled: boolean;
  /** Toggle voice mode on/off */
  toggleVoice: () => void;
  /** Whether the mic is actively listening */
  isListening: boolean;
  /** Whether audio is currently playing */
  isPlaying: boolean;
  /** Whether the browser supports Web Speech API */
  speechSupported: boolean;
  /** Start listening via microphone */
  startListening: () => void;
  /** Stop listening */
  stopListening: () => void;
  /** Speak text via backend TTS and play the audio (full text, waits for complete synthesis) */
  speakResponse: (text: string) => Promise<void>;
  /** Feed streaming deltas — sentences are synthesized and queued as they complete */
  feedDelta: (delta: string) => void;
  /** Signal that the stream is done — flush any remaining text */
  flushSpeech: () => void;
  /** Stop any currently playing audio and clear the queue */
  stopPlayback: () => void;
  /** Current interim transcript while listening */
  transcript: string;
  /** Current voice mood (from voice evolution) */
  mood: string;
  /** Proactive presence message (if any) */
  presenceMessage: string | null;
  /** Clear the current presence message */
  clearPresence: () => void;
  /** Dream thoughts prepared while user was away */
  dreamThoughts: Array<{ dream_type: string; content: string }>;
  /** Clear consumed dream thoughts */
  clearDreams: () => void;
}

export function useVoice(): UseVoiceReturn {
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [mood, setMood] = useState("neutral");
  const [presenceMessage, setPresenceMessage] = useState<string | null>(null);
  const [dreamThoughts, setDreamThoughts] = useState<
    Array<{ dream_type: string; content: string }>
  >([]);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const onTranscriptRef = useRef<((text: string) => void) | null>(null);
  const voiceEnabledRef = useRef(false);
  const isPlayingRef = useRef(false);
  const gotFinalRef = useRef(false);

  // AudioContext — initialized on first user gesture to satisfy autoplay policy
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Sentence-chunked TTS queue
  const speechBufferRef = useRef("");
  const audioQueueRef = useRef<Blob[]>([]);
  const isSpeakingRef = useRef(false); // currently playing from queue
  const pendingSynthRef = useRef(0); // number of in-flight TTS requests
  const streamDoneRef = useRef(false); // flushSpeech was called

  const SpeechRecognition = getSpeechRecognition();
  const speechSupported = SpeechRecognition !== null;

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
      recognitionRef.current?.abort();
    };
  }, []);

  const toggleVoice = useCallback(() => {
    setVoiceEnabled((prev) => {
      const next = !prev;
      voiceEnabledRef.current = next;
      if (next) {
        // Initialize AudioContext on user gesture to satisfy autoplay policy
        if (!audioCtxRef.current) {
          audioCtxRef.current = new AudioContext();
        }
        if (audioCtxRef.current.state === "suspended") {
          audioCtxRef.current.resume();
        }
      } else {
        // Turning off — stop everything
        recognitionRef.current?.abort();
        setIsListening(false);
        setTranscript("");
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }
        // Clear the queue
        audioQueueRef.current = [];
        isSpeakingRef.current = false;
        speechBufferRef.current = "";
        streamDoneRef.current = false;
        setIsPlaying(false);
        isPlayingRef.current = false;
      }
      return next;
    });
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognition) return;
    if (isPlayingRef.current) return; // don't listen while she's speaking

    // Stop any existing recognition
    recognitionRef.current?.abort();
    gotFinalRef.current = false;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setIsListening(true);
      setTranscript("");
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      if (finalTranscript) {
        gotFinalRef.current = true;
        setTranscript(finalTranscript);
        onTranscriptRef.current?.(finalTranscript);
      } else {
        setTranscript(interimTranscript);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setIsListening(false);
      // "no-speech" is normal silence timeout — restart if voice still on
      if (
        event.error === "no-speech" &&
        voiceEnabledRef.current &&
        !isPlayingRef.current
      ) {
        setTimeout(() => startListening(), 300);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      // If we got a final transcript, Chat.tsx will send it and speakResponse
      // will play audio. After audio ends, speakResponse restarts listening.
      // If no final transcript (silence/abort), restart listening immediately.
      if (
        !gotFinalRef.current &&
        voiceEnabledRef.current &&
        !isPlayingRef.current
      ) {
        setTimeout(() => startListening(), 300);
      }
    };

    recognition.start();
  }, [SpeechRecognition]);

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  const speakResponse = useCallback(
    async (text: string) => {
      // Clean text for speech: strip task injection markers
      const cleaned = text.replace(/\[\[TASK:\{.*?\}\]\]/g, "").trim();
      if (!cleaned) return;

      stopPlayback();
      // Stop listening while she speaks
      recognitionRef.current?.abort();
      setIsListening(false);

      try {
        const blob = await api.speakText(cleaned);
        setIsPlaying(true);
        isPlayingRef.current = true;

        const ctx = audioCtxRef.current;
        if (ctx && ctx.state !== "closed") {
          if (ctx.state === "suspended") await ctx.resume();
          const arrayBuffer = await blob.arrayBuffer();
          const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
          const source = ctx.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(ctx.destination);
          source.onended = () => {
            setIsPlaying(false);
            isPlayingRef.current = false;
            if (voiceEnabledRef.current)
              setTimeout(() => startListening(), 400);
          };
          source.start(0);
        } else {
          // Fallback
          const url = URL.createObjectURL(blob);
          audioUrlRef.current = url;
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onended = () => {
            setIsPlaying(false);
            isPlayingRef.current = false;
            URL.revokeObjectURL(url);
            audioUrlRef.current = null;
            if (voiceEnabledRef.current)
              setTimeout(() => startListening(), 400);
          };
          audio.onerror = () => {
            setIsPlaying(false);
            isPlayingRef.current = false;
            if (voiceEnabledRef.current)
              setTimeout(() => startListening(), 400);
          };
          await audio.play();
        }
      } catch {
        setIsPlaying(false);
        isPlayingRef.current = false;
        if (voiceEnabledRef.current) setTimeout(() => startListening(), 400);
      }
    },
    [stopPlayback, startListening],
  );

  // ─── Sentence-chunked streaming TTS ─────────────────────────────────
  // Play the next blob from the queue, chaining sequentially.
  const playNextInQueue = useCallback(async () => {
    const blob = audioQueueRef.current.shift();
    if (!blob) {
      // Queue empty
      isSpeakingRef.current = false;
      setIsPlaying(false);
      isPlayingRef.current = false;
      // If stream is done and nothing left, resume mic
      if (streamDoneRef.current && voiceEnabledRef.current) {
        streamDoneRef.current = false;
        setTimeout(() => startListening(), 400);
      }
      return;
    }

    setIsPlaying(true);
    isPlayingRef.current = true;

    try {
      const ctx = audioCtxRef.current;
      if (ctx && ctx.state !== "closed") {
        // Use AudioContext (unlocked from user gesture) — no autoplay issues
        if (ctx.state === "suspended") await ctx.resume();
        const arrayBuffer = await blob.arrayBuffer();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);
        source.onended = () => playNextInQueue();
        source.start(0);
        console.debug(
          "[voice] playing chunk via AudioContext,",
          blob.size,
          "bytes",
        );
      } else {
        // Fallback to Audio element
        const url = URL.createObjectURL(blob);
        if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => {
          URL.revokeObjectURL(url);
          audioUrlRef.current = null;
          playNextInQueue();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(url);
          audioUrlRef.current = null;
          playNextInQueue();
        };
        await audio.play();
        console.debug(
          "[voice] playing chunk via Audio element,",
          blob.size,
          "bytes",
        );
      }
    } catch (err) {
      console.error("[voice] playback failed:", err);
      // Skip this chunk, try next
      playNextInQueue();
    }
  }, [startListening]);

  // Synthesize a chunk and enqueue it for playback
  const enqueueChunk = useCallback(
    async (text: string) => {
      const cleaned = text.replace(/\[\[TASK:\{.*?\}\]\]/g, "").trim();
      if (!cleaned) return;

      console.debug("[voice] synthesizing chunk:", cleaned.slice(0, 60));
      pendingSynthRef.current += 1;
      try {
        const blob = await api.speakText(cleaned);
        console.debug("[voice] got audio blob:", blob.size, "bytes");
        audioQueueRef.current.push(blob);
        // Start playing if not already
        if (!isSpeakingRef.current) {
          isSpeakingRef.current = true;
          playNextInQueue();
        }
      } catch (err) {
        console.error("[voice] synthesis failed:", err);
      } finally {
        pendingSynthRef.current -= 1;
      }
    },
    [playNextInQueue],
  );

  /** Feed streaming deltas from the chat response. Sentences are synthesized
   *  and queued as they complete, so audio starts before the full response. */
  const feedDelta = useCallback(
    (delta: string) => {
      if (!voiceEnabledRef.current) return;

      speechBufferRef.current += delta;

      // Stop listening while response is streaming
      if (!isSpeakingRef.current && !isPlayingRef.current) {
        recognitionRef.current?.abort();
        setIsListening(false);
      }

      // Extract complete sentences from the buffer
      let buf = speechBufferRef.current;
      let match = SENTENCE_RE.exec(buf);
      while (match) {
        const sentenceEnd = match.index + match[0].length;
        const sentence = buf.slice(0, sentenceEnd).trim();
        if (sentence) {
          console.debug("[voice] sentence detected:", sentence.slice(0, 80));
          void enqueueChunk(sentence);
        }
        buf = buf.slice(sentenceEnd);
        SENTENCE_RE.lastIndex = 0; // reset for non-global regex safety
        match = SENTENCE_RE.exec(buf);
      }
      speechBufferRef.current = buf;
    },
    [enqueueChunk],
  );

  /** Signal that the streaming response is complete — flush remaining text. */
  const flushSpeech = useCallback(() => {
    streamDoneRef.current = true;
    const remaining = speechBufferRef.current.trim();
    speechBufferRef.current = "";
    console.debug(
      "[voice] flushSpeech, remaining:",
      remaining.slice(0, 80) || "(empty)",
    );
    if (remaining) {
      void enqueueChunk(remaining);
    } else if (!isSpeakingRef.current && audioQueueRef.current.length === 0) {
      // Nothing to play — resume mic immediately
      streamDoneRef.current = false;
      if (voiceEnabledRef.current) {
        setTimeout(() => startListening(), 400);
      }
    }
  }, [enqueueChunk, startListening]);

  // Auto-start listening when voice mode is toggled on
  useEffect(() => {
    if (voiceEnabled && speechSupported && !isPlaying) {
      startListening();
    }
    // Only react to voiceEnabled toggling on
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceEnabled]);

  // ─── Proactive presence polling ─────────────────────────────────────
  useEffect(() => {
    if (!voiceEnabled) return;

    const poll = async () => {
      try {
        const { presence } = await api.getVoicePresence();
        if (presence?.message) {
          setPresenceMessage(presence.message);
          // Speak the proactive message
          void enqueueChunk(presence.message);
        }
      } catch {
        // silent — presence polling is best-effort
      }

      try {
        const profile = await api.getVoiceProfile();
        if (profile?.mood) setMood(profile.mood);
      } catch {
        // silent
      }

      // check for dream thoughts (prepared while away)
      try {
        const { dreams } = await api.getVoiceDreams();
        if (dreams && dreams.length > 0) {
          setDreamThoughts(
            dreams.map((d) => ({
              dream_type: d.dream_type,
              content: d.content,
            })),
          );
        }
      } catch {
        // silent
      }
    };

    // Poll every 30 seconds
    const interval = setInterval(poll, 30_000);
    // Initial check
    void poll();

    return () => clearInterval(interval);
  }, [voiceEnabled, enqueueChunk]);

  const clearPresence = useCallback(() => {
    setPresenceMessage(null);
  }, []);

  const clearDreams = useCallback(() => {
    setDreamThoughts([]);
  }, []);

  return {
    voiceEnabled,
    toggleVoice,
    isListening,
    isPlaying,
    speechSupported,
    startListening,
    stopListening,
    speakResponse,
    feedDelta,
    flushSpeech,
    stopPlayback,
    transcript,
    mood,
    presenceMessage,
    clearPresence,
    dreamThoughts,
    clearDreams,
  };
}

// Re-export the ref setter so Chat can wire up the transcript callback
export function setTranscriptCallback(
  hook: UseVoiceReturn & {
    _onTranscriptRef?: React.MutableRefObject<((text: string) => void) | null>;
  },
  callback: (text: string) => void,
): void {
  // This is handled internally via the ref
  void hook;
  void callback;
}
