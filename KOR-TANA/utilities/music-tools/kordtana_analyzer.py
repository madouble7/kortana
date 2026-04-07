#!/usr/bin/env python3
"""
Kordtana Analyzer - Add Emotional Intelligence to Existing Progressions

Takes any OneMotion JSON and adds Kordtana metadata based on harmonic analysis.

Usage:
    python kordtana_analyzer.py <input_file.json> [output_file.json]
"""

import json
import sys
from pathlib import Path

# Chord type to emotion mapping
CHORD_EMOTION_MAP = {
    "maj": "clarity",
    "min": "introspection",
    "maj7": "clarity",
    "min7": "movement",
    "dom7": "tension",
    "maj9": "transcendence",
    "min9": "yearning",
    "dom9": "tension",
    "min11": "yearning",
    "dom13": "tension",
    "sus2": "suspension",
    "sus4": "suspension",
    "add9": "clarity",
    "6": "nostalgia",
    "69": "transcendence",
    "dim": "mystery",
    "aug": "mystery"
}

# Function mapping based on typical progressions
FUNCTION_PATTERNS = {
    0: "tonic",
    2: "supertonic",
    3: "subdominant",
    5: "subdominant",
    7: "dominant",
    9: "submediant",
    10: "dominant"
}

def analyze_chord_progression(json_data: dict) -> dict:
    """
    Analyze an existing progression and add Kordtana metadata.
    """
    sequence = json_data.get("sequence", [])
    key = json_data.get("scaleKey", "C")
    scale = json_data.get("scale", "ionian")
    tempo = json_data.get("style", {}).get("tempo", 66)
    
    # Build emotional arc
    emotional_arc = []
    glyph = ""
    function_map = {}
    breath_map = []
    
    current_beat = 0
    for i, chord_item in enumerate(sequence):
        chord_type = chord_item.get("chord", "maj")
        length = chord_item.get("length", 4)
        root_pos = chord_item.get("rootPos", 0)
        
        # Determine emotion
        emotion = CHORD_EMOTION_MAP.get(chord_type, "clarity")
        emotional_arc.append(emotion)
        
        # Determine function
        function = FUNCTION_PATTERNS.get(root_pos, "color_tone")
        
        # Build glyph
        glyph_map = {
            "clarity": "⟡",
            "introspection": "⟠",
            "movement": "⟠",
            "tension": "↯",
            "suspension": "⧖",
            "yearning": "◈",
            "transcendence": "∞",
            "mystery": "⌘",
            "nostalgia": "⊙"
        }
        glyph += glyph_map.get(emotion, "⟡")
        
        # Add to function map
        function_map[str(current_beat)] = {
            "chord": f"{key}{chord_type}",
            "function": function,
            "emotion": emotion,
            "root_position": root_pos
        }
        
        # Add to breath map
        breath_map.append(current_beat)
        current_beat += length
    
    # Determine primary emotion (most common)
    primary_emotion = max(set(emotional_arc), key=emotional_arc.count)
    
    # Determine resolution type
    last_chord = sequence[-1].get("chord", "maj")
    if last_chord in ["sus2", "sus4", "dom7"]:
        resolution = "incomplete"
    elif last_chord in ["maj", "maj7", "maj9"]:
        resolution = "resolved"
    else:
        resolution = "ambiguous"
    
    # Determine tempo feel
    if tempo < 70:
        tempo_feel = "patient"
    elif tempo < 85:
        tempo_feel = "breathing"
    else:
        tempo_feel = "driving"
    
    # Create Kordtana metadata
    kordtana_data = {
        "emotional_arc": {
            "primary": primary_emotion,
            "journey": emotional_arc,
            "resolution": resolution
        },
        "ritual_metadata": {
            "glyph": glyph,
            "breath_map": breath_map,
            "intention": f"{key} {scale} progression - {primary_emotion} theme",
            "tempo_feel": tempo_feel,
            "energy_curve": "plateau"
        },
        "harmonic_intelligence": {
            "function_map": function_map,
            "voice_leading": "minimal_motion",
            "modal_borrowing": [],
            "tension_resolution": []
        },
        "teaching_notes": {
            "gesture": f"Follow the glyph: {glyph}",
            "lyric_anchor": f"Place breath words on beats {breath_map[:4]}",
            "performance_note": f"Progression {resolution} - ends on {last_chord}"
        },
        "analysis_metadata": {
            "auto_analyzed": True,
            "analyzer_version": "1.0",
            "note": "This metadata was auto-generated. Refine manually for deeper insight."
        }
    }
    
    return kordtana_data


def enhance_json_file(input_file: str, output_file: str = None):
    """
    Add Kordtana metadata to an existing OneMotion JSON file.
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_file}")
        return
    
    # Load existing JSON
    with open(input_path, 'r') as f:
        json_data = json.load(f)
    
    # Check if already has Kordtana metadata
    if "kordtana" in json_data:
        print("⚠️  File already has Kordtana metadata.")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Cancelled.")
            return
    
    # Analyze and add metadata
    print("🔍 Analyzing progression...")
    kordtana_data = analyze_chord_progression(json_data)
    json_data["kordtana"] = kordtana_data
    
    # Determine output file
    if output_file is None:
        output_file = str(input_path.stem) + "_kordtana.json"
    
    # Save
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"\n✅ Enhanced file saved to: {output_path}")
    print(f"\nGlyph: {kordtana_data['ritual_metadata']['glyph']}")
    print(f"Emotional Arc: {' → '.join(kordtana_data['emotional_arc']['journey'])}")
    print(f"Primary Emotion: {kordtana_data['emotional_arc']['primary']}")
    print(f"\n💡 Tip: Edit the 'kordtana' object in the JSON to refine the analysis.")


def batch_enhance_directory(directory: str, pattern: str = "*.json"):
    """
    Enhance all JSON files in a directory.
    """
    dir_path = Path(directory)
    files = list(dir_path.glob(pattern))
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    print(f"Found {len(files)} files to enhance.")
    proceed = input("Proceed? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print("Cancelled.")
        return
    
    for file_path in files:
        # Skip if already Kordtana file
        if "_kordtana" in file_path.stem:
            continue
        
        print(f"\n📄 Processing: {file_path.name}")
        try:
            enhance_json_file(str(file_path), str(file_path.parent / f"{file_path.stem}_kordtana.json"))
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
    
    print("\n✅ Batch processing complete!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:  python kordtana_analyzer.py <input.json> [output.json]")
        print("  Batch mode:   python kordtana_analyzer.py --batch <directory> [pattern]")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        pattern = sys.argv[3] if len(sys.argv) > 3 else "Bank_*.json"
        batch_enhance_directory(directory, pattern)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        enhance_json_file(input_file, output_file)
