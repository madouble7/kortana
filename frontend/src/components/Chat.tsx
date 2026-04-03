import { ClipboardList, Loader2, Send, Sparkles } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../lib/api';
import { cn, formatRelativeTime } from '../lib/utils';
import type { Message } from '../types';

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

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const sessionId = getSessionId();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load persisted history from DB on mount
  useEffect(() => {
    api.getChatHistory(sessionId, 40)
      .then((data: any) => {
        if (data?.messages?.length) {
          const loaded: Message[] = data.messages.map((m: any, i: number) => ({
            id: `hist_${i}`,
            role: m.role === 'user' ? 'user' : 'assistant',
            content: m.content,
            timestamp: m.created_at,
          }));
          setMessages(loaded);
        }
      })
      .catch(() => { /* history fetch is best-effort */ });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build history from current messages (last 10 turns)
      const history = messages.slice(-10).map((m) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
      }));
      const response = await api.sendChatMessage(input, history, conversationId || undefined, sessionId);

      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response || response.message,
        timestamp: new Date().toISOString(),
        tasks_queued: response.tasks_queued?.length ? response.tasks_queued : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${error.message || 'Failed to send message'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
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
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
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
        {loading && (
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
