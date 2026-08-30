#!/usr/bin/env python3
"""
Knowledge Base Validation System

Validates:
- Missing fields
- Duplicate entries
- Broken metadata
- Schema violations
- Invalid references
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

# Schema definition (simplified - in production would load from schema.json)
SCHEMA_REQUIRED_FIELDS = [
    "title", "category", "subcategory", "summary", "description",
    "typical_scenario", "intent", "behavior", "requested_actions",
    "manipulation_techniques", "common_indicators", "legitimate_alternatives",
    "false_positives", "false_negatives", "real_world_examples",
    "recommendations", "tags", "version", "last_updated",
    "source_credibility", "language", "confidence"
]

VALID_CATEGORIES = [
    "scams", "legitimate", "behavioral_patterns", "communication_styles",
    "examples", "glossary", "metadata"
]

VALID_SCAM_SUBCATEGORIES = [
    "lottery", "prize", "banking", "otp", "fake_kyc", "delivery",
    "courier", "technical_support", "government", "income_tax",
    "scholarship", "loan", "insurance", "investment", "cryptocurrency",
    "job", "internship", "romance", "refund", "subscription",
    "password_reset", "account_verification", "charity"
]

VALID_COMMUNICATION_STYLES = ["formal", "informal", "business", "marketing",
                                "customer_support", "educational", "transactional", "personal"]

VALID_BEHAVIORAL_PATTERNS = ["urgency", "authority", "fear", "reward",
                              "curiosity", "scarcity", "reciprocity",
                              "trust_building", "social_proof", "pressure",
                              "personalization"]

LANGUAGE_CODES = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "ja-JP", "zh-CN"]


def load_document(filepath):
    """Load a knowledge base document from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(document):
    """Validate that document contains all required schema fields."""
    violations = []
    
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in document:
            violations.append(f"Missing required field: {field}")
        elif document[field] is None or document[field] == "":
            violations.append(f"Empty required field: {field}")
    
    # Validate field types
    if "confidence" in document:
        if not isinstance(document["confidence"], (int, float)) or not (0 <= document["confidence"] <= 1):
            violations.append(f"Invalid confidence value: {document.get('confidence')} (must be 0.0-1.0)")
    
    if "version" in document:
        if not re.match(r'^\d+\.\d+(\.\d+)?$', document["version"]):
            violations.append(f"Invalid version format: {document.get('version')} (expected semantic version)")
    
    if "language" in document and document["language"] not in LANGUAGE_CODES:
        violations.append(f"Unsupported language code: {document.get('language')}")
    
    if "category" in document and document["category"] not in VALID_CATEGORIES:
        violations.append(f"Invalid category: {document.get('category')}")
    
    return violations


def validate_metadata(document):
    """Validate document metadata fields."""
    violations = []
    
    # Check required metadata fields
    metadata_fields = ["category", "subcategory", "language", "tags", "version", 
                       "trust_level", "last_updated", "difficulty", "source"]
    
    for field in metadata_fields:
        if field not in document:
            violations.append(f"Missing metadata field: {field}")
    
    # Validate trust_level
    if "trust_level" in document and document["trust_level"] not in ["high", "medium", "low"]:
        violations.append(f"Invalid trust_level: {document.get('trust_level')} (must be high/medium/low)")
    
    # Validate last_updated format
    if "last_updated" in document:
        try:
            datetime.strptime(document["last_updated"], "%Y-%m-%d")
        except ValueError:
            violations.append(f"Invalid last_updated format: {document.get('last_updated')} (expected YYYY-MM-DD)")
    
    # Validate version
    if "version" in document and not re.match(r'^\d+\.\d+(\.\d+)?$', document["version"]):
        violations.append(f"Invalid version format: {document.get('version')}")
    
    # Validate tags is array
    if "tags" in document and not isinstance(document["tags"], list):
        violations.append(f"tags must be an array, got {type(document['tags']).__name__}")
    
    # Validate subcategory matches category
    if "category" in document and "subcategory" in document:
        cat = document["category"]
        sub = document["subcategory"]
        
        if cat == "scams" and sub not in VALID_SCAM_SUBCATEGORIES:
            violations.append(f"Invalid scams subcategory: {sub}")
        elif cat == "communication_styles" and sub not in VALID_COMMUNICATION_STYLES:
            violations.append(f"Invalid communication_styles subcategory: {sub}")
        elif cat == "behavioral_patterns" and sub not in VALID_BEHAVIORAL_PATTERNS:
            violations.append(f"Invalid behavioral_patterns subcategory: {sub}")
    
    return violations


