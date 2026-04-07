import React, { useState } from 'react';
import { Type, Loader2, Play, Download, Volume2 } from 'lucide-react';
import { textToSpeech } from '../services/apiService';

export default function TextToSpeech() {
  const [text, setText] = useState('');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await textToSpeech(text);
      const blob = await (await fetch(`data:${result.mime_type};base64,${result.audio_base64}`)).blob();
      setAudioUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError('Failed to generate speech. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Type className="text-pink-500" />
          Text to Speech
        </h2>
        <p className="text-gray-500">Convert your text into high-quality, natural-sounding speech.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="space-y-6">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type or paste the text you want to convert to speech..."
            className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 outline-none focus:ring-2 focus:ring-pink-500 min-h-[200px] resize-none text-lg"
          />

          <div className="flex flex-wrap gap-4 items-center justify-between">
            <button
              onClick={handleGenerate}
              disabled={isLoading || !text.trim()}
              className="bg-pink-600 hover:bg-pink-700 disabled:opacity-50 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-pink-200 dark:shadow-none"
            >
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Volume2 size={20} />}
              Generate Speech
            </button>

            {audioUrl && (
              <div className="flex items-center gap-4 bg-gray-50 dark:bg-gray-900 p-2 rounded-2xl border border-gray-200 dark:border-gray-700">
                <audio src={audioUrl} controls className="h-10" />
                <a 
                  href={audioUrl} 
                  download="speech.mp3"
                  className="p-2 text-gray-500 hover:text-pink-600 transition-colors"
                  title="Download Audio"
                >
                  <Download size={20} />
                </a>
              </div>
            )}
          </div>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl text-sm">
              {error}
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
          <h4 className="font-bold mb-2">Natural Voice</h4>
          <p className="text-sm text-gray-500">Powered by Gemini 2.5 Flash for human-like prosody.</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
          <h4 className="font-bold mb-2">Fast Processing</h4>
          <p className="text-sm text-gray-500">Near real-time conversion for even long passages.</p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
          <h4 className="font-bold mb-2">Multi-Speaker</h4>
          <p className="text-sm text-gray-500">Support for different voices and styles coming soon.</p>
        </div>
      </div>
    </div>
  );
}
