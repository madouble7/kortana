# Quick Setup: External AI Agents

## Three Ways to Connect AI Agents to Your OneMotion Remix System

### 🥇 Option 1: OpenAI GPT (Recommended)

**Cost:** ~$0.002 per remix (cheap!)
**Quality:** Excellent

```bash
# 1. Get API key from platform.openai.com ($5 = ~2500 remixes)
# 2. Set environment variable
set OPENAI_API_KEY=your-key-here

# 3. Generate remix
python openai_agent_simple.py "C:\Users\madou\Downloads\over.json" trap E 65
```

### 🆓 Option 2: Local LLM (Completely Free)

**Cost:** Free forever
**Quality:** Good (slower generation)

```bash
# 1. Install Ollama (one-time setup)
# Download from: https://ollama.ai/

# 2. Start Ollama and pull model
ollama serve
ollama pull llama2

# 3. Generate remix
python local_agent_simple.py "C:\Users\madou\Downloads\over.json" house C 124
```

### 💬 Option 3: Manual ChatGPT (Free Daily Limit)

**Cost:** Free
**Quality:** Excellent (manual process)

```bash
# 1. Copy content from AGENT_REMIX_INSTRUCTIONS.md
# 2. Paste into ChatGPT with your over.json content
# 3. Ask: "Generate a trap remix in E minor at 65 BPM"
# 4. Copy the JSON response and save as new file
```

## Which Should You Choose?

| Your Situation | Best Option |
|----------------|------------|
| Have $5 to spend, want automation | **OpenAI GPT** |
| Want completely free, don't mind setup | **Local LLM** |
| Want free, don't mind manual process | **Manual ChatGPT** |
| Testing/experimenting | **Manual ChatGPT** |
| Production use | **OpenAI GPT** or **Local LLM** |

## Test It Out

1. **Pick an option** from above
2. **Follow the setup steps**
3. **Generate a remix** of your "Over" file
4. **Load the result** in OneMotion Chord Player
5. **Export MIDI/WAV** for your DAW

The AI agents understand all the OneMotion format requirements and will generate proper JSON files that load without errors.

## Need Help?

- **Setup issues**: Check `EXTERNAL_AGENT_SETUP.md` for detailed instructions
- **Agent behavior**: See `AGENT_REMIX_INSTRUCTIONS.md` for how they work
- **Format problems**: Refer to `ONEMOTION_GUIDE.md` for JSON requirements

Start with **Manual ChatGPT** if you just want to test it out — no installation required!
