import json

with open(r'c:\kordtana_starter_pack\Holy_Beautiful_Instrumental.json') as f:
    data = json.load(f)

print('✨ BEAUTIFUL INSTRUMENTAL VERSION ✨')
print('=' * 70)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Musical Identity:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (E Major - uplifting!)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🎵 Enhanced Structure:')
print(f'   Chord segments: {len(data["sequence"])}')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])}')
print(f'   Length range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars')

print(f'\n🎸 Style Features:')
print(f'   Chord arpeggio: {data["style"]["chord"]["arp"]}')
print(f'   └─ Flowing 8-step cascade')
print(f'   Bass pattern: {data["style"]["bass"]["arp"]}')
print(f'   └─ Walking 8-step groove')
print(f'   Keep parameter: {data["style"]["chord"]["keep"]} notes sustained')
print(f'   Spread: {data["style"]["chord"]["spread"]} (open voicing)')
print(f'   Velocity: Bass {data["style"]["bass"]["velocity"]} / Chord {data["style"]["chord"]["velocity"]}')
print(f'   Effect: {data["effectType"]} reverb')
print(f'   Echo: {data["effectEcho"]["delay"]}s delay, {data["effectEcho"]["feedback"]} feedback')

print(f'\n🎨 Harmonic Palette:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'   • {chord}: {count}x')

print(f'\n📖 Progression Map (E Major):')
scale_notes = ['E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#']

sections = [
    (0, 4, 'INTRO (Spacious)'),
    (4, 12, 'VERSE 1 (Building)'),
    (12, 22, 'CHORUS 1 (Uplifting)'),
    (22, 30, 'VERSE 2 (Dynamic)'),
    (30, 38, 'BRIDGE (Emotional Lift)'),
    (38, 46, 'FINAL CHORUS/OUTRO')
]

for start, end, section_name in sections:
    print(f'\n   {section_name}:')
    for i in range(start, min(end, len(data["sequence"]))):
        seg = data["sequence"][i]
        root_note = scale_notes[seg["rootPos"]]
        
        if "bassPos" in seg:
            bass_note = scale_notes[seg["bassPos"]]
            chord_name = f'{root_note} {seg["chord"]} / {bass_note}'
        else:
            chord_name = f'{root_note} {seg["chord"]}'
        
        bars = seg["length"]
        bar_label = f'{bars} bar' if bars == 1 else f'{bars} bars'
        print(f'   {i+1:2}. {chord_name:18} ({bar_label})')

print(f'\n🌟 Key Features:')
print('   ✅ Extended harmonies: maj7, maj9, min7, min9')
print('   ✅ Slash bass (B/D#) for smooth voice leading')
print('   ✅ Suspended chords (sus2, sus4) for tension')
print('   ✅ Varied bar lengths (1-4) for organic flow')
print('   ✅ Cathedral reverb for spacious atmosphere')
print('   ✅ Keep: 3 notes for shimmering sustain')
print('   ✅ 8-step arpeggios for gentle movement')

print(f'\n💎 Character: Uplifting, beautiful, worshipful')
print('   Perfect for: Background music, meditation, worship moments')
print('=' * 70)
