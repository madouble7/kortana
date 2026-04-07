#!/usr/bin/env python3
"""
🎼 KORDTANA HARMONY STUDIO 🎼
Advanced Chord Progression & Melody Generator

Focus: Musical composition, not beats
"""

import openai
import json
import sys
import os
from pathlib import Path
import glob

class KordtanaHarmonyStudio:
    def __init__(self):
        self.api_key = "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"
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        
        self.progressions = {
            "1": {
                "name": "jazz_extensions",
                "desc": "Rich jazz harmonies with 7ths, 9ths, 11ths",
                "focus": "Extended chords, chromatic voice leading",
                "example": "Cmaj7 → Am7 → Dm9 → G13sus4"
            },
            "2": {
                "name": "modal_interchange", 
                "desc": "Borrowed chords from parallel modes",
                "focus": "Color tones, emotional depth",
                "example": "C → Am → F → Fm → C (borrowing from C minor)"
            },
            "3": {
                "name": "circle_fifths",
                "desc": "Movement through circle of fifths",
                "focus": "Strong harmonic motion, classical elegance",
                "example": "C → F → Bb → Eb → Ab → Db"
            },
            "4": {
                "name": "neo_soul", 
                "desc": "Modern R&B progressions with rich extensions",
                "focus": "Smooth voice leading, complex harmony",
                "example": "Cmaj9 → Em7add11 → Am7 → Fmaj7#11"
            },
            "5": {
                "name": "classical_cadences",
                "desc": "Traditional functional harmony patterns", 
                "focus": "Authentic cadences, voice leading rules",
                "example": "C → Am → F → G → C (i-vi-IV-V-I)"
            },
            "6": {
                "name": "quartal_harmony",
                "desc": "Chords built in 4ths instead of 3rds",
                "focus": "Modern, open sound, jazz influence", 
                "example": "C-F-Bb → G-C-F → D-G-C"
            },
            "7": {
                "name": "chromatic_mediant",
                "desc": "Unexpected chord relationships via chromatic mediants",
                "focus": "Surprising harmonic color, film music",
                "example": "C → Ab → F → Db → C"
            },
            "8": {
                "name": "sus_cascades",
                "desc": "Suspended chord resolutions and chains",
                "focus": "Harmonic tension and release",
                "example": "Csus4 → C → Fsus2 → F → Gsus4 → G"
            }
        }
        
        self.melodies = {
            "1": {
                "name": "stepwise_motion",
                "desc": "Smooth, connected melodic lines",
                "approach": "Scale-based, minimal leaps"
            },
            "2": {
                "name": "arpeggiated",
                "desc": "Melody follows chord tones",
                "approach": "Chord-based, harmonic outline"
            },
            "3": {
                "name": "intervallic_leaps",
                "desc": "Bold melodic jumps and intervals", 
                "approach": "Wide intervals, dramatic contour"
            },
            "4": {
                "name": "motivic_development",
                "desc": "Develops short musical ideas",
                "approach": "Theme and variations, classical technique"
            },
            "5": {
                "name": "pentatonic_flow",
                "desc": "Uses pentatonic scales for smoothness",
                "approach": "World music influence, natural feel"
            }
        }

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def show_banner(self):
        print("🎼" + "="*60 + "🎼")
        print("        KORDTANA HARMONY STUDIO")
        print("     Advanced Musical Composition System")
        print("🎼" + "="*60 + "🎼")
        print()

    def find_json_files(self):
        """Find all JSON files in common locations"""
        locations = [
            "C:/Users/madou/Downloads/*.json",
            "C:/kordtana_starter_pack/*.json", 
            "./*.json"
        ]
        
        files = []
        for pattern in locations:
            files.extend(glob.glob(pattern))
            
        # Filter out remix files, keep originals
        originals = [f for f in files if "_remix" not in f and "_harmony" not in f]
        return originals

    def select_source_file(self):
        files = self.find_json_files()
        
        if not files:
            print("❌ No JSON files found!")
            print("📁 Place your OneMotion JSON files in:")
            print("   • C:/Users/madou/Downloads/")
            print("   • C:/kordtana_starter_pack/") 
            print("   • Current directory")
            return None
            
        print("📁 SELECT SOURCE COMPOSITION:")
        for i, file in enumerate(files, 1):
            filename = Path(file).name
            print(f"  {i}. {filename}")
        
        print(f"  0. Enter custom path")
        
        while True:
            choice = input(f"\n🎼 Choose file (1-{len(files)}, 0 for custom): ").strip()
            
            if choice == "0":
                custom_path = input("📂 Enter full path to JSON file: ").strip().strip('"')
                if os.path.exists(custom_path):
                    return custom_path
                else:
                    print("❌ File not found!")
                    continue
                    
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    return files[idx]
            except ValueError:
                pass
                
            print("❌ Invalid choice!")

    def select_progression_style(self):
        print("\n🎵 SELECT HARMONIC PROGRESSION STYLE:")
        print("-" * 65)
        for num, prog in self.progressions.items():
            print(f"  {num}. {prog['name'].upper().replace('_', ' ')}")
            print(f"     {prog['desc']}")
            print(f"     Focus: {prog['focus']}")
            print(f"     Example: {prog['example']}")
            print()
        
        while True:
            choice = input(f"🎹 Choose progression style (1-{len(self.progressions)}): ").strip()
            if choice in self.progressions:
                return self.progressions[choice]
            print("❌ Invalid choice!")

    def select_melody_approach(self):
        print("\n🎶 SELECT MELODIC APPROACH:")
        print("-" * 50)
        for num, mel in self.melodies.items():
            print(f"  {num}. {mel['name'].upper().replace('_', ' ')}")
            print(f"     {mel['desc']}")
            print(f"     Approach: {mel['approach']}")
            print()
        
        while True:
            choice = input(f"🎵 Choose melodic approach (1-{len(self.melodies)}): ").strip()
            if choice in self.melodies:
                return self.melodies[choice]
            print("❌ Invalid choice!")

    def customize_harmonic_settings(self):
        print(f"\n🎼 HARMONIC CUSTOMIZATION:")
        
        # Key center
        current_key = "C"
        new_key = input(f"🎹 Target key center [{current_key}]: ").strip()
        if new_key:
            current_key = new_key
            
        # Complexity level
        print("\n🎯 Harmonic complexity:")
        print("  1. Simple (triads, basic 7ths)")
        print("  2. Intermediate (9ths, sus chords)")  
        print("  3. Advanced (11ths, 13ths, alterations)")
        
        complexity = input("Choose complexity (1-3) [2]: ").strip()
        if not complexity:
            complexity = "2"
            
        # Chord density
        density = input("🎼 Chords per measure (1-4) [2]: ").strip()
        if not density:
            density = "2"
            
        return current_key, complexity, density

    def generate_harmony_composition(self, source_file, progression_style, melody_style, key, complexity, density):
        print(f"\n🎼 Generating harmonic composition...")
        print(f"   📁 Source: {Path(source_file).name}")
        print(f"   🎹 Key: {key}")
        print(f"   🎵 Progression: {progression_style['name'].replace('_', ' ').title()}")
        print(f"   🎶 Melody: {melody_style['name'].replace('_', ' ').title()}")
        print(f"   🎯 Complexity: {complexity}/3")
        
        try:
            # Load source
            with open(source_file, 'r') as f:
                source_data = json.load(f)
            
            # Create sophisticated harmony prompt
            prompt = f"""
You are Kordtana, an advanced harmonic composition AI specializing in chord progressions, voice leading, and melodic development.

HARMONIC ANALYSIS OF SOURCE:
{json.dumps(source_data, indent=2)}

COMPOSITION REQUIREMENTS:
Target Key: {key}
Progression Style: {progression_style['name']} - {progression_style['desc']}
Melodic Approach: {melody_style['name']} - {melody_style['desc']}
Harmonic Complexity: Level {complexity}/3
Chord Density: {density} chord(s) per measure

ADVANCED HARMONIC TECHNIQUES TO APPLY:
1. Voice Leading: Smooth connection between chords (common tones, stepwise motion)
2. Chord Extensions: Use appropriate tensions (7ths, 9ths, 11ths, 13ths) based on complexity level
3. Harmonic Rhythm: Vary the pace of chord changes for musical interest
4. Modal Interchange: Borrow chords from parallel modes when appropriate
5. Secondary Dominants: Use V/V, V/vi etc. for harmonic sophistication
6. Chord Inversions: Use bass movement to create smooth progressions

MELODIC DEVELOPMENT FOCUS:
- Create memorable, singable melodies that work with the harmony
- Use the specified melodic approach: {melody_style['approach']}
- Ensure melody and harmony complement each other
- Add appropriate passing tones and neighbor notes

SPECIFIC STYLE GUIDANCE:
{progression_style['focus']}
Example progression pattern: {progression_style['example']}

Generate a musically sophisticated OneMotion JSON that transforms the source material using advanced harmonic concepts. Focus on MUSICAL CONTENT over rhythm or beats.

Only output the JSON, no explanations.
"""
            
            # Generate with AI
            response = self.client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher creativity for music
                max_tokens=2500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean up response
            if result.startswith('```'):
                lines = result.split('\n')
                result = '\n'.join(lines[1:-1]) if len(lines) > 2 else result
                
            harmony_data = json.loads(result)
            
            # Generate output filename
            source_path = Path(source_file)
            style_name = f"{progression_style['name']}_{melody_style['name']}"
            output_file = source_path.parent / f"{source_path.stem}_{style_name}_harmony.json"
            
            # Make sure we don't overwrite
            counter = 1
            while output_file.exists():
                output_file = source_path.parent / f"{source_path.stem}_{style_name}_harmony_{counter}.json"
                counter += 1
            
            # Save result
            with open(output_file, 'w') as f:
                json.dump(harmony_data, f, indent=2)
                
            print(f"✅ SUCCESS! Harmonic composition saved:")
            print(f"   📂 {output_file}")
            print(f"   🎼 Name: {harmony_data.get('name', 'Unknown')}")
            print(f"   🎹 Key: {harmony_data.get('scaleKey', 'Unknown')} {harmony_data.get('scale', '')}")
            
            # Show chord analysis
            if 'sequence' in harmony_data:
                print(f"   🎵 Progression: {' → '.join([chord.get('chord', '?') for chord in harmony_data['sequence'][:4]])}")
            
            return str(output_file)
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None

    def show_menu(self):
        print("\n" + "="*62)
        print("🎼 HARMONY STUDIO MENU:")
        print("  1. 🎹 Generate Harmonic Composition")
        print("  2. 📁 View Generated Compositions") 
        print("  3. 🎵 Analyze Chord Progressions")
        print("  4. 💰 View Cost Summary")
        print("  5. ❌ Exit")
        print("="*62)

    def view_compositions(self):
        harmony_files = glob.glob("C:/Users/madou/Downloads/*_harmony*.json")
        harmony_files.extend(glob.glob("C:/kordtana_starter_pack/*_harmony*.json"))
        harmony_files.extend(glob.glob("./*_harmony*.json"))
        
        if not harmony_files:
            print("\n📂 No harmonic compositions found yet!")
            return
            
        print(f"\n🎼 GENERATED COMPOSITIONS ({len(harmony_files)} total):")
        print("-" * 65)
        
        for i, file in enumerate(harmony_files, 1):
            filename = Path(file).name
            size = os.path.getsize(file)
            
            # Try to read and show key info
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                key_info = f"{data.get('scaleKey', '?')} {data.get('scale', '')}"
                chord_count = len(data.get('sequence', []))
                print(f"  {i:2d}. {filename}")
                print(f"      Key: {key_info}, Chords: {chord_count}, Size: {size:,} bytes")
            except:
                print(f"  {i:2d}. {filename} ({size:,} bytes)")
        
        input("\n📱 Press Enter to continue...")

    def analyze_progressions(self):
        print("\n🎵 CHORD PROGRESSION ANALYSIS")
        print("-" * 40)
        
        # Show available progressions
        harmony_files = glob.glob("*_harmony*.json")
        if not harmony_files:
            print("No harmony files to analyze!")
            return
            
        print("Select file to analyze:")
        for i, file in enumerate(harmony_files, 1):
            print(f"  {i}. {Path(file).name}")
            
        choice = input(f"\nChoose file (1-{len(harmony_files)}): ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(harmony_files):
                file_path = harmony_files[idx]
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                print(f"\n🎼 ANALYSIS: {Path(file_path).name}")
                print("-" * 50)
                print(f"Key: {data.get('scaleKey')} {data.get('scale')}")
                print(f"Time Signature: {data.get('style', {}).get('timeSignature', 'Unknown')}")
                
                sequence = data.get('sequence', [])
                print(f"\n🎹 CHORD PROGRESSION ({len(sequence)} chords):")
                
                for i, chord_info in enumerate(sequence, 1):
                    chord = chord_info.get('chord', 'Unknown')
                    length = chord_info.get('length', 1)
                    pos = chord_info.get('rootPos', 0)
                    print(f"  {i:2d}. {chord:<12} ({length} bars, pos {pos})")
                
        except (ValueError, IndexError, FileNotFoundError):
            print("Invalid selection!")
            
        input("\n📱 Press Enter to continue...")

    def show_cost_summary(self):
        harmony_count = len(glob.glob("C:/Users/madou/Downloads/*_harmony*.json"))
        harmony_count += len(glob.glob("C:/kordtana_starter_pack/*_harmony*.json")) 
        harmony_count += len(glob.glob("./*_harmony*.json"))
        
        cost_per_composition = 0.0025  # Slightly higher due to complexity
        total_cost = harmony_count * cost_per_composition
        remaining_budget = 5.00 - total_cost
        remaining_compositions = int(remaining_budget / cost_per_composition)
        
        print(f"\n💰 HARMONY STUDIO COST SUMMARY:")
        print("-" * 40)
        print(f"  🎼 Compositions Generated: {harmony_count}")
        print(f"  💵 Cost per Composition:  ${cost_per_composition:.4f}")
        print(f"  💳 Total Spent:          ${total_cost:.4f}")
        print(f"  🏦 Remaining Budget:     ${remaining_budget:.4f}")
        print(f"  🎹 Compositions Left:    ~{remaining_compositions:,}")
        
        if harmony_count > 0:
            print(f"\n🎵 Advanced harmonic AI: ${total_cost/harmony_count:.4f} per composition!")
            
        input("\n📱 Press Enter to continue...")

    def run(self):
        while True:
            self.clear_screen()
            self.show_banner()
            self.show_menu()
            
            choice = input("\n🎼 Your choice: ").strip()
            
            if choice == "1":
                self.clear_screen()
                self.show_banner()
                
                # Select source file
                source_file = self.select_source_file()
                if not source_file:
                    input("\n📱 Press Enter to continue...")
                    continue
                
                # Select harmonic progression style
                progression_style = self.select_progression_style()
                
                # Select melodic approach
                melody_style = self.select_melody_approach()
                
                # Customize harmonic settings
                key, complexity, density = self.customize_harmonic_settings()
                
                # Generate composition
                output_file = self.generate_harmony_composition(
                    source_file, progression_style, melody_style, key, complexity, density
                )
                
                if output_file:
                    print(f"\n🎊 Advanced harmonic composition ready!")
                    print(f"🎼 Load in OneMotion Chord Player to hear the harmony")
                    
                input("\n📱 Press Enter to continue...")
                
            elif choice == "2":
                self.view_compositions()
                
            elif choice == "3":
                self.analyze_progressions()
                
            elif choice == "4":
                self.show_cost_summary()
                
            elif choice == "5":
                print("\n👋 Thanks for using Kordtana Harmony Studio!")
                break
                
            else:
                print("❌ Invalid choice!")
                input("📱 Press Enter to continue...")

if __name__ == "__main__":
    studio = KordtanaHarmonyStudio()
    studio.run()