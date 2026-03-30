#!/usr/bin/env python3
"""
✅ OneMotion JSON Validator
Checks if your OneMotion Chord Player JSON is valid
"""

import json
import sys
from pathlib import Path

def validate_onemotion(filepath):
    """Validate OneMotion JSON structure"""
    print(f"🔍 Validating: {Path(filepath).name}")
    print("-" * 50)
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False
    
    errors = []
    warnings = []
    
    # Required root-level fields
    required_fields = [
        'name', 'instrument', 'scale', 'scaleKey', 'application',
        'chordLayout', 'sequence', 'style', 'effectType', 'effectEcho',
        'loopSequence', 'manualChordPositions', 'parallellScaleChords'
    ]
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    
    # Check application name
    if data.get('application') != 'OneMotion Chord-Player':
        errors.append(f"Application must be 'OneMotion Chord-Player', got: {data.get('application')}")
    
    # Check parallellScaleChords spelling (intentional double-l)
    if 'parallelScaleChords' in data and 'parallellScaleChords' not in data:
        errors.append("Wrong spelling: 'parallelScaleChords' should be 'parallellScaleChords' (double-l)")
    
    # Check chordLayout structure
    if 'chordLayout' in data:
        layout = data['chordLayout']
        if 'diatonicTriad' in layout or 'diatonic7' in layout:
            warnings.append("chordLayout should use hyphens: 'diatonic-triad', 'diatonic-7'")
    
    # Check sequence
    if 'sequence' in data:
        for i, chord in enumerate(data['sequence']):
            if 'chord' not in chord:
                errors.append(f"Sequence[{i}]: missing 'chord' field")
            if 'length' not in chord:
                errors.append(f"Sequence[{i}]: missing 'length' field")
            if 'rootPos' not in chord:
                errors.append(f"Sequence[{i}]: missing 'rootPos' field")
    
    # Check style object
    if 'style' in data:
        style = data['style']
        
        if 'tempo' not in style:
            errors.append("'tempo' must be inside 'style' object")
        if 'timeSignature' not in style:
            errors.append("'timeSignature' must be inside 'style' object")
        
        # Check bass section
        if 'bass' in style:
            bass = style['bass']
            if 'arpEvents' not in bass:
                errors.append("style.bass: missing 'arpEvents' object")
            if 'style' not in bass:
                errors.append("style.bass: missing 'style' field")
        
        # Check chord section
        if 'chord' in style:
            chord = style['chord']
            if 'arpEvents' not in chord:
                warnings.append("style.chord: missing 'arpEvents' object (can be empty {})")
            if 'style' not in chord:
                errors.append("style.chord: missing 'style' field")
    
    # Check effects are at root level
    if 'effectType' not in data:
        errors.append("'effectType' should be at root level, not nested")
    if 'effectEcho' not in data:
        errors.append("'effectEcho' should be at root level, not nested")
    
    # Print results
    print()
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ Perfect! No issues found.")
        print()
    
    # Summary
    print(f"📊 SUMMARY:")
    print(f"  Name: {data.get('name', 'N/A')}")
    print(f"  Key: {data.get('scaleKey', 'N/A')} {data.get('scale', 'N/A')}")
    if 'style' in data and 'tempo' in data['style']:
        print(f"  Tempo: {data['style']['tempo']} BPM")
    if 'sequence' in data:
        print(f"  Chords: {len(data['sequence'])}")
    print()
    
    return len(errors) == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python onemotion_validator.py <json_file>")
        print("\nOr drag and drop a JSON file onto this script!")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    filepath = sys.argv[1]
    is_valid = validate_onemotion(filepath)
    
    if is_valid:
        print("🎊 Ready to use in OneMotion Chord Player!")
    else:
        print("🔧 Please fix the errors above.")
    
    input("\nPress Enter to exit...")
