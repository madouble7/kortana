from typing import Any

from fastapi import APIRouter, HTTPException

from src.kortana.schemas import (
    ChordAnalysisRequest,
    ChordAnalysisResponse,
    ChordDetailSchema,
    SongGenerateRequest,
    SongGenerateResponse,
    SongwritingAnalyzeRequest,
    SongwritingAnalyzeResponse,
    SongwritingLineAnalysis,
    SongwritingProgression,
    SongwritingRhymePair,
    SyllableRequest,
    SyllableResponse,
)
from src.kortana.services.songwriting_service import (
    COMMON_PROGRESSIONS,
    SONG_STRUCTURE_TEMPLATES,
    analyze_lyrics,
    annotate_syllables,
    build_song_prompt,
    count_syllables_word,
    generate_structure,
    get_chords_in_key,
    resolve_progression_chords,
    score_alignment,
    suggest_chord_progressions,
)

router = APIRouter(prefix="/api/songwriting", tags=["songwriting"])


@router.post("/analyze", response_model=SongwritingAnalyzeResponse)
async def analyze_songwriting(
    payload: SongwritingAnalyzeRequest,
) -> SongwritingAnalyzeResponse:
    if not payload.lyrics.strip():
        raise HTTPException(status_code=400, detail="Lyrics cannot be empty.")

    lines = [line for line in payload.lyrics.splitlines() if line.strip()]
    analyses, rhyme_pairs = analyze_lyrics(lines)
    rhyme_scheme = "".join([entry.rhyme_label for entry in analyses])

    structure = generate_structure()
    alignment = score_alignment(analyses, target_syllables=structure["verse"][0])
    progressions = suggest_chord_progressions(
        payload.key, mood=payload.mood, genre=payload.genre
    )

    return SongwritingAnalyzeResponse(
        rhyme_scheme=rhyme_scheme,
        lines=[
            SongwritingLineAnalysis(
                line=item.line,
                syllables=item.syllables,
                rhyme_key=item.rhyme_key,
                rhyme_label=item.rhyme_label,
            )
            for item in analyses
        ],
        rhyme_pairs=[
            SongwritingRhymePair(label=pair.label, lines=pair.lines)
            for pair in rhyme_pairs
        ],
        structure=structure,
        chord_progressions=[
            SongwritingProgression(
                name=progression.name,
                numeral_progression=progression.numeral_progression,
                chords=progression.chords,
            )
            for progression in progressions
        ],
        alignment_score=alignment,
    )


@router.get("/progressions")
async def list_progressions(genre: str | None = None) -> dict[str, Any]:
    """List all named chord progressions, optionally filtered by genre."""
    result = {}
    for key, info in COMMON_PROGRESSIONS.items():
        if genre and genre.lower() not in [g.lower() for g in info.get("genres", [])]:
            continue
        result[key] = info
    return {"progressions": result, "count": len(result)}


@router.post("/chords", response_model=ChordAnalysisResponse)
async def chord_analysis(req: ChordAnalysisRequest) -> ChordAnalysisResponse:
    """
    Return all 7 diatonic chords for a key with degree, roman numeral,
    chord name, quality, and constituent notes. Optionally resolve a named
    or custom progression to actual chord names in that key.
    """
    try:
        chords = get_chords_in_key(req.key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resolved_progression: dict[str, Any] | None = None

    if req.progression and req.progression in COMMON_PROGRESSIONS:
        prog = COMMON_PROGRESSIONS[req.progression]
        chord_names = resolve_progression_chords(req.key, prog["degrees"])
        resolved_progression = {
            "key": req.progression,
            "name": prog["name"],
            "chord_names": chord_names,
            "feel": prog.get("feel", ""),
            "genres": prog.get("genres", []),
        }
    elif req.degrees:
        chord_names = resolve_progression_chords(req.key, req.degrees)
        resolved_progression = {
            "key": "custom",
            "degrees": req.degrees,
            "chord_names": chord_names,
        }

    return ChordAnalysisResponse(
        key=req.key,
        scale=[c.root for c in chords],
        diatonic_chords=[
            ChordDetailSchema(
                degree=c.degree,
                roman=c.roman,
                root=c.root,
                quality=c.quality,
                name=c.name,
                notes=list(c.notes),
            )
            for c in chords
        ],
        progression=resolved_progression,
    )


@router.post("/syllables", response_model=SyllableResponse)
async def count_syllables_endpoint(req: SyllableRequest) -> SyllableResponse:
    """Count syllables in a single line, with per-word breakdown."""
    import re

    words = re.sub(r"[^\w\s'-]", "", req.line).split()
    word_counts = [{"word": w, "syllables": count_syllables_word(w)} for w in words]
    total = sum(wc["syllables"] for wc in word_counts)
    return SyllableResponse(
        line=req.line, syllable_count=total, word_counts=word_counts
    )


@router.post("/generate", response_model=SongGenerateResponse)
async def generate_song(req: SongGenerateRequest) -> SongGenerateResponse:
    """
    AI-generate a complete song from topic, genre, mood, key, and progression.
    Returns chord context + structure alongside AI-generated lyrics (when an AI
    provider is available) and auto-analyzed rhyme/syllable data for the result.
    """
    try:
        chords = get_chords_in_key(req.key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.progression not in COMMON_PROGRESSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown progression '{req.progression}'. "
                f"Use GET /api/songwriting/progressions for valid options."
            ),
        )

    prompt = build_song_prompt(
        topic=req.topic,
        genre=req.genre,
        mood=req.mood,
        key=req.key,
        progression_key=req.progression,
        structure=req.structure,
    )

    lyrics: str | None = None
    try:
        from src.kortana.services.multi_model_ai import ai_service

        if ai_service is not None:
            ai_service._ensure_initialized()
            lyrics = await ai_service.analyze_text(prompt)
    except Exception as exc:
        from src.kortana.logger import get_logger

        get_logger(__name__).warning("AI song generation failed: %s", exc)

    prog_info = COMMON_PROGRESSIONS[req.progression]
    chord_names = resolve_progression_chords(req.key, prog_info["degrees"])
    sections = SONG_STRUCTURE_TEMPLATES.get(
        req.structure, SONG_STRUCTURE_TEMPLATES["standard"]
    )

    analysis: dict[str, Any] | None = None
    if lyrics:
        line_data = annotate_syllables(lyrics)
        raw_lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        lyric_analyses, lyric_pairs = analyze_lyrics(raw_lines)
        analysis = {
            "rhyme_scheme": "".join(a.rhyme_label for a in lyric_analyses),
            "syllables_per_line": line_data,
            "rhyme_pairs": [{"label": p.label, "lines": p.lines} for p in lyric_pairs],
        }

    return SongGenerateResponse(
        topic=req.topic,
        genre=req.genre,
        mood=req.mood,
        key=req.key,
        progression={
            "name": prog_info["name"],
            "chords": chord_names,
            "feel": prog_info.get("feel", ""),
        },
        structure=sections,
        scale=[c.root for c in chords],
        lyrics=lyrics,
        analysis=analysis,
        note=None
        if lyrics
        else "AI service unavailable; chord and structure data returned.",
    )
