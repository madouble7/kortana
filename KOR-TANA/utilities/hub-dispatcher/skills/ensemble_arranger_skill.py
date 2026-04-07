from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from kortana_hub.autonomous_skill_base import AutonomousSkill


@dataclass
class ArrangementTemplate:
    name: str
    style: str
    instrumentation: List[str]
    groove: str
    dynamic_curve: List[str]
    embellishments: List[str]
    education_focus: str
    therapy_alignment: str
    default_bpm: int


class EnsembleArrangerSkill(AutonomousSkill):
    """Arrange full musical productions by weaving songwriting, vocal, therapy, and
    education signals into coordinated templates."""

    ARRANGEMENT_TEMPLATES: List[ArrangementTemplate] = [
        ArrangementTemplate(
            name="jazz_chamber_quintet",
            style="jazz",
            instrumentation=["piano", "upright bass", "brush kit", "flugelhorn", "vocals"],
            groove="laid-back swing with brushed textures",
            dynamic_curve=["intro hush", "gentle lift", "solo shimmer", "warm resolve"],
            embellishments=["extended chords", "call-and-response licks", "brush crescendos"],
            education_focus="highlight II-V-I progressions and improvisation cues",
            therapy_alignment="grounding and reflective; reduces anxiety through predictable swells",
            default_bpm=92,
        ),
        ArrangementTemplate(
            name="cinematic_stringscape",
            style="orchestral",
            instrumentation=["piano", "chamber strings", "french horns", "synth pads", "choir"],
            groove="slow-blooming cinematic pulse",
            dynamic_curve=["distant shimmer", "emergent arcs", "heroic lift", "afterglow"],
            embellishments=["swells", "counter-melodies", "tremolo beds"],
            education_focus="demonstrate layering and motif development",
            therapy_alignment="hopeful catharsis; supports grief and resilience work",
            default_bpm=72,
        ),
        ArrangementTemplate(
            name="electronic_kinetic",
            style="electronic",
            instrumentation=["synth bass", "side-chained pads", "drum machine", "arps", "processed vocals"],
            groove="steady four-on-the-floor with syncopated percussion",
            dynamic_curve=["filtered rise", "beat drop", "energy plateau", "gradient fade"],
            embellishments=["stutter edits", "pitch-shifted doubles", "granular swells"],
            education_focus="illustrate arrangement automation and texture changes",
            therapy_alignment="energising focus; supports motivation and activation",
            default_bpm=124,
        ),
        ArrangementTemplate(
            name="world_rhythm_collective",
            style="world",
            instrumentation=["djembe ensemble", "nylon guitar", "woodwinds", "kalimba", "group vocals"],
            groove="polyrhythmic 6/8 with layered percussion",
            dynamic_curve=["call intro", "community chant", "percussive bloom", "breathing coda"],
            embellishments=["cross-rhythms", "unison shouts", "mallet ostinatos"],
            education_focus="teach polyrhythms and call-and-response phrasing",
            therapy_alignment="collective uplift; builds connection and trust",
            default_bpm=96,
        ),
        ArrangementTemplate(
            name="calming_binaural_suite",
            style="therapeutic",
            instrumentation=["soft piano", "glass harmonics", "sub bass drones", "field recordings", "vocal hums"],
            groove="minimal pulse with asymmetric breathing phrasing",
            dynamic_curve=["slow inhale", "weightless sustain", "release wash", "resting silence"],
            embellishments=["binaural beat layers", "harmonic overtones", "filtered ambience"],
            education_focus="demonstrate soundscape storytelling and mindful pacing",
            therapy_alignment="deep relaxation; supports anxiety and sleep protocols",
            default_bpm=60,
        ),
        ArrangementTemplate(
            name="adventure_learning_band",
            style="education",
            instrumentation=["acoustic guitar", "handclaps", "ukulele", "toy percussion", "call-out vocals"],
            groove="bouncey 4/4 with educational cues",
            dynamic_curve=["curious spark", "playful climb", "challenge break", "celebration"],
            embellishments=["mnemonic chants", "instrument spotlights", "question prompts"],
            education_focus="reinforce lesson objectives with repetition and movement",
            therapy_alignment="confidence building; ideal for children’s growth milestones",
            default_bpm=110,
        ),
    ]

    def __init__(self) -> None:
        self.completed_arrangements: int = 0
        self._history: List[Dict[str, Any]] = []
        self._last_template: str | None = None
        self._last_status_emit: datetime | None = None

    def can_handle(self, intent: str, data: Dict[str, Any] | None = None) -> bool:
        intent = intent.lower()
        return intent in {
            "arrange_song",
            "arranger_status",
            "list_arrangement_templates",
        }

    def handle(self, intent: str, data: Dict[str, Any] | None = None) -> str:
        data = data or {}
        intent = intent.lower()

        if intent == "list_arrangement_templates":
            names = ", ".join(t.name for t in self.ARRANGEMENT_TEMPLATES)
            return f"Available ensemble templates: {names}"

        if intent == "arranger_status":
            return self._format_status()

        if intent == "arrange_song":
            arrangement = self._build_arrangement_plan(data)
            self.completed_arrangements += 1
            self._last_template = arrangement["template"]["name"]
            self._history.append(
                {
                    "timestamp": arrangement["timestamp"],
                    "title": arrangement["title"],
                    "template": arrangement["template"]["name"],
                    "emotion": arrangement["emotion"]["profile"],
                    "education_level": arrangement["education"]["level"],
                }
            )

            memory = data.get("memory")
            if memory and hasattr(memory, "add_note"):
                memory_note = {
                    "kind": "arrangement_plan",
                    "title": arrangement["title"],
                    "template": arrangement["template"]["name"],
                    "sections": arrangement["sections"],
                    "recommended_bpm": arrangement["tempo_bpm"],
                    "mix_notes": arrangement["mix_notes"],
                }
                try:
                    memory.add_note(
                        text=json.dumps(memory_note, ensure_ascii=False),
                        source="ensemble_arranger_skill",
                    )
                except Exception:
                    pass

            summary = [
                f"Ensemble arrangement created for '{arrangement['title']}'",
                f"Template: {arrangement['template']['name']} ({arrangement['template']['style']})",
                f"Instrumentation: {', '.join(arrangement['template']['instrumentation'])}",
                f"Sections: {', '.join(section['name'] for section in arrangement['sections'])}",
                f"Emotion focus: {arrangement['emotion']['profile']} @ intensity {arrangement['emotion']['intensity']}",
                f"Recommended BPM: {arrangement['tempo_bpm']}",
                f"Vocal plan: {arrangement['vocal_plan']['approach']}",
            ]
            return "\n".join(summary)

        return "Ensemble arranger received an unknown intent."

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        """Emit periodic status updates so the audit trail shows arranger activity."""
        interval_minutes = int(config.get("ensemble_arranger_status_minutes", 30))
        now = datetime.utcnow()
        if (
            self._last_status_emit
            and now - self._last_status_emit < timedelta(minutes=interval_minutes)
        ):
            return

        status_note = {
            "kind": "ensemble_arranger_status",
            "completed": self.completed_arrangements,
            "last_template": self._last_template,
            "timestamp": now.isoformat(),
        }
        try:
            memory.add_note(
                text=json.dumps(status_note, ensure_ascii=False),
                source="ensemble_arranger_skill",
            )
        except Exception:
            pass
        self._last_status_emit = now

    def _format_status(self) -> str:
        last = self._history[-1] if self._history else None
        lines = [
            f"Arrangements completed: {self.completed_arrangements}",
            f"Last template: {self._last_template or 'n/a'}",
        ]
        if last:
            lines.extend(
                [
                    f"Last title: {last['title']}",
                    f"Last emotion: {last['emotion']}",
                    f"Last education level: {last['education_level']}",
                ]
            )
        return "\n".join(lines)

    def _build_arrangement_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = payload.get("title") or payload.get("lyrics", {}).get("title") or "Untitled Collaboration"
        emotion_profile = self._extract_emotion(payload)
        education_profile = self._extract_education(payload)
        therapy_focus = (payload.get("therapy") or {}).get("focus", "general_support")
        preferred_style = payload.get("style") or payload.get("vocal", {}).get("style_hint")

        template = self._choose_template(emotion_profile, education_profile, therapy_focus, preferred_style)

        sections = self._design_sections(template, payload)
        mix_notes = self._generate_mix_notes(template, payload)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "title": title,
            "template": {
                "name": template.name,
                "style": template.style,
                "instrumentation": template.instrumentation,
            },
            "tempo_bpm": payload.get("tempo_bpm") or template.default_bpm,
            "emotion": emotion_profile,
            "education": education_profile,
            "therapy": {"focus": therapy_focus},
            "sections": sections,
            "vocal_plan": self._vocal_plan(payload, template),
            "mix_notes": mix_notes,
        }

    def _choose_template(
        self,
        emotion: Dict[str, Any],
        education: Dict[str, Any],
        therapy_focus: str,
        preferred_style: str | None,
    ) -> ArrangementTemplate:
        if therapy_focus in {"sleep_support", "deep_relaxation"}:
            return self._template_by_name("calming_binaural_suite")
        if therapy_focus in {"confidence", "motivation"}:
            return self._template_by_name("electronic_kinetic")
        if education["level"] in {"early_childhood", "foundations"}:
            return self._template_by_name("adventure_learning_band")
        if preferred_style:
            for template in self.ARRANGEMENT_TEMPLATES:
                if template.style == preferred_style.lower() or template.name == preferred_style:
                    return template
        if emotion["profile"] in {"nostalgic", "romantic"}:
            return self._template_by_name("jazz_chamber_quintet")
        if emotion["profile"] in {"epic", "heroic"}:
            return self._template_by_name("cinematic_stringscape")
        return self.ARRANGEMENT_TEMPLATES[0]

    def _template_by_name(self, name: str) -> ArrangementTemplate:
        for template in self.ARRANGEMENT_TEMPLATES:
            if template.name == name:
                return template
        return self.ARRANGEMENT_TEMPLATES[0]

    def _extract_emotion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        emotion = payload.get("emotion") or {}
        profile = emotion.get("profile") or emotion.get("tone") or "uplifting"
        intensity = emotion.get("intensity") or 0.7
        color = emotion.get("color") or "saffron"
        return {"profile": profile, "intensity": float(intensity), "color": color}

    def _extract_education(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        education = payload.get("education") or payload.get("education_profile") or {}
        level = education.get("level") or "intermediate"
        focus = education.get("focus") or ["arrangement awareness"]
        if isinstance(focus, str):
            focus = [focus]
        return {"level": level, "focus": focus}

    def _design_sections(self, template: ArrangementTemplate, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        lyrical_structure = (payload.get("lyrics") or {}).get("structure") or ["verse", "chorus", "bridge"]
        sections: List[Dict[str, Any]] = []
        for index, name in enumerate(lyrical_structure):
            energy = self._section_energy(index, len(lyrical_structure), template)
            sections.append(
                {
                    "name": name.title(),
                    "energy": energy,
                    "lead_instrument": template.instrumentation[min(index, len(template.instrumentation) - 1)],
                    "arranger_notes": self._section_note(name, template),
                }
            )
        return sections

    def _section_energy(self, index: int, total: int, template: ArrangementTemplate) -> str:
        curve = template.dynamic_curve
        if index < len(curve):
            return curve[index]
        return curve[-1] if curve else "steady"

    def _section_note(self, section_name: str, template: ArrangementTemplate) -> str:
        lower = section_name.lower()
        if any(key in lower for key in ("verse", "story", "lesson")):
            return f"Spotlight lyrics with {template.instrumentation[0]} supporting and gentle pads."
        if any(key in lower for key in ("chorus", "hook", "anthem")):
            return f"Stack vocals and widen panorama; add embellishments: {template.embellishments[:2]}."
        if any(key in lower for key in ("bridge", "break", "solo")):
            return f"Introduce contrast using {template.embellishments[-1]}."
        return f"Maintain motif with subtle ornamentation from {template.instrumentation[-1]}."

    def _vocal_plan(self, payload: Dict[str, Any], template: ArrangementTemplate) -> Dict[str, Any]:
        vocal = payload.get("vocal") or {}
        character = vocal.get("profile") or template.style
        approach = vocal.get("approach") or f"Blend lead vocal with {template.style} phrasing."
        harmony = vocal.get("harmonies") or ["thirds", "fifths"] if template.style != "therapeutic" else ["octave humming"]
        return {
            "profile": character,
            "approach": approach,
            "harmonies": harmony,
            "double_tracking": template.style in {"electronic", "orchestral"},
        }

    def _generate_mix_notes(self, template: ArrangementTemplate, payload: Dict[str, Any]) -> List[str]:
        notes = [
            f"Balance dynamics to follow curve: {', '.join(template.dynamic_curve)}",
            f"Feature instrumentation layers: {', '.join(template.instrumentation)}",
        ]
        therapy_focus = (payload.get("therapy") or {}).get("focus")
        if therapy_focus in {"sleep_support", "deep_relaxation"}:
            notes.append("Ensure low-frequency energy remains below 60Hz for calming effect.")
        if (payload.get("education") or payload.get("education_profile")):
            notes.append("Annotate arrangement steps for educational replay.")
        emotion = self._extract_emotion(payload)
        if emotion["profile"] in {"epic", "heroic"}:
            notes.append("Automate brass/pad swells to mirror hero arc.")
        return notes
