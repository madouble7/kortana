#!/usr/bin/env python3
"""
OpenRouter-Compatible Agent for OneMotion Remixes
Usage: python openrouter_agent.py source.json style [key] [tempo]
"""

import openai
import json
import sys
import os
from pathlib import Path

class OpenRouterRemixAgent:
    def __init__(self, api_key=None):
        # Use OpenRouter endpoint with OpenAI client
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
        )
        
    def load_instructions(self):
        """Load agent instructions from file"""
        instructions_file = Path("AGENT_REMIX_INSTRUCTIONS.md")
        if instructions_file.exists():
            return instructions_file.read_text()
        else:
            return """
            You are an AI agent that generates OneMotion Chord Player JSON remixes.
            
            When given a source OneMotion JSON and remix style:
            1. Analyze the source structure
            2. Apply style-specific transformations (tempo, bass, chords, effects)
            3. Generate valid OneMotion JSON output
            4. Preserve required fields like "parallellScaleChords" and "application"
            
            Available styles: trap, house, drill, rnb, ambient
            """
    
    def generate_remix(self, source_file, style, key=None, tempo=None):
        """Generate remix using OpenRouter API"""
        
        # Load source file
        try:
            source_data = json.loads(Path(source_file).read_text())
        except Exception as e:
            print(f"Error loading source file: {e}")
            return None
            
        # Create prompt
        instructions = self.load_instructions()
        
        prompt = f"""
{instructions}

SOURCE ONEMOTION JSON:
{json.dumps(source_data, indent=2)}

REMIX REQUIREMENTS:
- Style: {style}
- Key: {key or 'keep original'}
- Tempo: {tempo or 'style appropriate'}

Generate a valid OneMotion JSON remix with the requested style changes.
Only output the JSON, no explanations.
"""
        
        try:
            # Use cheaper model for cost efficiency
            response = self.client.chat.completions.create(
                model="anthropic/claude-3.5-haiku", # Very cost effective
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            if result.startswith('```'):
                lines = result.split('\n')
                result = '\n'.join(lines[1:-1]) if len(lines) > 2 else result
                
            return json.loads(result)
            
        except Exception as e:
            print(f"API Error: {e}")
            return None
    
    def validate_output(self, data):
        """Validate OneMotion JSON structure"""
        required_fields = [
            'name', 'instrument', 'scale', 'scaleKey', 'application',
            'chordLayout', 'sequence', 'style', 'effectType', 
            'effectEcho', 'loopSequence', 'parallellScaleChords'
        ]
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            print(f"❌ Missing fields: {missing}")
            return False
            
        # Check specific format requirements
        if data.get('application') != 'OneMotion Chord-Player':
            print("❌ Wrong application field")
            return False
            
        if 'parallellScaleChords' not in data:
            print("❌ Missing parallellScaleChords (double-l)")
            return False
            
        return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python openrouter_agent.py source.json style [key] [tempo]")
        print("Styles: trap, house, drill, rnb, ambient")
        sys.exit(1)
    
    source_file = sys.argv[1]
    style = sys.argv[2]
    key = sys.argv[3] if len(sys.argv) > 3 else None
    tempo = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Get API key
    api_key = "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"
    
    if not api_key:
        print("Error: No OpenRouter API key found")
        sys.exit(1)
    
    # Create agent and generate remix
    agent = OpenRouterRemixAgent(api_key)
    
    print(f"🎵 Generating {style} remix from {source_file}...")
    if key:
        print(f"🎹 Target key: {key}")
    if tempo:
        print(f"🥁 Target tempo: {tempo}")
    
    result = agent.generate_remix(source_file, style, key, tempo)
    
    if result and agent.validate_output(result):
        # Generate output filename
        source_path = Path(source_file)
        output_file = source_path.parent / f"{source_path.stem}_{style}_remix.json"
        
        # Save result
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"✅ Remix saved to {output_file}")
        print(f"🎵 Name: {result['name']}")
        print(f"🎹 Key: {result['scaleKey']} {result['scale']}")
        print(f"🥁 Tempo: {result['style']['tempo']}")
        print(f"🎛️  Style: {style}")
        
    else:
        print("❌ Failed to generate valid remix")

if __name__ == "__main__":
    main()