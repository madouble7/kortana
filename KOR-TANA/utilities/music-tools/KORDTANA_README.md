# 🎹 Kordtana - The Sonic Architect

**Kordtana** is a musical intelligence system built on OneMotion Chord Player that transforms chord progressions into **emotional rituals**—compositions with harmonic depth, mnemonic architecture, and intentional design.

## What Makes Kordtana Different?

Traditional chord progressions: `C - Am - F - G`

**Kordtana progression**:

```
⟡◈⟠⧖
Cmaj7 → Am9 → Fmaj9 → Gsus4
clarity → yearning → movement → suspension
Breath at: 0, 6, 12, 18 beats
Intention: "Threshold crossing - standing at the edge of transformation"
```

## The Kordtana System

### 1. Enhanced Schema

Standard OneMotion JSON **+** Emotional/Ritual Metadata

- ✅ **100% Compatible** with OneMotion Chord Player
- ✅ **Harmonic Analysis**: Function, voice leading, modal theory
- ✅ **Emotional Taxonomy**: 8 core emotions with chord mappings
- ✅ **Glyph System**: Visual mnemonics (⟡↯⟠⧖◈⌘∞⊙)
- ✅ **Ritual Architecture**: Breath maps, gestures, intentions
- ✅ **Teaching Integration**: Performance notes, lyric anchors

### 2. Tools

**Kordtana Composer** (`kordtana_composer.py`)

- Interactive composition with emotional intention
- Generates progressions from emotional arcs
- Automatic glyph and metadata creation

**Kordtana Analyzer** (`kordtana_analyzer.py`)

- Add intelligence to existing progressions
- Batch processing for entire libraries
- Harmonic function analysis

**OneMotion Builder** (`onemotion_builder.py`)

- Standard progression creation
- JSON validation
- Quick prototyping

### 3. Documentation

| File | Purpose |
|------|---------|
| `KORDTANA_SCHEMA.md` | Complete schema specification |
| `KORDTANA_QUICKSTART.md` | Getting started guide |
| `ONEMOTION_GUIDE.md` | OneMotion format reference |
| `ONEMOTION_QUICKREF.md` | Quick reference card |
| `MELODY_EXPLORATION.md` | Melody system investigation |

## Quick Start

### Create Your First Kordtana Progression

```bash
python kordtana_composer.py
```

Follow the prompts:

```
Key: F
Mode: ionian
Emotional arc: clarity,yearning,movement,suspension
Tempo: 66
Intention: threshold crossing
```

Result: `Kordtana_threshold_crossing_F_ionian.json`

### Enhance an Existing Progression

```bash
python kordtana_analyzer.py Bank_01_C_Major_C_Am_F_G_Ballad.json
```

Adds Kordtana metadata while preserving OneMotion compatibility.

### Batch Process Your Library

```bash
python kordtana_analyzer.py --batch . "Bank_*.json"
```

## The 8 Core Emotions

| Emotion | Chords | Function | Glyph |
|---------|--------|----------|-------|
| **Clarity** | maj, maj7 | Tonic | ⟡ |
| **Yearning** | min9, min11, sus4 | Borrowed minor | ◈ |
| **Movement** | min7, dom7 | Supertonic/Dominant | ⟠ |
| **Suspension** | sus2, sus4 | Unresolved | ⧖ |
| **Tension** | dom7, dom9, dim | Dominant | ↯ |
| **Transcendence** | maj9, maj7#11 | Lydian | ∞ |
| **Mystery** | dim, m7b5 | Altered | ⌘ |
| **Release** | maj, maj6 | Resolution | ⊙ |

## Example Progressions

### Kordtana 01 - Threshold Crossing

**File**: `Kordtana_01_Threshold_Crossing_F_Ionian.json`

```
Key: F Ionian
Progression: Fmaj7 → Cm9 → Gm7 → Bbsus2
Glyph: ⟡◈⟠⧖
Arc: clarity → yearning → movement → suspension
Tempo: 66 bpm (patient)
Time: 3/4 (24 beats = 8 bars)

Harmonic Notes:
- Cm9 borrowed from F minor (modal interchange)
- Common tone voice leading (F-C shared, G-Bb-D shared)
- Bbsus2 hangs unresolved - invites loop return
- Breath every 6 beats (2 bars)

Intention: "Standing at the threshold of transformation"
```

