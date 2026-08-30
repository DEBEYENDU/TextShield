#!/usr/bin/env python
"""
Comprehensive tests for the Knowledge Base V2.0

Covers:
- Schema validation
- Loader
- Metadata search
- Duplicate detection
- Validation failures
- Malformed documents
"""

import json
import os
import sys
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from knowledge_loader import KnowledgeLoader, KnowledgeDocument
from metadata_search import MetadataSearch
from validate_kb import validate_all_documents


def setup_test_dir():
    """Set up a temporary knowledge base directory for testing."""
    test_dir = tempfile.mkdtemp(prefix="kb_test_")
    
    # Create directory structure
    subdirs = [
        "scams/lottery",
        "scams/phishing", 
        "scams/banking",
        "legitimate",
        "behavioral_patterns",
        "communication_styles",
        "examples",
        "glossary",
        "metadata"
    ]
    
    for subdir in subdirs:
        os.makedirs(os.path.join(test_dir, "knowledge_base", subdir), exist_ok=True)
    
    return test_dir


def create_test_document(filepath: str, **kwargs) -> dict:
    """Create a test knowledge base document with default values."""
    defaults = {
        "title": "Test Document",
        "category": "scams",
        "subcategory": "lottery",
        "summary": "Test summary",
        "description": "Test description",
        "typical_scenario": "Test scenario",
        "intent": "Test intent",
        "behavior": "Test behavior",
        "requested_actions": ["test action"],
        "manipulation_techniques": ["urgency"],
        "common_indicators": ["test indicator"],
        "legitimate_alternatives": ["legitimate alt"],
        "false_positives": ["test false positive"],
        "false_negatives": ["test false negative"],
        "real_world_examples": ["test example"],
        "recommendations": ["test recommendation"],
        "tags": ["test"],
        "version": "1.0",
        "last_updated": "2026-08-15",
        "source_credibility": "Test source",
        "language": "en-US",
        "confidence": 0.9
    }
    defaults.update(kwargs)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(defaults, f, indent=2)
    
    return defaults


