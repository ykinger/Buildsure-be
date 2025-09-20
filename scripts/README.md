# OBC Scripts Documentation

This directory contains scripts for managing Ontario Building Code (OBC) data in the BuildSure system.

## Current Scripts

### `obc_manager.py` - Unified OBC Management Tool
**Primary script for all OBC operations.**

#### Usage:
```bash
# Load OBC data from markdown file
python scripts/obc_manager.py load --file "assets/2024 OBC.Volume 1 refined.md"

# Load with clearing existing data first
python scripts/obc_manager.py load --file "assets/2024 OBC.Volume 1 refined.md" --clear

# Test query functionality
python scripts/obc_manager.py test

# Show database status
python scripts/obc_manager.py status

# Reset database (clear all OBC data)
python scripts/obc_manager.py reset
```

#### Features:
- **Clean Division Values**: Automatically generates clean division names ("Division A", "Division B", etc.) during parsing
- **Batch Processing**: Efficiently loads large files with progress tracking
- **Query Testing**: Validates exact equality queries vs LIKE patterns
- **Database Management**: Status checking, reset functionality
- **Error Handling**: Comprehensive error handling with rollback support

## Key Services

### `app/services/obc_parser.py` - Enhanced OBC Parser
- Parses hierarchical OBC markdown structure
- Generates clean division values from the start
- Supports all hierarchy levels: Division → Part → Section → Subsection → Article
- Handles Index sections separately

### `app/services/obc_query_service.py` - Optimized Query Service
- Provides optimized query methods using exact equality
- Avoids LIKE operators for structured data
- Includes performance-optimized patterns for hierarchical queries

## Database Schema

### `ontario_chunks` Table Structure:
```sql
CREATE TABLE ontario_chunks (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    reference VARCHAR(20) NOT NULL,
    division VARCHAR(50),           -- Clean values: "Division A", "Division B", etc.
    part VARCHAR(10),
    section VARCHAR(10),
    subsection VARCHAR(10),
    article VARCHAR(10),
    chunk_type VARCHAR(20) NOT NULL,  -- "division", "part", "section", "subsection", "article", "index"
    title VARCHAR(200),
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);
```

### Indexes:
- `ix_ontario_chunks_reference` - For reference lookups
- `ix_ontario_chunks_part` - For hierarchical queries
- `ix_ontario_chunks_section` - For hierarchical queries
- `ix_ontario_chunks_subsection` - For hierarchical queries
- `ix_ontario_chunks_article` - For hierarchical queries

## Query Optimization Guidelines

### ✅ DO:
- Use `==` for exact matches (division, part, section, etc.)
- Use indexed columns in WHERE clauses
- Use `IN()` for multiple specific values
- Use `ilike()` for case-insensitive pattern matching
- Combine conditions with `and_()` for readability

### ❌ DON'T:
- Use LIKE when `==` would work
- Use LIKE with `%` on both sides unless necessary
- Query without using indexed columns
- Use OR conditions when `IN()` would work better

## Example Queries

### Optimized Hierarchical Queries:
```python
# Get all articles in a specific subsection
articles = await service.get_all_articles_in_subsection(
    division="Division A",
    part="1", 
    section="2",
    subsection="1"
)

# Get specific article by reference
article = await service.get_article_by_reference(
    reference="1.2.1.1",
    division="Division A"
)

# Search content (appropriate use of LIKE)
fire_articles = await service.search_content(
    search_term="fire",
    chunk_type="article",
    division="Division A"
)
```

## Data Statistics

Current OBC database contains:
- **3,528 total chunks**
- **2,695 articles** (detailed building code provisions)
- **662 subsections** (grouped articles)
- **149 sections** (major topic areas)
- **18 parts** (high-level divisions)
- **4 divisions** (Division A, B, C, and Index)

## Archive

The `archive/` directory contains legacy scripts that have been consolidated:
- `load_obc_chunks.py` - Replaced by `obc_manager.py load`
- `clean_division_values.py` - No longer needed (clean values generated at parse time)
- `test_obc_retrieval.py` - Replaced by `obc_manager.py test`
- `optimized_obc_queries.py` - Functionality moved to `obc_query_service.py`
- `load_building_code.py` - Legacy loader
- `ingest_obc.py` - Legacy ingestion script
- `test_obc_system.py` - Legacy test script

## Migration Notes

The system has been upgraded to:
1. **Generate clean division values during parsing** (no post-processing needed)
2. **Use exact equality queries** for optimal performance
3. **Provide unified management interface** through single script
4. **Support flexible hierarchical retrieval** at any level

For any OBC-related operations, use `obc_manager.py` as the primary interface.
