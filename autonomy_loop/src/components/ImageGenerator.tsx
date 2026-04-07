import React, { useState } from 'react';
import { Image as ImageIcon, Loader2, Download, Sparkles } from 'lucide-react';
import { generateImage } from '../services/apiService';

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await generateImage(prompt);
      setImageUrl(`data:image/png;base64,${result.image_base64}`);
    } catch (err) {
      setError('Failed to generate image. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Image Generator</h2>
        <p className="text-gray-500">Transform your words into visual reality.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A futuristic city with neon lights..."
            className="flex-1 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
          <button
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all"
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
            Generate
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl mb-6 text-sm">
            {error}
          </div>
        )}

        <div className="aspect-square bg-gray-100 dark:bg-gray-900 rounded-2xl flex items-center justify-center overflow-hidden border-2 border-dashed border-gray-200 dark:border-gray-700">
          {imageUrl ? (
            <div className="relative group w-full h-full">
              <img src={imageUrl} alt={prompt} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <a 
                  href={imageUrl} 
                  download="generated-image.png"
                  className="bg-white text-gray-900 p-3 rounded-full hover:scale-110 transition-transform"
                >
                  <Download size={24} />
                </a>
              </div>
            </div>
          ) : (
            <div className="text-center p-8 opacity-30">
              <ImageIcon size={64} className="mx-auto mb-4" />
              <p>Your masterpiece will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
