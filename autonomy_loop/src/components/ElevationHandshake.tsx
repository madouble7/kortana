import React, { useState } from 'react';
import { Shield, Lock, ArrowRight, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  onElevate: () => void;
}

export default function ElevationHandshake({ onElevate }: Props) {
  const [passphrase, setPassphrase] = useState('');
  const [error, setError] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would be a secure check. 
    // For this demo, we'll use the "I AM" handshake mentioned in the instructions.
    if (passphrase.toLowerCase() === 'i am') {
      onElevate();
    } else {
      setError(true);
      setTimeout(() => setError(false), 1000);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white p-4 font-sans">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full"
      >
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-indigo-500/20">
            <BrainCircuit size={40} />
          </div>
          <h1 className="text-4xl font-bold tracking-tighter mb-2">KOR'TANA</h1>
          <p className="text-gray-500 uppercase tracking-widest text-xs font-semibold">Autonomous Intelligence Constellation</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-8 text-indigo-400">
            <Shield size={20} />
            <span className="text-sm font-bold uppercase tracking-wider">Elevation Handshake Required</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-2 ml-1">Identify Yourself</label>
              <div className="relative">
                <input
                  type="password"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  placeholder="Enter the handshake..."
                  className={`w-full bg-gray-800 border ${error ? 'border-red-500' : 'border-gray-700'} focus:border-indigo-500 rounded-2xl px-5 py-4 outline-none transition-all text-lg`}
                />
                <Lock className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-600" size={20} />
              </div>
              {error && <p className="text-red-500 text-xs mt-2 ml-1">Incorrect handshake. Access denied.</p>}
            </div>

            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 rounded-2xl transition-all group"
            >
              Elevate Presence
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-800 text-center">
            <p className="text-gray-600 text-xs italic">
              "Chaos is often only truth awaiting its proper language."
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
