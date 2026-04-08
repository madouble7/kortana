/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useRef, useEffect } from 'react';
import { generateVideo, getVideosOperation } from '../services/apiService';
import { Loader, AlertTriangle, Download, UploadCloud, Film, X } from 'lucide-react';
import { VideoOperation, VideoAspectRatio, VideoResolution } from '../types';
import { motion, AnimatePresence } from 'framer-motion';

type Status = 'idle' | 'generating' | 'polling' | 'success' | 'error';

const progressMessages = [
    "warming up the creative engines...",
    "storyboarding the digital dream...",
    "rendering the first few frames...",
    "composing the visual symphony...",
    "this is taking a moment, but good things come to those who wait...",
    "adding the final touches of pixel magic...",
    "almost there, polishing the masterpiece...",
];

export default function VideoGenerator() {
    const [prompt, setPrompt] = useState('');
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [imageBase64, setImageBase64] = useState<string | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [status, setStatus] = useState<Status>('idle');
    const [error, setError] = useState<string | null>(null);
    const [progressMessage, setProgressMessage] = useState('');
    const [aspectRatio, setAspectRatio] = useState<VideoAspectRatio>('16:9');
    const [resolution, setResolution] = useState<VideoResolution>('720p');
    
    const operationRef = useRef<VideoOperation | null>(null);
    const pollIntervalRef = useRef<number | null>(null);
    const progressMessageIntervalRef = useRef<number | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const cleanupPolling = () => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
        }
        if (progressMessageIntervalRef.current) {
            clearInterval(progressMessageIntervalRef.current);
            progressMessageIntervalRef.current = null;
        }
    };

    useEffect(() => {
        return cleanupPolling;
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                setError('please select an image file.');
                return;
            }
            setError(null);
            setImageFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                const result = reader.result as string;
                const base64 = result.split(',')[1];
                setImageBase64(base64);
            };
            reader.readAsDataURL(file);
        }
    };

    const pollForVideo = async () => {
        if (!operationRef.current) return;
        
        try {
            const op = await getVideosOperation(operationRef.current.name);
            operationRef.current = op;

            if (op.done) {
                cleanupPolling();
                if (op.error) {
                    setError(`video generation failed: ${op.error.message}`);
                    setStatus('error');
                } else if (op.response?.generatedVideos?.[0]?.video?.uri) {
                    const downloadLink = op.response.generatedVideos[0].video.uri;
                    // Fetch through backend/proxy if needed to handle auth or CORS
                    const res = await fetch(downloadLink); 
                    if (!res.ok) {
                        throw new Error(`failed to download video file: ${res.status}`);
                    }
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    setVideoUrl(url);
                    setStatus('success');
                } else {
                    setError('generation completed, but no video was returned.');
                    setStatus('error');
                }
            }
        } catch (e) {
            cleanupPolling();
            const msg = e instanceof Error ? e.message : 'failed to check operation status.';
            setError(msg);
            setStatus('error');
        }
    };

    const handleGenerate = async () => {
        if (!prompt.trim() || status === 'generating' || status === 'polling') return;

        // Veo requires a paid API key selection
        const aiStudio = (window as any).aistudio;
        if (aiStudio && typeof aiStudio.hasSelectedApiKey === 'function') {
            const hasKey = await aiStudio.hasSelectedApiKey();
            if (!hasKey) {
                if (typeof aiStudio.openSelectKey === 'function') {
                    await aiStudio.openSelectKey();
                    // After opening, we assume success or user will try again
                } else {
                    setError("Please select a paid Gemini API key in the settings to use video generation.");
                    return;
                }
            }
        }

        setStatus('generating');
        setError(null);
        setVideoUrl(null);
        operationRef.current = null;
        setProgressMessage(progressMessages[0]);

        try {
            const imagePayload = imageFile && imageBase64 ? { base64: imageBase64, mimeType: imageFile.type } : null;
            const op = await generateVideo(prompt, imagePayload, aspectRatio, resolution);
            operationRef.current = op;
            setStatus('polling');
            
            pollIntervalRef.current = window.setInterval(pollForVideo, 10000);
            
            let msgIndex = 1;
            progressMessageIntervalRef.current = window.setInterval(() => {
                setProgressMessage(progressMessages[msgIndex % progressMessages.length]);
                msgIndex++;
            }, 8000);

        } catch (e) {
            console.error(e);
            const msg = e instanceof Error ? e.message : 'failed to start video generation.';
            if (msg.includes('fetch')) {
                setError('connection failed. is the local server running?');
            } else {
                setError(msg);
            }
            setStatus('error');
        }
    };
    
    const handleDownload = () => {
        if (!videoUrl) return;
        const link = document.createElement('a');
        link.href = videoUrl;
        const safeFilename = prompt.substring(0, 50).replace(/[^a-z0-9]/gi, '_').toLowerCase();
        link.download = `kortana_video_${safeFilename || 'video'}.mp4`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const isProcessing = status === 'generating' || status === 'polling';

    return (
        <div className="p-4 sm:p-8 max-w-4xl mx-auto">
            <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-10 sm:mb-12"
            >
                <h2 className="text-3xl sm:text-4xl font-bold mb-2">video generator</h2>
                <p className="text-md sm:text-lg text-gray-600 dark:text-gray-400">
                    describe the video you want to create. video generation can take a few minutes.
                </p>
            </motion.div>

            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8"
            >
                <h3 className="text-xl font-semibold mb-4">your prompt</h3>
                <textarea
                    className="w-full border bg-gray-100 dark:bg-gray-900 border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 h-24"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., a neon hologram of a cat driving at top speed"
                    disabled={isProcessing}
                    aria-label="Video generation prompt"
                />

                <h3 className="text-lg font-semibold mb-2 mt-4">optional image</h3>
                <div 
                  className="relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input 
                    ref={fileInputRef}
                    type="file" 
                    className="sr-only"
                    accept="image/*"
                    onChange={handleFileChange}
                    disabled={isProcessing}
                  />
                  <AnimatePresence mode="wait">
                      {!imageBase64 && (
                        <motion.div 
                            key="upload-prompt"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center text-gray-500 dark:text-gray-400"
                        >
                          <UploadCloud size={40} className="mb-2" />
                          <p className="font-semibold">drag & drop or click to upload</p>
                          <p className="text-sm">provide an initial image for the video</p>
                        </motion.div>
                      )}
                      {imageBase64 && (
                        <motion.div 
                            key="image-preview"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="relative"
                        >
                            <img src={`data:image/png;base64,${imageBase64}`} alt="preview" className="rounded-lg max-h-40 mx-auto" />
                            <button 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setImageFile(null);
                                    setImageBase64(null);
                                    if (fileInputRef.current) fileInputRef.current.value = '';
                                }}
                                className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                                aria-label="Remove image"
                            >
                                <X size={16} />
                            </button>
                        </motion.div>
                      )}
                  </AnimatePresence>
                </div>

                <div className="flex items-center gap-4 mt-4">
                    <label htmlFor="video-aspect-ratio" className="text-gray-700 dark:text-gray-300">Aspect Ratio:</label>
                    <select
                        id="video-aspect-ratio"
                        value={aspectRatio}
                        onChange={(e) => setAspectRatio(e.target.value as VideoAspectRatio)}
                        className="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                        disabled={isProcessing}
                    >
                        <option value="16:9">16:9 (landscape)</option>
                        <option value="9:16">9:16 (portrait)</option>
                    </select>
                     <label htmlFor="video-resolution" className="text-gray-700 dark:text-gray-300">Resolution:</label>
                    <select
                        id="video-resolution"
                        value={resolution}
                        onChange={(e) => setResolution(e.target.value as VideoResolution)}
                        className="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                        disabled={isProcessing}
                    >
                        <option value="720p">720p</option>
                        <option value="1080p">1080p</option>
                    </select>
                </div>
                
                <button
                    onClick={handleGenerate}
                    className="mt-6 rounded-lg px-4 py-2 border shadow-sm bg-indigo-600 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    disabled={!prompt.trim() || isProcessing}
                >
                    {isProcessing ? <Loader size={16} className="animate-spin" /> : <Film size={16} />}
                    {isProcessing ? 'generating...' : 'generate video'}
                </button>
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    video generation requires a paid gemini api key. 
                    <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" rel="noopener noreferrer" className="ml-1 text-indigo-600 hover:underline">
                        learn about billing
                    </a>
                </p>
            </motion.div>
            
            <AnimatePresence mode="wait">
                {status === 'error' && (
                     <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-4 text-red-500 bg-red-50 dark:bg-red-900/20 p-4 rounded-lg flex items-center gap-2 overflow-hidden"
                    >
                        <AlertTriangle size={16} />{error}
                    </motion.div>
                )}

                {isProcessing && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="text-center p-6 bg-gray-100 dark:bg-gray-800 rounded-xl"
                    >
                        <Loader size={32} className="animate-spin mx-auto text-indigo-500" />
                        <motion.p 
                            key={progressMessage}
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-4 text-lg font-semibold"
                        >
                            {progressMessage}
                        </motion.p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">please keep this window open. this can take a few minutes.</p>
                    </motion.div>
                )}
                
                {videoUrl && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-semibold">result</h3>
                            <button
                                onClick={handleDownload}
                                className="flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                                aria-label="Download generated video"
                            >
                                <Download size={16} />
                                download
                            </button>
                        </div>
                        <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
                            <video src={videoUrl} controls autoPlay loop className="w-full h-full object-contain" />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}