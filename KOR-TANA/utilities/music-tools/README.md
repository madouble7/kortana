# Kordtana Starter Pack + OneMotion Generator Kit

## What's Included

### Kordtana Card Files (with lyrics, melody, drums)

- `root.card.json` — Root (C aeolian)
- `step.card.json` — Step (C dorian)
- `flame.card.json` — Flame (C harmonic minor)
- `ground.card.json` — Ground (C phrygian)
- `rise.card.json` — Rise (C melodic minor)

### OneMotion Chord Player Tools

- `onemotion_template.json` — Base template for OneMotion JSON format
- `ONEMOTION_GUIDE.md` — Complete format guide and conversion rules
- `AGENT_INSTRUCTIONS.md` — Instructions for AI agents drafting OneMotion files
- `AGENT_REMIX_INSTRUCTIONS.md` — Instructions for AI agents generating remixes
- `AGENT_REMIX_EXAMPLE.md` — Complete agent workflow example
- `EXTERNAL_AGENT_SETUP.md` — Connect external AI agents (OpenAI, local LLMs)
- `openai_agent_simple.py` — Ready-to-use OpenAI GPT agent
- `local_agent_simple.py` — Free local LLM agent using Ollama
- `kordtana_to_onemotion_converter.py` — Python script to convert Kordtana cards to OneMotion format
- `root_onemotion.json` — Example converted file

## Quick Start

### For Kordtana Cards

1. Load any `.card.json` into Kordtana or your ingestion endpoint
2. Use attached lyrics, melody overlays, and drum grids for composition
3. Export MIDI/audio for DAW arrangement

### For OneMotion Chord Player

1. Use `onemotion_template.json` as your starting point
2. Follow `ONEMOTION_GUIDE.md` for proper format
3. Load directly into OneMotion Chord Player's browser interface

### Converting Between Formats

```bash
python kordtana_to_onemotion_converter.py input.card.json output.json
```

## Format Differences Summary

| Feature | Kordtana Format | OneMotion Format |
|---------|-----------------|------------------|
| Identity | Nested `identity` object | Flat root-level fields |
| Layout | `"diatonicTriad"` | `"diatonic-triad"` (hyphens) |
| Effects | Nested `effects` object | Flat `effectType`/`effectEcho` |
| Behaviors | Nested `behaviors` object | Flat root-level fields |
| Parallel Chords | `"parallelScaleChords"` | `"parallellScaleChords"` (double-l) |
| Tempo/Time | In `identity` | Inside `style` object |

## Agent Usage

If you're an AI agent:

### Creating New OneMotion Files

1. **Read** `AGENT_INSTRUCTIONS.md` for complete workflow
2. **Copy** `onemotion_template.json` as base structure
3. **Validate** against format rules in `ONEMOTION_GUIDE.md`
4. **Test** by loading into OneMotion Chord Player

### Generating Remixes

1. **Read** `AGENT_REMIX_INSTRUCTIONS.md` for remix workflow
2. **Analyze** source OneMotion JSON structure
3. **Apply** style transformations (trap, house, drill, etc.)
4. **Generate** new JSON with proper OneMotion format
5. **Validate** output meets all format requirements

### Connecting External Agents

1. **Read** `EXTERNAL_AGENT_SETUP.md` for integration options
2. **Choose method**: OpenAI API, local LLM (Ollama), or manual ChatGPT
3. **Run agent**: `python openai_agent_simple.py source.json style` or similar
4. **Load result** in OneMotion Chord Player

## Drake "Over" Remix Workflow

### Files Added

- `OVER_REMIX_GUIDE.md` — Complete remix strategies and examples
- `over_trap_remix.json` — Trap-style remix (65 BPM, E minor)
- `over_house_remix.json` — House-style remix (124 BPM, C major)
- `over_remix_generator.py` — Automated remix generator script

### Quick Remix Commands

**Built-in Generator:**

```bash
# Generate trap remix in E minor at 65 BPM
python over_remix_generator.py trap E 65

# Generate house remix in C major at 124 BPM
python over_remix_generator.py house C 124

# Generate drill remix in F# minor at 95 BPM
python over_remix_generator.py drill F# 95
```

**External AI Agents:**

```bash
# OpenAI GPT agent (requires API key)
python openai_agent_simple.py over.json trap E 65

# Free local LLM agent (requires Ollama)
python local_agent_simple.py over.json house C 124

# Manual ChatGPT (copy/paste workflow)
# See EXTERNAL_AGENT_SETUP.md for instructions
```

### Available Styles

- **trap** — Slower tempo, block chords, minimal arps
- **house** — 124 BPM, offbeat chords, driving bass
- **drill** — 95 BPM, stab chords, aggressive bass
- **rnb** — Original tempo, smooth arpeggios
- **ambient** — Slow tempo, sustained chords, heavy reverb

### Remix Process

1. **Choose style** from the 5 presets
2. **Pick key** (C, D, E, F#, Ab, etc.)
3. **Set tempo** (or use style default)
4. **Run generator** to create JSON file
5. **Load in OneMotion** Chord Player
6. **Export MIDI/WAV** for your DAW

## Next Steps Available

- Convert all starter cards to OneMotion format
- Generate MIDI files from melody/drum overlays
- Create DAW-ready audio stems
- Add more remix styles (afrobeat, reggaeton, etc.)

Choose your next step and the kit will generate accordingly.
