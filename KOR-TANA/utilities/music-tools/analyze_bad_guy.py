import json

with open(r'c:\Users\madou\Downloads\Chords Gm-Cm-D7 130bpm.json') as f:
    data = json.load(f)

print('🔍 ANALYZING "BAD GUY" PROGRESSION')
print('=' * 60)
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (G Minor)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (faster!)')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Simple 3-Chord Progression:')
scale_notes = ['G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#']

for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_type = seg["chord"]
    bars = seg["length"]
    print(f'   {i}. {root_note} {chord_type} - {bars} bars')

print(f'\n🎸 Style:')
print(f'   Bass: Complex syncopated pattern (64-step!)')
print(f'   Chord: Rhythmic 16-step pattern')
print(f'   Effect: {data["effectType"]}')
print(f'   Total loop: {sum(seg["length"] for seg in data["sequence"])} bars')

print(f'\n💡 "Bad Guy" vibes:')
print('   • Minimal 3-chord loop (Gm - Cm - D7)')
print('   • Dark, minor key')
print('   • Faster tempo (130 bpm)')
print('   • Groovy, rhythmic bass')
print('   • Perfect for edgy, confident songs')

print(f'\n✅ Let\'s create a simple clean version!')
print('=' * 60)
