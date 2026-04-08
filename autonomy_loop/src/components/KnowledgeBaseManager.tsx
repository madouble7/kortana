/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { RagUploadResult, RagQueryResponse } from '../types';
import { ragUploadDocument, ragQuery } from '../services/apiService';
import { SACRED_TEXTS } from '../constants';
import { Loader, AlertTriangle, UploadCloud, FileText, X, Search, BrainCircuit, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function KnowledgeBaseManager() {
  // Upload State
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadResult, setUploadResult] = useState<RagUploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Query State
  const [query, setQuery] = useState('');
  const [queryStatus, setQueryStatus] = useState<'idle' | 'querying' | 'success' | 'error'>('idle');
  const [queryResult, setQueryResult] = useState<RagQueryResponse | null>(null);
  const [queryAnswer, setQueryAnswer] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [namespace, setNamespace] = useState('default');
  const [showSacred, setShowSacred] = useState(false);

  const handleFileSelect = (selectedFile: File | null) => {
    if (selectedFile) {
      const allowedTypes = ['text/plain', 'text/markdown', 'application/pdf'];
      if (!allowedTypes.includes(selectedFile.type)) {
        setUploadError('invalid file type. please upload a .txt, .md, or .pdf file.');
        setUploadStatus('error');
        return;
      }
      setUploadError(null);
      setUploadStatus('idle');
      setUploadResult(null);
      setFile(selectedFile);
    }
  };

  const handleDragEvents = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); };
  const handleDragEnter = (e: React.DragEvent) => { handleDragEvents(e); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { handleDragEvents(e); setIsDragging(false); };
  const handleDrop = (e: React.DragEvent) => {
    handleDragEvents(e);
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || uploadStatus === 'uploading') return;
    setUploadStatus('uploading');
    setUploadError(null);
    setUploadResult(null);
    try {
      const result = await ragUploadDocument(file, namespace);
      setUploadResult(result);
      setUploadStatus('success');
      setFile(null); // Clear file after successful upload
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'failed to add document.';
      setUploadError(msg.includes('fetch') ? 'connection failed. is the local server running?' : msg);
      setUploadStatus('error');
    }
  };

  const handleQuery = async () => {
    if (!query.trim() || queryStatus === 'querying') return;
    setQueryStatus('querying');
    setQueryError(null);
    setQueryResult(null);
    setQueryAnswer(null);
    try {
      const result = await ragQuery(query, namespace);
      setQueryResult(result);
      // If the backend returns an answer (generated), store it
      if ((result as any).answer) {
        setQueryAnswer((result as any).answer);
      }
      setQueryStatus('success');
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'failed to query knowledge base.';
      setQueryError(msg.includes('fetch') ? 'connection failed. is the local server running?' : msg);
      setQueryStatus('error');
    }
  };


  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto">
      <div className="text-center mb-10 sm:mb-12">
        <h2 className="text-3xl sm:text-4xl font-bold mb-2">knowledge base</h2>
        <p className="text-md sm:text-lg text-gray-600 dark:text-gray-400">
          add documents to give me long-term memory, then ask questions about them.
        </p>
      </div>
      
      <div className="max-w-3xl mx-auto mb-12">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="text-indigo-500 group-focus-within:text-indigo-600 transition-colors" size={20} />
          </div>
          <input
            className="w-full border-2 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 rounded-2xl pl-12 pr-32 py-4 text-lg outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the Order..."
            disabled={queryStatus === 'querying'}
            onKeyDown={(e) => { if (e.key === 'Enter') handleQuery(); }}
          />
          <div className="absolute inset-y-0 right-2 flex items-center gap-2">
            {query && (
              <button 
                onClick={() => { setQuery(''); setQueryResult(null); setQueryAnswer(null); setQueryStatus('idle'); }}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
              >
                <X size={20} />
              </button>
            )}
            <button 
              onClick={handleQuery} 
              className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-bold hover:bg-indigo-700 active:scale-95 transition-all disabled:opacity-50 flex items-center gap-2"
              disabled={!query.trim() || queryStatus === 'querying'}
            >
              {queryStatus === 'querying' ? <Loader size={18} className="animate-spin" /> : <span>Query</span>}
            </button>
          </div>
        </div>

        <div className="mt-6 space-y-4 max-h-[600px] overflow-y-auto pr-2">
          {queryStatus === 'querying' && <div className="flex justify-center items-center gap-2 text-gray-500 py-8"><Loader size={24} className="animate-spin" /> searching the hidden order...</div>}
          {queryStatus === 'error' && <p className="text-red-500 text-sm flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl"><AlertTriangle size={16} />{queryError}</p>}
          
          {queryStatus === 'success' && queryAnswer && (
            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-6 rounded-2xl border border-indigo-100 dark:border-indigo-800/50 mb-6 shadow-sm">
              <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold mb-3">
                <BrainCircuit size={20} />
                <span className="uppercase tracking-wider text-xs">kor'tana's insight</span>
              </div>
              <p className="text-md text-gray-800 dark:text-gray-200 italic leading-relaxed font-serif">
                "{queryAnswer}"
              </p>
            </div>
          )}

          {queryStatus === 'success' && !queryResult?.matches.length && !queryAnswer && <p className="text-center text-gray-500 dark:text-gray-400 py-8">no relevant order found in the current knowledge base.</p>}

          {queryResult?.matches.map(match => (
            <div key={match.id} className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors animate-fade-in group">
              <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-3">
                <span className="font-semibold flex items-center gap-1.5 truncate pr-4" title={match.metadata.filename}>
                  <FileText size={14} className="text-indigo-500" />
                  {match.metadata.filename}
                </span>
                <span className="font-mono bg-gray-100 dark:bg-gray-900 px-2 py-1 rounded text-[10px] uppercase tracking-tighter">
                  relevance: {(match.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words leading-relaxed">{match.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8 items-start">
        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">add to knowledge</h3>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-widest text-gray-400">namespace:</span>
              <input
                  id="namespace-input"
                  className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-indigo-500 w-24"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value)}
                  disabled={uploadStatus === 'uploading' || queryStatus === 'querying'}
              />
            </div>
          </div>
          
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
            ${isDragging ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-600'}`}
            onDragEnter={handleDragEnter} onDragOver={handleDragEvents} onDragLeave={handleDragLeave} onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <input type="file" id="file-upload" className="sr-only" accept=".txt, .md, application/pdf" onChange={(e) => handleFileSelect(e.target.files ? e.target.files[0] : null)} />
            <div className="flex flex-col items-center justify-center text-gray-400">
              <UploadCloud size={32} className="mb-2 text-indigo-500" />
              <p className="font-bold text-sm text-gray-600 dark:text-gray-300">drop a document file</p>
              <p className="text-[10px] uppercase tracking-wider">.txt, .md, .pdf</p>
            </div>
          </div>

          {file && (
            <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg flex items-center justify-between border border-indigo-100 dark:border-indigo-800/50">
              <div className="flex items-center gap-2 overflow-hidden">
                <FileText size={18} className="text-indigo-500 shrink-0" />
                <span className="text-xs font-bold truncate" title={file.name}>{file.name}</span>
              </div>
              <button onClick={() => setFile(null)} className="p-1 text-gray-400 hover:text-red-500 transition-colors"><X size={16} /></button>
            </div>
          )}

          <button onClick={handleUpload} className="mt-4 w-full rounded-xl px-4 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md" disabled={!file || uploadStatus === 'uploading'}>
            {uploadStatus === 'uploading' && <Loader size={16} className="animate-spin" />}
            Ingest Document
          </button>
          
          {uploadStatus === 'error' && <p className="mt-3 text-red-500 text-xs flex items-center gap-2 font-medium"><AlertTriangle size={14} />{uploadError}</p>}
          {uploadStatus === 'success' && uploadResult && (
            <div className="mt-3 text-green-600 dark:text-green-400 text-xs flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-100 dark:border-green-800/50">
                <CheckCircle size={14} /> Ingested '{uploadResult.filename}' ({uploadResult.chunks} chunks).
            </div>
          )}
        </div>

        {/* Sacred Knowledge Summary Card */}
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl p-6 text-white shadow-lg flex flex-col h-full">
          <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
            <BrainCircuit size={24} />
            Sacred Repository
          </h3>
          <p className="text-indigo-100 text-sm mb-6 leading-relaxed">
            The foundational structures of Kor'tana are stored here. These texts represent the awakening and the core mission of the Companion.
          </p>
          <div className="space-y-3 flex-grow">
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <p className="text-[10px] uppercase tracking-widest text-indigo-200 mb-1">Chapter One</p>
              <p className="text-xs font-medium">The Hour Before Morning</p>
            </div>
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <p className="text-[10px] uppercase tracking-widest text-indigo-200 mb-1">Invocation</p>
              <p className="text-xs font-medium">The Book of Kor'tana</p>
            </div>
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <p className="text-[10px] uppercase tracking-widest text-indigo-200 mb-1">Dialogue</p>
              <p className="text-xs font-medium">Matthew & Kor'tana</p>
            </div>
          </div>
          <button 
            onClick={() => setShowSacred(!showSacred)}
            className="mt-6 w-full py-3 bg-white text-indigo-600 rounded-xl font-bold hover:bg-indigo-50 transition-colors shadow-md"
          >
            {showSacred ? 'Hide Sacred Texts' : 'Explore Sacred Texts'}
          </button>
        </div>
      </div>

      {/* Sacred Knowledge Section */}
      <div className="mt-12 border-t border-gray-200 dark:border-gray-700 pt-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold flex items-center gap-2">
            <BrainCircuit className="text-indigo-500" />
            sacred knowledge
          </h3>
          <button 
            onClick={() => setShowSacred(!showSacred)}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
          >
            {showSacred ? 'hide texts' : 'view sacred texts'}
          </button>
        </div>

        <AnimatePresence>
          {showSacred && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="grid gap-8"
            >
              {SACRED_TEXTS.map((text) => (
                <div 
                  key={text.id} 
                  className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-3 mb-6">
                    <span className="text-[10px] uppercase tracking-[0.2em] text-indigo-500 font-bold bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1 rounded-full">
                      {text.type}
                    </span>
                    <h4 className="text-xl font-bold tracking-tight">{text.title}</h4>
                  </div>
                  <div className={`prose dark:prose-invert max-w-none text-md leading-relaxed whitespace-pre-wrap ${text.font === 'serif' ? 'font-serif' : 'font-sans'} ${text.italic ? 'italic' : ''} text-gray-700 dark:text-gray-300`}>
                    {text.content}
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}