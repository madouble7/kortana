import re
from dataclasses import dataclass
from typing import Iterable


_VOWELS = "aeiouy"
_WORD_RE = re.compile(r"[A-Za-z']+")


@dataclass(frozen=True)
class LineAnalysis:
    line: str
    syllables: int
    rhyme_key: str
    rhyme_label: str


@dataclass(frozen=True)
class RhymePair:
    label: str
    lines: list[int]


@dataclass(frozen=True)
class ProgressionSuggestion:
    name: str
    numeral_progression: list[str]
    chords: list[str]


def analyze_lyrics(lines: Iterable[str]) -> tuple[list[LineAnalysis], list[RhymePair]]:
    line_items = [line.rstrip("\n") for line in lines if line.strip()]
    rhyme_labels: dict[str, str] = {}
    label_iter = (chr(c) for c in range(ord("A"), ord("Z") + 1))
    analyses: list[LineAnalysis] = []

    for idx, line in enumerate(line_items):
        syllables = count_syllables_line(line)
        rhyme_key = extract_rhyme_key(line)
        if rhyme_key not in rhyme_labels:
            rhyme_labels[rhyme_key] = next(label_iter)
        analyses.append(
            LineAnalysis(
                line=line,
                syllables=syllables,
                rhyme_key=rhyme_key,
                rhyme_label=rhyme_labels[rhyme_key],
            )
        )

    pairs: dict[str, list[int]] = {}
    for idx, analysis in enumerate(analyses):
        pairs.setdefault(analysis.rhyme_label, []).append(idx)

    rhyme_pairs = [
        RhymePair(label=label, lines=line_indexes)
        for label, line_indexes in pairs.items()
        if len(line_indexes) > 1
    ]
    return analyses, rhyme_pairs


def count_syllables_line(line: str) -> int:
    words = _WORD_RE.findall(line.lower())
    return sum(count_syllables_word(word) for word in words)


def count_syllables_word(word: str) -> int:
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if not cleaned:
        return 0

    groups = _vowel_groups(cleaned)
    syllables = max(1, len(groups))

    if cleaned.endswith("e") and not cleaned.endswith("le") and syllables > 1:
        syllables -= 1

    if cleaned.endswith("le") and len(cleaned) > 2:
        if cleaned[-3] not in _VOWELS:
            syllables += 1

    return max(1, syllables)


def extract_rhyme_key(line: str) -> str:
    words = _WORD_RE.findall(line.lower())
    if not words:
        return ""
    last_word = re.sub(r"[^a-z]", "", words[-1])
    return rhyme_key_for_word(last_word)


def rhyme_key_for_word(word: str) -> str:
    if not word:
        return ""
    last_vowel_index = -1
    for idx in range(len(word) - 1, -1, -1):
        if word[idx] in _VOWELS:
            last_vowel_index = idx
            break
    if last_vowel_index == -1:
        return word
    return word[last_vowel_index:]


def suggest_chord_progressions(
    key: str, *, mood: str = "neutral", genre: str = "pop"
) -> list[ProgressionSuggestion]:
    root, is_minor = _parse_key(key)
    progressions = _progression_bank(mood=mood, genre=genre, is_minor=is_minor)
    suggestions: list[ProgressionSuggestion] = []

    for name, numerals in progressions:
        chords = [_numeral_to_chord(numeral, root, is_minor) for numeral in numerals]
        suggestions.append(
            ProgressionSuggestion(
                name=name,
                numeral_progression=numerals,
                chords=chords,
            )
        )
    return suggestions


def generate_structure(
    *, verse_lines: int = 4, chorus_lines: int = 4, bridge_lines: int = 2
) -> dict[str, list[int]]:
    return {
        "verse": [8] * verse_lines,
        "chorus": [8] * chorus_lines,
        "bridge": [7] * bridge_lines,
    }


def score_alignment(
    analyses: list[LineAnalysis], *, target_syllables: int = 8
) -> dict[str, float]:
    if not analyses:
        return {"syllable_score": 0.0, "rhyme_score": 0.0}

    syllable_deltas = [abs(a.syllables - target_syllables) for a in analyses]
    syllable_score = max(0.0, 1.0 - (sum(syllable_deltas) / (len(analyses) * 10)))

    unique_labels = {a.rhyme_label for a in analyses}
    rhyme_score = 1.0 if len(unique_labels) <= len(analyses) else 0.0

    return {
        "syllable_score": round(syllable_score, 3),
        "rhyme_score": round(rhyme_score, 3),
    }


def _vowel_groups(word: str) -> list[str]:
    groups = []
    current = ""
    for ch in word:
        if ch in _VOWELS:
            current += ch
        else:
            if current:
                groups.append(current)
                current = ""
    if current:
        groups.append(current)
    return groups


def _parse_key(key: str) -> tuple[str, bool]:
    normalized = key.strip().lower()
    is_minor = "minor" in normalized or normalized.endswith("m")
    root = normalized.replace("major", "").replace("minor", "").strip()
    root = root[:-1] if root.endswith("m") else root
    root = root.strip().upper()
    if len(root) > 1:
        root = root[0] + root[1:].replace("B", "b").replace("#", "#")
    return root or "C", is_minor


def _progression_bank(
    *, mood: str, genre: str, is_minor: bool
) -> list[tuple[str, list[str]]]:
    mood_key = mood.lower()
    genre_key = genre.lower()

    if is_minor:
        if mood_key in {"sad", "dark"}:
            return [
                ("i-VI-III-VII", ["i", "VI", "III", "VII"]),
                ("i-iv-VII-III", ["i", "iv", "VII", "III"]),
            ]
        return [
            ("i-VI-III-VII", ["i", "VI", "III", "VII"]),
            ("i-iv-v-i", ["i", "iv", "v", "i"]),
        ]

    if genre_key in {"pop", "rock"}:
        return [
            ("I-V-vi-IV", ["I", "V", "vi", "IV"]),
            ("I-vi-IV-V", ["I", "vi", "IV", "V"]),
        ]

    if mood_key in {"sad", "melancholy"}:
        return [
            ("vi-IV-I-V", ["vi", "IV", "I", "V"]),
            ("I-V-vi-iii", ["I", "V", "vi", "iii"]),
        ]

    return [
        ("I-IV-V-I", ["I", "IV", "V", "I"]),
        ("I-ii-IV-V", ["I", "ii", "IV", "V"]),
    ]


def _numeral_to_chord(numeral: str, root: str, is_minor: bool) -> str:
    scale = _major_scale(root) if not is_minor else _minor_scale(root)
    degree_map = {
        "I": 0,
        "ii": 1,
        "III": 2,
        "iii": 2,
        "IV": 3,
        "iv": 3,
        "V": 4,
        "v": 4,
        "VI": 5,
        "vi": 5,
        "VII": 6,
        "vii": 6,
    }
    idx = degree_map.get(numeral, 0)
    note = scale[idx]

    if numeral.islower() or numeral in {"ii", "iii", "iv", "v", "vi"}:
        return f"{note}m"
    return note


def _major_scale(root: str) -> list[str]:
    chroma = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    steps = [0, 2, 4, 5, 7, 9, 11]
    root = root or "C"
    root_index = chroma.index(root) if root in chroma else 0
    return [chroma[(root_index + step) % 12] for step in steps]


def _minor_scale(root: str) -> list[str]:
    chroma = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    steps = [0, 2, 3, 5, 7, 8, 10]
    root = root or "A"
    root_index = chroma.index(root) if root in chroma else 0
    return [chroma[(root_index + step) % 12] for step in steps]
