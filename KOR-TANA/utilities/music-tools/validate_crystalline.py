import json

with open(r'c:\kordtana_starter_pack\Crystalline_Dreams_Original.json') as f:
    data = json.load(f)

print('✨ NEW ORIGINAL COMPOSITION ✨')
print('=' * 50)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Musical Identity:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} mode')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (meditative)')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Structure:')
print(f'   Chord segments: {len(data["sequence"])}')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'   Length range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars')

print(f'\n🎸 Unique Features:')
print(f'   Chord arpeggio: Custom floating cascade (16-step)')
print(f'   Bass pattern: 1-5-3-5 gentle pulse')
print(f'   Effect: {data["effectType"]} + echo')
print(f'   Spread: {data["style"]["chord"]["spread"]} (shimmering)')
print(f'   Keep: {data["style"]["chord"]["keep"]} notes sustained')

print(f'\n🎨 Harmonic Palette:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'   • {chord}: {count}x')

print(f'\n💫 Character:')
print('   Lydian mode = bright, dreamy (#4 scale degree)')
print('   Electric piano = crystalline, bell-like')
print('   High octave (5) + open voicings = floating')
print('   Cathedral reverb = vast space')
print('   Gentle shuffle = human, organic feel')

print('\n🌟 Concept: Ethereal, contemplative, peaceful')
print('   Perfect for meditation, creative work, relaxation')
print('=' * 50)
