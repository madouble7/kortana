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


# ---------------------------------------------------------------------------
# Extended music theory: key-based chord analysis & named progressions
# ---------------------------------------------------------------------------

_CHROMATIC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_ENHARMONIC: dict[str, str] = {
    "Db": "C#",
    "Eb": "D#",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
}

_MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

_DEGREE_QUALITY: dict[int, str] = {
    1: "major",
    2: "minor",
    3: "minor",
    4: "major",
    5: "major",
    6: "minor",
    7: "diminished",
}

_ROMAN: dict[int, str] = {
    1: "I",
    2: "ii",
    3: "iii",
    4: "IV",
    5: "V",
    6: "vi",
    7: "vii°",
}

# Named progressions (degrees reference major key scale degrees 1-7)
COMMON_PROGRESSIONS: dict[str, dict] = {
    "I-V-vi-IV": {
        "degrees": [1, 5, 6, 4],
        "name": "Pop Progression",
        "genres": ["pop", "rock", "ballad"],
        "feel": "uplifting, anthemic",
    },
    "I-IV-V": {
        "degrees": [1, 4, 5],
        "name": "Blues / Rock",
        "genres": ["blues", "rock", "country", "gospel"],
        "feel": "driving, classic",
    },
    "I-IV-vi-V": {
        "degrees": [1, 4, 6, 5],
        "name": "Contemporary Pop",
        "genres": ["pop", "r&b"],
        "feel": "smooth, contemporary",
    },
    "vi-IV-I-V": {
        "degrees": [6, 4, 1, 5],
        "name": "Axis Progression",
        "genres": ["pop", "indie", "worship"],
        "feel": "emotional, cinematic",
    },
    "I-vi-IV-V": {
        "degrees": [1, 6, 4, 5],
        "name": "50s Doo-Wop",
        "genres": ["doo-wop", "pop", "oldies"],
        "feel": "nostalgic, romantic",
    },
    "ii-V-I": {
        "degrees": [2, 5, 1],
        "name": "Jazz Turnaround",
        "genres": ["jazz", "soul", "neo-soul"],
        "feel": "sophisticated, resolved",
    },
    "I-iii-IV-V": {
        "degrees": [1, 3, 4, 5],
        "name": "Classic Build",
        "genres": ["pop", "rock", "folk"],
        "feel": "building, energetic",
    },
    "I-IV-I-V": {
        "degrees": [1, 4, 1, 5],
        "name": "Gospel Progression",
        "genres": ["gospel", "r&b", "soul"],
        "feel": "soulful, declarative",
    },
    "I-V-vi-iii-IV": {
        "degrees": [1, 5, 6, 3, 4],
        "name": "Canon Progression",
        "genres": ["classical", "pop", "wedding"],
        "feel": "timeless, elegant",
    },
    "I-bVII-IV": {
        "degrees": [1, 7, 4],
        "name": "Mixolydian Rock",
        "genres": ["rock", "alternative"],
        "feel": "edgy, modal",
    },
    "I-IV-V-IV": {
        "degrees": [1, 4, 5, 4],
        "name": "Shuffle / Boogie",
        "genres": ["blues", "boogie", "rock-n-roll"],
        "feel": "groovy, danceable",
    },
}

SONG_STRUCTURE_TEMPLATES: dict[str, list[str]] = {
    "standard": ["verse", "chorus", "verse", "chorus", "bridge", "chorus"],
    "simple": ["verse", "chorus", "verse", "chorus"],
    "verse_heavy": ["verse", "verse", "chorus", "verse", "chorus"],
    "extended": [
        "intro",
        "verse",
        "pre-chorus",
        "chorus",
        "verse",
        "pre-chorus",
        "chorus",
        "bridge",
        "chorus",
        "outro",
    ],
    "aba": ["verse", "bridge", "verse"],
    "aaba": ["verse", "verse", "bridge", "verse"],
}


@dataclass(frozen=True)
class ChordDetail:
    degree: int
    roman: str
    root: str
    quality: str
    name: str
    notes: tuple[str, ...]


