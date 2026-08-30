#!/usr/bin/env python3
"""
Knowledge Base Loader

Capabilities:
- Reading all knowledge files
- Validating schema
- Returning structured objects
- Handling malformed documents
"""

import json
import os
import re
from datetime import datetime
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class KnowledgeDocument:
    """Represents a validated knowledge base document."""
    
    def __init__(self, data: dict, filepath: str):
        self.filepath = filepath
        self.raw_data = data
        self.title = data.get("title", "")
        self.category = data.get("category", "")
        self.subcategory = data.get("subcategory", "")
        self.summary = data.get("summary", "")
        self.description = data.get("description", "")
        self.typical_scenario = data.get("typical_scenario", "")
        self.intent = data.get("intent", "")
        self.behavior = data.get("behavior", "")
        self.requested_actions = data.get("requested_actions", [])
        self.manipulation_techniques = data.get("manipulation_techniques", [])
        self.common_indicators = data.get("common_indicators", [])
        self.legitimate_alternatives = data.get("legitimate_alternatives", [])
        self.false_positives = data.get("false_positives", [])
        self.false_negatives = data.get("false_negatives", [])
        self.real_world_examples = data.get("real_world_examples", [])
        self.recommendations = data.get("recommendations", [])
        self.tags = data.get("tags", [])
        self.version = data.get("version", "1.0")
        self.last_updated = data.get("last_updated", "")
        self.source_credibility = data.get("source_credibility", "")
        self.language = data.get("language", "en-US")
        self.confidence = data.get("confidence", 0.5)
        
        # Metadata
        self.category_meta = data.get("category", "")
        self.subcategory_meta = data.get("subcategory", "")
        self.language_meta = data.get("language", "en-US")
        self.tags_meta = data.get("tags", [])
        self.version_meta = data.get("version", "1.0")
        self.trust_level = data.get("trust_level", "medium")
        self.last_updated_meta = data.get("last_updated", "")
        self.difficulty = data.get("difficulty", "intermediate")
        self.source_meta = data.get("source", "")
        
        # Validation state
        self.schema_valid = True
        self.metadata_valid = True
        self.errors = []
    
    def is_valid(self) -> bool:
        """Check if document passed validation."""
        return self.schema_valid and self.metadata_valid and len(self.errors) == 0


