import json

with open(r'c:\Users\madou\Downloads\Bills on bills on bills (1).json') as f:
    data = json.load(f)

print('🔍 ANALYZING BASE PROGRESSION')
print('=' * 60)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (Ab Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Structure:')
print(f'   Chord segments: {len(data["sequence"])}')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')

print(f'\n🎸 Style:')
print(f'   Chord style: {data["style"]["chord"]["style"]} (split pattern)')
print(f'   Chord arp: {data["style"]["chord"]["arp"]}')
print(f'   Bass style: {data["style"]["bass"]["style"]}')
print(f'   Bass arp: {data["style"]["bass"]["arp"]}')
print(f'   Effect: {data["effectType"]}')
print(f'   Parallel scale chords: {data["parallellScaleChords"]}')

print(f'\n🎨 Chord Progression (simplified):')
scale_notes = ['Ab', 'A', 'Bb', 'B', 'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G']
chord_types = {}
unique_patterns = []
prev_chord = None

for i, seg in enumerate(data["sequence"][:20], 1):  # First 20 to see pattern
    root_note = scale_notes[seg["rootPos"]]
    chord = f'{root_note} {seg["chord"]}'
    
    if chord != prev_chord:
        unique_patterns.append(f'{chord} ({seg["length"]} bars)')
        prev_chord = chord
    
    chord_types[seg["chord"]] = chord_types.get(seg["chord"], 0) + 1

print('\n   Unique patterns (first occurrences):')
for pattern in unique_patterns[:12]:
    print(f'   • {pattern}')

print(f'\n💡 Chord types used:')
for chord_type, count in sorted(chord_types.items()):
    print(f'   • {chord_type}: {count}x')

print(f'\n✅ This is clean and simple - perfect base for variations!')
print('=' * 60)
