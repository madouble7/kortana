import {
  AlertTriangle,
  ClipboardList,
  Loader2,
  Mic,
  MicOff,
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { getCachedModelLaneSummary } from "../hooks/useRuntimeTelemetry";
import { useVoice } from "../hooks/useVoice";
import { api, type ApiError } from "../lib/api";
import {
  cn,
  formatCompactNumber,
  formatCompactUsd,
  formatRelativeTime,
} from "../lib/utils";
import type {
  ChatHistoryEntry,
  ChatPhase,
  ChatUsageMetrics,
  Message,
  ModelLaneSummary,
} from "../types";

// Stable session ID persisted in localStorage so history survives page refreshes.
function getSessionId(): string {
  const key = "kortana_session_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem(key, id);
  }
  return id;
}

function buildChatHistory(messages: Message[]): ChatHistoryEntry[] {
  return messages
    .filter(
      (message): message is Message & { role: "user" | "assistant" } =>
        message.role === "user" || message.role === "assistant",
    )
    .slice(-10)
    .map((message) => ({
      role: message.role,
      content: message.content,
      phase: message.phase,
    }));
}

function formatChatPhase(phase: ChatPhase): string {
  return phase.replace(/_/g, " ");
}

type ChatNoticeTone = "info" | "warning" | "error";

interface ChatNotice {
  message: string;
  tone: ChatNoticeTone;
}

interface ActiveStreamUsage {
  messageId: string;
  promptTokens: number;
  provider?: string;
  model?: string;
  responseText: string;
  baselineSummary: ModelLaneSummary | null;
  latestSummary: ModelLaneSummary | null;
  sessionCostBaseUsd: number;
  sessionTokensBase: number;
  actualInputTokens?: number;
  actualOutputTokens?: number;
}

function estimateTokens(text: string): number {
  const normalized = text.trim();
  if (!normalized) {
    return 0;
  }
  return Math.max(1, Math.round(normalized.length / 4));
}

function getProviderRates(
  summary: ModelLaneSummary | null,
  provider?: string,
): { inputCostPer1k: number; outputCostPer1k: number } | null {
  if (!summary || !provider) {
    return null;
  }

  const details = summary.cost_router?.cost?.providers?.[provider];
  if (!details) {
    return null;
  }

  return {
    inputCostPer1k: details.input_cost_per_1k ?? 0,
    outputCostPer1k: details.output_cost_per_1k ?? 0,
  };
}

function getProviderTokenTotal(
  usage: ModelLaneSummary["runtime_usage"] | undefined,
  provider?: string,
): number {
  if (!usage || !provider) {
    return 0;
  }
  const memoryTokens = usage.memory?.by_provider_tokens?.[provider] ?? 0;
  const persistedTokens = usage.persisted?.by_provider_tokens?.[provider] ?? 0;
  return Math.max(memoryTokens, persistedTokens);
}

function getTelemetryTokenDelta(
  baseline: ModelLaneSummary | null,
  latest: ModelLaneSummary | null,
  provider?: string,
): number {
  if (!baseline || !latest || !provider) {
    return 0;
  }

  const baselineTotal = getProviderTokenTotal(baseline.runtime_usage, provider);
  const latestTotal = getProviderTokenTotal(latest.runtime_usage, provider);
  return Math.max(0, latestTotal - baselineTotal);
}

function buildUsageMetrics(
  tracker: ActiveStreamUsage,
  options: {
    live: boolean;
    source: ChatUsageMetrics["source"];
    telemetryTokens?: number;
  },
): ChatUsageMetrics {
  const { live, source, telemetryTokens = 0 } = options;
  const estimatedOutputTokens = estimateTokens(tracker.responseText);
  const resolvedInputTokens = tracker.actualInputTokens ?? tracker.promptTokens;
  const resolvedOutputTokens =
    tracker.actualOutputTokens ?? estimatedOutputTokens;
  const resolvedTokens = Math.max(
    resolvedInputTokens + resolvedOutputTokens,
    telemetryTokens,
  );

  const rates = getProviderRates(tracker.latestSummary, tracker.provider);
  const inputTokensForCost = tracker.actualInputTokens ?? tracker.promptTokens;
  const outputTokensForCost =
    tracker.actualOutputTokens ?? estimatedOutputTokens;
  const costUsd = rates
    ? (inputTokensForCost / 1000) * rates.inputCostPer1k +
      (outputTokensForCost / 1000) * rates.outputCostPer1k
    : 0;

  return {
    tokens: resolvedTokens,
    inputTokens: tracker.actualInputTokens,
    outputTokens: tracker.actualOutputTokens,
    costUsd,
    sessionCostUsd: tracker.sessionCostBaseUsd + costUsd,
    live,
    estimated:
      tracker.actualInputTokens === undefined ||
      tracker.actualOutputTokens === undefined,
    source,
  };
}

