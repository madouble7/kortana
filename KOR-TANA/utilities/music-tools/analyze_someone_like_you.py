import json

with open(r'c:\Users\madou\Downloads\Chords A-C#m-F#m-D 68bpm.json') as f:
    data = json.load(f)

print('🔍 ANALYZING ADELE "SOMEONE LIKE YOU" PROGRESSION')
print('=' * 60)
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (A Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (ballad tempo)')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Simple 4-Chord Progression:')
scale_notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_type = seg["chord"]
    bars = seg["length"]
    print(f'   {i}. {root_note} {chord_type} - {bars} bars')

print(f'\n🎸 Style:')
print(f'   Chord style: {data["style"]["chord"]["style"]}')
print(f'   Bass: {data["style"]["bass"]["style"]} (root only)')
print(f'   Effect: {data["effectType"]}')
print(f'   Total loop: {sum(seg["length"] for seg in data["sequence"])} bars')

print(f'\n💡 Perfect ballad template:')
print('   • Simple 4-chord loop')
print('   • Emotional minor chords mixed with major')
print('   • Slow tempo (68 bpm)')
print('   • Easy to sing over')
print('   • Clean and minimal')

print(f'\n✅ Let\'s create 5 original progressions like this!')
print('=' * 60)
