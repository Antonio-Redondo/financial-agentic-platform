# Relevance Calculation System

## Overview

The Financial Forecast AI application uses a sophisticated **two-tier relevance scoring system** that combines AI-powered vector similarity with domain-specific financial scoring logic. This ensures that financial queries receive the most contextually relevant and accurate document matches.

## Architecture

```
Query → Vector Search → Custom Scoring → Final Ranking
  ↓           ↓              ↓             ↓
User    Amazon Titan    Financial Logic   Sorted
Input   Embeddings      Term Frequency    Results
        + PostgreSQL    + Header Boosts
        pgvector        + Deal Filtering
```

## 1. Vector Similarity Score (Primary Layer)

### Technology Stack
- **Embedding Model**: Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`)
- **Vector Database**: PostgreSQL with pgvector extension
- **Similarity Metric**: Cosine similarity

### Implementation
```python
# In vector_store.py
docs = self.vector_store.similarity_search_with_score(
    query=query,
    k=k
)
```

### Score Characteristics
- **Range**: 0.0 to ~2.0 (cosine distance)
- **Direction**: Lower values = higher similarity
- **Purpose**: Semantic understanding of query intent
- **Strengths**: Handles synonyms, context, and conceptual relationships

### Example
Query: "pricing speed for deal" → Finds documents containing "settlement speed", "execution velocity", etc.

## 2. Custom Query Relevance Score (Enhancement Layer)

### Purpose
Adds financial domain expertise and precision to the semantic search results.

### Implementation
```python
# From financial_agent.py
scored_results = []
for result in strict_filtered_results:
    content = result.get('content', '').lower()
    score = 0
    
    # Base scoring for query terms
    for term in query_terms.split():
        if term in content:
            score += content.count(term)
    
    # Enhanced scoring for specific financial queries
    if any(word in query.lower() for word in ['tranche', 'tranches', 'count', 'number', 'how many']):
        if 'number_of_tranches' in content:
            score += 1000  # Critical field boost
        elif 'deal_number' in content and deal_number in content:
            score += 100   # Header section boost
    
    result['query_relevance_score'] = score
```

### Scoring Components

#### A. Term Frequency Scoring
- **Formula**: `content.count(term)` for each query word
- **Purpose**: Rewards documents with multiple mentions of query terms
- **Example**: "pricing speed" query gets +2 for a document mentioning "pricing" twice

#### B. Financial Context Boosts
- **Tranche Count Queries**: +1000 points for `NUMBER_OF_TRANCHES` field
- **Deal Header Information**: +100 points for deal header sections
- **Critical Field Detection**: Identifies and prioritizes key financial data fields

#### C. Deal-Specific Filtering
Before scoring, results are filtered for deal specificity:

```python
# Strict deal filtering
if deal_number in filename.lower():
    strict_filtered_results.append(result)
elif f"deal_number                       :  {deal_number}" in content:
    strict_filtered_results.append(result)
else:
    # Reject - not from the correct deal
    pass
```

## 3. Smart Document Chunking Impact

The relevance system benefits from intelligent document preprocessing:

### Financial Document Splitter
- **Deal Information**: Kept as single chunks (critical for header queries)
- **Tranche Information**: Split by individual tranches
- **Structure Preservation**: Maintains logical document sections

### Chunk Optimization
```python
# Deal header chunks preserved for queries like "how many tranches"
if "DEAL INFORMATION" in section.upper():
    chunks.append(section)  # Keep complete header
