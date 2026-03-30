import json

with open(r'c:\kordtana_starter_pack\Came_To_My_Rescue_Enhanced_Flow.json') as f:
    data = json.load(f)

print('🌊 ENHANCED FLOW VERSION ✨')
print('=' * 70)
print(f'\n🎹 {data["name"]}')
print(f'\n🎼 Musical Identity:')
print(f'   Key: {data["scaleKey"]} {data["scale"]} (G Major)')
print(f'   Instrument: {data["instrument"]}')
print(f'   Tempo: {data["style"]["tempo"]} bpm')
print(f'   Time: {data["style"]["timeSignature"]}')

print(f'\n🌊 ENHANCED FLOW FEATURES:')
print(f'   Chord segments: {len(data["sequence"])} (was 38)')
print(f'   Total bars: {sum(c["length"] for c in data["sequence"])} (was 144)')
print(f'   Length range: {min(c["length"] for c in data["sequence"])}-{max(c["length"] for c in data["sequence"])} bars (varied!)')

print(f'\n🎸 Enhanced Style:')
print(f'   Chord arpeggio: {data["style"]["chord"]["arp"]}')
print(f'   └─ 16-step flowing cascade (was 8-step)')
print(f'   Bass pattern: {data["style"]["bass"]["arp"]}')
print(f'   └─ 8-step walking bass (was 4-step)')
print(f'   Keep parameter: {data["style"]["chord"]["keep"]} notes (was 3)')
print(f'   Spread: {data["style"]["chord"]["spread"]} (was 0.10)')
print(f'   Velocity: {data["style"]["chord"]["velocity"]} (was 0.72)')
print(f'   Effect amount: {data["effectAmount"]} (was 0.82)')
print(f'   Echo delay: {data["effectEcho"]["delay"]}s (was 1.15s)')
print(f'   Echo feedback: {data["effectEcho"]["feedback"]} (was 0.10)')

print(f'\n🎨 Harmonic Variety & Transitions:')
chord_types = {}
for seg in data["sequence"]:
    chord_type = seg["chord"]
    chord_types[chord_type] = chord_types.get(chord_type, 0) + 1

for chord, count in sorted(chord_types.items()):
    print(f'   • {chord}: {count}x')

print(f'\n💫 Dynamic Movement Examples:')
scale_notes = ['G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#']
print('\n   First 20 segments showing variation:')
for i, seg in enumerate(data["sequence"][:20], 1):
    root_note = scale_notes[seg["rootPos"]]
    chord_name = f'{root_note} {seg["chord"]}'
    bars = seg["length"]
    bar_label = f'{bars} bar' if bars == 1 else f'{bars} bars'
    print(f'   {i:2}. {chord_name:15} ({bar_label})')

print(f'\n🌟 Key Enhancements:')
print('   ✅ Varied bar lengths: 1-3 bars (not uniform 2 or 4)')
print('   ✅ Chord color shifts: maj7↔maj9, min7↔min9 within same root')
print('   ✅ Suspended tension: sus2/sus4 transitions')
print('   ✅ 16-step arpeggio: more complex flowing pattern')
print('   ✅ 8-step bass: walking movement (not static)')
print('   ✅ Keep: 4 notes sustained (richer pad)')
print('   ✅ Higher spread: 0.12 (wider atmosphere)')
print('   ✅ Stronger velocity: 0.78 (more presence)')
print('   ✅ Deeper reverb/echo: longer tail, more space')

print(f'\n💎 Character: Flowing, dynamic, evolving')
print('   The progression now breathes and moves organically')
print('   Each chord has time to develop before transitioning')
print('=' * 70)
