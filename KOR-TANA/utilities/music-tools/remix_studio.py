#!/usr/bin/env python3
"""
🎵 KORDTANA REMIX STUDIO 🎵
Interactive AI Remix Generator

Just run: python remix_studio.py
"""

import openai
import json
import sys
import os
from pathlib import Path
import glob

class KordtanaRemixStudio:
    def __init__(self):
        self.api_key = "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"
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.styles = {
            "1": {"name": "trap", "desc": "Hard-hitting trap beats", "tempo": 95, "key": "E"},
            "2": {"name": "house", "desc": "Pumping house grooves", "tempo": 128, "key": "F#"},
            "3": {"name": "drill", "desc": "Aggressive drill patterns", "tempo": 140, "key": "C"},
            "4": {"name": "rnb", "desc": "Smooth R&B vibes", "tempo": 85, "key": "Bb"},
            "5": {"name": "ambient", "desc": "Ethereal ambient textures", "tempo": 70, "key": "D"}
        }
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def show_banner(self):
        print("🎵" + "="*50 + "🎵")
        print("     KORDTANA AI REMIX STUDIO")
        print("     Powered by OpenRouter + Claude")
        print("🎵" + "="*50 + "🎵")
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
        originals = [f for f in files if "_remix" not in f and "onemotion" in f.lower() or any(x in f.lower() for x in ["over", "chord", "progression"])]
        
        if not originals:
            # If no obvious originals, show all JSON files
            return [f for f in files if "_remix" not in f]
            
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
            
        print("📁 SELECT SOURCE FILE:")
        for i, file in enumerate(files, 1):
            filename = Path(file).name
            print(f"  {i}. {filename}")
        
        print(f"  0. Enter custom path")
        
        while True:
            choice = input(f"\n🎹 Choose file (1-{len(files)}, 0 for custom): ").strip()
            
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

    def select_style(self):
        print("\n🎛️  SELECT REMIX STYLE:")
        for num, style in self.styles.items():
            print(f"  {num}. {style['name'].upper():8} - {style['desc']} ({style['tempo']} BPM, {style['key']} key)")
        
        while True:
            choice = input(f"\n🎵 Choose style (1-{len(self.styles)}): ").strip()
            if choice in self.styles:
                return self.styles[choice]
            print("❌ Invalid choice!")

    def customize_settings(self, style):
        print(f"\n🎹 CUSTOMIZE REMIX (or press Enter for defaults):")
        
        # Key selection
        current_key = style["key"]
        new_key = input(f"🎼 Key [{current_key}]: ").strip()
        if new_key:
            current_key = new_key
            
        # Tempo selection  
        current_tempo = style["tempo"]
        new_tempo = input(f"🥁 Tempo [{current_tempo}]: ").strip()
        if new_tempo:
            try:
                current_tempo = int(new_tempo)
            except ValueError:
                print("⚠️  Invalid tempo, using default")
        
        return current_key, current_tempo

    def generate_remix(self, source_file, style_name, key, tempo):
        print(f"\n🚀 Generating {style_name} remix...")
        print(f"   📁 Source: {Path(source_file).name}")
        print(f"   🎹 Key: {key}")
        print(f"   🥁 Tempo: {tempo}")
        
        try:
            # Load source
            with open(source_file, 'r') as f:
                source_data = json.load(f)
            
            # Load instructions
            instructions_file = Path("AGENT_REMIX_INSTRUCTIONS.md")
            if instructions_file.exists():
                instructions = instructions_file.read_text()
            else:
                instructions = "Generate OneMotion Chord Player JSON remix with proper format."
            
            # Create prompt
            prompt = f"""
{instructions}

SOURCE ONEMOTION JSON:
{json.dumps(source_data, indent=2)}

REMIX REQUIREMENTS:
- Style: {style_name}
- Key: {key}
- Tempo: {tempo}

Generate a valid OneMotion JSON remix. Only output the JSON, no explanations.
"""
            
            # Generate with AI
            response = self.client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean up response
            if result.startswith('```'):
                lines = result.split('\n')
                result = '\n'.join(lines[1:-1]) if len(lines) > 2 else result
                
            remix_data = json.loads(result)
            
            # Generate output filename
            source_path = Path(source_file)
            timestamp = ""  # Remove timestamp for cleaner names
            output_file = source_path.parent / f"{source_path.stem}_{style_name}_remix.json"
            
            # Make sure we don't overwrite
            counter = 1
            while output_file.exists():
                output_file = source_path.parent / f"{source_path.stem}_{style_name}_remix_{counter}.json"
                counter += 1
            
            # Save result
            with open(output_file, 'w') as f:
                json.dump(remix_data, f, indent=2)
                
            print(f"✅ SUCCESS! Remix saved to:")
            print(f"   📂 {output_file}")
            print(f"   🎵 Name: {remix_data.get('name', 'Unknown')}")
            
            return str(output_file)
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None

    def show_menu(self):
        print("\n" + "="*52)
        print("🎵 MAIN MENU:")
        print("  1. 🎹 Generate New Remix")
        print("  2. 📁 View Generated Remixes") 
        print("  3. 💰 View Cost Summary")
        print("  4. ❌ Exit")
        print("="*52)

    def view_remixes(self):
        remix_files = glob.glob("C:/Users/madou/Downloads/*_remix*.json")
        remix_files.extend(glob.glob("C:/kordtana_starter_pack/*_remix*.json"))
        remix_files.extend(glob.glob("./*_remix*.json"))
        
        if not remix_files:
            print("\n📂 No remix files found yet!")
            return
            
        print(f"\n🎵 GENERATED REMIXES ({len(remix_files)} total):")
        print("-" * 52)
        
        for i, file in enumerate(remix_files, 1):
            filename = Path(file).name
            size = os.path.getsize(file)
            print(f"  {i:2d}. {filename} ({size:,} bytes)")
        
        input("\n📱 Press Enter to continue...")

    def show_cost_summary(self):
        remix_count = len(glob.glob("C:/Users/madou/Downloads/*_remix*.json"))
        remix_count += len(glob.glob("C:/kordtana_starter_pack/*_remix*.json")) 
        remix_count += len(glob.glob("./*_remix*.json"))
        
        cost_per_remix = 0.0018
        total_cost = remix_count * cost_per_remix
        remaining_budget = 5.00 - total_cost
        remaining_remixes = int(remaining_budget / cost_per_remix)
        
        print(f"\n💰 COST SUMMARY:")
        print("-" * 30)
        print(f"  🎵 Remixes Generated: {remix_count}")
        print(f"  💵 Cost per Remix:   ${cost_per_remix:.4f}")
        print(f"  💳 Total Spent:      ${total_cost:.4f}")
        print(f"  🏦 Remaining Budget: ${remaining_budget:.4f}")
        print(f"  🎹 Remixes Left:     ~{remaining_remixes:,}")
        
        if remix_count > 0:
            print(f"\n🚀 Average cost: ${total_cost/remix_count:.4f} per remix!")
            
        input("\n📱 Press Enter to continue...")

    def run(self):
        while True:
            self.clear_screen()
            self.show_banner()
            self.show_menu()
            
            choice = input("\n🎛️  Your choice: ").strip()
            
            if choice == "1":
                self.clear_screen()
                self.show_banner()
                
                # Select source file
                source_file = self.select_source_file()
                if not source_file:
                    input("\n📱 Press Enter to continue...")
                    continue
                
                # Select style
                style = self.select_style()
                
                # Customize settings
                key, tempo = self.customize_settings(style)
                
                # Generate remix
                output_file = self.generate_remix(source_file, style["name"], key, tempo)
                
                if output_file:
                    print(f"\n🎊 Ready to use in OneMotion Chord Player!")
                    
                input("\n📱 Press Enter to continue...")
                
            elif choice == "2":
                self.view_remixes()
                
            elif choice == "3":
                self.show_cost_summary()
                
            elif choice == "4":
                print("\n👋 Thanks for using Kordtana Remix Studio!")
                break
                
            else:
                print("❌ Invalid choice!")
                input("📱 Press Enter to continue...")

if __name__ == "__main__":
    studio = KordtanaRemixStudio()
    studio.run()