function tokenLabel(usage: ChatUsageMetrics): string {
  return `${usage.estimated ? "~" : ""}${formatCompactNumber(usage.tokens)} tok`;
}

function costLabel(usage: ChatUsageMetrics): string {
  return `${usage.estimated ? "~" : ""}${formatCompactUsd(usage.costUsd)}`;
}

function toChatNotice(error: unknown, fallback: string): ChatNotice {
  const apiError = error as Partial<ApiError> | undefined;
  if (apiError?.isAborted) {
    return {
      tone: "info",
      message: "Generation stopped.",
    };
  }
  if (apiError?.isRateLimited) {
    return {
      tone: "warning",
      message: apiError.retryAfterSeconds
        ? `Rate limit reached. Try again in ${apiError.retryAfterSeconds}s.`
        : "Rate limit reached. Please wait a moment and try again.",
    };
  }
  if (apiError?.isOffline) {
    return {
      tone: "warning",
      message: "Backend is unreachable right now. Check the API and try again.",
    };
  }
  if (error instanceof Error && error.message) {
    return { tone: "error", message: error.message };
  }
  return { tone: "error", message: fallback };
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sessionId] = useState(() => getSessionId());
  const [notice, setNotice] = useState<ChatNotice | null>(null);
  const [sessionCostUsd, setSessionCostUsd] = useState(0);
  const [sessionTokens, setSessionTokens] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const deltaBufferRef = useRef("");
  const deltaTargetRef = useRef<string | null>(null);
  const deltaFrameRef = useRef<number | null>(null);
  const usageFrameRef = useRef<number | null>(null);
  const usageTargetRef = useRef<{
    messageId: string;
    usage: ChatUsageMetrics;
  } | null>(null);
  const activeStreamUsageRef = useRef<ActiveStreamUsage | null>(null);
  const retryPromptRef = useRef<string | null>(null);

  // Voice mode (mic input + audio playback)
  const {
    voiceEnabled,
    toggleVoice,
    isListening,
    speechSupported,
    startListening,
    stopListening,
    feedDelta: feedVoiceDelta,
    flushSpeech,
    transcript,
    presenceMessage,
    clearPresence,
    dreamThoughts,
    clearDreams,
  } = useVoice();

  // When mic produces a final transcript, auto-send it
  const prevTranscriptRef = useRef("");
  useEffect(() => {
    if (
      transcript &&
      transcript !== prevTranscriptRef.current &&
      !isListening
    ) {
      prevTranscriptRef.current = transcript;
      setInput(transcript);
      // Auto-submit after a short delay to let state settle
      const timer = setTimeout(() => {
        const form = document.querySelector<HTMLFormElement>("form");
        form?.requestSubmit();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [transcript, isListening]);

  // Proactive presence — inject kor'tana's reach-out as a chat message
  useEffect(() => {
    if (presenceMessage) {
      const presenceId = `presence-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: presenceId,
          role: "assistant" as const,
          content: presenceMessage,
          timestamp: new Date().toISOString(),
        },
      ]);
      clearPresence();
    }
  }, [presenceMessage, clearPresence]);

  // Dream state — inject thoughts kor'tana prepared while matt was away
  useEffect(() => {
    if (dreamThoughts.length > 0) {
      const dreamContent = dreamThoughts.map((d) => d.content).join("\n\n");
      setMessages((prev) => [
        ...prev,
        {
          id: `dream-${Date.now()}`,
          role: "assistant" as const,
          content: `*thoughts while you were away...*\n\n${dreamContent}`,
          timestamp: new Date().toISOString(),
        },
      ]);
      clearDreams();
    }
  }, [dreamThoughts, clearDreams]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const updateMessage = useCallback(
    (id: string, updater: (message: Message) => Message) => {
      setMessages((prev) =>
        prev.map((message) => (message.id === id ? updater(message) : message)),
      );
    },
    [],
  );

  const flushDeltaBuffer = () => {
    const targetId = deltaTargetRef.current;
    const buffered = deltaBufferRef.current;
    if (!targetId || !buffered) {
      deltaFrameRef.current = null;
      return;
    }

    deltaBufferRef.current = "";
    deltaFrameRef.current = null;
    updateMessage(targetId, (message) => ({
      ...message,
      content: message.content + buffered,
    }));
  };

  const queueDelta = (messageId: string, delta: string) => {
    deltaTargetRef.current = messageId;
    deltaBufferRef.current += delta;
    if (deltaFrameRef.current !== null) {
      return;
    }
    deltaFrameRef.current = window.requestAnimationFrame(flushDeltaBuffer);
  };

  const flushDeltaIfNeeded = () => {
    if (deltaFrameRef.current !== null) {
      window.cancelAnimationFrame(deltaFrameRef.current);
    }
    flushDeltaBuffer();
  };

  const flushUsageUpdate = useCallback(() => {
    const pending = usageTargetRef.current;
    usageFrameRef.current = null;
    usageTargetRef.current = null;
    if (!pending) {
      return;
    }

    updateMessage(pending.messageId, (message) => ({
      ...message,
      usage: pending.usage,
    }));
  }, [updateMessage]);

  const queueUsageUpdate = useCallback(
    (messageId: string, usage: ChatUsageMetrics) => {
      usageTargetRef.current = { messageId, usage };
      if (usageFrameRef.current !== null) {
        return;
      }
      usageFrameRef.current = window.requestAnimationFrame(flushUsageUpdate);
    },
    [flushUsageUpdate],
  );

  const refreshActiveUsage = useCallback(
    (
      source: ChatUsageMetrics["source"],
      { live = true }: { live?: boolean } = {},
    ) => {
      const tracker = activeStreamUsageRef.current;
      if (!tracker) {
        return;
      }

      const telemetryTokens = getTelemetryTokenDelta(
        tracker.baselineSummary,
        tracker.latestSummary,
        tracker.provider,
      );
      queueUsageUpdate(
        tracker.messageId,
        buildUsageMetrics(tracker, {
          live,
          source,
          telemetryTokens,
        }),
      );
    },
    [queueUsageUpdate],
  );

  // Load persisted history from DB on mount
  useEffect(() => {
    api
      .getChatHistory(sessionId, 40)
      .then((data) => {
        if (data?.messages?.length) {
          const loaded: Message[] = data.messages.map((m, i: number) => ({
            id: `hist_${m.created_at ?? i}_${m.role}_${i}`,
            role: m.role,
            content: m.content,
            timestamp: m.created_at ?? new Date().toISOString(),
            phase: m.phase,
            provider: m.provider,
            model: m.model,
            lane: m.lane,
            response_id: m.response_id,
            stateful: m.stateful,
            used_previous_response_id: m.used_previous_response_id,
          }));
          setMessages(loaded);
        }
      })
      .catch((error: unknown) => {
        setNotice(
          toChatNotice(error, "Previous chat history could not be loaded."),
        );
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    return () => {
      if (deltaFrameRef.current !== null) {
        window.cancelAnimationFrame(deltaFrameRef.current);
      }
      if (usageFrameRef.current !== null) {
        window.cancelAnimationFrame(usageFrameRef.current);
      }
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!loading) {
      return undefined;
    }

    let cancelled = false;
    let timeoutId: number | null = null;

    const pollTelemetry = async () => {
      const tracker = activeStreamUsageRef.current;
      if (!tracker) {
        return;
      }

      try {
        const summary = await getCachedModelLaneSummary(1200);
        if (cancelled) {
          return;
        }
        const activeTracker = activeStreamUsageRef.current;
        if (!activeTracker || activeTracker.messageId !== tracker.messageId) {
          return;
        }
        activeTracker.latestSummary = summary;
        if (!activeTracker.baselineSummary) {
          activeTracker.baselineSummary = summary;
        }
        refreshActiveUsage("telemetry");
      } catch {
        // The live badge is additive telemetry. Keep the chat path resilient if this fails.
      } finally {
        if (!cancelled) {
          timeoutId = window.setTimeout(() => {
            void pollTelemetry();
          }, 1200);
        }
      }
    };

    void pollTelemetry();

    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [loading, refreshActiveUsage]);

  const sendPrompt = async (promptText: string) => {
    if (!promptText.trim() || loading) return;
    setNotice(null);
    retryPromptRef.current = null;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: promptText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const assistantMessageId = `${Date.now() + 1}`;
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      phase: "commentary",
      streaming: true,
    };

    setMessages((prev) => [...prev, assistantPlaceholder]);

    const promptTokens = estimateTokens(promptText);
    activeStreamUsageRef.current = {
      messageId: assistantMessageId,
      promptTokens,
      responseText: "",
      baselineSummary: null,
      latestSummary: null,
      sessionCostBaseUsd: sessionCostUsd,
      sessionTokensBase: sessionTokens,
    };
    queueUsageUpdate(
      assistantMessageId,
      buildUsageMetrics(activeStreamUsageRef.current, {
        live: true,
        source: "local",
      }),
    );

    void getCachedModelLaneSummary(1200)
      .then((summary) => {
        const tracker = activeStreamUsageRef.current;
        if (!tracker || tracker.messageId !== assistantMessageId) {
          return;
        }
        tracker.baselineSummary = summary;
        tracker.latestSummary = summary;
        refreshActiveUsage("telemetry");
      })
      .catch(() => {
        // Live counters can continue from local estimation if runtime telemetry is unavailable.
      });

    try {
      const history = buildChatHistory(messages);
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      await api.sendChatMessageStream(
        promptText,
        history,
        conversationId || undefined,
        sessionId,
        {
          onStart: (payload) => {
            const tracker = activeStreamUsageRef.current;
            if (tracker && tracker.messageId === assistantMessageId) {
              tracker.provider = payload.provider;
              tracker.model = payload.model;
              if (typeof payload.input_tokens === "number") {
                tracker.actualInputTokens = payload.input_tokens;
              }
              if (typeof payload.output_tokens === "number") {
                tracker.actualOutputTokens = payload.output_tokens;
              }
              refreshActiveUsage("local");
            }
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              provider: payload.provider,
              model: payload.model,
              lane: payload.lane,
              stateful: payload.stateful,
              used_previous_response_id: payload.used_previous_response_id,
              input_tokens: payload.input_tokens,
              output_tokens: payload.output_tokens,
            }));
          },
          onPhase: (phase) => {
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              phase,
            }));
          },
          onDelta: (delta) => {
            const tracker = activeStreamUsageRef.current;
            if (tracker && tracker.messageId === assistantMessageId) {
              tracker.responseText += delta;
              refreshActiveUsage("local");
            }
            queueDelta(assistantMessageId, delta);
            feedVoiceDelta(delta);
          },
          onFinal: (response) => {
            flushDeltaIfNeeded();
            if (response.conversation_id && !conversationId) {
              setConversationId(response.conversation_id);
            }

            const tracker = activeStreamUsageRef.current;
            let finalUsage: ChatUsageMetrics | undefined;
            if (tracker && tracker.messageId === assistantMessageId) {
              tracker.provider = response.provider ?? tracker.provider;
              tracker.model = response.model ?? tracker.model;
              tracker.responseText =
                response.response || response.message || tracker.responseText;
              if (typeof response.input_tokens === "number") {
                tracker.actualInputTokens = response.input_tokens;
              }
              if (typeof response.output_tokens === "number") {
                tracker.actualOutputTokens = response.output_tokens;
              }
              const telemetryTokens = getTelemetryTokenDelta(
                tracker.baselineSummary,
                tracker.latestSummary,
                tracker.provider,
              );
              finalUsage = buildUsageMetrics(tracker, {
                live: false,
                source:
                  tracker.actualInputTokens !== undefined ||
                  tracker.actualOutputTokens !== undefined
                    ? "openai"
                    : telemetryTokens > 0
                      ? "telemetry"
                      : "local",
                telemetryTokens,
              });
              setSessionCostUsd(
                tracker.sessionCostBaseUsd + finalUsage.costUsd,
              );
              setSessionTokens(tracker.sessionTokensBase + finalUsage.tokens);
              activeStreamUsageRef.current = null;
            }

            updateMessage(assistantMessageId, (message) => ({
              ...message,
              content: response.response || response.message || message.content,
              phase: response.phase ?? "final_answer",
              provider: response.provider,
              model: response.model,
              lane: response.lane,
              response_id: response.response_id,
              stateful: response.stateful,
              used_previous_response_id: response.used_previous_response_id,
              input_tokens: response.input_tokens,
              output_tokens: response.output_tokens,
              tasks_queued: response.tasks_queued?.length
                ? response.tasks_queued
                : undefined,
              streaming: false,
              usage: finalUsage ?? message.usage,
            }));

            // Auto-speak when voice mode is enabled
            if (voiceEnabled) {
              flushSpeech();
            }
          },
          onError: (streamError) => {
            flushDeltaIfNeeded();
            retryPromptRef.current = promptText;
            setNotice({ tone: "error", message: streamError });
            const tracker = activeStreamUsageRef.current;
            if (tracker && tracker.messageId === assistantMessageId) {
              tracker.responseText = tracker.responseText || "";
              refreshActiveUsage("local", { live: false });
              activeStreamUsageRef.current = null;
            }
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              role: message.content ? "assistant" : "system",
              content: message.content
                ? `${message.content}\n\n[stream interrupted: ${streamError}]`
                : `Error: ${streamError}`,
              streaming: false,
              phase: undefined,
            }));
          },
        },
        { signal: abortController.signal, voiceMode: voiceEnabled },
      );
    } catch (error: unknown) {
      flushDeltaIfNeeded();
      const apiError = error as Partial<ApiError> | undefined;
      retryPromptRef.current = promptText;
      setNotice(toChatNotice(error, "Failed to send chat message."));
      const tracker = activeStreamUsageRef.current;
      if (tracker && tracker.messageId === assistantMessageId) {
        refreshActiveUsage("local", { live: false });
        activeStreamUsageRef.current = null;
      }
      updateMessage(assistantMessageId, (message) => {
        if (apiError?.isAborted) {
          return {
            ...message,
            content: message.content || "Generation stopped.",
            streaming: false,
          };
        }
        return {
          ...message,
          role: "system",
          content: `Error: ${error instanceof Error ? error.message : "Failed to send message"}`,
          streaming: false,
          phase: undefined,
        };
      });
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
    }
  };

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    const promptText = input.trim();
    if (!promptText || loading) return;
    setInput("");
    await sendPrompt(promptText);
  };

  const stopStreaming = () => {
    abortControllerRef.current?.abort();
  };

  const retryLastPrompt = async () => {
    const promptText = retryPromptRef.current;
    if (!promptText || loading) {
      return;
    }
    await sendPrompt(promptText);
  };

  const latestAssistantUsage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && message.usage)?.usage;
  const sessionLiveCostUsd =
    latestAssistantUsage?.live &&
    latestAssistantUsage.sessionCostUsd !== undefined
      ? latestAssistantUsage.sessionCostUsd
      : sessionCostUsd;
  const sessionLiveTokens = latestAssistantUsage?.live
    ? sessionTokens + latestAssistantUsage.tokens
    : sessionTokens;

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">
            Chat with Kor'tana
          </h2>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {sessionLiveTokens > 0 || sessionLiveCostUsd > 0 ? (
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1">
              <span className="text-[10px] uppercase tracking-[0.18em] text-emerald-200/70">
                Session
              </span>
              <span className="text-xs font-medium text-emerald-100">
                {formatCompactNumber(sessionLiveTokens)} tok
              </span>
              <span className="text-xs text-emerald-200/80">
                {formatCompactUsd(sessionLiveCostUsd)}
              </span>
            </div>
          ) : null}
          {conversationId && (
            <span className="text-xs text-gray-500">
              {messages.length} messages
            </span>
          )}
        </div>
      </div>
      {notice && (
        <div
          className={cn(
            "mx-6 mt-4 rounded-xl border px-4 py-3 text-sm flex items-start gap-3",
            notice.tone === "error"
              ? "border-red-800/80 bg-red-950/60 text-red-100"
              : notice.tone === "warning"
                ? "border-amber-700/70 bg-amber-950/50 text-amber-100"
                : "border-sky-800/70 bg-sky-950/50 text-sky-100",
          )}
        >
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="flex-1">{notice.message}</p>
          <button
            type="button"
            onClick={() => setNotice(null)}
            className="text-current/70 hover:text-current transition-colors"
            aria-label="Dismiss chat notice"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {retryPromptRef.current && !loading ? (
        <div className="mx-6 mt-3 flex justify-end">
          <button
            type="button"
            onClick={retryLastPrompt}
            className="text-xs font-medium text-indigo-300 hover:text-indigo-200 transition-colors"
          >
            Retry Last Prompt
          </button>
        </div>
      ) : null}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="w-16 h-16 text-indigo-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Start a Conversation
            </h3>
            <p className="text-gray-400 max-w-md">
              Ask me anything. I can help with tasks, analyze code, answer
              questions, and coordinate autonomous operations.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.role === "user" ? "justify-end" : "justify-start",
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-4 py-3",
                  message.role === "user"
                    ? "bg-indigo-600 text-white"
                    : message.role === "assistant"
                      ? "bg-gray-800 text-gray-100"
                      : "bg-red-900/20 text-red-400 border border-red-900",
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1">
                    {message.streaming && !message.content ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">
                        {message.content}
                      </p>
                    )}
                    <p
                      className={cn(
                        "text-xs mt-1",
                        message.role === "user"
                          ? "text-indigo-200"
                          : message.role === "assistant"
                            ? "text-gray-500"
                            : "text-red-400/70",
                      )}
                    >
                      {formatRelativeTime(message.timestamp)}
                    </p>
                    {message.role === "assistant" &&
                    message.phase &&
                    message.phase !== "final_answer" ? (
                      <p className="text-[10px] uppercase tracking-[0.2em] text-indigo-300/70 mt-1">
                        {formatChatPhase(message.phase)}
                      </p>
                    ) : null}
                    {message.role === "assistant" &&
                    (message.provider || message.model || message.stateful) ? (
                      <p className="text-[10px] text-gray-400 mt-1">
                        {[
                          message.provider,
                          message.model,
                          message.stateful ? "threaded" : null,
                          message.used_previous_response_id
                            ? "continued"
                            : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    ) : null}
                    {message.role === "assistant" && message.usage ? (
                      <div
                        className="mt-2 flex flex-wrap gap-1.5"
                        aria-label={
                          message.usage.live
                            ? "Live token and cost telemetry for this response"
                            : "Token and cost telemetry for this response"
                        }
                      >
                        <span
                          title={
                            message.usage.estimated
                              ? "Estimated total tokens for this response"
                              : "Total tokens for this response"
                          }
                          className={cn(
                            "inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-medium tracking-[0.12em]",
                            message.usage.live
                              ? "border-sky-500/20 bg-sky-500/10 text-sky-100"
                              : "border-gray-700 bg-gray-900/80 text-gray-200",
                          )}
                        >
                          {tokenLabel(message.usage)}
                        </span>
                        <span
                          title={
                            message.usage.estimated
                              ? "Estimated cost for this response"
                              : "Estimated session cost based on shared provider pricing"
                          }
                          className={cn(
                            "inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-medium tracking-[0.12em]",
                            message.usage.live
                              ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-100"
                              : "border-gray-700 bg-gray-900/80 text-gray-200",
                          )}
                        >
                          {costLabel(message.usage)}
                        </span>
                        {message.usage.sessionCostUsd !== undefined ? (
                          <span
                            title="Estimated total for this chat session"
                            className="inline-flex items-center rounded-full border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 text-[10px] font-medium tracking-[0.12em] text-indigo-100"
                          >
                            session{" "}
                            {formatCompactUsd(message.usage.sessionCostUsd)}
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                    {message.tasks_queued?.length ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {message.tasks_queued.map((t) => (
                          <span
                            key={t.id}
                            title={`branch: ${t.branch}`}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-900/60 border border-indigo-700/50 text-indigo-300 text-[10px] font-medium"
                          >
                            <ClipboardList className="w-3 h-3" />
                            queued: {t.name}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        {loading && !messages.some((message) => message.streaming) && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-100 rounded-lg px-4 py-3">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={sendMessage}
        className="px-6 py-4 border-t border-gray-800"
      >
        <div className="flex gap-2">
          {/* Voice toggle */}
          <button
            type="button"
            onClick={toggleVoice}
            className={cn(
              "rounded-lg px-3 py-3 transition-colors",
              voiceEnabled
                ? "bg-indigo-600 text-white hover:bg-indigo-700"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white",
            )}
            title={voiceEnabled ? "Disable voice mode" : "Enable voice mode"}
          >
            {voiceEnabled ? (
              <Volume2 className="w-5 h-5" />
            ) : (
              <VolumeX className="w-5 h-5" />
            )}
          </button>

          <input
            type="text"
            value={isListening ? transcript || input : input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? "listening..." : "Type a message..."}
            className={cn(
              "flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500",
              isListening && "ring-2 ring-red-500/50",
            )}
            disabled={loading || isListening}
          />

          {/* Mic button — only visible when voice mode is on */}
          {voiceEnabled && speechSupported && !loading && (
            <button
              type="button"
              onClick={isListening ? stopListening : startListening}
              className={cn(
                "rounded-lg px-3 py-3 transition-colors",
                isListening
                  ? "bg-red-600 text-white hover:bg-red-700 animate-pulse"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white",
              )}
              title={isListening ? "Stop listening" : "Start listening"}
            >
              {isListening ? (
                <MicOff className="w-5 h-5" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </button>
          )}

          {loading ? (
            <button
              type="button"
              onClick={stopStreaming}
              className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-6 py-3 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() && !isListening}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg px-6 py-3 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
