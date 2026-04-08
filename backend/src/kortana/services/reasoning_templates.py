"""V24D — reasoning templates: structured justification for constitutional decisions."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReasoningSection(Enum):
    """Standard sections in a published reasoning."""

    FINDINGS_OF_FACT = "findings_of_fact"
    LEGAL_BASIS = "legal_basis"
    ANALYSIS = "analysis"
    CONCLUSION = "conclusion"
    CONDITIONS = "conditions"
    DISSENT = "dissent"


@dataclass
class ReasoningTemplate:
    """Template defining required sections for a decision type."""

    template_id: str
    decision_type: str
    required_sections: list[ReasoningSection]
    optional_sections: list[ReasoningSection] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "decision_type": self.decision_type,
            "required_sections": [s.value for s in self.required_sections],
            "optional_sections": [s.value for s in self.optional_sections],
            "description": self.description,
        }


@dataclass
class PublishedReasoning:
    """A published reasoning document for a constitutional decision."""

    reasoning_id: str
    reference_id: str
    decision_type: str
    sections: dict[str, str]
    cited_articles: list[str] = field(default_factory=list)
    cited_precedents: list[str] = field(default_factory=list)
    author: str = ""
    published_at: str = ""
    reasoning_hash: str = ""

    def __post_init__(self) -> None:
        if not self.published_at:
            self.published_at = datetime.now(timezone.utc).isoformat()
        if not self.reasoning_hash:
            blob = f"{self.reasoning_id}:{self.reference_id}:{self.decision_type}:{self.author}"
            self.reasoning_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning_id": self.reasoning_id,
            "reference_id": self.reference_id,
            "decision_type": self.decision_type,
            "sections": self.sections,
            "cited_articles": self.cited_articles,
            "cited_precedents": self.cited_precedents,
            "author": self.author,
            "published_at": self.published_at,
            "reasoning_hash": self.reasoning_hash,
        }


@dataclass
class ValidationResult:
    """Result of validating a reasoning against its template."""

    valid: bool
    missing_sections: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: str = ""

    def __post_init__(self) -> None:
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "missing_sections": self.missing_sections,
            "warnings": self.warnings,
            "checked_at": self.checked_at,
        }


def _default_templates() -> list[ReasoningTemplate]:
    """Default reasoning templates for constitutional decisions."""
    return [
        ReasoningTemplate(
            template_id="rt-001",
            decision_type="appeal_decision",
            required_sections=[
                ReasoningSection.FINDINGS_OF_FACT,
                ReasoningSection.LEGAL_BASIS,
                ReasoningSection.ANALYSIS,
                ReasoningSection.CONCLUSION,
            ],
            optional_sections=[ReasoningSection.CONDITIONS, ReasoningSection.DISSENT],
            description="Template for appeal decisions — full legal reasoning required",
        ),
        ReasoningTemplate(
            template_id="rt-002",
            decision_type="waiver_decision",
            required_sections=[
                ReasoningSection.FINDINGS_OF_FACT,
                ReasoningSection.ANALYSIS,
                ReasoningSection.CONCLUSION,
                ReasoningSection.CONDITIONS,
            ],
            optional_sections=[ReasoningSection.LEGAL_BASIS, ReasoningSection.DISSENT],
            description="Template for waiver decisions — conditions are mandatory",
        ),
        ReasoningTemplate(
            template_id="rt-003",
            decision_type="emergency_review",
            required_sections=[
                ReasoningSection.FINDINGS_OF_FACT,
                ReasoningSection.ANALYSIS,
                ReasoningSection.CONCLUSION,
            ],
            optional_sections=[
                ReasoningSection.CONDITIONS,
                ReasoningSection.LEGAL_BASIS,
            ],
            description="Template for post-emergency reviews",
        ),
    ]


class ReasoningRegistry:
    """Manages reasoning templates and published reasoning documents."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._templates: list[ReasoningTemplate] = []
        self._published: list[PublishedReasoning] = []
        if load_defaults:
            self._templates = _default_templates()

    def add_template(self, template: ReasoningTemplate) -> None:
        """Add or replace a reasoning template."""
        self._templates = [t for t in self._templates if t.decision_type != template.decision_type]
        self._templates.append(template)

    def get_template(self, decision_type: str) -> ReasoningTemplate | None:
        for t in self._templates:
            if t.decision_type == decision_type:
                return t
        return None

    def publish(
        self,
        reference_id: str,
        decision_type: str,
        sections: dict[str, str],
        cited_articles: list[str] | None = None,
        cited_precedents: list[str] | None = None,
        author: str = "",
    ) -> PublishedReasoning:
        """Publish a reasoning document."""
        reasoning = PublishedReasoning(
            reasoning_id=f"rsn-{uuid.uuid4().hex[:12]}",
            reference_id=reference_id,
            decision_type=decision_type,
            sections=sections,
            cited_articles=cited_articles or [],
            cited_precedents=cited_precedents or [],
            author=author,
        )
        self._published.append(reasoning)
        return reasoning

    def validate(self, reasoning: PublishedReasoning) -> ValidationResult:
        """Validate a reasoning document against its template."""
        template = self.get_template(reasoning.decision_type)
        if template is None:
            return ValidationResult(
                valid=True,
                warnings=[f"No template found for decision type '{reasoning.decision_type}' — skipping validation"],
            )

        missing: list[str] = []
        warnings: list[str] = []

        for section in template.required_sections:
            if section.value not in reasoning.sections:
                missing.append(section.value)
            elif not reasoning.sections[section.value].strip():
                missing.append(section.value)

        if not reasoning.cited_articles:
            warnings.append("No constitutional articles cited")
        if not reasoning.author:
            warnings.append("No author specified")

        return ValidationResult(
            valid=len(missing) == 0,
            missing_sections=missing,
            warnings=warnings,
        )

    def get_published(
        self,
        reference_id: str | None = None,
        decision_type: str | None = None,
        author: str | None = None,
    ) -> list[PublishedReasoning]:
        result = list(self._published)
        if reference_id is not None:
            result = [r for r in result if r.reference_id == reference_id]
        if decision_type is not None:
            result = [r for r in result if r.decision_type == decision_type]
        if author is not None:
            result = [r for r in result if r.author == author]
        return result

    def get_reasoning(self, reasoning_id: str) -> PublishedReasoning | None:
        for r in self._published:
            if r.reasoning_id == reasoning_id:
                return r
        return None

    @property
    def template_count(self) -> int:
        return len(self._templates)

    @property
    def published_count(self) -> int:
        return len(self._published)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for r in self._published:
            by_type[r.decision_type] = by_type.get(r.decision_type, 0) + 1
        return {
            "total_templates": len(self._templates),
            "total_published": len(self._published),
            "by_decision_type": by_type,
        }


_registry: ReasoningRegistry | None = None


def get_reasoning_registry() -> ReasoningRegistry:
    """Module singleton."""
    global _registry
    if _registry is None:
        _registry = ReasoningRegistry()
    return _registry
