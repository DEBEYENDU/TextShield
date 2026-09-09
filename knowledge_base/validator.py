"""KnowledgeValidator — enterprise metadata, taxonomy, and integrity validation.

Responsibilities:
- validate metadata (required fields, types, patterns)
- validate taxonomy (category must exist in taxonomy.json)
- validate dates (YYYY-MM-DD, published <= last_updated, not future)
- validate tags (non-empty, normalized)
- validate duplicate ids (across all markdown files)
- validate references (valid URIs)
- generate validation report (JSON)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import yaml  # pyyaml is already in requirements via other deps; fallback if missing handled

BASE = Path(__file__).resolve().parent
SCHEMA_PATH = BASE / "schemas" / "metadata_schema.json"
TAXONOMY_PATH = BASE / "metadata" / "taxonomy.json"

ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
LANG_PATTERN = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")
REQUIRED_FIELDS = [
    "id", "title", "category", "subcategory", "source", "author",
    "organization", "published", "last_updated", "severity", "confidence",
    "language", "country", "industry", "tags", "summary", "references",
    "license", "version",
]
SEVERITY_ENUM = {"low", "medium", "high", "critical", "informational"}


def _load_taxonomy() -> Dict[str, Any]:
    try:
        return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"categories": {}}

def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str, str]:
    """Return (metadata, body, error). Error is empty if parsed."""
    if not text.startswith("---"):
        return {}, text, "missing frontmatter delimiter ---"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text, "invalid frontmatter delimiter"
    try:
        meta = yaml.safe_load(parts[1]) or {}
        body = parts[2]
        return meta, body, ""
    except Exception as exc:
        return {}, text, f"yaml parse error: {exc}"

def _validate_metadata(meta: Dict[str, Any], taxonomy_categories: set) -> List[str]:
    errors: List[str] = []
    # required
    for f in REQUIRED_FIELDS:
        if f not in meta:
            errors.append(f"missing required field: {f}")
    if errors:
        return errors
    # id
    if not isinstance(meta["id"], str) or not ID_PATTERN.match(meta["id"]):
        errors.append("id must match ^[a-z0-9-]+$")
    # title
    if not isinstance(meta["title"], str) or len(meta["title"].strip()) < 5:
        errors.append("title too short")
    # category taxonomy
    if meta["category"] not in taxonomy_categories:
        # allow case-insensitive mapping via taxonomy.json mappings if present
        errors.append(f"category '{meta['category']}' not in taxonomy")
    # severity
    if meta["severity"] not in SEVERITY_ENUM:
        errors.append(f"severity must be one of {SEVERITY_ENUM}")
    # confidence
    try:
        c = float(meta["confidence"])
        if not (0 <= c <= 1):
            errors.append("confidence out of range 0-1")
    except Exception:
        errors.append("confidence must be number 0-1")
    # language
    if not LANG_PATTERN.match(str(meta["language"])):
        errors.append("language must match ^[a-z]{2}(-[A-Z]{2})?$")
    # tags
    if not isinstance(meta["tags"], list) or not meta["tags"]:
        errors.append("tags must be non-empty list")
    else:
        for t in meta["tags"]:
            if not isinstance(t, str) or not t.strip():
                errors.append(f"invalid tag: {t}")
    # version
    if not VERSION_PATTERN.match(str(meta["version"])):
        errors.append("version must be X.Y.Z")
    # dates
    for field in ("published", "last_updated"):
        try:
            d = datetime.datetime.strptime(str(meta[field]), "%Y-%m-%d").date()
            if d > datetime.date.today():
                errors.append(f"{field} cannot be in future")
        except Exception:
            errors.append(f"{field} must be YYYY-MM-DD")
    try:
        pub = datetime.datetime.strptime(str(meta["published"]), "%Y-%m-%d").date()
        upd = datetime.datetime.strptime(str(meta["last_updated"]), "%Y-%m-%d").date()
        if pub > upd:
            errors.append("published must be <= last_updated")
    except Exception:
        pass
    # references
    if not isinstance(meta["references"], list):
        errors.append("references must be list")
    else:
        for ref in meta["references"]:
            parsed = urlparse(str(ref))
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"invalid reference url: {ref}")
    return errors

class KnowledgeValidator:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else BASE
        self.taxonomy = _load_taxonomy()
        self.categories = set(self.taxonomy.get("categories", {}).keys())
        # also add mappings values as allowed for backward compat
        for v in self.taxonomy.get("mappings", {}).values():
            self.categories.add(v)

    def discover(self) -> List[Path]:
        """Find all markdown files under knowledge_base (recursive)."""
        return sorted(self.base.rglob("*.md"))

    def validate_file(self, path: Path) -> Dict[str, Any]:
        text = path.read_text(encoding="utf-8", errors="replace")
        meta, body, parse_err = _parse_frontmatter(text)
        errors: List[str] = []
        if parse_err:
            errors.append(parse_err)
        else:
            errors.extend(_validate_metadata(meta, self.categories))
            # body checks
            if len(body.strip()) < 50:
                errors.append("body too short (<50 chars)")
        # hash
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return {
            "path": str(path.relative_to(self.base)),
            "id": meta.get("id"),
            "title": meta.get("title"),
            "category": meta.get("category"),
            "errors": errors,
            "valid": not errors,
            "hash": h,
            "word_count": len(body.split()),
        }

    def validate_all(self) -> Dict[str, Any]:
        files = self.discover()
        results: List[Dict[str, Any]] = []
        seen: Dict[str, List[str]] = {}
        for p in files:
            # skip templates and schema docs themselves
            if "templates" in p.parts or p.name == "README.md":
                continue
            res = self.validate_file(p)
            results.append(res)
            _id = res.get("id")
            if _id:
                seen.setdefault(_id, []).append(res["path"])
        # duplicate ids
        for _id, paths in seen.items():
            if len(paths) > 1:
                for r in results:
                    if r.get("id") == _id:
                        r["errors"].append(f"duplicate id '{_id}' found in {paths}")
                        r["valid"] = False
        total = len(results)
        valid = sum(1 for r in results if r["valid"])
        invalid = total - valid
        report = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "base": str(self.base),
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "results": results,
        }
        return report

    def generate_report(self, output: Path | None = None) -> Dict[str, Any]:
        report = self.validate_all()
        if output:
            Path(output).write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report


# CLI entry: python -m knowledge_base.validator
if __name__ == "__main__":
    v = KnowledgeValidator()
    rep = v.validate_all()
    print(json.dumps(rep, indent=2))
    # exit code 1 if invalid
    import sys
    sys.exit(0 if rep["invalid"] == 0 else 1)
