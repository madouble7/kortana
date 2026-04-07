# Connecting External AI Agents to OneMotion Remix System

## Overview

Your OneMotion remix system can be used by external AI agents through several integration methods. Here are the practical options for connecting "cheap or free" agents.

## Integration Methods

### 1. OpenAI API Agents (GPT-3.5/4)

#### Setup Process

```bash
# Install OpenAI Python library
pip install openai

# Set API key (get from platform.openai.com)
export OPENAI_API_KEY="your-key-here"
```

#### Agent Integration Script

```python
# openai_remix_agent.py
import openai
import json
from pathlib import Path

class OneMotionRemixAgent:
    def __init__(self, api_key=None):
        self.client = openai.OpenAI(api_key=api_key)
        self.instructions = Path("AGENT_REMIX_INSTRUCTIONS.md").read_text()

    def generate_remix(self, source_file, style, key=None, tempo=None):
        # Load source OneMotion file
        source_data = json.loads(Path(source_file).read_text())

        # Create agent prompt
        prompt = f"""
        {self.instructions}

        TASK: Generate a {style} remix of the following OneMotion file.
        Key: {key or 'keep original'}
        Tempo: {tempo or 'use style default'}

        SOURCE FILE:
        {json.dumps(source_data, indent=2)}

        Return only valid OneMotion JSON for the remix.
        """

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" for better results
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        # Parse and save remix
        remix_json = response.choices[0].message.content
        output_file = f"{source_data['name']}_{style}_remix.json"
        Path(output_file).write_text(remix_json)

        return output_file

# Usage
agent = OneMotionRemixAgent()
remix_file = agent.generate_remix("over.json", "trap", "E", 65)
```

### 2. Local LLM Agents (Free)

#### Using Ollama (Free Local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a capable model
ollama pull llama2:13b
# or ollama pull codellama:13b
```

#### Local Agent Script

```python
# local_remix_agent.py
import requests
import json
from pathlib import Path

class LocalRemixAgent:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.instructions = Path("AGENT_REMIX_INSTRUCTIONS.md").read_text()

    def generate_remix(self, source_file, style, key=None, tempo=None):
        source_data = json.loads(Path(source_file).read_text())

        prompt = f"""
        {self.instructions}

        Generate a {style} remix of this OneMotion file:
        {json.dumps(source_data, indent=2)}

        Style: {style}
        Key: {key or 'original'}
        Tempo: {tempo or 'style default'}

        Return valid OneMotion JSON only.
        """

        response = requests.post(f"{self.base_url}/api/generate", json={
            "model": "llama2:13b",
            "prompt": prompt,
            "stream": False
        })

        remix_json = response.json()["response"]
        output_file = f"{source_data['name']}_{style}_local_remix.json"
        Path(output_file).write_text(remix_json)
        return output_file

# Usage
agent = LocalRemixAgent()
remix = agent.generate_remix("over.json", "house", "C", 124)
```

### 3. Hugging Face Agents (Free Tier)

#### Setup

```bash
pip install transformers torch
```

#### HuggingFace Agent

```python
# hf_remix_agent.py
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import json
from pathlib import Path

class HuggingFaceRemixAgent:
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.generator = pipeline("text-generation",
                                model=self.model,
                                tokenizer=self.tokenizer)

    def generate_remix(self, source_file, style, key=None, tempo=None):
        instructions = Path("AGENT_REMIX_INSTRUCTIONS.md").read_text()
        source_data = json.loads(Path(source_file).read_text())

        prompt = f"""
        Instructions: {instructions[:1000]}...

        Task: Generate {style} remix
        Source: {json.dumps(source_data)[:500]}...

        Output OneMotion JSON:
        """

        result = self.generator(prompt, max_length=2000, temperature=0.7)
        remix_text = result[0]["generated_text"]

        # Extract JSON (you may need to clean this up)
        json_start = remix_text.find('{"')
        if json_start != -1:
            remix_json = remix_text[json_start:]
            output_file = f"{source_data['name']}_{style}_hf_remix.json"
            Path(output_file).write_text(remix_json)
            return output_file
        else:
            raise ValueError("No valid JSON found in response")
```

### 4. Cloud Agent Services (Free Tiers)

#### Google Colab Agent (Free)

```python
# colab_remix_agent.py - Run in Google Colab
!pip install openai

import json
from pathlib import Path
from google.colab import files

# Upload your files
uploaded = files.upload()  # Upload AGENT_REMIX_INSTRUCTIONS.md and source JSON

class ColabRemixAgent:
    def __init__(self):
        self.instructions = open('AGENT_REMIX_INSTRUCTIONS.md').read()

    def generate_remix(self, source_filename, style):
        source_data = json.load(open(source_filename))

        # Use free ChatGPT web interface or other free API
        print("PROMPT TO COPY TO CHATGPT:")
        print("="*50)
        print(f"{self.instructions}\n")
        print(f"Generate {style} remix of:")
        print(json.dumps(source_data, indent=2))
        print("="*50)

        # Manual process - copy output back
        remix_json = input("Paste the generated JSON here: ")

        with open(f"{source_data['name']}_{style}_remix.json", 'w') as f:
            f.write(remix_json)

        files.download(f"{source_data['name']}_{style}_remix.json")

# Usage
agent = ColabRemixAgent()
agent.generate_remix("over.json", "trap")
```

## Cost Comparison

| Method | Cost | Setup Difficulty | Quality |
|--------|------|-----------------|---------|
| OpenAI GPT-3.5 | ~$0.002/request | Easy | High |
| OpenAI GPT-4 | ~$0.03/request | Easy | Very High |
| Ollama (Local) | Free | Medium | Good |
| HuggingFace | Free | Medium | Variable |
| Google Colab | Free | Easy | Manual |

## Quick Start: Cheapest Options

### Option 1: OpenAI GPT-3.5 (Best Balance)

```bash
# $5 credit lasts ~2500 remixes
pip install openai
python openai_remix_agent.py
```

### Option 2: Ollama Local (Completely Free)

```bash
# One-time setup, then free forever
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2:13b
python local_remix_agent.py
```

### Option 3: Manual ChatGPT (Free Daily Limit)

1. Copy `AGENT_REMIX_INSTRUCTIONS.md` content
2. Paste into ChatGPT with your source JSON
3. Copy generated remix back

## Production Integration

### Web API Wrapper

```python
# remix_api.py - Flask wrapper for any agent
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/remix', methods=['POST'])
def create_remix():
    data = request.json
    source_file = data['source_file']
    style = data['style']
    key = data.get('key')
    tempo = data.get('tempo')

    # Use any agent backend
    agent = LocalRemixAgent()  # or OpenAIAgent, etc.
    remix_file = agent.generate_remix(source_file, style, key, tempo)

    return jsonify({
        'success': True,
        'remix_file': remix_file,
        'download_url': f'/download/{remix_file}'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Usage

```bash
curl -X POST http://localhost:5000/remix \
  -H "Content-Type: application/json" \
  -d '{"source_file": "over.json", "style": "trap", "key": "E"}'
```

## Recommended Setup

**For Development**: Start with OpenAI GPT-3.5 ($5 gives you thousands of remixes)

**For Production**: Use Ollama local setup (free, private, unlimited)

**For Testing**: Use manual ChatGPT method (free daily limit)

Choose based on your budget, privacy needs, and technical comfort level.
