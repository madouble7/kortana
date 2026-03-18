import OpenAI from "openai";

const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

type Msg = {
    role: "user" | "assistant";
    content: string;
};

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const messages = Array.isArray(body?.messages) ? (body.messages as Msg[]) : null;

        if (!messages) {
            return Response.json({ error: "messages must be an array" }, { status: 400 });
        }

        const input = [
            {
                role: "developer" as const,
                content:
                    "you are kor'tana: clear, kind, concise, lowercase, practical, reverent when users use sacred language, but never claim divine authority.",
            },
            ...messages.map((m) => ({
                role: m.role,
                content: String(m.content ?? ""),
            })),
        ];

        const response = await client.responses.create({
            model: process.env.OPENAI_MODEL || "gpt-5.4",
            input,
        });

        return Response.json({ text: response.output_text });
    } catch (error) {
        console.error(error);
        return Response.json({ error: "failed to generate response" }, { status: 500 });
    }
}
