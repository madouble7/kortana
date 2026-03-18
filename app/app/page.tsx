"use client";

import { FormEvent, useState } from "react";

type Msg = {
    role: "user" | "assistant";
    content: string;
};

export default function Home() {
    const [messages, setMessages] = useState<Msg[]>([
        {
            role: "assistant",
            content: "hello — i'm kor'tana. how can i help?",
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        const text = input.trim();
        if (!text || loading) return;

        const nextMessages: Msg[] = [...messages, { role: "user", content: text }];
        setMessages(nextMessages);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ messages: nextMessages }),
            });

            const data = await res.json();

            setMessages([
                ...nextMessages,
                {
                    role: "assistant",
                    content: data.text || data.error || "something went wrong.",
                },
            ]);
        } catch {
            setMessages([
                ...nextMessages,
                {
                    role: "assistant",
                    content: "network error. please try again.",
                },
            ]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <main style={{ maxWidth: 820, margin: "0 auto", padding: 24 }}>
            <h1 style={{ fontSize: 32, marginBottom: 8 }}>kor'tana</h1>
            <p style={{ opacity: 0.7, marginBottom: 24 }}>
                presence-forward ai companion
            </p>

            <div
                style={{
                    border: "1px solid #ddd",
                    borderRadius: 16,
                    padding: 16,
                    minHeight: 420,
                    marginBottom: 16,
                    overflowY: "auto",
                    maxHeight: 500,
                }}
            >
                {messages.map((m, i) => (
                    <div
                        key={i}
                        style={{
                            marginBottom: 14,
                            padding: 12,
                            borderRadius: 12,
                            background: m.role === "user" ? "#f4f4f4" : "#ffffff",
                            border: "1px solid #eee",
                        }}
                    >
                        <strong>{m.role}:</strong> {m.content}
                    </div>
                ))}

                {loading && <div style={{ padding: 12, fontSize: 14, opacity: 0.7 }}>assistant: thinking…</div>}
            </div>

            <form onSubmit={onSubmit} style={{ display: "flex", gap: 12 }}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="send a message"
                    disabled={loading}
                    style={{
                        flex: 1,
                        padding: 12,
                        borderRadius: 12,
                        border: "1px solid #ccc",
                        fontSize: 14,
                    }}
                />
                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        padding: "12px 18px",
                        borderRadius: 12,
                        border: "1px solid #ccc",
                        cursor: loading ? "not-allowed" : "pointer",
                        background: "#fff",
                        fontSize: 14,
                    }}
                >
                    send
                </button>
            </form>
        </main>
    );
}
