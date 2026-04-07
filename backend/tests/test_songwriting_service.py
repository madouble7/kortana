import pytest
from src.kortana.services.songwriting_service import (
    COMMON_PROGRESSIONS,
    SONG_STRUCTURE_TEMPLATES,
    analyze_lyrics,
    annotate_syllables,
    build_song_prompt,
    count_syllables_line,
    count_syllables_word,
    generate_structure,
    get_chords_in_key,
    resolve_progression_chords,
    suggest_chord_progressions,
)

# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------


def test_syllable_count_simple() -> None:
    assert count_syllables_line("hello world") == 3


def test_rhyme_scheme_detection() -> None:
    lines = ["I see the light", "You see the night", "We walk away"]
    analyses, rhyme_pairs = analyze_lyrics(lines)
    scheme = "".join([entry.rhyme_label for entry in analyses])
    assert scheme == "AAB"
    assert any(pair.label == "A" and pair.lines == [0, 1] for pair in rhyme_pairs)


def test_chord_progressions_major_pop() -> None:
    suggestions = suggest_chord_progressions("C", mood="neutral", genre="pop")
    chords = next(item.chords for item in suggestions if item.name == "I-V-vi-IV")
    assert chords == ["C", "G", "Am", "F"]


def test_chord_progressions_minor_sad() -> None:
    suggestions = suggest_chord_progressions("A minor", mood="sad", genre="pop")
    chords = next(item.chords for item in suggestions if item.name == "i-VI-III-VII")
    assert chords == ["Am", "F", "C", "G"]


def test_structure_defaults() -> None:
    structure = generate_structure()
    assert structure["verse"] == [8, 8, 8, 8]
    assert structure["chorus"] == [8, 8, 8, 8]
    assert structure["bridge"] == [7, 7]


# ---------------------------------------------------------------------------
# Extended: syllable counting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word,expected",
    [
        ("hello", 2),
        ("world", 1),
        ("beautiful", 3),  # algorithm: vowel groups beau/ti/u = 3
        ("fire", 1),  # silent -e subtracted
        ("table", 3),  # -le rule adds 1 to 2 vowel groups
        ("talked", 2),  # -ed ending doesn't reduce (consonant cluster)
        ("running", 2),
        ("I", 1),
        ("a", 1),
    ],
)
def test_count_syllables_word(word: str, expected: int) -> None:
    assert count_syllables_word(word) == expected


def test_count_syllables_line_multiword() -> None:
    # algorithm: somewhere=3, over=2, the=1, rainbow=2 = 8
    assert count_syllables_line("somewhere over the rainbow") == 8


def test_annotate_syllables_multiline() -> None:
    text = "I see the light\nYou see the night\nWe walk away"
    result = annotate_syllables(text)
    assert len(result) == 3
    assert result[0]["syllables"] == 4
    assert (
        result[2]["syllables"] == 4
    )  # we(1)+walk(1)+away(2)=4 by vowel-group algorithm


# ---------------------------------------------------------------------------
# Extended: key-based chord theory
# ---------------------------------------------------------------------------


def test_get_chords_in_key_c_major() -> None:
    chords = get_chords_in_key("C")
    names = [c.name for c in chords]
    assert names == ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]


def test_get_chords_in_key_g_major() -> None:
    chords = get_chords_in_key("G")
    names = [c.name for c in chords]
    assert names == ["G", "Am", "Bm", "C", "D", "Em", "F#dim"]


def test_get_chords_in_key_degrees() -> None:
    chords = get_chords_in_key("C")
    assert chords[0].roman == "I"
    assert chords[1].roman == "ii"
    assert chords[4].roman == "V"
    assert chords[5].roman == "vi"


def test_get_chords_in_key_notes() -> None:
    chords = get_chords_in_key("C")
    c_chord = chords[0]
    assert c_chord.notes == ("C", "E", "G")


def test_get_chords_invalid_key() -> None:
    with pytest.raises(ValueError, match="Unknown key"):
        get_chords_in_key("H")


def test_resolve_progression_chords_c_major() -> None:
    result = resolve_progression_chords("C", [1, 5, 6, 4])
    assert result == ["C", "G", "Am", "F"]


def test_resolve_progression_chords_g_major() -> None:
    result = resolve_progression_chords("G", [1, 4, 5])
    assert result == ["G", "C", "D"]


# ---------------------------------------------------------------------------
# Extended: COMMON_PROGRESSIONS and SONG_STRUCTURE_TEMPLATES
# ---------------------------------------------------------------------------


def test_common_progressions_contains_pop() -> None:
    assert "I-V-vi-IV" in COMMON_PROGRESSIONS
    prog = COMMON_PROGRESSIONS["I-V-vi-IV"]
    assert prog["degrees"] == [1, 5, 6, 4]
    assert "pop" in prog["genres"]


def test_common_progressions_jazz_turnaround() -> None:
    prog = COMMON_PROGRESSIONS["ii-V-I"]
    chords = resolve_progression_chords("C", prog["degrees"])
    assert chords == ["Dm", "G", "C"]


def test_song_structure_templates_standard() -> None:
    sections = SONG_STRUCTURE_TEMPLATES["standard"]
    assert "verse" in sections
    assert "chorus" in sections
    assert "bridge" in sections


def test_song_structure_templates_extended() -> None:
    sections = SONG_STRUCTURE_TEMPLATES["extended"]
    assert sections.count("chorus") >= 2


# ---------------------------------------------------------------------------
# Extended: build_song_prompt
# ---------------------------------------------------------------------------


def test_build_song_prompt_contains_key_info() -> None:
    prompt = build_song_prompt(
        topic="hope",
        genre="gospel",
        mood="uplifting",
        key="C",
        progression_key="I-V-vi-IV",
        structure="standard",
    )
    assert "C" in prompt
    assert "gospel" in prompt
    assert "hope" in prompt
    assert "C → G → Am → F" in prompt
    assert "VERSE" in prompt
    assert "CHORUS" in prompt


def test_build_song_prompt_unknown_progression_falls_back() -> None:
    # Should not raise even for unknown progression key
    prompt = build_song_prompt(
        topic="test",
        genre="pop",
        mood="neutral",
        key="G",
        progression_key="unknown-key",
        structure="simple",
    )
    assert "test" in prompt
    assert "G" in prompt
