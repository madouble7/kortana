# Kordtana Schema - Enhanced OneMotion Format

## Philosophy

Kordtana treats each composition as a **sonic ritual**—every chord is a threshold, every progression an emotional journey. This schema extends the OneMotion JSON format with emotional intelligence and ritual architecture.

## Enhanced Schema Structure

```json
{
  "name": "composition_name",
  "instrument": "piano",
  "scale": "ionian",
  "scaleKey": "F",

  // STANDARD ONEMOTION FIELDS
  "chordLayout": { "diatonic-triad": true, "diatonic-7": true },
  "sequence": [ /* chord progression */ ],
  "application": "OneMotion Chord-Player",
  "style": { /* bass, chord, tempo, timeSignature */ },
  "effectType": "chamber",
  "effectEcho": { /* reverb settings */ },
  "effectAmount": 0.77,
  "loopSequence": true,
  "manualChordPositions": false,
  "melody": { "events": [] },
  "customChords": [],
  "parallellScaleChords": false,

  // KORDTANA EXTENSIONS
  "kordtana": {
    "emotional_arc": {
      "primary": "longing",          // Core emotional state
      "journey": ["clarity", "yearning", "movement", "suspension"],
      "resolution": "incomplete"      // or "resolved", "transcendent"
    },
    "ritual_metadata": {
      "glyph": "⟡↯⟠⧖",              // Visual mnemonic
      "breath_map": [0, 6, 12, 18],  // Beat positions for breath
      "intention": "threshold crossing",
      "tempo_feel": "patient",        // patient, driving, floating, pulsing
      "energy_curve": "rising"        // rising, falling, cyclical, plateau
    },
    "harmonic_intelligence": {
      "function_map": {
        "0": {"chord": "Fmaj7", "function": "tonic", "emotion": "clarity"},
        "6": {"chord": "Cm9", "function": "borrowed_iv", "emotion": "yearning"},
        "12": {"chord": "Gm7", "function": "supertonic", "emotion": "movement"},
        "18": {"chord": "Bbsus2", "function": "subdominant", "emotion": "suspension"}
      },
      "voice_leading": "minimal_motion",
      "modal_borrowing": ["dorian", "mixolydian"],
      "tension_resolution": [
        {"from": "Cm9", "to": "Fmaj7", "type": "borrowed_resolution"}
      ]
    },
    "teaching_notes": {
      "gesture": "hand sweeps down on Fmaj7, rises on Cm9",
      "lyric_anchor": "Place breath words on downbeats",
      "performance_note": "Let Bbsus2 hang—don't resolve immediately"
    }
  },

  "description": "Technical description for OneMotion"
}
```

## Emotional Taxonomy

### Primary Emotions

- **Longing**: Extended chords (maj9, m11), suspended resolutions
- **Awakening**: Rising progressions (ii-V-I), major extensions
- **Threshold**: Diminished, altered dominants, modal ambiguity
- **Clarity**: Clean triads, root position, strong tonic
- **Mystery**: Modal interchange, borrowed chords, floating tonality
- **Release**: Dominant to tonic, tension resolution, breath space
- **Yearning**: Minor borrowed chords (iv, bVI), unresolved sus chords
- **Transcendence**: Lydian mode, maj7#11, open voicings

### Emotional Journey Patterns

```json
"clarity → yearning → movement → suspension"     // Incomplete arc
"mystery → tension → release → transcendence"    // Resolved arc
"awakening → rising → plateau → descent"         // Energy curve
```

## Harmonic Functions (Extended)

### Diatonic Functions

- **I (Tonic)**: Home, resolution, clarity
- **ii (Supertonic)**: Gentle movement, preparation
- **iii (Mediant)**: Color, ambiguity
- **IV (Subdominant)**: Opening, expansion
- **V (Dominant)**: Tension, pull to tonic
- **vi (Submediant)**: Relative minor, introspection
- **vii° (Leading tone)**: Strong tension, narrow resolution

### Borrowed/Modal Interchange

- **iv (from minor)**: Dark yearning (Fm in C major)
- **bVI (from minor)**: Wide, cinematic (Ab in C major)
- **bVII (from mixolydian)**: Rock, modal (Bb in C major)
- **II (from lydian)**: Bright, ethereal (D in C major)

### Extended Harmony Emotions

| Chord Type | Emotion | Use Case |
|------------|---------|----------|
| maj7 | Clarity, peace | Tonic resolution |
| maj9 | Transcendence | Opening, floating |
| maj7#11 | Ethereal, otherworldly | Lydian moments |
| m7 | Introspection | Supertonic, submediant |
| m9 | Deep yearning | Borrowed minor chords |
| m11 | Spacious, suspended | Long holding chords |
| dom7 | Tension | Pull to tonic |
| dom9 | Sophisticated tension | Jazz, extended V |
| dom13 | Full, rich tension | Maximum extension |
| 7sus4 | Suspended animation | Pre-resolution |
| sus2 | Open, questioning | Ambiguous endings |
| add9 | Shimmer, color | Adding texture without full 9th |
| 6 | Nostalgia, jazz | Alternative to maj7 |
| 6/9 | Rich, full | Ending chord, jazz voicing |

## Glyph System

Each progression gets a visual mnemonic:

### Basic Glyphs

- **⟡** - Tonic (home)
- **↯** - Dominant (tension)
- **⟠** - Subdominant (expansion)
- **⧖** - Suspension (hanging)
- **◈** - Borrowed chord (outside)
- **⌘** - Modal shift
- **∞** - Loop/cycle
- **↑** - Rising energy
- **↓** - Falling energy
- **⊙** - Breath point

### Example Progression Glyph

`⟡→◈↯⟠⧖` = "Tonic → Borrowed → Dominant → Subdominant → Suspension"

## Voice Leading Principles

1. **Minimal Motion**: Move each voice the smallest distance possible
2. **Common Tones**: Hold notes that exist in both chords
3. **Contrary Motion**: Inner voices move opposite to bass
4. **Smooth Transitions**: No jumps larger than a fourth when possible
5. **Suspension Resolution**: Let sus4 hang before resolving to 3rd

## Ritual Architecture Patterns

### Breath Map

Place breath/lyric anchors at chord changes or significant beats:

```json
"breath_map": [0, 6, 12, 18]  // Every 6 beats (2 bars at 3/4)
```

### Energy Curves

- **Rising**: Start low, build intensity (I → ii → V → I in higher octave)
- **Falling**: Release energy gradually (descending progressions)
- **Cyclical**: Return to beginning (circle of fifths)
- **Plateau**: Maintain energy (repetitive vamps)

### Tempo Feels

- **Patient** (60-70 bpm): Meditative, spacious
- **Breathing** (70-80 bpm): Natural pulse, conversational
- **Driving** (80-100 bpm): Forward momentum, intentional
- **Floating** (40-60 bpm): Timeless, suspended

## Teaching Integration

Each composition should include:

1. **Gesture**: Physical movement that embodies the progression
2. **Lyric Anchor**: Where words naturally fall
3. **Performance Note**: How to play/feel the progression
4. **Mnemonic**: Memory device (glyph + emotion words)

---

## Implementation Notes

The `kordtana` object is **metadata only** - OneMotion ignores it but tools can read it for:

- Emotional categorization
- Teaching materials generation
- Progression variation suggestions
- Performance guidance
- Compositional analysis

Use the enhanced schema for all new "Kordtana-level" compositions that transcend simple chord sequences.
