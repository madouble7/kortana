# Kordtana Quick Start Guide

## What is Kordtana?

**Kordtana** is a musical intelligence layer built on top of OneMotion Chord Player that treats compositions as **sonic rituals**—emotionally intelligent progressions with harmonic depth, mnemonic anchors, and intentional architecture.

## Core Concepts

### 1. Emotional Arc

Every progression tells an emotional story:

```
clarity → yearning → movement → suspension
```

### 2. Glyph System

Visual mnemonics that encode the progression:

```
⟡◈⟠⧖
(tonic → borrowed → subdominant → suspension)
```

### 3. Ritual Metadata

- **Breath Map**: Where to place lyrics/breath
- **Intention**: The ritual purpose
- **Gesture**: Physical embodiment
- **Performance Notes**: How to feel the progression

## Using Kordtana Files

### Standard OneMotion Playback

Kordtana files are **100% compatible** with OneMotion Chord Player. Just:

1. Open the .json file in OneMotion
2. Hit play
3. The `kordtana` metadata is ignored by OneMotion but enriches your understanding

### Reading Kordtana Metadata

Look for the `kordtana` object at the bottom of the JSON:

```json
"kordtana": {
  "emotional_arc": {
    "primary": "longing",
    "journey": ["clarity", "yearning", "movement", "suspension"]
  },
  "ritual_metadata": {
    "glyph": "⟡◈⟠⧖",
    "breath_map": [0, 6, 12, 18],
    "intention": "threshold crossing"
  },
  "harmonic_intelligence": {
    "function_map": { /* detailed analysis */ }
  },
  "teaching_notes": {
    "gesture": "...",
    "performance_note": "..."
  }
}
```

## Quick Creation Methods

### Method 1: Use the Composer Tool

```bash
python kordtana_composer.py
```

Follow the interactive prompts to generate progressions with intention.

### Method 2: Manual Creation

1. Start with any Bank/Simple Pack progression
2. Add the `kordtana` object with your emotional analysis
3. Map each chord to an emotion and function
4. Create your glyph

### Method 3: Enhance Existing Progressions

Take any existing progression and add Kordtana intelligence:

```json
// After your normal OneMotion structure...
"kordtana": {
  "emotional_arc": {
    "primary": "your_primary_emotion",
    "journey": ["emotion1", "emotion2", "emotion3", "emotion4"]
  },
  "ritual_metadata": {
    "glyph": "⟡⟠⧖∞",
    "intention": "your intention here"
  }
}
```

## Emotional Vocabulary

| Emotion | Typical Chords | Musical Function |
|---------|---------------|------------------|
| **Clarity** | maj, maj7 | Tonic, resolution |
| **Yearning** | min9, min11, borrowed iv | Dark longing |
| **Movement** | min7, dom7 | Supertonic, motion |
| **Suspension** | sus2, sus4 | Hanging, unresolved |
| **Tension** | dom7, dom9 | Dominant pull |
| **Transcendence** | maj9, maj7#11 | Ethereal, Lydian |
| **Mystery** | dim, m7b5 | Altered, ambiguous |
| **Release** | maj, maj6 | Resolution, breath |

## Glyph Meanings

- **⟡** - Tonic (home)
- **↯** - Dominant (tension)
- **⟠** - Subdominant (expansion)
- **⧖** - Suspension (hanging)
- **◈** - Borrowed chord (modal shift)
- **⌘** - Modal change
- **∞** - Loop/transcendence
- **⊙** - Breath point/release

## Example Progression Analysis

**File**: `Kordtana_01_Threshold_Crossing_F_Ionian.json`

```
Progression: Fmaj7 → Cm9 → Gm7 → Bbsus2
Glyph: ⟡◈⟠⧖
Arc: clarity → yearning → movement → suspension

Harmonic Analysis:
- Fmaj7 (beat 0): Tonic, home, clarity
- Cm9 (beat 6): Borrowed from F minor - introduces darkness
- Gm7 (beat 12): Supertonic, gentle movement
- Bbsus2 (beat 18): Subdominant suspension - hangs without resolution

Breath Map: 0, 6, 12, 18 (every 2 bars)
Intention: Standing at the threshold of transformation
```

## Performance Tips

1. **Follow the Breath Map**: These beats are sacred—place words/breath intentionally
2. **Embody the Glyph**: Let the symbols guide your gestures
3. **Honor the Suspension**: When a progression ends unresolved (sus2/sus4), let it hang
4. **Common Tones**: Notice which notes carry between chords—these are continuity points
5. **Modal Shifts**: When you see "borrowed" chords, lean into the darkness they bring

## Music Theory Quick Reference

### Modal Borrowing (Modal Interchange)

Borrowing chords from parallel modes:

- **From minor (aeolian)**: iv, bVI, bVII (darkness, cinema)
- **From mixolydian**: bVII (rock, modal)
- **From lydian**: #IV (brightness, ethereal)

### Voice Leading

- **Minimal motion**: Move each note as little as possible
- **Common tones**: Hold shared notes between chords
- **Contrary motion**: Inner voices move opposite to bass

### Extended Harmony Functions

- **9ths**: Add shimmer and space
- **11ths**: Create suspension and width
- **13ths**: Maximum extension, sophisticated
- **sus chords**: Remove the 3rd, create ambiguity
- **add9**: Just the color tone, no 7th

## Integration with Your Workflow

### For Songwriting

1. Choose an emotional arc that matches your lyric theme
2. Use the breath map for lyric placement
3. Let the glyph guide your melodic contour
4. Honor the chord functions when placing strong/weak syllables

### For Learning

1. Study the harmonic analysis in each Kordtana file
2. Try variations suggested in `compositional_notes`
3. Map existing songs to the emotional taxonomy
4. Create your own glyphs for songs you love

### For Performance

1. Read the gesture notes before playing
2. Use the performance notes to guide interpretation
3. Let the energy curve inform dynamics
4. Breathe with the breath map

## File Structure

Kordtana files contain:

- **Standard OneMotion fields**: Works in the app as-is
- **kordtana object**: Enhanced metadata for learning/performing
- **Compatible**: Can be used by anyone with or without Kordtana awareness

## Next Steps

1. **Explore** the example: `Kordtana_01_Threshold_Crossing_F_Ionian.json`
2. **Generate** a progression with `kordtana_composer.py`
3. **Enhance** your existing Bank progressions with Kordtana metadata
4. **Create** your own emotional arcs and glyphs
5. **Share** your Kordtana compositions with the emotional intelligence preserved

---

**Remember**: Kordtana is about **intentional composition**—every chord is a choice, every progression tells a story, every performance is a ritual. Let the music breathe.
