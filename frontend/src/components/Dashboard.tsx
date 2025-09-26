import React from 'react';
import PublicApisPanel from './PublicApisPanel';

const Dashboard: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4 dark:text-white">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Start Conversation Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Start Conversation</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Begin a new chat session with AI assistance.</p>
          <button
            onClick={() => alert('Starting Conversation...')}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Start Chat
          </button>
        </div>

        {/* Transcribe Audio Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Transcribe Audio</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Upload audio files for transcription.</p>
          <button
            onClick={() => alert('Upload Audio for Transcription')}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            Upload Audio
          </button>
        </div>

        {/* Scan Document Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Scan Document</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Process images or PDFs for text extraction.</p>
          <button
            onClick={() => alert('Scan Document')}
            className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded"
          >
            Scan File
          </button>
        </div>

        {/* Start Day Capture Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Start Day Capture</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Record daily audio notes and summaries.</p>
          <button
            onClick={() => alert('Start Audio Recording')}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded"
          >
            Record Audio
          </button>
        </div>

        {/* Manage Knowledge Base Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Manage Knowledge Base</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Upload documents to build your knowledge repository.</p>
          <button
            onClick={() => alert('Manage Knowledge Base')}
            className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded"
          >
            Upload Docs
          </button>
        </div>

        {/* Privacy Policy Kit Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Privacy Policy Kit</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Generate customized privacy policies.</p>
          <button
            onClick={() => alert('Generate Privacy Policy')}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            Generate
          </button>
        </div>

        {/* Local Server Guide Card */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">Local Server Guide</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Access guides for setting up local servers.</p>
          <button
            onClick={() => alert('View Local Server Guide')}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
          >
            View Guide
          </button>
        </div>
      </div>
      
      {/* Public APIs Panel */}
      <PublicApisPanel />
    </div>
  );
};

export default Dashboard;
