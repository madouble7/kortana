import json

print('🎼 THREE VARIATIONS FROM "BILLS ON BILLS" 🎼')
print('=' * 70)

files = [
    ('c:\\kordtana_starter_pack\\Bills_Variation_1_Extended.json', '1️⃣ EXTENDED HARMONIES'),
    ('c:\\kordtana_starter_pack\\Bills_Variation_2_Suspended.json', '2️⃣ SUSPENDED TENSION'),
    ('c:\\kordtana_starter_pack\\Bills_Variation_3_Ambient.json', '3️⃣ AMBIENT FLOW')
]

for filepath, title in files:
    with open(filepath) as f:
        data = json.load(f)
    
    print(f'\n{title}')
    print('-' * 70)
    print(f'🎹 {data["name"]}')
    print(f'   Instrument: {data["instrument"]}')
    print(f'   Tempo: {data["style"]["tempo"]} bpm')
    print(f'   Segments: {len(data["sequence"])}')
    print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')
    print(f'   Bar range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars')
    
    print(f'\n   Style:')
    print(f'   • Chord arp: {data["style"]["chord"]["arp"]}')
    print(f'   • Bass arp: {data["style"]["bass"]["arp"]}')
    print(f'   • Keep: {data["style"]["chord"]["keep"]}')
    print(f'   • Spread: {data["style"]["chord"]["spread"]}')
    print(f'   • Effect: {data["effectType"]}')
    print(f'   • Echo delay: {data["effectEcho"]["delay"]}s')
    
    chord_types = {}
    for seg in data["sequence"]:
        chord_type = seg["chord"]
        chord_types[chord_type] = chord_types.get(chord_type, 0) + 1
    
    print(f'\n   Chord palette:')
    for chord, count in sorted(chord_types.items()):
        print(f'   • {chord}: {count}x')
    
    print(f'\n   💡 {data["description"]}')

print('\n' + '=' * 70)
print('✅ All three variations keep the Ab Major core but explore different')
print('   harmonic colors, rhythms, and sonic textures!')
print('=' * 70)
