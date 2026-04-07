import json

with open(r'c:\Users\madou\Downloads\Mix Kings and Queens vs No Time to Die.json') as f:
    data = json.load(f)

print('🔍 ORIGINAL COMPOSITION ANALYSIS')
print('=' * 50)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Current Setup:')
print(f'   Key: {data["scaleKey"]} {data["scale"]}')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Structure:')
print(f'   Chord segments: {len(data["sequence"])}')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'   All segments: {data["sequence"][0]["length"]} bars each')

print(f'\n🎸 Style Elements:')
print(f'   Chord arpeggio: Custom 32-step pattern')
print(f'   Bass pattern: {data["style"]["bass"]["arp"]} style')
print(f'   Effect: {data["effectType"]} + echo')
print(f'   Velocity: {data["style"]["chord"]["velocity"]}')

print(f'\n🎨 Current Chord Progression:')
for i, seg in enumerate(data["sequence"], 1):
    root_note = ['C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#'][seg["rootPos"]]
    print(f'   {i}. {root_note} {seg["chord"]} ({seg["length"]} bars)')

print(f'\n💡 Enhancement Opportunities:')
print('   • Add chord extensions (7th, 9th)')
print('   • Vary chord lengths for dynamics')
print('   • Add sus2/sus4 for tension')
print('   • Enhance arpeggio with keep parameter')
print('   • Adjust velocity for expression')
print('=' * 50)
