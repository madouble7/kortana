import { AlertTriangle, ClipboardList, Loader2, Send, Sparkles, X } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type ApiError } from '../lib/api';
import { cn, formatRelativeTime } from '../lib/utils';
import type { ChatHistoryEntry, ChatPhase, Message } from '../types';

// Stable session ID persisted in localStorage so history survives page refreshes.
function getSessionId(): string {
  const key = 'kortana_session_id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem(key, id);
  }
  return id;
}

function buildChatHistory(messages: Message[]): ChatHistoryEntry[] {
  return messages
    .filter((message): message is Message & { role: 'user' | 'assistant' } => (
      message.role === 'user' || message.role === 'assistant'
    ))
    .slice(-10)
    .map((message) => ({
      role: message.role,
      content: message.content,
      phase: message.phase,
    }));
}

function formatChatPhase(phase: ChatPhase): string {
  return phase.replace(/_/g, ' ');
}

type ChatNoticeTone = 'info' | 'warning' | 'error';

interface ChatNotice {
  message: string;
  tone: ChatNoticeTone;
}

function toChatNotice(error: unknown, fallback: string): ChatNotice {
  const apiError = error as Partial<ApiError> | undefined;
  if (apiError?.isRateLimited) {
    return {
      tone: 'warning',
      message: apiError.retryAfterSeconds
        ? `Rate limit reached. Try again in ${apiError.retryAfterSeconds}s.`
        : 'Rate limit reached. Please wait a moment and try again.',
    };
  }
  if (apiError?.isOffline) {
    return {
      tone: 'warning',
      message: 'Backend is unreachable right now. Check the API and try again.',
    };
  }
  if (error instanceof Error && error.message) {
    return { tone: 'error', message: error.message };
  }
  return { tone: 'error', message: fallback };
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sessionId] = useState(() => getSessionId());
  const [notice, setNotice] = useState<ChatNotice | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const updateMessage = (id: string, updater: (message: Message) => Message) => {
    setMessages((prev) => prev.map((message) => (
      message.id === id ? updater(message) : message
    )));
  };

  // Load persisted history from DB on mount
  useEffect(() => {
    api.getChatHistory(sessionId, 40)
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
        setNotice(toChatNotice(error, 'Previous chat history could not be loaded.'));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    setNotice(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const assistantMessageId = `${Date.now() + 1}`;
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      phase: 'commentary',
      streaming: true,
    };

    setMessages((prev) => [...prev, assistantPlaceholder]);

    try {
      const history = buildChatHistory(messages);
      await api.sendChatMessageStream(
        input,
        history,
        conversationId || undefined,
        sessionId,
        {
          onStart: (payload) => {
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              provider: payload.provider,
              model: payload.model,
              lane: payload.lane,
              stateful: payload.stateful,
              used_previous_response_id: payload.used_previous_response_id,
            }));
          },
          onPhase: (phase) => {
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              phase,
            }));
          },
          onDelta: (delta) => {
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              content: message.content + delta,
            }));
          },
          onFinal: (response) => {
            if (response.conversation_id && !conversationId) {
              setConversationId(response.conversation_id);
            }

            updateMessage(assistantMessageId, (message) => ({
              ...message,
              content: response.response || response.message || message.content,
              phase: response.phase ?? 'final_answer',
              provider: response.provider,
              model: response.model,
              lane: response.lane,
              response_id: response.response_id,
              stateful: response.stateful,
              used_previous_response_id: response.used_previous_response_id,
              tasks_queued: response.tasks_queued?.length ? response.tasks_queued : undefined,
              streaming: false,
            }));
          },
          onError: (streamError) => {
            setNotice({ tone: 'error', message: streamError });
            updateMessage(assistantMessageId, (message) => ({
              ...message,
              role: message.content ? 'assistant' : 'system',
              content: message.content
                ? `${message.content}\n\n[stream interrupted: ${streamError}]`
                : `Error: ${streamError}`,
              streaming: false,
              phase: undefined,
            }));
          },
        }
      );
    } catch (error: unknown) {
      setNotice(toChatNotice(error, 'Failed to send chat message.'));
      updateMessage(assistantMessageId, (message) => ({
        ...message,
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        streaming: false,
        phase: undefined,
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">Chat with Kor'tana</h2>
        </div>
        {conversationId && (
          <span className="text-xs text-gray-500">
            {messages.length} messages
          </span>
        )}
      </div>
      {notice && (
        <div
          className={cn(
            'mx-6 mt-4 rounded-xl border px-4 py-3 text-sm flex items-start gap-3',
            notice.tone === 'error'
              ? 'border-red-800/80 bg-red-950/60 text-red-100'
              : notice.tone === 'warning'
                ? 'border-amber-700/70 bg-amber-950/50 text-amber-100'
                : 'border-sky-800/70 bg-sky-950/50 text-sky-100'
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

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="w-16 h-16 text-indigo-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Start a Conversation
            </h3>
            <p className="text-gray-400 max-w-md">
              Ask me anything. I can help with tasks, analyze code, answer questions,
              and coordinate autonomous operations.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  'max-w-[80%] rounded-lg px-4 py-3',
                  message.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : message.role === 'assistant'
                      ? 'bg-gray-800 text-gray-100'
                      : 'bg-red-900/20 text-red-400 border border-red-900'
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1">
                    {message.streaming && !message.content ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                    <p
                      className={cn(
                        'text-xs mt-1',
                        message.role === 'user'
                          ? 'text-indigo-200'
                          : message.role === 'assistant'
                            ? 'text-gray-500'
                            : 'text-red-400/70'
                      )}
                    >
                      {formatRelativeTime(message.timestamp)}
                    </p>
                    {message.role === 'assistant' && message.phase && message.phase !== 'final_answer' ? (
                      <p className="text-[10px] uppercase tracking-[0.2em] text-indigo-300/70 mt-1">
                        {formatChatPhase(message.phase)}
                      </p>
                    ) : null}
                    {message.role === 'assistant' && (message.provider || message.model || message.stateful) ? (
                      <p className="text-[10px] text-gray-400 mt-1">
                        {[
                          message.provider,
                          message.model,
                          message.stateful ? 'threaded' : null,
                          message.used_previous_response_id ? 'continued' : null,
                        ].filter(Boolean).join(' · ')}
                      </p>
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
      <form onSubmit={sendMessage} className="px-6 py-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg px-6 py-3 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
