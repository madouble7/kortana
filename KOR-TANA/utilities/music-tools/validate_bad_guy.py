import json

with open(r'c:\kordtana_starter_pack\Bad_Guy_Simple_Dark.json') as f:
    data = json.load(f)

print('😈 BAD GUY - SIMPLE DARK LOOP 😈')
print('=' * 50)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (G Minor - dark!)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (groovy)')

print(f'\n🎵 Minimal Progression (16 bars total):')
scale_notes = ['G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#']

for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_type = seg["chord"]
    bars = seg["length"]
    
    if chord_type == "min":
        chord_name = f'{root_note}m'
    else:
        chord_name = f'{root_note}{chord_type}'
    
    print(f'   {i}. {chord_name} - {bars} bars')

print(f'\n🎸 Style:')
print(f'   Bass arp: {data["style"]["bass"]["arp"]} (groovy bounce)')
print(f'   Chord arp: {data["style"]["chord"]["arp"]} (rhythmic stabs)')
print(f'   Effect: {data["effectType"]}')
print(f'   Note duration: {data["style"]["bass"]["noteDuration"]} (short & punchy)')

print(f'\n💡 Character:')
print('   • Dark, minimal, edgy')
print('   • 3-chord simplicity')
print('   • Rhythmic, groovy bass')
print('   • Short, staccato chords')
print('   • Perfect for confident, attitude songs')

print(f'\n✅ Clean, simple loop - just the vibe!')
print('=' * 50)
