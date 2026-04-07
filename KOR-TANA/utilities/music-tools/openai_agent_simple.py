#!/usr/bin/env python3
"""
Simple OpenAI Agent for OneMotion Remixes
Usage: python openai_agent_simple.py source.json style [key] [tempo]
"""

import openai
import json
import sys
import os
from pathlib import Path

class SimpleRemixAgent:
    def __init__(self, api_key=None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        
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
        """Generate remix using OpenAI API"""
        
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

TASK: Generate a {style} style remix of the OneMotion file below.

SPECIFICATIONS:
- Style: {style}
- Key: {key if key else 'keep original key'}  
- Tempo: {tempo if tempo else 'use style-appropriate tempo'}

SOURCE ONEMOTION FILE:
{json.dumps(source_data, indent=2)}

REQUIREMENTS:
1. Return ONLY valid OneMotion JSON (no explanations)
2. Preserve the "parallellScaleChords" field (with double-l)
3. Keep "application": "OneMotion Chord-Player"
4. Apply style-appropriate tempo, bass, and chord changes
5. Maintain musical coherence

Generate the remix JSON:
"""

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert music AI that generates OneMotion Chord Player JSON files."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract JSON response
            remix_json = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            if remix_json.startswith('```json'):
                remix_json = remix_json[7:]
            if remix_json.endswith('```'):
                remix_json = remix_json[:-3]
            remix_json = remix_json.strip()
            
            # Validate JSON
            try:
                remix_data = json.loads(remix_json)
            except json.JSONDecodeError as e:
                print(f"Generated invalid JSON: {e}")
                print("Raw response:", remix_json[:500])
                return None
                
            # Save output file
            original_name = source_data.get('name', 'remix')
            output_file = f"{original_name}_{style}_ai_remix.json"
            
            Path(output_file).write_text(json.dumps(remix_data, indent=2))
            
            print(f"✅ Generated remix: {output_file}")
            print(f"   Style: {style}")
            print(f"   Key: {remix_data.get('scaleKey', 'unknown')}")
            print(f"   Tempo: {remix_data.get('style', {}).get('tempo', 'unknown')} BPM")
            
            return output_file
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python openai_agent_simple.py source.json style [key] [tempo]")
        print("Example: python openai_agent_simple.py over.json trap E 65")
        print("Styles: trap, house, drill, rnb, ambient")
        return
    
    source_file = sys.argv[1]
    style = sys.argv[2] 
    key = sys.argv[3] if len(sys.argv) > 3 else None
    tempo = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   Get your key from: https://platform.openai.com/api-keys")
        return
        
    # Check source file
    if not Path(source_file).exists():
        print(f"❌ Source file not found: {source_file}")
        return
        
    print(f"🎵 Generating {style} remix from {source_file}...")
    
    # Generate remix
    agent = SimpleRemixAgent()
    result = agent.generate_remix(source_file, style, key, tempo)
    
    if result:
        print(f"\n🎉 Success! Load {result} in OneMotion Chord Player")
    else:
        print("\n❌ Failed to generate remix")

if __name__ == "__main__":
    main()