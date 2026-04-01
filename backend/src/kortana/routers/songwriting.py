from fastapi import APIRouter, HTTPException

from src.kortana.schemas import (
    SongwritingAnalyzeRequest,
    SongwritingAnalyzeResponse,
    SongwritingLineAnalysis,
    SongwritingProgression,
    SongwritingRhymePair,
)
from src.kortana.services.songwriting_service import (
    analyze_lyrics,
    generate_structure,
    score_alignment,
    suggest_chord_progressions,
)

router = APIRouter(prefix="/api/songwriting", tags=["songwriting"])


@router.post("/analyze", response_model=SongwritingAnalyzeResponse)
async def analyze_songwriting(payload: SongwritingAnalyzeRequest) -> SongwritingAnalyzeResponse:
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
