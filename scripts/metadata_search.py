#!/usr/bin/env python3
"""
Metadata Search System

Support filtering by:
- Category
- Subcategory
- Tags
- Language
- Trust Level
- Version

Does NOT implement semantic retrieval.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


class MetadataSearch:
    """Search knowledge base documents using metadata filters."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = Path(kb_dir).resolve()
        self.indexed: bool = False
        self.index: Dict[str, List[dict]] = {}
    
    def index_documents(self) -> None:
        """Index all knowledge base documents for searching."""
        self.index = {}
        
        if not self.kb_dir.exists():
            return
        
        # Walk through all .json and .md files
        for root, dirs, files in os.walk(self.kb_dir):
            # Skip metadata directory
            if Path(root).name == "metadata" and root != str(self.kb_dir):
                continue
            
            for filename in files:
                if not (filename.endswith('.json') or filename.endswith('.md')):
                    continue
                
                filepath = Path(root) / filename
                try:
                    doc = self._load_for_indexing(filepath)
                    if doc:
                        self._add_to_index(doc)
                except Exception as e:
                    print(f"Error indexing {filepath}: {e}")
        
        self.indexed = True
    
    def _load_for_indexing(self, filepath: Path) -> Optional[dict]:
        """Load a document for indexing purposes."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try JSON first
            if filepath.suffix == '.json':
                data = json.loads(content)
                return {
                    "filepath": str(filepath),
                    "title": data.get("title", filepath.stem),
                    "category": data.get("category", ""),
                    "subcategory": data.get("subcategory", ""),
                    "tags": data.get("tags", []),
                    "language": data.get("language", "en-US"),
                    "trust_level": data.get("trust_level", "medium"),
                    "version": data.get("version", "1.0"),
                }
            
            # Markdown file
            else:
                # Extract title from first heading
                title = filepath.stem.replace('_', ' ').title()
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
                
                return {
                    "filepath": str(filepath),
                    "title": title,
                    "category": Path(root).parent.name if Path(root).parent.name != self.kb_dir.name else "unknown",
                    "subcategory": "",
                    "tags": [],
                    "language": "en-US",
                    "trust_level": "medium",
                    "version": "1.0",
                }
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def _add_to_index(self, doc: dict) -> None:
        """Add a document to the search index."""
        category = doc["category"].lower()
        
        if category not in self.index:
            self.index[category] = []
        
        self.index[category].append(doc)
    
    def search(self, 
               category: Optional[str] = None,
               subcategory: Optional[str] = None,
               tags: Optional[List[str]] = None,
               language: Optional[str] = None,
               trust_level: Optional[str] = None,
               version: Optional[str] = None) -> List[dict]:
        """Search documents using metadata filters.
        
        Args:
            category: Filter by category (e.g., "scams", "legitimate")
            subcategory: Filter by subcategory (e.g., "phishing", "banking")
            tags: Filter by tags (matches if any of the provided tags exist)
            language: Filter by language code (e.g., "en-US")
            trust_level: Filter by trust level (e.g., "high")
            version: Filter by version (exact match or prefix)
        
        Returns:
            List of matching document metadata
        """
        if not self.indexed:
            self.index_documents()
        
        # Start with all categories or filter by specific category
        categories_to_search = [category] if category else list(self.index.keys())
        
        # Collect matching documents
        matches: List[dict] = []
        
        for cat in categories_to_search:
            if cat not in self.index:
                continue
            
            for doc in self.index[cat]:
                # Apply filters
                if not self._matches_filters(doc, subcategory, tags, language, trust_level, version):
                    continue
                
                matches.append(doc)
        
        return matches
    
    def _matches_filters(self, 
                         doc: dict,
                         subcategory: Optional[str],
                         tags: Optional[List[str]],
                         language: Optional[str],
                         trust_level: Optional[str],
                         version: Optional[str]) -> bool:
        """Check if a document matches all provided filters."""
        
        # Subcategory filter (exact match)
        if subcategory and doc.get("subcategory", "").lower() != subcategory.lower():
            return False
        
        # Tags filter (document must have at least one of the specified tags)
        if tags:
            doc_tags = set(doc.get("tags", []))
            search_tags = set(t.lower() for t in tags)
            if not doc_tags.intersection(search_tags):
                return False
        
        # Language filter (exact match)
        if language and doc.get("language", "").lower() != language.lower():
            return False
        
        # Trust level filter (exact match)
        if trust_level and doc.get("trust_level", "").lower() != trust_level.lower():
            return False
        
        # Version filter (prefix match - documents matching this version range)
        if version:
            doc_version = doc.get("version", "1.0")
            # Simple prefix matching - e.g., "1.0" matches "1.0", "1.0.1", "1.1"
            if not doc_version.startswith(version):
                return False
        
        return True
    
    def search_by_category(self, category: str) -> List[dict]:
        """Convenience method to search by category only."""
        return self.search(category=category)
    
    def search_by_tags(self, tags: List[str]) -> List[dict]:
        """Convenience method to search by tags."""
        return self.search(tags=tags)
    
    def search_by_language(self, language: str) -> List[dict]:
        """Convenience method to search by language."""
        return self.search(language=language)
    
    def get_stats(self) -> dict:
        """Get indexing statistics."""
        total_docs = 0
        category_counts = {}
        
        for cat, docs in self.index.items():
            total_docs += len(docs)
            category_counts[cat] = len(docs)
        
        return {
            "total_indexed": total_docs,
            "categories": category_counts,
            "indexed": self.indexed
        }


def test_search():
    """Test the metadata search functionality."""
    search = MetadataSearch()
    search.index_documents()
    
    stats = search.get_stats()
    print(f"Indexing statistics: {stats}")
    
    # Test various searches
    tests = [
        ("Category: scams", lambda: search.search(category="scams")),
        ("Category: legitimate", lambda: search.search(category="legitimate")),
        ("Tags: [otp]", lambda: search.search(tags=["otp"])),
        ("Language: en-US", lambda: search.search(language="en-US")),
        ("Trust Level: high", lambda: search.search(trust_level="high")),
        ("Version: 1.0", lambda: search.search(version="1.0")),
        ("Subcategory: phishing", lambda: search.search(subcategory="phishing")),
        ("Mixed filters", lambda: search.search(
            category="scams",
            tags=["phishing", "otp"],
            language="en-US",
            trust_level="high"
        )),
    ]
    
    print("\nSearch tests:")
    for test_name, test_func in tests:
        results = test_func()
        print(f"  {test_name}: {len(results)} results")
        if results:
            # Show first result title
            first = results[0]
            print(f"    First: {first.get('title', 'N/A')} - {first.get('category', 'N/A')}")
    
    return stats


if __name__ == "__main__":
    test_search()