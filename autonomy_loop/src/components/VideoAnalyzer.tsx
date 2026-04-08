import React, { useState } from 'react';
import { Video, Loader2, Upload, Search } from 'lucide-react';
import { analyzeVideo } from '../services/apiService';

export default function VideoAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('Summarize this video and identify key events.');
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeVideo(file, prompt);
      setAnalysis(result.analysis);
    } catch (err) {
      setError('Failed to analyze video. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Video className="text-violet-500" />
          Video Analyzer
        </h2>
        <p className="text-gray-500">Upload a video and let Kor'tana analyze its content.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div 
            className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-3xl border-2 border-dashed border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center overflow-hidden relative group cursor-pointer"
            onClick={() => document.getElementById('video-upload')?.click()}
          >
            {preview ? (
              <video src={preview} className="w-full h-full object-cover" controls />
            ) : (
              <div className="text-center p-8 text-gray-400">
                <Upload size={48} className="mx-auto mb-4 opacity-20" />
                <p>Click to upload video</p>
              </div>
            )}
            <input 
              id="video-upload"
              type="file" 
              accept="video/*" 
              onChange={handleFileChange} 
              className="hidden" 
            />
          </div>

          <div className="space-y-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What would you like to know about this video?"
              className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-4 outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px] resize-none"
            />
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !file}
              className="w-full bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-violet-200 dark:shadow-none"
            >
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
              Analyze Video
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm min-h-[400px]">
          <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-gray-100">Analysis</h3>
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl mb-4 text-sm">
              {error}
            </div>
          )}
          {analysis ? (
            <div className="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {analysis}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
              <Video size={48} className="mb-4" />
              <p>Analysis will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
