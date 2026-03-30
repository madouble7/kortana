#!/usr/bin/env python3
"""
Kordtana Composer - Ritual-Based Chord Progression Generator

Creates OneMotion Chord Player JSONs with emotional intelligence,
harmonic analysis, and ritual architecture.

Usage:
    python kordtana_composer.py
    
Then follow the interactive prompts to compose with intention.
"""

import json
import sys
from typing import Dict, List, Tuple

# Emotional taxonomy
EMOTIONS = {
    "clarity": {"chords": ["maj", "maj7"], "function": "tonic", "glyph": "⟡"},
    "yearning": {"chords": ["min9", "min11", "sus4"], "function": "borrowed", "glyph": "◈"},
    "movement": {"chords": ["min7", "dom7"], "function": "supertonic/dominant", "glyph": "⟠"},
    "suspension": {"chords": ["sus2", "sus4"], "function": "subdominant", "glyph": "⧖"},
    "tension": {"chords": ["dom7", "dom9", "dim"], "function": "dominant", "glyph": "↯"},
    "transcendence": {"chords": ["maj9", "maj7#11"], "function": "lydian", "glyph": "∞"},
    "mystery": {"chords": ["dim", "min7b5"], "function": "altered", "glyph": "⌘"},
    "release": {"chords": ["maj", "maj6"], "function": "resolution", "glyph": "⊙"}
}

# Chord to scale degree mapping (F major example)
SCALE_DEGREES_F = {
    "F": 0, "G": 2, "A": 4, "Bb": 3, "C": 5, "D": 7, "E": 9,
    "Eb": 8, "Ab": 1, "Db": 6  # borrowed chords
}

# Extended chord voicing patterns
VOICING_PATTERNS = {
    "maj": {"notes": [0, 4, 7], "name": "Major Triad"},
    "min": {"notes": [0, 3, 7], "name": "Minor Triad"},
    "maj7": {"notes": [0, 4, 7, 11], "name": "Major 7th"},
    "min7": {"notes": [0, 3, 7, 10], "name": "Minor 7th"},
    "dom7": {"notes": [0, 4, 7, 10], "name": "Dominant 7th"},
    "maj9": {"notes": [0, 4, 7, 11, 14], "name": "Major 9th"},
    "min9": {"notes": [0, 3, 7, 10, 14], "name": "Minor 9th"},
    "dom9": {"notes": [0, 4, 7, 10, 14], "name": "Dominant 9th"},
    "min11": {"notes": [0, 3, 7, 10, 14, 17], "name": "Minor 11th"},
    "dom13": {"notes": [0, 4, 7, 10, 14, 21], "name": "Dominant 13th"},
    "sus2": {"notes": [0, 2, 7], "name": "Suspended 2nd"},
    "sus4": {"notes": [0, 5, 7], "name": "Suspended 4th"},
    "add9": {"notes": [0, 4, 7, 14], "name": "Add 9"},
    "6": {"notes": [0, 4, 7, 9], "name": "Major 6th"},
    "69": {"notes": [0, 4, 7, 9, 14], "name": "6/9 chord"}
}

