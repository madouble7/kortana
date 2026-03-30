import json

with open(r'c:\kordtana_starter_pack\Mix_Kings_Queens_Enhanced.json') as f:
    data = json.load(f)

print('✨ ENHANCED COMPOSITION ✨')
print('=' * 60)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Musical Identity:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (C# minor)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (moderate)')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Enhanced Structure:')
print(f'   Chord segments: {len(data["sequence"])} (was 8)')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])} (was 16)')
print(f'   Length range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars (was all 2)')

print(f'\n🎸 Enhanced Style:')
print(f'   Chord arpeggio: Original 32-step (kept)')
print(f'   Keep parameter: {data["style"]["chord"]["keep"]} notes sustained')
print(f'   Spread: {data["style"]["chord"]["spread"]} (gentle voicing)')
print(f'   Bass velocity: {data["style"]["bass"]["velocity"]} (was 0.7)')
print(f'   Chord velocity: {data["style"]["chord"]["velocity"]} (was 0.7)')
print(f'   Effect: {data["effectType"]} (was studio)')
print(f'   Effect amount: {data["effectAmount"]} (was 0.77)')
print(f'   Echo delay: {data["effectEcho"]["delay"]}s (was 1.0s)')
print(f'   Echo feedback: {data["effectEcho"]["feedback"]} (was 0.07)')

print(f'\n🎨 Enhanced Chord Progression:')
for i, seg in enumerate(data["sequence"], 1):
    root_note = ['C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#'][seg["rootPos"]]
    bars_text = f'{seg["length"]} bar' if seg["length"] == 1 else f'{seg["length"]} bars'
    print(f'   {i:2}. {root_note:2} {seg["chord"]:5} ({bars_text})')

print(f'\n💫 Harmonic Variety:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'   • {chord}: {count}x')

print(f'\n🌟 Key Enhancements:')
print('   ✅ Extended harmonies: 7th, 9th chords for richness')
print('   ✅ Suspended chords: sus2, sus4 for tension/release')
print('   ✅ Varied bar lengths: 1-4 bars for dynamic flow')
print('   ✅ Keep parameter: Sustained notes for lush texture')
print('   ✅ Cathedral reverb: Deeper atmospheric space')
print('   ✅ Enhanced echo: Longer delay, more feedback')
print('   ✅ Velocity boost: Slightly more presence (0.75)')
print('   ✅ Strategic spreads: Gentle voicing separation')

print(f'\n💎 Character: Dramatic, cinematic, emotionally powerful')
print('   Perfect for: Epic moments, emotional scenes, powerful storytelling')
print('=' * 60)