def _normalize_key(key: str) -> str:
    root = key[0].upper() + key[1:] if len(key) > 1 else key.upper()
    return _ENHARMONIC.get(root, root)


def get_chords_in_key(key: str) -> list[ChordDetail]:
    """Return all 7 diatonic triads for the given major key."""
    normalized = _normalize_key(key)
    if normalized not in _CHROMATIC:
        raise ValueError(f"Unknown key: '{key}'. Use letter names like C, D#, F#.")
    root_idx = _CHROMATIC.index(normalized)
    scale = [_CHROMATIC[(root_idx + i) % 12] for i in _MAJOR_INTERVALS]

    chords: list[ChordDetail] = []
    for i, note in enumerate(scale):
        degree = i + 1
        quality = _DEGREE_QUALITY[degree]
        ni = _CHROMATIC.index(note)
        if quality == "major":
            third = _CHROMATIC[(ni + 4) % 12]
            fifth = _CHROMATIC[(ni + 7) % 12]
        elif quality == "minor":
            third = _CHROMATIC[(ni + 3) % 12]
            fifth = _CHROMATIC[(ni + 7) % 12]
        else:  # diminished
            third = _CHROMATIC[(ni + 3) % 12]
            fifth = _CHROMATIC[(ni + 6) % 12]
        suffix = {"major": "", "minor": "m", "diminished": "dim"}[quality]
        chords.append(
            ChordDetail(
                degree=degree,
                roman=_ROMAN[degree],
                root=note,
                quality=quality,
                name=note + suffix,
                notes=(note, third, fifth),
            )
        )
    return chords


def resolve_progression_chords(key: str, degrees: list[int]) -> list[str]:
    """Translate scale degrees to chord names in key (e.g. [1,5,6,4] in C -> C,G,Am,F)."""
    chord_map = {c.degree: c for c in get_chords_in_key(key)}
    return [
        chord_map[((d - 1) % 7) + 1].name
        for d in degrees
        if ((d - 1) % 7) + 1 in chord_map
    ]


def annotate_syllables(text: str) -> list[dict]:
    """Return per-line syllable counts for multi-line text."""
    return [
        {"line": ln, "syllables": count_syllables_line(ln), "index": i}
        for i, ln in enumerate(text.strip().splitlines())
        if ln.strip()
    ]


def build_song_prompt(
    topic: str,
    genre: str,
    mood: str,
    key: str,
    progression_key: str,
    structure: str,
) -> str:
    """Build a detailed LLM prompt for full AI song generation."""
    chords = get_chords_in_key(key)
    prog_info = COMMON_PROGRESSIONS.get(progression_key, {})
    chord_names = resolve_progression_chords(
        key, prog_info.get("degrees", [1, 5, 6, 4])
    )
    sections = SONG_STRUCTURE_TEMPLATES.get(
        structure, SONG_STRUCTURE_TEMPLATES["standard"]
    )

    chord_str = " → ".join(chord_names) or progression_key
    scale_str = ", ".join(c.root for c in chords)
    sections_str = " / ".join(s.upper() for s in sections)

    return (
        f"You are an expert songwriter. Write a complete, singable song with these specs:\n\n"
        f"Topic: {topic}\n"
        f"Genre: {genre}\n"
        f"Mood: {mood}\n"
        f"Key: {key} major  (scale notes: {scale_str})\n"
        f"Chord Progression: {chord_str}  ({prog_info.get('name', progression_key)})\n"
        f"Structure: {sections_str}\n\n"
        f"Requirements:\n"
        f"- Label each section clearly (Verse 1:, Chorus:, Bridge:, etc.)\n"
        f"- Maintain a consistent rhyme scheme suited to {genre}\n"
        f"- Keep lines singable with natural syllabic phrasing\n"
        f"- Chorus must be memorable and repeat-worthy\n"
        f"- Bridge should provide harmonic or lyrical contrast\n\n"
        f"Write the full song now:"
    )
