import React, { useState } from 'react';
import { Eye, Loader2, Upload, Search } from 'lucide-react';
import { analyzeImage } from '../services/apiService';

export default function ImageAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('Describe this image in detail.');
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result as string);
      reader.readAsDataURL(selectedFile);
      setAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file || !preview) return;
    setIsLoading(true);
    setError(null);
    try {
      const base64 = preview.split(',')[1];
      const result = await analyzeImage({ base64, mimeType: file.type }, prompt);
      setAnalysis(result.analysis);
    } catch (err) {
      setError('Failed to analyze image. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Eye className="text-indigo-500" />
          Image Analyzer
        </h2>
        <p className="text-gray-500">Upload an image and ask Kor'tana to understand it.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div 
            className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-3xl border-2 border-dashed border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center overflow-hidden relative group cursor-pointer"
            onClick={() => document.getElementById('image-upload')?.click()}
          >
            {preview ? (
              <img src={preview} alt="Preview" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center p-8 text-gray-400">
                <Upload size={48} className="mx-auto mb-4 opacity-20" />
                <p>Click to upload image</p>
              </div>
            )}
            <input 
              id="image-upload"
              type="file" 
              accept="image/*" 
              onChange={handleFileChange} 
              className="hidden" 
            />
          </div>

          <div className="space-y-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What would you like to know about this image?"
              className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-4 outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px] resize-none"
            />
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !file}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-200 dark:shadow-none"
            >
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
              Analyze Image
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
              <Eye size={48} className="mb-4" />
              <p>Analysis will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
