import json

print('🎼 5 ORIGINAL SIMPLE PROGRESSIONS 🎼')
print('(Perfect for covers or writing original songs)')
print('=' * 70)

files = [
    ('c:\\kordtana_starter_pack\\Original_Progression_1_Melancholic.json', '1️⃣'),
    ('c:\\kordtana_starter_pack\\Original_Progression_2_Hopeful.json', '2️⃣'),
    ('c:\\kordtana_starter_pack\\Original_Progression_3_Descent.json', '3️⃣'),
    ('c:\\kordtana_starter_pack\\Original_Progression_4_Bittersweet.json', '4️⃣'),
    ('c:\\kordtana_starter_pack\\Original_Progression_5_Rising.json', '5️⃣')
]

scale_notes_map = {
    'C': ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'],
    'D': ['D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#'],
    'E': ['E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#'],
    'F': ['F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E'],
    'G': ['G', 'G#', 'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#']
}

for filepath, number in files:
    with open(filepath) as f:
        data = json.load(f)
    
    print(f'\n{number} {data["name"]}')
    print('-' * 70)
    
    scale_notes = scale_notes_map.get(data["scaleKey"], scale_notes_map['C'])
    
    chords = []
    for seg in data["sequence"]:
        root_note = scale_notes[seg["rootPos"]]
        chord_type = seg["chord"]
        if chord_type == "maj":
            chords.append(root_note)
        elif chord_type == "min":
            chords.append(f'{root_note}m')
        else:
            chords.append(f'{root_note}{chord_type}')
    
    print(f'   Progression: {" - ".join(chords)}')
    print(f'   Key: {data["scaleKey"]} {data["scale"]}')
    print(f'   Tempo: {data["style"]["tempo"]} bpm')
    print(f'   Effect: {data["effectType"]}')
    print(f'   💡 {data["description"]}')

print('\n' + '=' * 70)
print('✅ All 5 are simple 4-chord, 16-bar loops')
print('   Same clean style as "Someone Like You"')
print('   Ready to sing or play over!')
print('=' * 70)