```

## 4. Final Ranking System

### Primary Sort Key
Results are ranked by **query_relevance_score** (custom scoring):

```python
scored_results.sort(key=lambda x: x.get('query_relevance_score', 0), reverse=True)
```

### Score Preservation
Both scores are maintained for transparency:
- `similarity_score`: Original vector similarity
- `query_relevance_score`: Enhanced financial relevance

## 5. Query-Specific Optimizations

### Deal-Specific Queries
1. **Pattern Detection**: `20\d{2,3}-\d{3}` (e.g., "2025-003", "20250-001")
2. **Context Awareness**: Uses last mentioned deal from conversation history
3. **Targeted Search**: Searches specifically for deal-related content first

### Tranche Count Queries
- **Keywords**: "tranche", "tranches", "count", "number", "how many"
- **Boost Strategy**: +1000 for `NUMBER_OF_TRANCHES` field
- **Header Priority**: Ensures deal header information is top-ranked

### Pricing/Speed Queries
- **Keywords**: "pricing", "settlement", "speed", "rate"
- **Strategy**: Combines semantic search with exact term matching

## 6. Performance Metrics

### Latency Tracking
```python
# Component-level timing
embedding_latency = (time.time() - embedding_start_time) * 1000
search_latency = (time.time() - start_time) * 1000
```

### Quality Metrics
- **Average Similarity Score**: Tracks semantic relevance quality
- **Min/Max Similarity Range**: Ensures consistent result quality
- **Result Count**: Monitors search effectiveness

## 7. LangSmith Integration

### Comprehensive Tracing
```python
langsmith_manager.trace_vector_search(
    query=query,
    results=[{"doc_id": i, "score": r["similarity_score"]} for i, r in enumerate(results)],
    metadata={
        "embedding_model": "amazon.titan-embed-text-v2:0",
        "avg_similarity_score": avg_score,
        "min_similarity_score": min_score,
        "max_similarity_score": max_score,
        "total_latency_ms": search_latency
    }
)
```

### Debugging Capabilities
- Individual result scoring details
- Query enhancement tracking
- Performance profiling

## 8. Example Scoring Walkthrough

### Query: "How many tranches in deal 20250-001?"

#### Step 1: Vector Search
- Embeds query using Amazon Titan
- PostgreSQL returns semantically similar chunks
- Base `similarity_score`: 0.24 (good match)

#### Step 2: Deal Filtering
- Filters results to only include deal 20250-001
- Rejects cross-deal contamination

#### Step 3: Custom Scoring
- Term frequency: "tranches" appears 2 times → +2
- "how many" detected → triggers tranche count boost
- Found `NUMBER_OF_TRANCHES: 6` → +1000 boost
- **Final query_relevance_score**: 1002

#### Step 4: Final Ranking
- Ranked by query_relevance_score (1002)
- Higher than other results with lower boosts
- Ensures most relevant answer is first

## 9. Benefits of Dual Scoring

### Semantic Understanding
- Handles natural language variations
- Understands financial terminology context
- Captures user intent even with imprecise queries

### Financial Precision
- Prioritizes exact financial data fields
- Ensures deal-specific accuracy
- Boosts critical information (tranche counts, pricing)

### Context Preservation
- Maintains conversation context across queries
- Uses last mentioned deal for follow-up questions
- Preserves query topic focus

## 10. Configuration Parameters

### Vector Search Settings
- **k**: Number of results (typically 5-7)
- **embedding_model**: `amazon.titan-embed-text-v2:0`
- **chunk_size**: 1200 characters
- **chunk_overlap**: 100 characters

### Custom Scoring Weights
- **Term Frequency**: 1x per occurrence
- **Tranche Count Boost**: +1000
- **Deal Header Boost**: +100
- **Content Request Multiplier**: 7 vs 5 results

## 11. Future Enhancements

### Potential Improvements
1. **Dynamic Boost Weights**: Adjust boosts based on query complexity
2. **Temporal Relevance**: Consider document recency
3. **User Feedback Integration**: Learn from user interactions
4. **Multi-Modal Scoring**: Incorporate table/chart recognition

### Performance Optimizations
1. **Caching**: Cache embeddings for frequent queries
2. **Index Optimization**: Optimize PostgreSQL indexes
3. **Batch Processing**: Batch multiple queries for efficiency

---

## Summary

The relevance calculation system provides a sophisticated balance between AI-powered semantic understanding and financial domain expertise. This dual approach ensures that users receive accurate, contextual, and highly relevant financial information while maintaining the flexibility to handle natural language queries effectively.

The system's strength lies in its ability to understand both the semantic intent of queries and the specific requirements of financial data analysis, making it particularly effective for complex financial document analysis tasks.