### Your Existing Bank Library

All 39 Bank/Simple Pack progressions are **Kordtana-ready**:

- Standardized at 66 bpm, 3/4 time
- 0.77 velocity, chamber reverb
- Can be enhanced with `kordtana_analyzer.py`

## Music Theory Integration

### Modal Interchange

Borrow chords from parallel modes:

```
F Ionian (F major):     F - Gm - Am - Bb - C - Dm - Edim
F Aeolian (F minor):    Fm - Gm - Ab - Bb - Cm - Db - Eb
                                    ↓
Borrow Cm9, Ab, Db, Eb for darker color
```

### Voice Leading Principles

1. **Minimal motion** between chords
2. **Common tones** held across changes
3. **Contrary motion** in inner voices
4. **Smooth transitions** (no jumps > 4th)

### Extended Harmony

- **9ths**: Shimmer, space (maj9, min9, dom9)
- **11ths**: Suspension, width (min11)
- **13ths**: Maximum extension (dom13)
- **6/9**: Rich jazz endings (maj6/9)
- **sus**: Remove 3rd for ambiguity (sus2, sus4)

## Workflow Integration

### For Songwriting

1. Choose emotional arc matching lyric theme
2. Generate with `kordtana_composer.py`
3. Use breath map for lyric placement
4. Let glyph guide melodic contour

### For Performance

1. Read teaching notes before playing
2. Follow gesture suggestions
3. Honor breath map
4. Let final chord hang if unresolved

### For Learning

1. Study harmonic analysis in files
2. Try variations in compositional notes
3. Map favorite songs to taxonomy
4. Create your own glyphs

## File Structure

```
kordtana_starter_pack/
├── Tools
│   ├── kordtana_composer.py         # Generate with intention
│   ├── kordtana_analyzer.py         # Enhance existing files
│   ├── onemotion_builder.py         # Standard builder
│   └── onemotion_validator.py       # JSON validation
│
├── Documentation
│   ├── KORDTANA_SCHEMA.md           # Complete specification
│   ├── KORDTANA_QUICKSTART.md       # Getting started
│   ├── ONEMOTION_GUIDE.md           # Format reference
│   └── MELODY_EXPLORATION.md        # Melody system
│
├── Kordtana Compositions
│   └── Kordtana_01_Threshold_Crossing_F_Ionian.json
│
├── Bank Series (19 files)
│   ├── Bank_01-09: Simple progressions
│   └── Bank_10-19: Jazz sophistication
│
├── Simple Pack (10 files)
│   └── Simple_Pack_01-10: Various keys
│
└── Original/Bills/Holy/Bad Guy
    └── Legacy progressions (standardized)
```

## Philosophy

> "Every chord is a threshold, every progression an emotional journey, every performance a ritual."

Kordtana treats music not as pure entertainment but as **sonic architecture**—intentional, mnemonic, and alive. Each composition:

- **Tells a story** through harmonic function
- **Anchors memory** with glyphs and breath maps
- **Honors voice leading** for smooth transitions
- **Serves intention** through emotional design

## Technical Notes

- **OneMotion Compatibility**: 100% - `kordtana` object is metadata only
- **JSON Standard**: Follows OneMotion Chord Player format
- **Python Tools**: Python 3.7+, no external dependencies
- **File Format**: UTF-8 JSON with 2-space indentation

## Next Steps

1. **Explore** the example: `Kordtana_01_Threshold_Crossing_F_Ionian.json`
2. **Create** your first progression with `kordtana_composer.py`
3. **Enhance** existing Bank files with `kordtana_analyzer.py`
4. **Study** the schema in `KORDTANA_SCHEMA.md`
5. **Experiment** with glyphs and emotional arcs
6. **Share** your Kordtana compositions

## Contributing

Want to expand Kordtana?

- Add new emotional categories
- Create modal interchange libraries
- Build melody generation tools
- Design new glyph systems
- Document your progressions

## Credits

**Concept**: Matt (madouble7)
**Architecture**: Kordtana AI Intelligence Layer
**Platform**: OneMotion Chord Player
**Tools**: Claude (GitHub Copilot) + Python

---

**🎹 Let the music breathe. Let the chords speak. Let Kordtana guide your sonic rituals.**
