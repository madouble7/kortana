#!/usr/bin/env python3
"""
🎹 OneMotion Chord Player JSON Builder
Interactive tool to create valid OneMotion JSON files easily
"""

import json
import os
from pathlib import Path

class OneMotionBuilder:
    def __init__(self):
        self.template = self.load_template()
        
    def load_template(self):
        """Load the base template"""
        template_path = Path(__file__).parent / "onemotion_template.json"
        with open(template_path, 'r') as f:
            return json.load(f)
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        print("🎹" + "="*60 + "🎹")
        print("        OneMotion Chord Player JSON Builder")
        print("🎹" + "="*60 + "🎹")
        print()
    
    def get_basic_info(self):
        """Get basic composition info"""
        print("📋 BASIC INFO")
        print("-" * 40)
        
        name = input("🎵 Song name: ").strip()
        if not name:
            name = "untitled"
        
        print("\n🎹 Choose instrument:")
        print("  1. piano (default)")
        print("  2. electric-piano")
        print("  3. upright-piano")
        print("  4. organ")
        instrument_choice = input("Choice (1-4) [1]: ").strip()
        instruments = {
            "1": "piano",
            "2": "electric-piano",
            "3": "upright-piano",
            "4": "organ"
        }
        instrument = instruments.get(instrument_choice, "piano")
        
        print("\n🎼 Choose scale:")
        print("  1. aeolian (natural minor)")
        print("  2. ionian (major)")
        print("  3. dorian")
        print("  4. phrygian")
        print("  5. harmonic-minor")
        scale_choice = input("Choice (1-5) [1]: ").strip()
        scales = {
            "1": "aeolian",
            "2": "ionian",
            "3": "dorian",
            "4": "phrygian",
            "5": "harmonic-minor"
        }
        scale = scales.get(scale_choice, "aeolian")
        
        print("\n🎹 Choose key:")
        keys = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        for i, key in enumerate(keys, 1):
            print(f"  {i:2d}. {key}")
        key_choice = input(f"Choice (1-{len(keys)}) [1]: ").strip()
        try:
            scaleKey = keys[int(key_choice) - 1]
        except:
            scaleKey = "C"
        
        tempo = input("\n⏱️  Tempo (BPM) [64]: ").strip()
        try:
            tempo = int(tempo)
        except:
            tempo = 64
        
        return {
            "name": name,
            "instrument": instrument,
            "scale": scale,
            "scaleKey": scaleKey,
            "tempo": tempo
        }
    
    def get_chord_sequence(self):
        """Build chord progression"""
        print("\n🎼 CHORD SEQUENCE")
        print("-" * 40)
        print("Enter chords one at a time. Press Enter with empty chord to finish.")
        print("\nAvailable chord types:")
        print("  min, maj, dim, min7, maj7, dom7, minMaj7, sus2, sus4")
        print("\nExample: min, 4, 0 (means: minor chord, 4 bars, root position 0)")
        
        sequence = []
        chord_num = 1
        
        while True:
            print(f"\n--- Chord {chord_num} ---")
            chord_type = input("Chord type (or Enter to finish): ").strip()
            if not chord_type:
                break
            
            length = input("Length in bars [4]: ").strip()
            try:
                length = int(length)
            except:
                length = 4
            
            rootPos = input("Root position (0-11) [0]: ").strip()
            try:
                rootPos = int(rootPos)
            except:
                rootPos = 0
            
            sequence.append({
                "chord": chord_type,
                "length": length,
                "rootPos": rootPos
            })
            chord_num += 1
        
        if not sequence:
            # Default to template sequence
            sequence = [
                {"chord": "min", "length": 4, "rootPos": 0},
                {"chord": "maj", "length": 4, "rootPos": 5}
            ]
        
        return sequence
    
    def get_style_preferences(self):
        """Get style preferences"""
        print("\n🎛️  STYLE PREFERENCES")
        print("-" * 40)
        
        print("\n🎸 Bass style:")
        print("  1. once (single note)")
        print("  2. arpeggio (bass arpeggio)")
        bass_choice = input("Choice (1-2) [1]: ").strip()
        bass_style = "arpeggio" if bass_choice == "2" else "once"
        
        print("\n🎹 Chord style:")
        print("  1. block (all notes together)")
        print("  2. split-23-1 (arpeggiated 2+3+1)")
        chord_choice = input("Choice (1-2) [1]: ").strip()
        if chord_choice == "2":
            chord_style = "split-23-1"
            chord_arp = "23 1"
            chord_step = [1, 8]
        else:
            chord_style = "block"
            chord_arp = "off"
            chord_step = [1, 4]
        
        return {
            "bass_style": bass_style,
            "chord_style": chord_style,
            "chord_arp": chord_arp,
            "chord_step": chord_step
        }
    
    def get_effects(self):
        """Get effect settings"""
        print("\n🔊 EFFECTS")
        print("-" * 40)
        
        print("\nEffect type:")
        print("  1. chamber")
        print("  2. hall")
        print("  3. room")
        effect_choice = input("Choice (1-3) [1]: ").strip()
        effects = {"1": "chamber", "2": "hall", "3": "room"}
        effect_type = effects.get(effect_choice, "chamber")
        
        echo_active = input("\nEnable echo? (y/n) [y]: ").strip().lower()
        echo_active = echo_active != 'n'
        
        return {
            "effectType": effect_type,
            "echo_active": echo_active
        }
    
    def build_json(self, basic_info, sequence, style_prefs, effects):
        """Assemble the final JSON"""
        result = self.template.copy()
        
        # Basic info
        result["name"] = basic_info["name"]
        result["instrument"] = basic_info["instrument"]
        result["scale"] = basic_info["scale"]
        result["scaleKey"] = basic_info["scaleKey"]
        result["style"]["tempo"] = basic_info["tempo"]
        
        # Sequence
        result["sequence"] = sequence
        
        # Style
        result["style"]["bass"]["style"] = style_prefs["bass_style"]
        result["style"]["chord"]["style"] = style_prefs["chord_style"]
        result["style"]["chord"]["arp"] = style_prefs["chord_arp"]
        result["style"]["chord"]["step"] = style_prefs["chord_step"]
        
        # Effects
        result["effectType"] = effects["effectType"]
        result["effectEcho"]["active"] = effects["echo_active"]
        
        return result
    
    def save_json(self, data, name):
        """Save to file"""
        filename = f"{name.lower().replace(' ', '_')}_onemotion.json"
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def run(self):
        """Main builder flow"""
        self.clear_screen()
        self.show_banner()
        
        print("Let's build your OneMotion Chord Player JSON!\n")
        
        # Gather info
        basic_info = self.get_basic_info()
        sequence = self.get_chord_sequence()
        style_prefs = self.get_style_preferences()
        effects = self.get_effects()
        
        # Build JSON
        print("\n⚙️  Building JSON...")
        result = self.build_json(basic_info, sequence, style_prefs, effects)
        
        # Save
        filepath = self.save_json(result, basic_info["name"])
        
        print(f"\n✅ SUCCESS!")
        print(f"📁 Saved to: {filepath}")
        print(f"🎹 Name: {result['name']}")
        print(f"🎼 Key: {result['scaleKey']} {result['scale']}")
        print(f"⏱️  Tempo: {result['style']['tempo']} BPM")
        print(f"🎵 Chords: {len(sequence)}")
        print(f"\n🎊 Ready to load in OneMotion Chord Player!")
        
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    builder = OneMotionBuilder()
    builder.run()
