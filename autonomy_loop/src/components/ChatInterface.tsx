import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User, Bot, Sparkles } from 'lucide-react';
import { chatTextStream, chatProStream, chatFastStream, chatWithSearchStream } from '../services/apiService';
import { GeminiModel, GroundingSource } from '../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  sources?: GroundingSource[];
}

interface Props {
  initialInput?: string;
}

export default function ChatInterface({ initialInput }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(initialInput || '');
  const [isLoading, setIsLoading] = useState(false);
  const [model, setModel] = useState<GeminiModel>('gemini-3.1-flash-lite-preview');
  const [useThinking, setUseThinking] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialInput) {
      handleSend(initialInput);
    }
  }, []);

  const handleSend = async (textOverride?: string) => {
    const text = textOverride || input;
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    const assistantMsgId = (Date.now() + 1).toString();
    let assistantText = '';
    let assistantSources: GroundingSource[] = [];

    const updateAssistantMessage = (text: string, sources?: GroundingSource[]) => {
      setMessages(prev => {
        const existing = prev.find(m => m.id === assistantMsgId);
        if (existing) {
          return prev.map(m => m.id === assistantMsgId ? { ...m, text, sources: sources || m.sources } : m);
        } else {
          return [...prev, { id: assistantMsgId, role: 'assistant', text, timestamp: new Date(), sources }];
        }
      });
    };

    try {
      if (model === 'gemini-2.5-flash') {
        await chatProStream(text, (chunk) => {
          assistantText += chunk;
          updateAssistantMessage(assistantText);
        });
      } else if (model === 'gemini-3.1-flash-lite-preview') {
        // Use search grounding if the model is set to lite (or we can have a separate toggle)
        // For now, let's keep the logic but use the lite model
        await chatWithSearchStream(
          text, 
          (chunk) => {
            assistantText += chunk;
            updateAssistantMessage(assistantText, assistantSources);
          },
          (metadata) => {
            if (metadata.groundingChunks) {
              assistantSources = metadata.groundingChunks.map((chunk: any) => ({
                title: chunk.web?.title || 'Source',
                uri: chunk.web?.uri || ''
              }));
              updateAssistantMessage(assistantText, assistantSources);
            }
          }
        );
      } else {
        await chatTextStream(
          text,
          false,
          model,
          useThinking,
          (chunk) => {
            assistantText += chunk;
            updateAssistantMessage(assistantText);
          }
        );
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        id: (Date.now() + 2).toString(), 
        role: 'assistant', 
        text: 'I encountered an error while processing your request. Please try again.', 
        timestamp: new Date() 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-white dark:bg-gray-800">
      {/* Chat Header / Controls */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-900/50">
        <div className="flex items-center gap-4">
          <select 
            value={model} 
            onChange={(e) => setModel(e.target.value as GeminiModel)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="gemini-2.5-flash">Gemini 2.5 Flash (Pro)</option>
            <option value="gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite (Search)</option>
          </select>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input 
              type="checkbox" 
              checked={useThinking} 
              onChange={(e) => setUseThinking(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-gray-600 dark:text-gray-400">Thinking Mode</span>
          </label>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
            <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-4">
              <Sparkles size={32} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Welcome to Kor'tana</h3>
            <p className="max-w-md">
              I'm your calm, capable AI companion. How can I assist you today?
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
            }`}>
              {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
              msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-none'
                : 'bg-gray-100 dark:bg-gray-700/50 text-gray-900 dark:text-gray-100 rounded-tl-none'
            }`}>
              <div className="markdown-body prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-500 mb-2">Sources</p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((source, idx) => (
                      <a
                        key={idx}
                        href={source.uri}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-[10px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full px-2 py-1 hover:border-indigo-500 transition-colors"
                      >
                        <ExternalLink size={10} />
                        <span className="truncate max-w-[120px]">{source.title}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
              <div className={`text-[10px] mt-1 opacity-50 ${msg.role === 'user' ? 'text-right' : ''}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="max-w-4xl mx-auto flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 bg-gray-100 dark:bg-gray-900 border border-transparent focus:border-indigo-500 rounded-xl px-4 py-3 outline-none transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-all shadow-lg shadow-indigo-200 dark:shadow-none"
          >
            {isLoading ? <Loader2 size={24} className="animate-spin" /> : <Send size={24} />}
          </button>
        </form>
      </div>
    </div>
  );
}
