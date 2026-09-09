"""RFC-002 tests: ingestion pipeline (parsers, metadata, validation, chunks,
embedding cache, manifest, incremental indexing, CLI). All must pass."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from knowledge_pipeline.embeddings.embedding_cache import EmbeddingCache
from knowledge_pipeline.embeddings.embedding_manager import EmbeddingManager
from knowledge_pipeline.embeddings.embedding_provider import create_provider, list_providers
from knowledge_pipeline.indexing.incremental import IncrementalTracker
from knowledge_pipeline.indexing.manifest import Manifest
from knowledge_pipeline.ingestion.chunker import ChunkManager
from knowledge_pipeline.ingestion.cleaner import DocumentCleaner
from knowledge_pipeline.ingestion.deduplicator import Deduplicator
from knowledge_pipeline.ingestion.loader import DocumentLoader
from knowledge_pipeline.ingestion.metadata import MetadataExtractor
from knowledge_pipeline.ingestion.parser import parse_file
from knowledge_pipeline.ingestion.validator import DocumentValidator


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    root = tmp_path / "kb"
    (root / "phishing").mkdir(parents=True)
    (root / "phishing" / "fake_kyc.md").write_text(
        "# Fake KYC Scam\n\nYour account will be blocked. Click here to verify "
        "your identity immediately. This is a phishing attempt targeting banking users. "
        "More details about this scam pattern and how to detect it.\n",
        encoding="utf-8",
    )
    (root / "phishing" / "note.txt").write_text(
        "Urgent security alert. Your bank account needs verification. "
        "Do not click suspicious links. Contact your bank directly for assistance.\n",
        encoding="utf-8",
    )
    (root / "phishing" / "page.html").write_text(
        "<html><head><title>Phishing Alert</title></head>"
        "<body><h1>Warning</h1><p>Fake login page detected. Report it.</p></body></html>",
        encoding="utf-8",
    )
    (root / "phishing" / "binary.exe").write_bytes(b"MZ fake")
    return root


def _make_minimal_docx(path: Path, paragraphs: list[str]) -> None:
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paras = "".join(
        f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs
    )
    document_xml = (
        f'<?xml version="1.0"?><w:document xmlns:w="{ns}"><w:body>{paras}</w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document_xml)


def test_loader_discovers_and_skips_unsupported(sample_dir: Path):
    loader = DocumentLoader(sample_dir)
    found = loader.discover()
    exts = {d.extension for d in found}
    assert ".md" in exts and ".txt" in exts and ".html" in exts
    assert all(d.supported for d in found)
    assert any(p.suffix == ".exe" for p in loader.skipped)
    assert all(d.category == "phishing" for d in found)


def test_markdown_parsing(sample_dir: Path):
    doc = parse_file(sample_dir / "phishing" / "fake_kyc.md", category="phishing")
    assert doc.doc_id == "phishing:fake_kyc"
    assert "Fake KYC" in doc.title
    assert "phishing" in doc.text.lower()


def test_txt_and_html_parsing(sample_dir: Path):
    txt = parse_file(sample_dir / "phishing" / "note.txt", category="phishing")
    assert len(txt.text) > 60
    html_doc = parse_file(sample_dir / "phishing" / "page.html", category="phishing")
    assert "Fake login page" in html_doc.text
    assert "<" not in html_doc.text


def test_pdf_parsing_fallback(tmp_path: Path):
    pdf = tmp_path / "alert.pdf"
    pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n"
        b"This is a phishing alert document with enough text to pass validation checks. " * 4
    )
    doc = parse_file(pdf, category="general")
    assert isinstance(doc.text, str)


def test_docx_parsing(tmp_path: Path):
    docx_path = tmp_path / "report.docx"
    _make_minimal_docx(docx_path, [
        "Quarterly phishing report with sufficient length for validation purposes.",
        "Second paragraph describing attacker techniques and mitigations in detail.",
    ])
    doc = parse_file(docx_path, category="reports")
    assert "phishing report" in doc.text
    assert doc.category == "reports"


def test_metadata_extraction_defaults():
    extractor = MetadataExtractor()
    meta, warnings = extractor.extract(
        "phishing:fake_kyc", "Fake KYC", "Your account blocked. Verify now. " * 10,
        "/kb/phishing/fake_kyc.md", "phishing", {})
    assert meta.author == "unknown"
    assert meta.tags  # defaulted to category
    assert meta.severity in {"critical", "high", "medium", "low", "info"}
    assert meta.summary
    assert isinstance(warnings, list)


def test_cleaner_normalizes():
    cleaner = DocumentCleaner()
    dirty = "Hello   world!\r\n\r\n\r\n<script>alert(1)</script><p>Hi</p>\x00  **broken**  "
    cleaned = cleaner.clean(dirty)
    assert "\x00" not in cleaned
    assert "<script>" not in cleaned
    assert "  " not in cleaned


def test_validator_accepts_and_rejects():
    validator = DocumentValidator()
    good = validator.validate("a:x", "Title", "x" * 200,
                              {"source": "x.md", "category": "phishing", "language": "en"})
    assert good.valid
    bad = validator.validate("a:y", "", "short", {"source": "", "category": "", "language": "xx"})
    assert not bad.valid
    dup = validator.validate("a:x", "Title", "y" * 200,
                             {"source": "x.md", "category": "phishing", "language": "en"})
    assert any(i.code == "duplicate/id" for i in dup.errors)


def test_chunk_strategies():
    text = "# Heading One\n\n" + ("Sentence about phishing. " * 40) + "\n\n# Heading Two\n\n" + ("More details. " * 40)
    meta = {"source": "a.md", "category": "phishing"}
    for strategy in ["fixed", "overlap", "semantic", "heading", "paragraph"]:
        chunks = ChunkManager(chunk_size=300, overlap=50, strategy=strategy).chunk("d:1", text, meta)
        assert len(chunks) >= 1
        assert all(c.metadata["category"] == "phishing" for c in chunks)
        assert all(c.text.strip() for c in chunks)


def test_deduplicator():
    dedup = Deduplicator()
    dup1, _ = dedup.is_duplicate("a", "same text here")
    assert dup1 is False
    dup2, orig = dedup.is_duplicate("b", "same text here")
    assert dup2 is True and orig == "a"


def test_embedding_provider_abstraction():
    assert "hashing" in list_providers()
    for name in ["hashing", "openai", "gemini", "ollama", "huggingface"]:
        provider = create_provider(name)
        assert provider is not None
    with pytest.raises(ValueError):
        create_provider("nonexistent-xyz")


def test_embedding_cache_hit_miss(tmp_path: Path):
    manager = EmbeddingManager("hashing", cache_dir=tmp_path / "cache")
    first = manager.embed(["hello world phishing detection"])
    assert first.shape[0] == 1
    misses_before = manager.cache.misses
    second = manager.embed(["hello world phishing detection"])
    assert manager.cache.hits >= 1
    assert (first == second).all()
    assert manager.cache.misses == misses_before  # second call served from cache


def test_manifest_generation(tmp_path: Path):
    manifest = Manifest(tmp_path / "knowledge_manifest.json")
    from knowledge_pipeline.indexing.manifest import ManifestEntry

    manifest.upsert(ManifestEntry(doc_id="phishing:a", file_hash="abc",
                                  last_modified=123.0, chunk_count=3, indexed=True,
                                  validation_status="valid", category="phishing",
                                  size=100, source_path="/kb/a.md", chunk_ids=["x"]))
    manifest.save()
    assert (tmp_path / "knowledge_manifest.json").exists()
    reloaded = Manifest(tmp_path / "knowledge_manifest.json")
    assert reloaded.get("phishing:a").chunk_count == 3


def test_incremental_plan(sample_dir: Path, tmp_path: Path):
    manifest = Manifest(tmp_path / "m.json")
    tracker = IncrementalTracker(manifest)
    loader = DocumentLoader(sample_dir)
    discovered = loader.discover()
    plan1 = tracker.plan(discovered)
    assert len(plan1.to_add) == len(discovered) and plan1.unchanged == 0
    # Simulate ingested state, then re-plan -> all unchanged
    from knowledge_pipeline.indexing.manifest import ManifestEntry

    for item in discovered:
        manifest.upsert(ManifestEntry(doc_id=f"{item.category}:{item.path.stem}",
                                      file_hash=item.sha256, last_modified=item.mtime,
                                      indexed=True, category=item.category,
                                      source_path=str(item.path)))
    plan2 = tracker.plan(discovered)
    assert plan2.unchanged == len(discovered)
    assert not plan2.to_add and not plan2.to_update


def test_cli_ingest_dry_run(sample_dir: Path, tmp_path: Path, capsys):
    from knowledge_pipeline.pipeline import IngestionPipeline

    pipeline = IngestionPipeline(kb_root=sample_dir,
                                 manifest_path=tmp_path / "manifest.json",
                                 provider="hashing", dry_run=True)
    result = pipeline.run()
    assert result["discovered"] >= 3
    assert result["dry_run"] is True
    assert result["chunks_created"] >= 1


def test_cli_entry_points(sample_dir: Path):
    from knowledge_pipeline.cli import ingest as ingest_cli
    from knowledge_pipeline.cli import validate as validate_cli

    parser = ingest_cli.build_parser()
    args = parser.parse_args(["--folder", str(sample_dir), "--dry-run"])
    assert args.dry_run is True
    assert validate_cli is not None
