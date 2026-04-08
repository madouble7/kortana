# AI Studio Integration Point

This directory is the landing zone for logic and prompts exported from Google AI Studio.

## Standard Layout

- `prompts/`: Landing zone for .md or .txt prompt files.
- `logic/`: Python logic extracted from exported main.py.

## Merge Process

1. Export ZIP from AI Studio.
2. Place Gemini logic in `logic/`.
3. Place system instructions in `prompts/`.
4. Update `backend/src/kortana/services/gemini.py` to use these local assets.