def create_kordtana_progression(
    key: str = "F",
    scale: str = "ionian",
    emotional_arc: List[str] = None,
    tempo: int = 66,
    time_signature: str = "3/4",
    beats_per_chord: int = 6,
    intention: str = ""
) -> Dict:
    """
    Create a Kordtana progression with emotional intelligence.
    
    Args:
        key: Root key (e.g., "F", "C", "Ab")
        scale: Mode (ionian, aeolian, dorian, etc.)
        emotional_arc: List of emotions from EMOTIONS dict
        tempo: BPM (default 66 for patient feel)
        time_signature: "3/4" or "4/4" etc.
        beats_per_chord: Usually 6 for 2 bars at 3/4
        intention: Ritual intention text
    """
    if emotional_arc is None:
        emotional_arc = ["clarity", "yearning", "movement", "suspension"]
    
    # Build progression
    progression = {
        "name": f"Kordtana - {intention if intention else 'Untitled'}",
        "instrument": "piano",
        "scale": scale,
        "scaleKey": key,
        "chordLayout": {
            "diatonic-triad": True,
            "diatonic-7": True,
            "diatonic-9": True,
            "sus2": True,
            "sus4": True
        },
        "sequence": [],
        "application": "OneMotion Chord-Player",
        "style": {
            "bass": {
                "style": "arpeggio",
                "velocity": 0.77,
                "octave": 2,
                "arp": "once",
                "loop": True,
                "arpEvents": {
                    "0": {"items": [{"n": 0, "keep": False}], "envelopes": {}}
                },
                "arpLength": 1,
                "octaveOffset": 0,
                "noteDuration": 1.2,
                "step": [1, 8]
            },
            "chord": {
                "style": "arpeggio",
                "velocity": 0.77,
                "spread": 0,
                "octave": 4,
                "arp": "1 3 5 7",
                "loop": True,
                "arpEvents": {
                    "0": {"items": [{"n": 0, "keep": False}], "envelopes": {}},
                    "1": {"items": [{"n": 2, "keep": False}], "envelopes": {}},
                    "2": {"items": [{"n": 4, "keep": False}], "envelopes": {}},
                    "3": {"items": [{"n": 6, "keep": False}], "envelopes": {}}
                },
                "arpLength": 4,
                "octaveOffset": 0,
                "inversions": True,
                "open": False,
                "keep": False,
                "noteDuration": 1,
                "step": [1, 8]
            },
            "shuffle": "1:1",
            "sustain": "chord",
            "tempo": tempo,
            "timeSignature": time_signature
        },
        "effectType": "chamber",
        "effectEcho": {
            "active": True,
            "delay": 0.5,
            "feedback": 0.17,
            "amount": 0.77
        },
        "effectAmount": 0.77,
        "loopSequence": True,
        "manualChordPositions": False,
        "melody": {"events": []},
        "customChords": [],
        "parallellScaleChords": False,
        "description": f"Kordtana ritual composition. {key} {scale}. Emotional arc: {' → '.join(emotional_arc)}."
    }
    
    # Build sequence and metadata
    function_map = {}
    glyph = ""
    breath_map = []
    
    for i, emotion in enumerate(emotional_arc):
        beat_position = i * beats_per_chord
        breath_map.append(beat_position)
        
        emotion_data = EMOTIONS.get(emotion, EMOTIONS["clarity"])
        chord_type = emotion_data["chords"][0]  # Pick first chord option
        
        # Map to scale degree (simplified - would need proper implementation)
        root_pos = i * 3  # Placeholder - needs proper voice leading logic
        
        progression["sequence"].append({
            "chord": chord_type,
            "length": beats_per_chord,
            "rootPos": root_pos
        })
        
        function_map[str(beat_position)] = {
            "chord": f"{key}{chord_type}",
            "function": emotion_data["function"],
            "emotion": emotion
        }
        
        glyph += emotion_data["glyph"]
    
    # Add Kordtana metadata
    progression["kordtana"] = {
        "emotional_arc": {
            "primary": emotional_arc[0] if emotional_arc else "clarity",
            "journey": emotional_arc,
            "resolution": "incomplete" if emotional_arc[-1] in ["suspension", "mystery"] else "resolved"
        },
        "ritual_metadata": {
            "glyph": glyph,
            "breath_map": breath_map,
            "intention": intention,
            "tempo_feel": "patient" if tempo < 70 else "breathing" if tempo < 85 else "driving",
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
            "lyric_anchor": f"Place breath words on beats {breath_map}",
            "performance_note": "Let final chord breathe before loop return"
        }
    }
    
    return progression


def interactive_composer():
    """Interactive composition session."""
    print("=" * 60)
    print("KORDTANA COMPOSER")
    print("Ritual-Based Chord Progression Generator")
    print("=" * 60)
    print()
    
    # Get key
    key = input("Key (e.g., F, C, Ab) [F]: ").strip() or "F"
    
    # Get scale/mode
    print("\nModes: ionian (major), aeolian (minor), dorian, lydian, mixolydian")
    scale = input("Scale/Mode [ionian]: ").strip() or "ionian"
    
    # Get emotional arc
    print("\nAvailable emotions:")
    for emotion in EMOTIONS.keys():
        print(f"  - {emotion}")
    print()
    
    arc_input = input("Emotional arc (comma-separated) [clarity,yearning,movement,suspension]: ").strip()
    if arc_input:
        emotional_arc = [e.strip() for e in arc_input.split(",")]
    else:
        emotional_arc = ["clarity", "yearning", "movement", "suspension"]
    
    # Get tempo
    tempo_input = input("\nTempo (BPM) [66]: ").strip()
    tempo = int(tempo_input) if tempo_input else 66
    
    # Get intention
    intention = input("\nRitual intention (e.g., 'threshold crossing'): ").strip() or "Untitled"
    
    # Generate
    print("\n🎹 Generating Kordtana progression...")
    progression = create_kordtana_progression(
        key=key,
        scale=scale,
        emotional_arc=emotional_arc,
        tempo=tempo,
        intention=intention
    )
    
    # Display
    print("\n" + "=" * 60)
    print(f"Glyph: {progression['kordtana']['ritual_metadata']['glyph']}")
    print(f"Emotional Arc: {' → '.join(emotional_arc)}")
    print(f"Breath Map: {progression['kordtana']['ritual_metadata']['breath_map']}")
    print("=" * 60)
    
    # Save
    filename = f"Kordtana_{intention.replace(' ', '_')}_{key}_{scale}.json"
    with open(filename, 'w') as f:
        json.dump(progression, f, indent=2)
    
    print(f"\n✅ Saved to: {filename}")
    print("\nOpen in OneMotion Chord Player to experience the ritual.")


if __name__ == "__main__":
    interactive_composer()
