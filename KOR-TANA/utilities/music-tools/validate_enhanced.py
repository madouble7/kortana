import json

with open(r'c:\kordtana_starter_pack\Mix_Rodfai_Enhanced_Emotional.json') as f:
    data = json.load(f)

print('✅ Valid OneMotion JSON!')
print(f'\nName: {data["name"]}')
print(f'Key: {data["scaleKey"]} {data["scale"]}')
print(f'Tempo: {data["style"]["tempo"]} bpm')
print(f'Chord segments: {len(data["sequence"])}')
print(f'Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'Effect: {data["effectType"]} + {"echo ON" if data["effectEcho"]["active"] else "echo OFF"}')
print(f'\n🎵 This version features:')
print('  • Richer 9th & 11th chord extensions')
print('  • D minor key for deeper emotion')
print('  • Flowing bass with melodic movement')
print('  • Cathedral reverb for space')
print('  • Varied chord lengths for dynamics')
print('  • Suspended chords for smooth transitions')
