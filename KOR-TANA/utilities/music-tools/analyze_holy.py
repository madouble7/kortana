import json

with open(r'c:\Users\madou\Downloads\holyChords E-B_D#-C#m7-A 77bpm.json') as f:
    data = json.load(f)

print('🔍 ANALYZING HOLY CHORD PROGRESSION')
print('=' * 60)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (E Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Core Progression:')
scale_notes = ['E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#']
for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_type = seg["chord"]
    bars = seg["length"]
    
    if "bassPos" in seg:
        bass_note = scale_notes[seg["bassPos"]]
        chord_name = f'{root_note} {chord_type} / {bass_note} bass'
    else:
        chord_name = f'{root_note} {chord_type}'
    
    print(f'   {i}. {chord_name} ({bars} bars)')

print(f'\n🎸 Style Features:')
print(f'   Bass arp: Complex 32-step pattern')
print(f'   Chord arp: Syncopated 16-step pattern')
print(f'   Effect: {data["effectType"]}')
print(f'   Parallel scale chords: {data["parallellScaleChords"]}')

print(f'\n💡 This is a clean, uplifting E major progression!')
print('   Perfect foundation for a beautiful instrumental!')
print('=' * 60)
