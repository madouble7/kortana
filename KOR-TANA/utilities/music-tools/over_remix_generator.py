#!/usr/bin/env python3
"""
OneMotion "Over" Remix Generator

Usage:
    python over_remix_generator.py [style] [key] [tempo]
    
Styles: trap, house, drill, rnb, ambient
Keys: C, D, E, F, G, A, B (add # or b as needed)  
Tempo: 60-180 BPM

Example:
    python over_remix_generator.py trap E 65
"""

import json
import sys
from pathlib import Path

# Base template from original "over"  
BASE_TEMPLATE = {
    "name": "over_remix",
    "instrument": "piano",
    "scale": "aeolian", 
    "scaleKey": "C",
    "chordLayout": {
        "diatonic-sus2": True,
        "diatonic-triad": True,
        "diatonic-sus4": True,
        "diatonic-7": True
    },
    "sequence": [
        {"chord": "maj", "length": 4, "rootPos": 8},
        {"chord": "min", "length": 2, "rootPos": 7},
        {"chord": "min", "length": 2, "rootPos": 0},
        {"chord": "min", "length": 4, "rootPos": 5},
        {"chord": "min", "length": 2, "rootPos": 7},
        {"chord": "min", "length": 2, "rootPos": 0}
    ],
    "application": "OneMotion Chord-Player",
    "effectType": "chamber",
    "effectAmount": 0.5,
    "loopSequence": True,
    "manualChordPositions": False,
    "melody": {"events": []},
    "customChords": [],
    "parallellScaleChords": False,
    "description": ""
}

STYLE_PRESETS = {
    "trap": {
        "tempo": 65,
        "bass": {
            "arp": "xs", "loop": False, "step": [1, 2], "style": "once",
            "octave": 2, "velocity": 0.85, "noteDuration": 2,
            "arpEvents": {"0": {"items": [{"n": 0, "keep": False, "sustain": True, "remaining": True}]}}
        },
        "chord": {
            "arp": "off", "style": "block", "step": [1, 8], "velocity": 0.75,
            "octave": 4, "inversions": False, "arpEvents": {}
        },
        "effectEcho": {"active": False, "delay": 1, "feedback": 0.5, "amount": 0.5}
    },
    "house": {
        "tempo": 124,
        "bass": {
            "arp": "xs", "loop": True, "step": [1, 4], "style": "arpeggio",
            "octave": 2, "velocity": 0.8, "noteDuration": 0.9,
            "arpEvents": {
                "0": {"items": [{"n": 0, "keep": False, "sustain": False}]},
                "1": {"items": [{"n": 0, "keep": False, "fifth": True}]}
            }
        },
        "chord": {
            "arp": ". x", "style": "offbeat", "step": [1, 4], "velocity": 0.7,
            "octave": 4, "inversions": True, "octaveOffset": 1,
            "arpEvents": {"1": {"items": [{"n": 0, "keep": False}, {"n": 1, "keep": False}]}}
        },
        "effectEcho": {"active": True, "delay": 0.25, "feedback": 0.15, "amount": 0.35}
    },
    "drill": {
        "tempo": 95,
        "bass": {
            "arp": "xs", "loop": True, "step": [1, 8], "style": "arpeggio", 
            "octave": 1, "velocity": 0.9, "noteDuration": 0.5,
            "arpEvents": {"0": {"items": [{"n": 0, "keep": False, "sustain": False}]}}
        },
        "chord": {
            "arp": "off", "style": "stab", "step": [1, 16], "velocity": 0.8,
            "octave": 4, "inversions": False, "arpEvents": {}
        },
        "effectEcho": {"active": False, "delay": 0.5, "feedback": 0.3, "amount": 0.2}
    },
    "rnb": {
        "tempo": 78,
        "bass": {
            "arp": "xs", "loop": False, "step": [1, 1], "style": "once",
            "octave": 3, "velocity": 0.7, "noteDuration": 1,
            "arpEvents": {"0": {"items": [{"n": 0, "keep": False, "sustain": True, "remaining": True}]}}
        },
        "chord": {
            "arp": "23 1", "style": "split-23-1", "step": [1, 6], "velocity": 0.7,
            "octave": 4, "inversions": True, "arpLength": 2,
            "arpEvents": {"0": {"items": [{"n": 1, "keep": False}, {"n": 2, "keep": False}]}}
        },
        "effectEcho": {"active": True, "delay": 0.75, "feedback": 0.1, "amount": 0.4}
    },
    "ambient": {
        "tempo": 55,
        "bass": {
            "arp": "xs", "loop": False, "step": [1, 1], "style": "once",
            "octave": 3, "velocity": 0.6, "noteDuration": 4,
            "arpEvents": {"0": {"items": [{"n": 0, "keep": False, "sustain": True, "remaining": True}]}}
        },
        "chord": {
            "arp": "off", "style": "block", "step": [1, 16], "velocity": 0.65,
            "octave": 4, "inversions": False, "arpEvents": {}
        },
        "effectEcho": {"active": True, "delay": 1.5, "feedback": 0.3, "amount": 0.7}
    }
}

def generate_remix(style="trap", key="C", tempo=None):
    """Generate a remix with specified style, key, and tempo"""
    
    if style not in STYLE_PRESETS:
        print(f"❌ Unknown style '{style}'. Available: {list(STYLE_PRESETS.keys())}")
        return None
        
    preset = STYLE_PRESETS[style]
    remix = BASE_TEMPLATE.copy()
    
    # Set name and key
    remix["name"] = f"over_{style}_remix"
    remix["scaleKey"] = key
    
    # Override tempo if provided
    if tempo:
        preset = preset.copy()
        preset["tempo"] = int(tempo)
    
    # Build style object
    style_obj = {
        "bass": {
            "arp": "xs", "loop": False, "step": [1, 1], "style": "once",
            "double": False, "mirror": False, "octave": 3, "velocity": 0.7,
            "arpLength": 1, "cropLength": 0, "noteDuration": 1, "octaveOffset": -3
        },
        "chord": {
            "arp": "off", "keep": False, "loop": True, "open": False,
            "style": "block", "double": False, "mirror": False, "octave": 4,
            "spread": 0, "numNotes": 0, "velocity": 0.7, "arpLength": 1,
            "cropLength": 0, "inversions": False, "noteDuration": 1, "octaveOffset": 0
        },
        "tempo": preset["tempo"],
        "shuffle": "1:1", "sustain": "chord", "timeSignature": "4/4"
    }
    
    # Apply preset overrides
    style_obj["bass"].update(preset["bass"])
    style_obj["chord"].update(preset["chord"])
    
    remix["style"] = style_obj
    remix["effectEcho"] = preset["effectEcho"]
    remix["description"] = f"{style.title()} remix of Over - {key} {remix['scale']} @ {preset['tempo']} BPM"
    
    return remix

def main():
    style = sys.argv[1] if len(sys.argv) > 1 else "trap"
    key = sys.argv[2] if len(sys.argv) > 2 else "C" 
    tempo = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"🎵 Generating {style} remix in {key}...")
    
    remix = generate_remix(style, key, tempo)
    if not remix:
        return
        
    output_file = f"over_{style}_remix_{key.replace('#', 'sharp').replace('b', 'flat')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(remix, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {output_file}")
    print(f"   Style: {style}")
    print(f"   Key: {key} {remix['scale']}")  
    print(f"   Tempo: {remix['style']['tempo']} BPM")
    print(f"   Ready to load in OneMotion Chord Player!")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(__doc__)
    else:
        main()