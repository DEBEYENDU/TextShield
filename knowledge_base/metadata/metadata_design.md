Metadata Design Document

Every knowledge base document must include the following machine-readable metadata fields:

1. category: High-level classification (e.g., scams, legitimate, behavioral_patterns, communication_styles, examples, glossary, metadata)
   - Purpose: Enables categorization-based filtering and retrieval
   - Values: Controlled vocabulary based on knowledge base structure

2. subcategory: Specific sub-classification within the category
   - Purpose: Enables granular filtering within categories
   - Values: Depends on category (e.g., scams: lottery, phishing, banking, otp, etc.)

3. language: Language code following ISO 639-1 format (e.g., en-US, en-GB, es-ES, fr-FR)
   - Purpose: Language filtering for multilingual knowledge bases
   - Default: en-US

4. tags: Array of keyword tags for categorization, search, and filtering
   - Purpose: Enables tag-based search and classification
   - Values: Free-form keywords relevant to document content
   - Example: ["phishing", "credential_theft", "financial_fraud"]

5. version: Document version number following semantic versioning (MAJOR.MINOR.PATCH)
   - Purpose: Version tracking and compatibility management
   - Format: 1.0, 1.1, 2.0, etc.
   - Default: 1.0
   - Rule: Increment MAJOR for schema changes, MINOR for content updates, PATCH for minor fixes

6. trust_level: Assessment of information reliability source
   - Purpose: Indicates credibility and reliability of the document content
   - Values: high, medium, low
   - Determination: Based on source credibility, evidence quality, consensus

7. last_updated: Date the document was last reviewed or modified (YYYY-MM-DD format)
   - Purpose: Tracks document currency and freshness
   - Format: 2026-08-15
   - Rule: Must be updated whenever document content is modified

8. difficulty: Assessment of reading/comprehension difficulty
   - Purpose: Helps match documents to appropriate audience expertise levels
   - Values: beginner, intermediate, advanced
   - Determination: Based on technical content, terminology, and complexity

9. source: Original source or references for the document information
   - Purpose: Traceability and credibility verification
   - Values: Authority name, URL, or reference identifier
   - Example: "FTC", "APWG", "RBI", "World Bank", specific report URLs

Additional Considerations:
- All metadata fields are required (no optional fields)
- Metadata should be machine-readable (JSON format recommended)
- Metadata schema should align with the main knowledge document schema
- Versioning should support backward compatibility
- Trust level should be independently verifiable
- Last_updated should be automated where possible
- Tags should follow controlled vocabulary where feasible