# 🎹 OneMotion Quick Reference Card

## 🚀 Quick Start

### Use the Builder (Easiest!)

```bash
cd C:\kordtana_starter_pack
python onemotion_builder.py
```

Interactive tool walks you through creating a valid OneMotion JSON.

### Validate Your JSON

```bash
python onemotion_validator.py your_file.json
```

Checks for errors and provides specific fixes.

---

## 📋 Chord Types Reference

### Basic Triads

- `maj` — Major triad
- `min` — Minor triad
- `dim` — Diminished
- `aug` — Augmented

### Seventh Chords

- `maj7` — Major 7th
- `min7` — Minor 7th
- `dom7` — Dominant 7th
- `minMaj7` — Minor-major 7th
- `dim7` — Diminished 7th
- `halfDim7` — Half-diminished 7th

### Suspended

- `sus2` — Suspended 2nd
- `sus4` — Suspended 4th

---

## 🎼 Scale Types

- `ionian` — Major scale (happy)
- `aeolian` — Natural minor (sad)
- `dorian` — Minor with raised 6th
- `phrygian` — Spanish/dark sound
- `lydian` — Major with raised 4th
- `mixolydian` — Major with lowered 7th
- `harmonic-minor` — Minor with raised 7th
- `melodic-minor` — Minor with raised 6/7

---

## 🎹 Key Names

Use these EXACT spellings:

- `C`, `C#`, `D`, `Eb`, `E`, `F`, `F#`, `G`, `Ab`, `A`, `Bb`, `B`

(Note: Use `Eb` not `D#`, `Ab` not `G#`, `Bb` not `A#`)

---

## 🎸 Style Patterns

### Bass Styles

```json
"bass": {
  "style": "once",      // Single bass note
  "style": "arpeggio"   // Bass arpeggio pattern
}
```

### Chord Styles

```json
"chord": {
  "arp": "off",         // Block chords
  "style": "block"
}

"chord": {
  "arp": "23 1",        // 2+3+1 arpeggio
  "style": "split-23-1",
  "step": [1, 8]
}
```

---

## ⚠️ Common Gotchas

### ❌ WRONG → ✅ RIGHT

```json
// Tempo location
❌ "tempo": 64  (at root)
✅ "style": { "tempo": 64 }

// Parallel spelling
❌ "parallelScaleChords": true
✅ "parallellScaleChords": true  (double-l!)

// Chord layout
❌ "diatonicTriad": true
✅ "diatonic-triad": true  (use hyphens!)

// Effects location
❌ "effects": { "type": "chamber" }
✅ "effectType": "chamber"  (flat, at root)
```

---

## 📝 Minimal Valid Example

```json
{
  "name": "my_song",
  "instrument": "piano",
  "scale": "aeolian",
  "scaleKey": "C",
  "application": "OneMotion Chord-Player",

  "chordLayout": {
    "diatonic-triad": true,
    "diatonic-7": false
  },

  "sequence": [
    { "chord": "min", "length": 4, "rootPos": 0 },
    { "chord": "maj", "length": 4, "rootPos": 5 }
  ],

  "style": {
    "tempo": 64,
    "timeSignature": "4/4",
    "bass": {
      "style": "once",
      "arp": "xs",
      "octave": 3,
      "velocity": 0.7,
      "step": [1, 1],
      "arpEvents": { "0": { "items": [{"n": 0, "sustain": true}] } }
    },
    "chord": {
      "style": "block",
      "arp": "off",
      "octave": 4,
      "velocity": 0.7,
      "step": [1, 4],
      "arpEvents": {}
    }
  },

  "effectType": "chamber",
  "effectEcho": {
    "active": true,
    "delay": 1,
    "feedback": 0.07,
    "amount": 0.5
  },
  "effectAmount": 0.5,

  "loopSequence": true,
  "manualChordPositions": false,
  "parallellScaleChords": true,

  "melody": { "events": [] },
  "customChords": [],
  "description": "",
  "public": false,
  "free": true
}
```

---

## 🎯 Workflow Tips

1. **Start simple** — Use `onemotion_builder.py` for your first few
2. **Copy & modify** — Duplicate working files and tweak them
3. **Validate often** — Run `onemotion_validator.py` after changes
4. **Use harmony_studio.py** — For AI-generated advanced progressions
5. **Keep template handy** — `onemotion_template.json` has all fields

---

## 🆘 Troubleshooting

### "Invalid JSON file"

- Run through validator: `python onemotion_validator.py file.json`
- Check for missing commas or brackets
- Ensure all strings use double quotes `"` not single `'`

### "Chords not playing"

- Verify `sequence` array has valid chord types
- Check `rootPos` is 0-11
- Ensure `length` is positive integer

### "Effects not working"

- Check `effectType` at root level (not nested)
- Verify `effectEcho` structure with all fields
- Set `effectEcho.active` to `true`

---

## 📚 Full Documentation

See `ONEMOTION_GUIDE.md` for complete field reference.

---

**Happy composing! 🎼**
