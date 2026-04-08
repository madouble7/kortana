import React, { useEffect, useState } from 'react';

interface MatrixMessage {
    agent: string;
    event: string;
    timestamp: string;
    [key: string]: any;
}

export const FractalDashboard: React.FC = () => {
    const [messages, setMessages] = useState<MatrixMessage[]>([]);
    const [status, setStatus] = useState<string>('Disconnected');

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/api/matrix/stream');

        ws.onopen = () => {
            setStatus('Connected to Matrix Swarm');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setMessages((prev) => [data, ...prev].slice(0, 50)); // Keep last 50
            } catch (err) {
                console.error('Failed to parse matrix message', err);
            }
        };

        ws.onclose = () => {
            setStatus('Disconnected');
        };

        return () => ws.close();
    }, []);

    return (
        <div className="p-4 bg-gray-900 text-green-400 font-mono h-screen flex flex-col">
            <h1 className="text-2xl mb-4 font-bold border-b border-green-700 pb-2">
                🌌 Phase 10: Fractal Swarm Dashboard
            </h1>
            <div className="mb-4">
                Status: <span className={status === 'Disconnected' ? 'text-red-500' : 'text-green-300'}>{status}</span>
            </div>

            <div className="flex-1 overflow-y-auto bg-black p-4 rounded border border-gray-700">
                <h2 className="text-lg mb-2">Live Hive Matrix:</h2>
                {messages.length === 0 && <span className="opacity-50">Awaiting swarm data...</span>}
                {messages.map((msg, index) => (
                    <div key={index} className="mb-2 text-sm border-b border-gray-800 pb-1">
                        <span className="text-blue-400 font-bold">[{msg.timestamp}]</span>{' '}
                        <span className="text-purple-400">[{msg.agent}]</span>{' '}
                        <span className="text-yellow-400">{msg.event}</span>:{' '}
                        <span className="text-gray-300">
                            {JSON.stringify(Object.fromEntries(Object.entries(msg).filter(([k]) => !['agent', 'event', 'timestamp'].includes(k))))}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};