def check_duplicates(documents_dir):
    """Check for duplicate document titles across the knowledge base."""
    violations = []
    titles = {}
    
    for filename in os.listdir(documents_dir):
        if filename.endswith('.json') or filename.endswith('.md'):
            filepath = os.path.join(documents_dir, filename)
            try:
                doc = load_document(filepath)
                title = doc.get("title", filename)
                
                if title in titles:
                    violations.append(f"Duplicate title: '{title}' found in {titles[title]} and {filepath}")
                else:
                    titles[title] = filepath
            except (json.JSONDecodeError, KeyError):
                violations.append(f"Could not parse: {filename}")
    
    return violations


def check_references(documents_dir):
    """Check that references/source_credibility values are valid."""
    violations = []
    
    for filename in os.listdir(documents_dir):
        if filename.endswith('.json') or filename.endswith('.md'):
            filepath = os.path.join(documents_dir, filename)
            try:
                doc = load_document(filepath)
                
                if "source_credibility" in doc:
                    source = doc["source_credibility"]
                    # Basic check - source should not be empty
                    if not source or source.strip() == "":
                        violations.append(f"Empty source_credibility in {filename}")
                
                if "references" in doc:
                    refs = doc["references"]
                    if not isinstance(refs, list):
                        violations.append(f"references must be array in {filename}")
                    elif len(refs) > 0 and not all(isinstance(r, str) for r in refs):
                        violations.append(f"references must contain strings in {filename}")
            except (json.JSONDecodeError, KeyError):
                violations.append(f"Could not parse: {filename}")
    
    return violations


def validate_all_documents(documents_dir):
    """Validate all documents in the knowledge base."""
    all_violations = []
    
    # Find all .json and .md files in subdirectories
    for root, dirs, files in os.walk(documents_dir):
        for filename in files:
            if filename.endswith('.json') or filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                
                try:
                    doc = load_document(filepath)
                    
                    # Schema validation
                    schema_violations = validate_schema(doc)
                    all_violations.extend([f"SCHEMA: {v}" for v in schema_violations])
                    
                    # Metadata validation
                    metadata_violations = validate_metadata(doc)
                    all_violations.extend([f"METADATA: {v}" for v in metadata_violations])
                    
                except json.JSONDecodeError as e:
                    all_violations.append(f"JSON PARSE ERROR in {filepath}: {str(e)}")
                except Exception as e:
                    all_violations.append(f"ERROR processing {filepath}: {str(e)}")
    
    # Check for duplicates
    dup_violations = check_duplicates(documents_dir)
    all_violations.extend([f"DUPLICATE: {v}" for v in dup_violations])
    
    # Check references
    ref_violations = check_references(documents_dir)
    all_violations.extend([f"REFERENCE: {v}" for v in ref_violations])
    
    return all_violations


def main():
    """Main validation entry point."""
    documents_dir = "C:/Users/GOD KAKAROT/TextShield/knowledge_base"
    
    print("=" * 60)
    print("Knowledge Base Validation Report")
    print("=" * 60)
    
    violations = validate_all_documents(documents_dir)
    
    if not violations:
        print("✓ All documents valid! No violations found.")
    else:
        print(f"✗ Found {len(violations)} violation(s):")
        print()
        
        # Group by type
        by_type = {}
        for v in violations:
            category = v.split(":")[0]
            message = ": ".join(v.split(": ", 1)[1:]) if ": " in v else v.split(": ", 1)[1]
            if category not in by_type:
                by_type[category] = []
            by_type[category].append(message)
        
        for category, messages in sorted(by_type.items()):
            print(f"\n{category} ({len(messages)}):")
            for msg in messages:
                print(f"  - {msg}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()