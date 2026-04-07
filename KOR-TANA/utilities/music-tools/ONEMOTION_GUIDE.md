# OneMotion Chord Player JSON Format Guide

## Template Structure

Use `onemotion_template.json` as your base. OneMotion expects a flat JSON structure with specific field names and arrangements.

## Key Differences from Kordtana.card Format

### Identity → Root Level Fields

```json
// Kordtana nested
"identity": {
  "name": "song_name",
  "instrument": "piano",
  "scale": "aeolian",
  "scaleKey": "C",
  "tempo": 64,
  "timeSignature": "4/4"
}

// OneMotion flat
"name": "song_name",
"instrument": "piano",
"scale": "aeolian",
"scaleKey": "C",
"style": {
  "tempo": 64,
  "timeSignature": "4/4"
}
```

### Layout → chordLayout

```json
// Kordtana
"layout": { "diatonicTriad": true, "diatonic7": false }

// OneMotion
"chordLayout": { "diatonic-triad": true, "diatonic-7": false }
```

### Effects Structure

```json
// Kordtana nested
"effects": {
  "type": "chamber",
  "echo": { "active": true, "delay": 1, "feedback": 0.07, "amount": 0.5 }
}

// OneMotion flat
"effectType": "chamber",
"effectEcho": { "active": true, "delay": 1, "feedback": 0.07, "amount": 0.5 },
"effectAmount": 0.5
```

### Behaviors → Root Level

```json
// Kordtana nested
"behaviors": {
  "loopSequence": true,
  "manualChordPositions": false,
  "parallelScaleChords": true
}

// OneMotion flat
"loopSequence": true,
"manualChordPositions": false,
"parallellScaleChords": true  // NOTE: "parallell" misspelling is intentional
```

## Required Fields Always Present

### Essential Structure

- `name` (string)
- `instrument` (string: "piano", "electric-piano", "upright-piano", etc.)
- `scale` (string: "aeolian", "ionian", "dorian", "harmonic-minor", etc.)
- `scaleKey` (string: "C", "D", "Eb", etc.)
- `application` (string: "OneMotion Chord-Player")

### Chord Layout

```json
"chordLayout": {
  "diatonic-triad": true,
  "diatonic-7": false,
  "diatonic-sus2": false,
  "diatonic-sus4": false
}
```

### Sequence Format

```json
"sequence": [
  { "chord": "min", "length": 4, "rootPos": 0 }
]
```

- `chord`: "min", "maj", "dim", "min7", "maj7", "minMaj7", etc.
- `length`: bars (integer)
- `rootPos`: semitones from scale root (0-11)

### Style Object

Must include both `bass` and `chord` with full arpEvents structure:

```json
"style": {
  "bass": {
    "arp": "xs",
    "loop": false,
    "step": [1, 1],
    "style": "once",
    "octave": 3,
    "velocity": 0.7,
    "arpEvents": {
      "0": {
        "items": [{"n": 0, "keep": false, "sustain": true, "remaining": true}]
      }
    },
    "arpLength": 1,
    "octaveOffset": -3,
    "noteDuration": 1
  },
  "chord": {
    "arp": "off",
    "style": "block",
    "octave": 4,
    "velocity": 0.7,
    "step": [1, 4],
    "arpEvents": {},
    "inversions": false
  },
  "tempo": 64,
  "timeSignature": "4/4",
  "shuffle": "1:1",
  "sustain": "chord"
}
```

### Always Include

```json
"melody": { "events": [] },
"customChords": [],
"description": "",
"public": false,
"free": true
```

## Common Patterns

### Basic Block Chords

```json
"chord": {
  "arp": "off",
  "style": "block",
  "step": [1, 4]
}
```

### Arpeggiated Chords

```json
"chord": {
  "arp": "23 1",
  "style": "split-23-1",
  "step": [1, 8],
  "arpLength": 2
}
```

### Bass Patterns

- `"style": "once"` — single bass note
- `"style": "arpeggio"` — bass arp pattern
- `"arp": "xs"` — basic arp

## Validation Checklist

✅ All required root-level fields present
✅ `parallellScaleChords` (with double-l)
✅ `chordLayout` uses hyphens
✅ `style.tempo` and `style.timeSignature` inside style object
✅ `effectType` and `effectEcho` at root level
✅ `arpEvents` object present (even if empty)
✅ `melody.events` array present
✅ `application` = "OneMotion Chord-Player"

## Agent Instructions

When drafting OneMotion JSON:

1. **Start with template** — copy `onemotion_template.json`
2. **Fill core identity** — name, scale, key, tempo
3. **Define sequence** — chord progression with lengths and positions
4. **Set style parameters** — bass/chord patterns, arps, velocities
5. **Configure effects** — chamber/echo settings
6. **Validate structure** — check required fields and naming

### Common Mistakes to Avoid

- ❌ Nested identity object (should be flat)
- ❌ `parallelScaleChords` (missing double-l)
- ❌ `diatonicTriad` (should use hyphens)
- ❌ Missing `arpEvents` in style sections
- ❌ Effects in nested object (should be flat)
- ❌ Tempo/timeSignature outside style object
