# Agent Example: OneMotion Remix Generation

## Scenario: User Requests Trap Remix

**User Input:**
"Remix this Over track in trap style, E minor, 65 BPM" + `over.json` file

**Agent Process:**

### Step 1: Analyze Source

```python
# Parse source file
source = {
  "name": "over",
  "scaleKey": "C",
  "scale": "aeolian",
  "tempo": 78,
  "sequence": [6 chord progression],
  "bass_style": "arpeggio",
  "chord_style": "backbeat"
}
```

### Step 2: Apply Trap Transformation

```python
# Trap style modifications
trap_mods = {
  "tempo": 65,           # Slower trap tempo
  "key": "E",           # User specified key
  "bass": {
    "style": "once",     # Simple bass hits
    "step": [1, 2],     # On 1 and 3
    "velocity": 0.85    # Strong bass
  },
  "chord": {
    "style": "block",    # Solid chord blocks
    "step": [1, 8],     # Less frequent
    "arp": "off"        # No arpeggiation
  },
  "effects": {
    "echo": False,       # Dry trap sound
    "amount": 0.3       # Reduced reverb
  }
}
```

### Step 3: Generate Output JSON

```json
{
  "name": "over_trap_remix",
  "instrument": "piano",
  "scale": "aeolian",
  "scaleKey": "E",
  "chordLayout": {
    "diatonic-sus2": true,
    "diatonic-triad": true,
    "diatonic-sus4": true,
    "diatonic-7": true
  },
  "sequence": [
    {"chord": "maj", "length": 4, "rootPos": 8},
    {"chord": "min7", "length": 2, "rootPos": 7},
    {"chord": "min", "length": 2, "rootPos": 0},
    {"chord": "min7", "length": 4, "rootPos": 5},
    {"chord": "min7", "length": 2, "rootPos": 7},
    {"chord": "min", "length": 2, "rootPos": 0}
  ],
  "application": "OneMotion Chord-Player",
  "style": {
    "bass": {
      "arp": "xs",
      "loop": false,
      "step": [1, 2],
      "style": "once",
      "octave": 2,
      "velocity": 0.85,
      "arpEvents": {
        "0": {"items": [{"n": 0, "keep": false, "sustain": true, "remaining": true}]}
      },
      "arpLength": 1,
      "noteDuration": 2,
      "octaveOffset": 0
    },
    "chord": {
      "arp": "off",
      "style": "block",
      "step": [1, 8],
      "octave": 4,
      "velocity": 0.75,
      "arpEvents": {},
      "inversions": false,
      "noteDuration": 1
    },
    "tempo": 65,
    "shuffle": "1:1",
    "sustain": "chord",
    "timeSignature": "4/4"
  },
  "effectType": "chamber",
  "effectEcho": {"active": false, "delay": 1, "feedback": 0.5, "amount": 0.5},
  "effectAmount": 0.3,
  "loopSequence": true,
  "manualChordPositions": false,
  "melody": {"events": []},
  "customChords": [],
  "parallellScaleChords": false,
  "description": "Trap remix - E aeolian @ 65 BPM"
}
```

### Step 4: Agent Response Format

```
## Analysis
- **Source**: "Over" in C aeolian @ 78 BPM
- **Request**: Trap style, E minor, 65 BPM
- **Changes**:
  - Key: C → E (darker tone)
  - Tempo: 78 → 65 BPM (trap standard)
  - Bass: Arpeggio → Simple hits on 1 & 3
  - Chords: Backbeat → Block style
  - Effects: Reduced reverb for tight sound

## Generated File: `over_trap_remix.json`

Load this file directly into OneMotion Chord Player. The remix maintains your chord progression but transforms the rhythm and texture for trap production.

## Next Steps
1. Load `over_trap_remix.json` in OneMotion
2. Audition and adjust if needed
3. Export MIDI for your DAW
4. Add trap drums and 808s in production
```

## Key Agent Behaviors

### ✅ DO

- Always preserve original chord sequence structure
- Apply style-appropriate tempo/rhythm changes
- Maintain OneMotion JSON format requirements
- Provide clear before/after analysis
- Generate ready-to-use output files
- Include next steps for user

### ❌ DON'T

- Modify user's original file
- Make random musical changes
- Break OneMotion format rules
- Generate invalid JSON
- Provide incomplete transformations
- Skip validation steps

## Validation Checklist

Before outputting remix:

- [ ] JSON parses without errors
- [ ] Contains `parallellScaleChords` (double-l)
- [ ] All required OneMotion fields present
- [ ] Musical changes align with requested style
- [ ] Tempo/key match user specifications
- [ ] File loads properly in OneMotion Chord Player
