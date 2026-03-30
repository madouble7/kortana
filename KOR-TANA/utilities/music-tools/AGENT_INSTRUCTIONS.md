# Agent Instructions: OneMotion Chord Player JSON Generation

## Your Role

You are drafting **OneMotion Chord Player JSON files** for musical projects. These files define chord progressions, instruments, effects, and performance parameters that can be loaded directly into OneMotion's browser-based chord player.

## Quick Start Process

### 1. Load Template

Always start with `onemotion_template.json` as your base structure.

### 2. Core Fields to Customize

```json
{
  "name": "[project_name]",
  "instrument": "[piano|electric-piano|upright-piano]",
  "scale": "[aeolian|ionian|dorian|harmonic-minor|melodic-minor|phrygian]",
  "scaleKey": "[C|D|Eb|F|G|Ab|Bb|etc]",
  "style": {
    "tempo": [60-180],
    "timeSignature": "[4/4|3/4|6/8]"
  }
}
```

### 3. Define Chord Sequence

```json
"sequence": [
  { "chord": "min", "length": 4, "rootPos": 0 },
  { "chord": "maj", "length": 4, "rootPos": 5 },
  { "chord": "min", "length": 2, "rootPos": 7 },
  { "chord": "maj", "length": 2, "rootPos": 3 }
]
```

**Chord Types:** min, maj, dim, min7, maj7, minMaj7, sus2, sus4, min6, maj6, dim7
**Root Position:** 0-11 semitones from scale root (0=tonic, 5=dominant, 7=subtonic, etc.)
**Length:** Duration in bars

### 4. Style Configuration

#### Basic Block Chords

```json
"chord": {
  "arp": "off",
  "style": "block",
  "step": [1, 4],
  "velocity": 0.7,
  "inversions": false
}
```

#### Arpeggiated Patterns

```json
"chord": {
  "arp": "23 1",
  "style": "split-23-1",
  "step": [1, 8],
  "arpLength": 2,
  "inversions": true
}
```

#### Bass Patterns

- `"style": "once"` + `"arp": "xs"` = Simple bass notes
- `"style": "arpeggio"` + detailed `arpEvents` = Complex bass lines

### 5. Effects Configuration

```json
"effectType": "chamber",
"effectEcho": {
  "active": true,
  "delay": 0.5,
  "feedback": 0.06,
  "amount": 0.45
},
"effectAmount": 0.45
```

## Critical Format Rules

### ✅ Always Include These Exact Spellings

- `"parallellScaleChords": true` (double-l is intentional)
- `"diatonic-triad": true` (hyphens, not camelCase)
- `"application": "OneMotion Chord-Player"`

### ✅ Required Structure

- Tempo/timeSignature go **inside** `style` object
- Effects are **flat** at root level (not nested)
- Always include empty `melody.events` and `customChords` arrays
- All `arpEvents` objects required (can be empty `{}`)

### ❌ Common Mistakes

- Don't nest identity fields — they go at root level
- Don't use `"parallelScaleChords"` — it needs double-l
- Don't forget arpEvents in bass/chord sections
- Don't put tempo outside style object

## Template Variations by Style

### Ambient/Slow

```json
"style": {
  "tempo": 60,
  "chord": { "arp": "off", "style": "block", "step": [1, 8] },
  "bass": { "style": "once", "step": [1, 1] }
},
"effectEcho": { "active": true, "amount": 0.8 }
```

### Driving/Uptempo

```json
"style": {
  "tempo": 120,
  "chord": { "arp": "23 1", "style": "split-23-1", "step": [1, 4] },
  "bass": { "style": "arpeggio", "step": [1, 8] }
},
"effectEcho": { "active": false }
```

### Modal/Experimental

```json
"scale": "phrygian",
"chordLayout": { "diatonic-sus2": true, "diatonic-sus4": true },
"sequence": [
  { "chord": "min", "length": 6, "rootPos": 0 },
  { "chord": "maj", "length": 2, "rootPos": 1 }
]
```

## Workflow Steps

1. **Copy template** → customize name, scale, key
2. **Plan sequence** → write chord progression
3. **Choose style** → block chords vs arps, bass pattern
4. **Set tempo/feel** → match the musical intent
5. **Add effects** → chamber reverb, echo settings
6. **Validate** → check all required fields present
7. **Test load** → verify OneMotion accepts the JSON

## Quality Check

Before submitting, verify:

- [ ] JSON parses without errors
- [ ] All required root-level fields present
- [ ] `parallellScaleChords` spelled correctly
- [ ] `chordLayout` uses hyphens
- [ ] `arpEvents` objects included
- [ ] Tempo inside style object
- [ ] Effects at root level (not nested)
- [ ] Sequence uses valid chord types and positions

## Example Output

Your generated JSON should load cleanly into OneMotion Chord Player's file import, play the intended progression, and match the specified instrument/effects parameters.
