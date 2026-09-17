"""Model versioning: fingerprint everything that affects an evaluation.

Tracks model version, prompt versions (agent prompt hashes), knowledge
version, graph version, embedding version, weight configuration, agent
versions and evaluation date — so any two runs are comparable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def _file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except Exception:
        return "missing"


def fingerprint() -> dict:
    """Capture the current system fingerprint."""
    from app.agents import __version__ as agents_version
    from app.behavior import __version__ as behavior_version
    from app.core.config import settings
    from app.knowledge_graph import __version__ as graph_version
    from app.understanding import __version__ as understanding_version

    root = Path(".")
    prompt_hashes = {}
    for prompt in sorted((root / "app" / "agents" / "prompts").glob("*.md")):
        prompt_hashes[prompt.stem] = _file_hash(prompt)
    weights = {}
    for key in ("RISK_SPAM_BASE", "RISK_HAM_BASE", "RISK_HIGH_THRESHOLD",
                "RISK_MEDIUM_THRESHOLD", "RISK_CRITICAL_THRESHOLD"):
        weights[key] = getattr(settings, key, None)
    model_meta = {}
    try:
        meta_path = getattr(settings, "MODEL_METADATA_PATH", None)
        if meta_path and Path(meta_path).exists():
            model_meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "model_version": str(model_meta.get("version",
                             model_meta.get("algorithm", "unknown"))),
        "model_hash": _file_hash(getattr(settings, "MODEL_PATH", Path("models/model.joblib"))),
        "prompt_versions": prompt_hashes,
        "knowledge_version": _file_hash(root / "knowledge_base" / "schema.json"),
        "graph_version": str(graph_version),
        "embedding_version": str(getattr(settings, "EMBEDDING_PROVIDER", "hashing")),
        "embedding_model": str(getattr(settings, "EMBEDDING_MODEL", "")),
        "weight_configuration": weights,
        "agent_versions": {"agents": str(agents_version),
                           "behavior": str(behavior_version),
                           "understanding": str(understanding_version)},
        "evaluation_date": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def fingerprint_id(fingerprint_dict: dict) -> str:
    """Short stable id for a fingerprint (excludes evaluation date)."""
    core = {k: v for k, v in fingerprint_dict.items() if k != "evaluation_date"}
    return hashlib.sha256(json.dumps(core, sort_keys=True, default=str)
                          .encode()).hexdigest()[:12]
