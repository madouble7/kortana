#!/usr/bin/env python3
"""
Kordtana.card to OneMotion Chord Player JSON Converter

Usage:
    python kordtana_to_onemotion_converter.py input.card.json output.json
"""

import json
import sys
from pathlib import Path


def convert_kordtana_to_onemotion(kordtana_data):
    """Convert Kordtana.card format to OneMotion Chord Player JSON format"""

    # Extract identity fields to root level
    identity = kordtana_data.get("identity", {})

    # Base OneMotion structure
    onemotion = {
        "name": identity.get("name", "untitled"),
        "instrument": identity.get("instrument", "piano"),
        "scale": identity.get("scale", "aeolian"),
        "scaleKey": identity.get("scaleKey", "C"),
        "application": "OneMotion Chord-Player",
    }

    # Convert layout to chordLayout with hyphens
    layout = kordtana_data.get("layout", {})
    onemotion["chordLayout"] = {
        "diatonic-triad": layout.get("diatonicTriad", True),
        "diatonic-7": layout.get("diatonic7", False),
        "diatonic-sus2": layout.get("diatonicSus2", False),
        "diatonic-sus4": layout.get("diatonicSus4", False),
    }

    # Copy sequence directly (format is compatible)
    onemotion["sequence"] = kordtana_data.get("sequence", [])

    # Convert style - move tempo/timeSignature inside
    kord_style = kordtana_data.get("style", {})
    onemotion["style"] = {
        "bass": convert_bass_style(kord_style.get("bass", {})),
        "chord": convert_chord_style(kord_style.get("chord", {})),
        "tempo": identity.get("tempo", 64),
        "timeSignature": identity.get("timeSignature", "4/4"),
        "shuffle": kord_style.get("shuffle", "1:1"),
        "sustain": kord_style.get("sustain", "chord"),
    }

    # Convert effects to flat structure
    effects = kordtana_data.get("effects", {})
    onemotion["effectType"] = effects.get("type", "chamber")
    echo = effects.get("echo", {})
    onemotion["effectEcho"] = {
        "active": echo.get("active", False),
        "delay": echo.get("delay", 1),
        "feedback": echo.get("feedback", 0.07),
        "amount": echo.get("amount", 0.5),
    }
    onemotion["effectAmount"] = echo.get("amount", 0.5)

    # Convert behaviors to flat structure
    behaviors = kordtana_data.get("behaviors", {})
    onemotion["loopSequence"] = behaviors.get("loopSequence", True)
    onemotion["manualChordPositions"] = behaviors.get("manualChordPositions", False)
    # Note the intentional misspelling
    onemotion["parallellScaleChords"] = behaviors.get("parallelScaleChords", True)

    # Add required OneMotion fields
    onemotion["melody"] = {"events": []}
    onemotion["customChords"] = []
    onemotion["description"] = ""
    onemotion["public"] = False
    onemotion["free"] = True

    return onemotion


def convert_bass_style(bass_style):
    """Convert Kordtana bass style to OneMotion format"""
    return {
        "arp": bass_style.get("arp", "xs"),
        "loop": bass_style.get("loop", False),
        "step": bass_style.get("step", [1, 1]),
        "style": bass_style.get("style", "once"),
        "double": bass_style.get("double", False),
        "mirror": bass_style.get("mirror", False),
        "octave": bass_style.get("octave", 3),
        "velocity": bass_style.get("velocity", 0.7),
        "arpEvents": {
            "0": {
                "items": [{"n": 0, "keep": False, "sustain": True, "remaining": True}]
            }
        },
        "arpLength": bass_style.get("arpLength", 1),
        "cropLength": bass_style.get("cropLength", 0),
        "noteDuration": bass_style.get("noteDuration", 1),
        "octaveOffset": bass_style.get("octaveOffset", -3),
    }


def convert_chord_style(chord_style):
    """Convert Kordtana chord style to OneMotion format"""
    return {
        "arp": chord_style.get("arp", "off"),
        "keep": chord_style.get("keep", False),
        "loop": chord_style.get("loop", True),
        "open": chord_style.get("open", False),
        "step": chord_style.get("step", [1, 4]),
        "style": chord_style.get("style", "block"),
        "double": chord_style.get("double", False),
        "mirror": chord_style.get("mirror", False),
        "octave": chord_style.get("octave", 4),
        "spread": chord_style.get("spread", 0),
        "numNotes": chord_style.get("numNotes", 0),
        "velocity": chord_style.get("velocity", 0.7),
        "arpEvents": chord_style.get("arpEvents", {}),
        "arpLength": chord_style.get("arpLength", 1),
        "cropLength": chord_style.get("cropLength", 0),
        "inversions": chord_style.get("inversions", False),
        "noteDuration": chord_style.get("noteDuration", 1),
        "octaveOffset": chord_style.get("octaveOffset", 0),
    }


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python kordtana_to_onemotion_converter.py input.card.json output.json"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found")
        sys.exit(1)

    try:
        # Load Kordtana card
        with open(input_path, "r", encoding="utf-8") as f:
            kordtana_data = json.load(f)

        # Convert to OneMotion format
        onemotion_data = convert_kordtana_to_onemotion(kordtana_data)

        # Write OneMotion JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(onemotion_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Converted {input_path} → {output_path}")
        print(f"   Name: {onemotion_data['name']}")
        print(f"   Scale: {onemotion_data['scaleKey']} {onemotion_data['scale']}")
        print(f"   Sequence: {len(onemotion_data['sequence'])} chords")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
