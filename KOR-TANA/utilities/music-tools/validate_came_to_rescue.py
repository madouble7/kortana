import json

with open(r'c:\kordtana_starter_pack\Came_To_My_Rescue_OneMotion.json') as f:
    data = json.load(f)

print('🙏 WORSHIP ARRANGEMENT ✨')
print('=' * 60)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Musical Identity:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (G Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm (worshipful, flowing)')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Structure:')
print(f'   Chord segments: {len(data["sequence"])}')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'   Length range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars')

print(f'\n🎸 Style Features:')
print(f'   Chord arpeggio: {data["style"]["chord"]["arp"]} (flowing cascade)')
print(f'   Bass pattern: {data["style"]["bass"]["arp"]} (gentle pulse)')
print(f'   Keep parameter: {data["style"]["chord"]["keep"]} notes sustained')
print(f'   Spread: {data["style"]["chord"]["spread"]} (open voicing)')
print(f'   Velocity: {data["style"]["chord"]["velocity"]} (warm)')
print(f'   Effect: {data["effectType"]} + echo')
print(f'   Inversions: {data["style"]["chord"]["inversions"]} (smooth voice-leading)')

print(f'\n🎨 Harmonic Palette:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'   • {chord}: {count}x')

print(f'\n📖 Chord Map (G Major scale):')
scale_notes = ['G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#']
print('\n   Section breakdown:')
current_bar = 0
for i, seg in enumerate(data["sequence"], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_name = f'{root_note} {seg["chord"]}'
    bars = seg["length"]
    current_bar += bars
    
    if i <= 4:
        section = 'INTRO'
    elif i <= 12:
        section = 'VERSE 1'
    elif i <= 17:
        section = 'CHORUS 1'
    elif i <= 26:
        section = 'CHORUS 2'
    elif i <= 30:
        section = 'VERSE 2'
    elif i <= 34:
        section = 'BRIDGE'
    else:
        section = 'VAMP/OUTRO'
    
    print(f'   {i:2}. [{section:12}] {chord_name:15} ({bars} bar{"s" if bars > 1 else " "}) → bar {current_bar}')

print(f'\n💫 Universal Settings (tailored):')
print('   ✅ Vel: 72 (warm, not harsh)')
print('   ✅ Dur: 90% (smooth sustain)')
print('   ✅ Step: 1/8 × 8 (gentle rhythmic motion)')
print('   ✅ Reset: 8 beats (balanced flow)')
print('   ✅ Inversions: Auto (smooth transitions)')
print('   ✅ Spread: Medium (3-4 octaves, atmospheric)')
print('   ✅ Cathedral reverb + gentle echo')

print(f'\n🌟 Character: Worshipful, intimate, building')
print('   Perfect for: Corporate worship, reflection, Scripture meditation')
print('   Scripture: "The Lord is my light and salvation—whom shall I fear?"')
print('=' * 60)
