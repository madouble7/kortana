#!/usr/bin/env python3
"""
Free Local LLM Agent using Ollama
Usage: python local_agent_simple.py source.json style [key] [tempo]
"""

import requests
import json
import sys
from pathlib import Path

class LocalLLMAgent:
    def __init__(self, base_url="http://localhost:11434", model="llama2"):
        self.base_url = base_url
        self.model = model
        
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def load_instructions(self):
        """Load agent instructions"""
        instructions_file = Path("AGENT_REMIX_INSTRUCTIONS.md")
        if instructions_file.exists():
            return instructions_file.read_text()[:2000]  # Truncate for local LLM
        else:
            return """
            Generate OneMotion Chord Player JSON remixes.
            
            For each style:
            - trap: 65 BPM, block chords, simple bass
            - house: 124 BPM, offbeat chords, driving bass  
            - drill: 95 BPM, stab chords, aggressive bass
            - rnb: 78 BPM, smooth arpeggios
            - ambient: 55 BPM, sustained chords, reverb
            
            Always preserve "parallellScaleChords" and required OneMotion fields.
            """
            
    def generate_remix(self, source_file, style, key=None, tempo=None):
        """Generate remix using local Ollama LLM"""
        
        # Check Ollama connection
        if not self.check_ollama():
            print("❌ Ollama not running. Start it with: ollama serve")
            print("   Install: https://ollama.ai/")
            return None
            
        # Load source
        try:
            source_data = json.loads(Path(source_file).read_text())
        except Exception as e:
            print(f"Error loading source: {e}")
            return None
            
        # Create focused prompt for local LLM
        instructions = self.load_instructions()
        
        # Simplified prompt for better local LLM performance
        prompt = f"""
Task: Create {style} remix of OneMotion JSON

Instructions: {instructions}

Source: {json.dumps(source_data, indent=1)}

Requirements:
- Change tempo for {style} style
- Modify bass and chord patterns
- Keep "parallellScaleChords" field
- Return valid JSON only

{style.upper()} REMIX JSON:
"""

        try:
            # Call Ollama API
            response = requests.post(f"{self.base_url}/api/generate", 
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 4096
                    }
                },
                timeout=120  # Local LLMs can be slow
            )
            
            if response.status_code != 200:
                print(f"Ollama API error: {response.status_code}")
                return None
                
            result = response.json()
            remix_text = result.get("response", "")
            
            # Extract JSON from response
            json_start = remix_text.find('{')
            json_end = remix_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                print("❌ No JSON found in response")
                print("Response:", remix_text[:200])
                return None
                
            remix_json = remix_text[json_start:json_end]
            
            # Validate JSON
            try:
                remix_data = json.loads(remix_json)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON generated: {e}")
                return None
                
            # Save output
            original_name = source_data.get('name', 'remix')
            output_file = f"{original_name}_{style}_local_remix.json"
            
            Path(output_file).write_text(json.dumps(remix_data, indent=2))
            
            print(f"✅ Generated local remix: {output_file}")
            print(f"   Style: {style}")
            print(f"   Model: {self.model}")
            
            return output_file
            
        except requests.exceptions.Timeout:
            print("❌ Request timed out. Local LLM may be too slow.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

def setup_ollama():
    """Print Ollama setup instructions"""
    print("""
🔧 OLLAMA SETUP (Free Local LLM)

1. Install Ollama:
   curl -fsSL https://ollama.ai/install.sh | sh

2. Start Ollama server:
   ollama serve

3. Pull a model (choose one):
   ollama pull llama2           # 3.8GB, good balance
   ollama pull codellama        # 3.8GB, better with code  
   ollama pull llama2:13b       # 7.3GB, higher quality

4. Run this script again
""")

def main():
    if len(sys.argv) < 3:
        print("Usage: python local_agent_simple.py source.json style [key] [tempo]")
        print("Example: python local_agent_simple.py over.json trap E 65")
        print("Styles: trap, house, drill, rnb, ambient")
        return
        
    source_file = sys.argv[1]
    style = sys.argv[2]
    key = sys.argv[3] if len(sys.argv) > 3 else None
    tempo = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Check source file
    if not Path(source_file).exists():
        print(f"❌ Source file not found: {source_file}")
        return
    
    print(f"🎵 Generating {style} remix using local LLM...")
    
    # Try to generate remix
    agent = LocalLLMAgent()
    
    if not agent.check_ollama():
        setup_ollama()
        return
        
    result = agent.generate_remix(source_file, style, key, tempo)
    
    if result:
        print(f"\n🎉 Success! Load {result} in OneMotion Chord Player")
        print("💡 Local LLM is free and private!")
    else:
        print("\n❌ Failed to generate remix")
        print("💡 Try: ollama pull llama2 (if model not installed)")

if __name__ == "__main__":
    main()