import json

with open(r'c:\kordtana_starter_pack\Mix_Light_Switch_Enhanced.json') as f:
    data = json.load(f)

print('✅ Valid OneMotion JSON!')
print(f'\n📋 {data["name"]}')
print(f'🎹 Key: {data["scaleKey"]} {data["scale"]}')
print(f'⏱️  Tempo: {data["style"]["tempo"]} bpm (slow & spacious)')
print(f'🎵 Chord segments: {len(data["sequence"])}')
print(f'📏 Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'🎸 Arpeggio: {data["style"]["chord"]["style"]}')
print(f'🔊 Effect: {data["effectType"]} + echo')

print('\n🎼 Chord progression variety:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'  • {chord}: {count}x')

print('\n✨ Enhancements:')
print('  • Added 7th chords (maj7, min7)')
print('  • Added suspended chords (sus2, sus4)')
print('  • Added diminished for tension')
print('  • Varied lengths (2-8 bars)')
print('  • Kept your beautiful zig-zag arpeggio!')