class KnowledgeLoader:
    """Loader for reading and validating all knowledge base documents."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = Path(kb_dir).resolve()
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.loaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
    
    def read_all_files(self) -> Tuple[int, int, int]:
        """Read all knowledge base files and return counts.
        
        Returns:
            Tuple of (loaded, failed, skipped)
        """
        self.documents = {}
        self.loaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        if not self.kb_dir.exists():
            print(f"Knowledge base directory not found: {self.kb_dir}")
            return 0, 0, 0
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.kb_dir):
            # Skip metadata directory at top level (handled separately)
            relative_root = Path(root).relative_to(self.kb_dir)
            if relative_root.name == "metadata" and root != str(self.kb_dir):
                continue
            
            for filename in files:
                filepath = Path(root) / filename
                
                try:
                    # Attempt to load as JSON first (structured documents)
                    if filename.endswith('.json'):
                        doc_data = self._load_json(filepath)
                        if doc_data is not None:
                            doc = KnowledgeDocument(doc_data, str(filepath))
                            self._process_document(doc)
                            self.loaded_count += 1
                    
                    # Load as Markdown for narrative documents
                    elif filename.endswith('.md'):
                        doc_data = self._load_markdown(filepath)
                        if doc_data is not None:
                            doc = KnowledgeDocument(doc_data, str(filepath))
                            self._process_document(doc)
                            self.loaded_count += 5  # MD files are typically example/glossary entries
                    
                    else:
                        # Try to load as text
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            doc = KnowledgeDocument({"title": filename, "description": content}, str(filepath))
                            self._process_document(doc)
                            self.loaded_count += 1
                        except UnicodeDecodeError:
                            self.skipped_count += 1
                            print(f"Skipped (encoding): {filepath}")
                
                except Exception as e:
                    self.failed_count += 1
                    print(f"Failed to load {filepath}: {str(e)}")
        
        return self.loaded_count, self.failed_count, self.skipped_count
    
    def _load_json(self, filepath: Path) -> Optional[dict]:
        """Load and parse a JSON knowledge document."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {filepath}: {e}")
            return None
        except UnicodeDecodeError:
            print(f"Encoding error in {filepath}")
            return None
    
    def _load_markdown(self, filepath: Path) -> Optional[dict]:
        """Load a Markdown file and extract basic metadata."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first heading or filename
            title = filepath.stem.replace('_', ' ').title()
            
            # Try to extract title from first # heading
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            return {
                "title": title,
                "description": content,
                "category": filepath.parent.parent.name if filepath.parent.parent.name != self.kb_dir.name else "examples",
                "tags": []
            }
        except UnicodeDecodeError:
            print(f"Encoding error in {filepath}")
            return None
        except Exception as e:
            print(f"Error loading markdown {filepath}: {str(e)}")
            return None
    
    def _process_document(self, doc: KnowledgeDocument) -> None:
        """Process a loaded document, running validation."""
        # Reset validation state
        doc.schema_valid = True
        doc.metadata_valid = True
        doc.errors = []
        
        # Schema validation
        schema_violations = self._validate_schema(doc)
        if schema_violations:
            doc.schema_valid = False
            doc.errors.extend(schema_violations)
        
        # Metadata validation
        metadata_violations = self._validate_metadata(doc)
        if metadata_violations:
            doc.metadata_valid = False
            doc.errors.extend(metadata_violations)
        
        # Store document keyed by title (disambiguate with path)
        title_key = f"{doc.title}_{Path(doc.filepath).parent.name}"
        self.documents[title_key] = doc
    
    def _validate_schema(self, doc: KnowledgeDocument) -> List[str]:
        """Validate document against schema requirements."""
        violations = []
        
        # Check required fields exist and are non-empty
        required_fields = {
            "title": doc.title,
            "category": doc.category,
            "subcategory": doc.subcategory,
            "summary": doc.summary,
            "description": doc.description,
            "typical_scenario": doc.typical_scenario,
            "intent": doc.intent,
            "behavior": doc.behavior,
        }
        
        for field, value in required_fields.items():
            if not value or (isinstance(value, str) and value.strip() == ""):
                violations.append(f"Missing or empty required field: {field}")
        
        # Validate confidence range
        if not (0.0 <= doc.confidence <= 1.0):
            violations.append(f"Confidence out of range: {doc.confidence} (must be 0.0-1.0)")
        
        # Validate version format
        version_pattern = r'^\d+\.\d+(\.\d+)?$'
        if not re.match(version_pattern, doc.version):
            violations.append(f"Invalid version format: {doc.version}")
        
        # Validate language
        if doc.language not in ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"]:
            violations.append(f"Unsupported language: {doc.language}")
        
        # Validate category
        valid_categories = ["scams", "legitimate", "behavioral_patterns", 
                           "communication_styles", "examples", "glossary", "metadata"]
        if doc.category not in valid_categories:
            violations.append(f"Invalid category: {doc.category}")
        
        return violations
    
    def _validate_metadata(self, doc: KnowledgeDocument) -> List[str]:
        """Validate document metadata."""
        violations = []
        
        # Check metadata fields
        if not doc.category_meta:
            violations.append("Missing category metadata")
        if not doc.subcategory_meta:
            violations.append("Missing subcategory metadata")
        if not doc.language_meta:
            violations.append("Missing language metadata")
        if not isinstance(doc.tags_meta, list):
            violations.append("tags metadata must be an array")
        if not re.match(r'^\d+\.\d+(\.\d+)?$', doc.version_meta):
            violations.append(f"Invalid version format: {doc.version_meta}")
        if doc.trust_level not in ["high", "medium", "low"]:
            violations.append(f"Invalid trust_level: {doc.trust_level}")
        if doc.difficulty not in ["beginner", "intermediate", "advanced"]:
            violations.append(f"Invalid difficulty: {doc.difficulty}")
        
        # Validate last_updated date format
        try:
            if doc.last_updated_meta:
                datetime.strptime(doc.last_updated_meta, "%Y-%m-%d")
        except ValueError:
            violations.append(f"Invalid last_updated format: {doc.last_updated_meta}")
        
        return violations
    
    def get_document(self, title_or_key: str) -> Optional[KnowledgeDocument]:
        """Retrieve a document by title or key."""
        # Try exact match first
        if title_or_key in self.documents:
            return self.documents[title_or_key]
        
        # Try partial match
        for key, doc in self.documents.items():
            if title_or_key.lower() in key.lower() or title_or_key.lower() in doc.title.lower():
                return doc
        
        return None
    
    def get_documents_by_category(self, category: str) -> List[KnowledgeDocument]:
        """Get all documents in a specific category."""
        return [doc for doc in self.documents.values() 
                if doc.category == category and doc.is_valid()]
    
    def get_documents_by_tag(self, tag: str) -> List[KnowledgeDocument]:
        """Get all documents containing a specific tag."""
        return [doc for doc in self.documents.values() 
                if tag in doc.tags and doc.is_valid()]
    
    def get_statistics(self) -> dict:
        """Return loading statistics."""
        total = self.loaded_count + self.failed_count
        valid_docs = sum(1 for d in self.documents.values() if d.is_valid())
        
        return {
            "total_files_found": self.loaded_count + self.failed_count + self.skipped_count,
            "loaded_successfully": self.loaded_count,
            "failed_to_load": self.failed_count,
            "skipped": self.skipped_count,
            "total_documents_parsed": len(self.documents),
            "valid_documents": valid_docs,
            "invalid_documents": len(self.documents) - valid_docs
        }
    
    def export_structured(self) -> dict:
        """Export all documents as structured objects for RAG system."""
        structured = {
            "total_documents": len(self.documents),
            "documents": [],
            "statistics": self.get_statistics()
        }
        
        for doc in self.documents.values():
            if doc.is_valid():
                structured["documents"].append({
                    "title": doc.title,
                    "category": doc.category,
                    "subcategory": doc.subcategory,
                    "summary": doc.summary,
                    "description": doc.description,
                    "tags": doc.tags,
                    "version": doc.version,
                    "language": doc.language,
                    "confidence": doc.confidence,
                    "metadata": {
                        "trust_level": doc.trust_level,
                        "last_updated": doc.last_updated_meta,
                        "difficulty": doc.difficulty,
                        "source": doc.source_meta
                    }
                })
        
        return structured


def test_loader():
    """Test function to verify loader functionality."""
    loader = KnowledgeLoader()
    loaded, failed, skipped = loader.read_all_files()
    stats = loader.get_statistics()
    
    print(f"\nLoader Statistics:")
    print(f"  Loaded: {loaded}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total documents in memory: {len(loader.documents)}")
    print(f"  Valid documents: {stats['valid_documents']}")
    print(f"  Invalid documents: {stats['invalid_documents']}")
    
    # Show a few document titles
    print(f"\n  Sample documents:")
    for i, (key, doc) in enumerate(list(loader.documents.items())[:5]):
        print(f"    {i+1}. {doc.title} ({doc.category}/{doc.subcategory})")
    
    # Export structured
    structured = loader.export_structured()
    print(f"\n  Structured export: {structured['total_documents']} valid documents")
    
    return loaded, failed, skipped


if __name__ == "__main__":
    test_loader()