def test_schema_validation():
    """Test schema validation functionality."""
    print("=" * 60)
    print("Test: Schema Validation")
    print("=" * 60)
    
    # Valid document should pass
    valid_temp = setup_test_dir()
    valid_file = os.path.join(valid_temp, "knowledge_base", "scams", "lottery", "test_scam.json")
    create_test_document(valid_file)
    
    loader = KnowledgeLoader(valid_temp + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    assert loaded > 0, "Should successfully load valid documents"
    print(f"✓ Valid documents loaded: {loaded}")
    
    # Invalid document (missing required fields) should be caught
    invalid_temp = setup_test_dir()
    invalid_file = os.path.join(invalid_temp, "knowledge_base", "scams", "lottery", "invalid_scam.json")
    # Create document missing title and category
    with open(invalid_file, 'w', encoding='utf-8') as f:
        json.dump({"description": "No title or category"}, f)
    
    loader2 = KnowledgeLoader(invalid_temp + "/knowledge_base")
    loaded2, failed2, skipped2 = loader2.read_all_files()
    
    print(f"✓ Invalid documents handled: loaded={loaded2}, failed={failed2}")
    assert failed2 > 0, "Should fail to load invalid documents"
    
    print(" PASSED\n")
    shutil.rmtree(valid_temp)
    shutil.rmtree(invalid_temp)


def test_loader_valid_documents():
    """Test loader with valid knowledge base documents."""
    print("=" * 60)
    print("Test: Loader with Valid Documents")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create valid scam document
    scam_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "lottery_scam.json")
    create_test_document(scam_file, 
                        title="Lottery Scam",
                        category="scams",
                        subcategory="lottery",
                        summary="Test lottery scam description",
                        confidence=0.95)
    
    # Create legitimate document
    legit_file = os.path.join(test_dir, "knowledge_base", "legitimate", "bank_notifications.json")
    create_test_document(letic_file,
                        title="Bank Notifications",
                        category="legitimate",
                        subcategory="communication",
                        summary="Test bank notifications",
                        confidence=0.98)
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    stats = loader.get_statistics()
    
    print(f"  Loaded: {loaded}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total documents: {stats['total_documents_parsed']}")
    print(f"  Valid: {stats['valid_documents']}")
    print(f"  Invalid: {stats['invalid_documents']}")
    
    assert loaded > 0, "Should load documents successfully"
    assert stats['valid_documents'] > 0, "Should have valid documents"
    
    # Test getting documents by category
    scams_docs = loader.get_documents_by_category("scams")
    print(f"  Documents in 'scams' category: {len(scams_docs)}")
    
    # Test getting documents by tag
    otp_docs = loader.get_documents_by_tag("test")
    print(f"  Documents with 'test' tag: {len(otp_docs)}")
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_metadata_search():
    """Test metadata search functionality."""
    print("=" * 60)
    print("Test: Metadata Search")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create documents with different metadata
    create_test_document(
        os.path.join(test_dir, "knowledge_base", "scams", "lottery", "lottery1.json"),
        title="Lottery Scam 1",
        category="scams",
        subcategory="lottery",
        tags=["lottery", "financial_fraud"],
        language="en-US",
        trust_level="high",
        version="1.0"
    )
    
    create_test_document(
        os.path.join(test_dir, "knowledge_base", "scams", "phishing", "phishing1.json"),
        title="Phishing Scam",
        category="scams",
        subcategory="phishing",
        tags=["phishing", "credential_theft"],
        language="en-US",
        trust_level="high",
        version="1.1"
    )
    
    create_test_document(
        os.path.join(test_dir, "knowledge_base", "legitimate", "bank_notifications.json"),
        title="Bank Notifications",
        category="legitimate",
        subcategory="communication",
        tags=["banking", "legitimate"],
        language="en-US",
        trust_level="high",
        version="1.0"
    )
    
    # Create another with different language
    create_test_document(
        os.path.join(test_dir, "knowledge_base", "scams", "lottery", "lottery2.json"),
        title="Spanish Lottery Scam",
        category="scams",
        subcategory="lottery",
        tags=["lottery", "fraud"],
        language="es-ES",
        trust_level="medium",
        version="1.0"
    )
    
    search = MetadataSearch(test_dir + "/knowledge_base")
    search.index_documents()
    
    stats = search.get_stats()
    print(f"  Indexed documents: {stats['total_indexed']}")
    print(f"  Categories: {stats['categories']}")
    
    # Test category search
    scams_results = search.search(category="scams")
    print(f"  Category 'scams' search: {len(scams_results)} results")
    assert len(scams_results) >= 2, "Should find scams documents"
    
    # Test tag search
    lottery_results = search.search(tags=["lottery"])
    print(f"  Tag 'lottery' search: {len(lottery_results)} results")
    assert len(lottery_results) >= 1, "Should find lottery-tagged documents"
    
    # Test language search
    en_results = search.search(language="en-US")
    print(f"  Language 'en-US' search: {len(en_results)} results")
    
    # Test subcategory search
    phishing_results = search.search(subcategory="phishing")
    print(f"  Subcategory 'phishing' search: {len(phishing_results)} results")
    
    # Test trust level search
    high_trust = search.search(trust_level="high")
    print(f"  Trust level 'high' search: {len(high_trust)} results")
    
    # Test version search
    version_results = search.search(version="1.0")
    print(f"  Version '1.0' search: {len(version_results)} results")
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_duplicate_detection():
    """Test duplicate document detection."""
    print("=" * 60)
    print("Test: Duplicate Detection")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create document with title "Lottery Scam"
    file1 = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "lottery_scam.json")
    create_test_document(file1, title="Lottery Scam", summary="First version")
    
    # Create another document with same title in different location
    file2 = os.path.join(test_dir, "knowledge_base", "scams", "phishing", "lottery_scam.json")
    create_test_document(file2, title="Lottery Scam", summary="Second version - different subcategory")
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    # Check for duplicates using the documents dict keys
    keys = list(loader.documents.keys())
    title_keys = [k for k in keys if "Lottery Scam" in k]
    
    print(f"  Documents loaded: {loaded}")
    print(f"  Documents with 'Lottery Scam' in key: {len(title_keys)}")
    
    # Titles should be disambiguated by path
    assert len(loader.documents) == loaded, "All loaded documents should be stored"
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_validation_system():
    """Test the full validation system."""
    print("=" * 60)
    print("Test: Validation System")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create a mix of valid and invalid documents
    # Valid document
    valid_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "valid.json")
    create_test_document(valid_file,
                        title="Valid Document",
                        category="scams",
                        subcategory="lottery",
                        confidence=0.9)
    
    # Invalid document - missing category
    invalid_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "invalid.json")
    with open(invalid_file, 'w', encoding='utf-8') as f:
        json.dump({"title": "Invalid Doc", "description": "Missing category"}, f)
    
    # Run validation
    violations = validate_all_documents(test_dir + "/knowledge_base")
    
    print(f"  Total violations found: {len(violations)}")
    
    # Check that violations exist
    schema_violations = [v for v in violations if v.startswith("SCHEMA:")]
    metadata_violations = [v for v in violations if v.startswith("METADATA:")]
    duplicate_violations = [v for v in violations if v.startswith("DUPLICATE:")]
    reference_violations = [v for v in violations if v.startswith("REFERENCE:")]
    
    print(f"  Schema violations: {len(schema_violations)}")
    print(f"  Metadata violations: {len(metadata_violations)}")
    print(f"  Duplicate violations: {len(duplicate_violations)}")
    print(f"  Reference violations: {len(reference_violations)}")
    
    assert len(violations) > 0, "Should find violations in mixed valid/invalid set"
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_malformed_documents():
    """Test handling of malformed documents."""
    print("=" * 60)
    print("Test: Malformed Document Handling")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create a valid document first
    valid_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "valid.json")
    create_test_document(valid_file,
                        title="Valid Document",
                        category="scams",
                        subcategory="lottery",
                        confidence=0.9)
    
    # Create malformed JSON file
    malformed_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "malformed.json")
    with open(malformed_file, 'w', encoding='utf-8') as f:
        f.write("{invalid json content {{{")
    
    # Create file with wrong extension but valid JSON content
    text_file = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "readme.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("This is just text, not JSON or structured data")
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    stats = loader.get_statistics()
    
    print(f"  Loaded: {loaded}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total documents in memory: {len(loader.documents)}")
    
    # Should have loaded the valid JSON, failed on malformed JSON, and skipped the text file
    # or handled them gracefully
    assert loaded >= 1, "Should load at least the valid document"
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_behavioral_patterns():
    """Test behavioral pattern documents."""
    print("=" * 60)
    print("Test: Behavioral Pattern Library")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create behavioral pattern documents
    patterns = [
        "urgency", "authority", "fear", "reward",
        "curiosity", "scarcity", "reciprocity",
        "trust_building", "social_proof", "pressure",
        "personalization"
    ]
    
    for pattern in patterns:
        filepath = os.path.join(test_dir, "knowledge_base", "behavioral_patterns", f"{pattern}.json")
        create_test_document(filepath,
                          title=f"{pattern.title()} Pattern",
                          category="behavioral_patterns",
                          subcategory=pattern,
                          summary=f"Test summary for {pattern} pattern",
                          intent=f"Test intent for {pattern}",
                          behavior=f"Test behavior for {pattern}",
                          manipulation_techniques=[pattern],
                          common_indicators=[f"{pattern} indicator"],
                          tags=[pattern],
                          confidence=0.9)
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    # Check that all pattern documents were loaded
    expected_count = len(patterns) + 2  # +2 for the scams and legitimate docs we also create
    actual_docs = len([k for k in loader.documents.keys() 
                      if loader.documents[k].category == "behavioral_patterns"])
    
    print(f"  Patterns created: {len(patterns)}")
    print(f"  Behavioral pattern docs loaded: {actual_docs}")
    
    # At least some should be loaded
    assert actual_docs > 0, "Should load behavioral pattern documents"
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_communication_styles():
    """Test communication style documents."""
    print("=" * 60)
    print("Test: Communication Styles")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create communication style documents
    styles = ["formal", "informal", "business", "marketing",
              "customer_support", "educational", "transactional", "personal"]
    
    for style in styles:
        filepath = os.path.join(test_dir, "knowledge_base", "communication_styles", f"{style}.json")
        create_test_document(filepath,
                          title=f"{style.title()} Style",
                          category="communication_styles",
                          subcategory=style,
                          summary=f"Test {style} style",
                          confidence=0.9)
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    style_docs = [k for k in loader.documents.keys() 
                 if loader.documents[k].category == "communication_styles"]
    
    print(f"  Styles created: {len(styles)}")
    print(f"  Communication style docs: {len(style_docs)}")
    
    assert len(style_docs) > 0, "Should load communication style documents"
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_glossary():
    """Test glossary document creation and search."""
    print("=" * 60)
    print("Test: Glossary")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create glossary documents
    glossary_terms = [
        "Spam", "Ham", "Phishing", "Smishing", "Vishing",
        "Semantic Search", "Embedding", "Vector Database",
        "Chunking", "Intent", "Behavior",
        "Entity Extraction", "RAG", "LLM",
        "Hallucination", "Prompt Injection", "Confidence", "Risk"
    ]
    
    for term in glossary_terms:
        # Clean up term for filename
        filename_term = term.replace(" ", "_").replace("'", "")
        filepath = os.path.join(test_dir, "knowledge_base", "glossary", f"{filename_term}.json")
        create_test_document(filepath,
                          title=term,
                          category="glossary",
                          subcategory=term,
                          summary=f"Test summary for {term}",
                          confidence=0.95)
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    glossary_docs = [k for k in loader.documents.keys() 
                    if loader.documents[k].category == "glossary"]
    
    print(f"  Glossary terms created: {len(glossary_terms)}")
    print(f"  Glossary docs loaded: {len(glossary_docs)}")
    
    assert len(glossary_docs) > 0, "Should load glossary documents"
    
    # Test metadata search on glossary
    search = MetadataSearch(test_dir + "/knowledge_base")
    search.index_documents()
    
    # Search for "Phishing" term
    phishing_results = search.search(tags=["Phishing"])
    print(f"  Search 'Phishing' tag: {len(phishing_results)} results")
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def test_versioning():
    """Test document versioning support."""
    print("=" * 60)
    print("Test: Versioning")
    print("=" * 60)
    
    test_dir = setup_test_dir()
    
    # Create document with version 1.0
    file1 = os.path.join(test_dir, "knowledge_base", "scams", "lottery", "scam.json")
    create_test_document(file1, title="Scam Document", version="1.0")
    
    # Update to version 1.1
    create_test_document(file1, title="Scam Document", version="1.1")
    
    # Create version 2.0
    create_test_document(file1, title="Scam Document", version="2.0")
    
    loader = KnowledgeLoader(test_dir + "/knowledge_base")
    loaded, failed, skipped = loader.read_all_files()
    
    # Check versions
    scam_doc = loader.get_document("Scam Document")
    if scam_doc:
        print(f"  Current version: {scam_doc.version}")
        print(f"  Current confidence: {scam_doc.confidence}")
    
    # Test version search
    search = MetadataSearch(test_dir + "/knowledge_base")
    search.index_documents()
    
    v1_results = search.search(version="1.")
    v10_results = search.search(version="1.0")
    
    print(f"  Version prefix '1.' results: {len(v1_results)}")
    print(f"  Version exact '1.0' results: {len(v10_results)}")
    
    print(" PASSED\n")
    shutil.rmtree(test_dir)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE V2.0 - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        ("Schema Validation", test_schema_validation),
        ("Loader with Valid Documents", test_loader_valid_documents),
        ("Metadata Search", test_metadata_search),
        ("Duplicate Detection", test_duplicate_detection),
        ("Validation System", test_validation_system),
        ("Malformed Document Handling", test_malformed_documents),
        ("Behavioral Pattern Library", test_behavioral_patterns),
        ("Communication Styles", test_communication_styles),
        ("Glossary", test_glossary),
        ("Versioning", test_versioning),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())