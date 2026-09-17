"""Validation of normalized documents: completeness, taxonomy, length, sections."""

from __future__ import annotations

from dataclasses import dataclass, field

MIN_CONTENT_LENGTH = 60
REQUIRED_SECTIONS_MIN = 1  # at least one non-trivial paragraph


@dataclass
class ValidationIssue:
    doc_id: str
    code: str
    message: str
    level: str = "error"  # error | warning


@dataclass
class ValidationReport:
    doc_id: str
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "valid": self.valid,
            "errors": [vars(i) for i in self.errors],
            "warnings": [vars(i) for i in self.warnings],
        }


class DocumentValidator:
    """Verify metadata completeness, duplicate ids, taxonomy, length, language."""

    def __init__(self, allowed_categories: set[str] | None = None,
                 min_length: int = MIN_CONTENT_LENGTH,
                 supported_languages: set[str] | None = None):
        self.allowed_categories = allowed_categories  # None = any non-empty
        self.min_length = min_length
        self.supported_languages = supported_languages or {"en", "unknown"}
        self._seen_ids: set[str] = set()

    def reset(self) -> None:
        self._seen_ids.clear()

    def validate(self, doc_id: str, title: str, text: str, metadata: dict) -> ValidationReport:
        issues: list[ValidationIssue] = []

        def err(code: str, message: str):
            issues.append(ValidationIssue(doc_id, code, message, "error"))

        def warn(code: str, message: str):
            issues.append(ValidationIssue(doc_id, code, message, "warning"))

        if not title or not title.strip():
            err("metadata/title", "title is missing")
        if not metadata.get("source"):
            err("metadata/source", "source is missing")
        if not metadata.get("category"):
            err("metadata/category", "category is missing")
        elif self.allowed_categories is not None and metadata["category"] not in self.allowed_categories:
            err("taxonomy/category", f"unknown category '{metadata['category']}'")
        if doc_id in self._seen_ids:
            err("duplicate/id", f"duplicate document id '{doc_id}'")
        else:
            self._seen_ids.add(doc_id)
        if len(text.strip()) < self.min_length:
            err("content/length", f"content too short ({len(text.strip())} < {self.min_length})")
        language = str(metadata.get("language", "en")).lower()
        if language not in self.supported_languages:
            warn("language/unsupported", f"unsupported language '{language}'")
        sections = [s for s in (p.strip() for p in text.split("\n\n")) if len(s) >= 20]
        if len(sections) < REQUIRED_SECTIONS_MIN:
            warn("content/sections", "document has no substantial sections")
        for w in metadata.get("_warnings", []) if isinstance(metadata, dict) else []:
            warn("metadata/inferred", str(w))
        valid = not any(i.level == "error" for i in issues)
        return ValidationReport(doc_id=doc_id, valid=valid, issues=issues)
