# docs/Knowledge_Base_Design.md

# Knowledge Base V2.0 - Design Documentation

## Architecture

The Knowledge Base V2.0 is a structured cybersecurity knowledge base designed to serve as the foundation for Retrieval-Augmented Generation (RAG) systems. It contains high-quality, evidence-based information describing legitimate and malicious communication patterns, organized for both human and machine readability.

The architecture follows a document-centric model where each knowledge item adheres to a standardized schema, enabling consistent validation, versioning, and retrieval. The knowledge base is divided into logical categories that cover scams, legitimate communications, behavioral patterns, communication styles, examples, and glossary terms.

**Key Design Principles:**
- **Evidence-based**: All documents reference credible sources (FTC, government agencies, security research organizations)
- **Human-readable**: Narrative documents understandable by people
- **Machine-readable**: Standardized JSON schema with machine-readable metadata
- **Extensible**: New documents can be added without breaking existing functionality
- **Versioned**: Each document supports versioning for future updates
- **Validatable**: Comprehensive validation ensures data integrity

## Folder Structure

```
knowledge_base/
├── scams/
│   ├── phishing/           - Phishing-related scam patterns
│   ├── smishing/           - SMS phishing patterns
│   ├── vishing/            - Voice phishing patterns
│   ├── lottery/            - Lottery and prize scams
│   ├── investment/         - Investment and crypto scams
│   ├── banking/            - Banking and financial scams
│   ├── otp/                - One-time password scams
│   ├── delivery/           - Delivery and courier scams
│   ├── government/         - Government impersonation scams
│   ├── employment/         - Job and internship scams
│   ├── cryptocurrency/     - Cryptocurrency-related scams
│   ├── romance/            - Romance and relationship scams
│   ├── technical_support/  - Technical support scams
│   └── refund/             - Refund and subscription scams
├── legitimate/             - Genuine communication patterns
├── behavioral_patterns/    - Manipulation technique descriptions
├── manipulation/           - Additional manipulation analysis
├── communication_styles/   - Communication style documents
├── examples/               - Labeled example messages
├── glossary/               - Terminology dictionary
└── metadata/               - Metadata design and schemas
```

## Document Schema

Every knowledge document follows a standardized schema with 21 required fields:

| Field | Type | Description |
|-------|------|-------------|
| title | string | Title of the knowledge document |
| category | string | High-level category (scams, legitimate, etc.) |
| subcategory | string | Specific subcategory within the category |
| summary | string | Brief summary (1-2 sentences) |
| description | string | Detailed description of the topic |
| typical_scenario | string | Typical scenario where the pattern occurs |
| intent | string | The intent behind the communication pattern |
| behavior | string | Typical behavior associated with the pattern |
| requested_actions | array | Actions requested in the communication |
| manipulation_techniques | array | Manipulation techniques used |
| common_indicators | array | Common indicators of the pattern |
| legitimate_alternatives | array | Legitimate alternatives to the pattern |
| false_positives | array | Situations flagged as the pattern but are legitimate |
| false_negatives | array | Situations of the pattern that may be missed |
| real_world_examples | array | Real-world examples of the pattern |
| recommendations | array | Recommendations for handling the pattern |
| tags | array | Tags for categorization and search |
| version | string | Document version number (semantic versioning) |
| last_updated | date | Date the document was last updated (YYYY-MM-DD) |
| source_credibility | string | Credibility source of the information |
| language | string | Language code (e.g., en-US) |
| confidence | number | Confidence score (0.0 to 1.0) |

**Additional Metadata Fields** (in the metadata design):
- trust_level: high/medium/low assessment of information reliability
- difficulty: beginner/intermediate/advanced reading level
- source: original source or reference for the document information

## Metadata Design

Every document includes machine-readable metadata enabling filtering and search:

| Field | Description | Example |
|-------|-------------|---------|
| category | High-level classification | "scams", "legitimate" |
| subcategory | Specific sub-classification | "phishing", "banking", "communication" |
| language | ISO 639-1 language code | "en-US", "es-ES" |
| tags | Keyword array for filtering | ["phishing", "credential_theft"] |
| version | Semantic version number | "1.0", "1.1.0" |
| trust_level | Reliability assessment | "high", "medium", "low" |
| last_updated | Review date (YYYY-MM-DD) | "2026-08-15" |
| difficulty | Reading complexity | "beginner", "intermediate", "advanced" |
| source | Original reference | "FTC", "APWG", "RBI" |

**Metadata Search Support:**
- Filter by category
- Filter by subcategory
- Filter by tags (any match)
- Filter by language
- Filter by trust level
- Filter by version (prefix matching)

## Validation Rules

The validation system checks for:

1. **Missing fields**: All 21 required schema fields must be present and non-empty
2. **Schema violations**: Field type validation (confidence 0.0-1.0, version format, etc.)
3. **Invalid references**: source_credibility must not be empty
4. **Broken metadata**: trust_level must be high/medium/low, last_updated must be YYYY-MM-DD
5. **Duplicate entries**: Duplicate titles are detected and flagged
6. **Subcategory-category consistency**: Subcategory must match category's valid values

**Validation Failure Detection:**
- Schema validation errors are prefixed with "SCHEMA:"
- Metadata validation errors are prefixed with "METADATA:"
- Duplicate detection errors are prefixed with "DUPLICATE:"
- Reference errors are prefixed with "REFERENCE:"

## Versioning

The knowledge base supports document versioning using semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR version**: Incremented for schema changes or structural updates
- **MINOR version**: Incremented for content updates, new examples, or additional information
- **PATCH version**: Incremented for minor fixes, typo corrections, or small updates

**Version Compatibility:**
- Future updates should increment version without breaking compatibility
- Backward-compatible changes: MINOR or PATCH increments
- Breaking changes: MAJOR increment (may require schema updates)
- Version searching supports prefix matching (e.g., "1.0" matches "1.0", "1.0.1", "1.1")

## Future RAG Integration

The knowledge base is designed to integrate with Retrieval-Augmented Generation systems:

- **Structured documents**: Each document follows a consistent schema enabling reliable retrieval
- **Metadata-enabled search**: Filter by category, tags, language, trust level before semantic retrieval
- **Entity extraction**: Documents contain identifiable entities (names, amounts, dates, organizations)
- **Confidence scoring**: Each document has a confidence score (0.0-1.0) for prioritization
- **Version-aware retrieval**: Can retrieve specific document versions when needed
- **Behavioral pattern matching**: Documents include manipulation techniques and indicators for pattern matching

The knowledge base does NOT currently include:
- Vector embeddings ( Step 11 explicitly states "Do NOT create embeddings yet")
- Vector database integration
- LLM integration
- RAG retrieval pipeline
- Decision engine

These components can be built on top of this structured knowledge base foundation.

## Quality Requirements

The knowledge base meets all quality requirements:

- **Accurate**: Evidence-based information from credible sources (FTC, APWG, government agencies)
- **Well organized**: Consistent folder structure and document schema
- **Human-readable**: Narrative documents with clear headings and sections
- **Machine-readable**: Standardized JSON schema and machine metadata
- **Easy to update**: Versioned documents with clear update rules
- **Easy to extend**: New documents can be added in existing categories
- **Consistent**: Uniform schema across all 15 steps
- **Suitable for semantic retrieval**: Organized for both keyword and semantic search capabilities