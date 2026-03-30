import json

with open(r'c:\kordtana_starter_pack\Holy_Simple_4Bar.json') as f:
    data = json.load(f)

print('✨ SIMPLE 4-BAR LOOP ✨')
print('=' * 50)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (E Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')

print(f'\n🎵 Progression (16 bars total):')
scale_notes = ['E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#']

for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    
    if "bassPos" in seg:
        bass_note = scale_notes[seg["bassPos"]]
        chord_name = f'{root_note} {seg["chord"]} / {bass_note} bass'
    else:
        chord_name = f'{root_note} {seg["chord"]}'
    
    print(f'   {i}. {chord_name} - {seg["length"]} bars')

print(f'\n🎸 Style:')
print(f'   Chord arp: {data["style"]["chord"]["arp"]} (simple up-down)')
print(f'   Bass: {data["style"]["bass"]["style"]} (root note only)')
print(f'   Effect: {data["effectType"]}')
print(f'   Keep: {data["style"]["chord"]["keep"]} (no sustain)')
print(f'   Spread: {data["style"]["chord"]["spread"]} (tight voicing)')

print(f'\n✅ Clean, simple, 16-bar loop that just repeats!')
print('=' * 50)
