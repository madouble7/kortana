# OneMotion Melody System - Exploration Guide

## Current Status

All progression files currently have empty melody arrays:

```json
"melody": { "events": [] }
```

## What We Need to Figure Out

### Melody Event Structure

Based on the OneMotion Chord Player interface, melodies likely use a similar event-based system to bass and chord arpeggios. We need to determine:

1. **Note Specification**
   - How are melody notes defined? (scale degree? MIDI note? relative to chord?)
   - Example possibilities:

     ```json
     {
       "note": 0,           // scale degree (0-based)?
       "time": 0,           // beat position in sequence
       "duration": 1,       // note length
       "velocity": 0.8      // volume
     }
     ```

2. **Timing System**
   - How does timing work relative to chord changes?
   - Is it beat-based or step-based like arpeggios?

3. **Pitch System**
   - Relative to current chord root?
   - Relative to scale?
   - Absolute MIDI notes?

4. **Octave Control**
   - Is there an octave parameter?
   - Default melody octave range?

## Hypothesis: Melody Event Structure

Based on patterns from bass/chord arpEvents, melody events might look like:

```json
"melody": {
  "events": [
    {
      "beat": 0,           // position in sequence (in beats)
      "note": 0,           // scale degree or chord tone
      "duration": 2,       // length in beats
      "velocity": 0.8,     // volume (0-1)
      "octave": 5          // optional octave specification
    },
    {
      "beat": 2,
      "note": 2,
      "duration": 1,
      "velocity": 0.75,
      "octave": 5
    }
  ],
  "octave": 5,            // default melody octave?
  "velocity": 0.8,        // default velocity?
  "style": "legato"       // articulation?
}
```

## Alternative Hypothesis: Grid-Based System

Melodies might use a step-based grid like arpeggios:

```json
"melody": {
  "events": {
    "0": { "note": 0, "velocity": 0.8 },
    "4": { "note": 2, "velocity": 0.8 },
    "8": { "note": 4, "velocity": 0.8 }
  },
  "step": [1, 8],         // timing resolution
  "octave": 5,
  "noteDuration": 1
}
```

## Testing Strategy

To discover the actual melody format:

1. **Try exporting from OneMotion** - Create a progression with melody in the app, export JSON, examine structure
2. **Test simple melody** - Add a single note and see if it plays
3. **Iterate** - Build understanding of note system, timing, octaves

## Questions for Testing

- [ ] What note value represents middle C?
- [ ] Are notes relative to chord root or scale root?
- [ ] What's the timing resolution? (beats, steps, milliseconds?)
- [ ] Can melodies overlap chord boundaries?
- [ ] Is there sustain/legato control?
- [ ] How does velocity work?
- [ ] Can you specify articulation?

## Next Steps

1. **Create a melody in OneMotion UI** - Use the app to add a simple melody
2. **Export and analyze** - Look at the JSON structure
3. **Document the format** - Update this guide with findings
4. **Create melody builder tool** - Make it easy to add melodies to progressions

---

**Status**: 🔍 **Discovery Phase** - Need actual OneMotion melody examples to reverse-engineer the format

**Last Updated**: October 12, 2025
