from src.kortana.services.songwriting_service import (
    analyze_lyrics,
    count_syllables_line,
    generate_structure,
    suggest_chord_progressions,
)


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
    chords = next(
        item.chords for item in suggestions if item.name == "I-V-vi-IV"
    )
    assert chords == ["C", "G", "Am", "F"]


def test_chord_progressions_minor_sad() -> None:
    suggestions = suggest_chord_progressions("A minor", mood="sad", genre="pop")
    chords = next(
        item.chords for item in suggestions if item.name == "i-VI-III-VII"
    )
    assert chords == ["Am", "F", "C", "G"]


def test_structure_defaults() -> None:
    structure = generate_structure()
    assert structure["verse"] == [8, 8, 8, 8]
    assert structure["chorus"] == [8, 8, 8, 8]
    assert structure["bridge"] == [7, 7]
