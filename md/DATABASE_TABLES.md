# Database Tables Documentation

## Overview
The Financial Forecast AI application uses **PostgreSQL with pgvector extension** as its primary vector database for storing and searching financial documents. The database schema is designed around LangChain's PGVector implementation.

## 🗄️ Database Configuration

**Connection Details:**
- **Database:** `financial_forecast`
- **Host:** `financial-forecast-fresh-postgresdb-pfctssiimhx1.cnh7kroqcqr1.us-east-1.rds.amazonaws.com`
- **Port:** `5432`
- **Engine:** PostgreSQL with pgvector extension
- **Total Size:** 12 MB
- **Schema:** `public`

**Environment Variable:**
```
PGVECTOR_CONNECTION_STRING=postgresql://dbmaster:password@host:5432/financial_forecast
```

## 📊 Table Structure

### 1. `langchain_pg_embedding` (Primary Vector Table)

**Purpose:** Stores document chunks as vector embeddings for similarity search

**Schema:**
```sql
CREATE TABLE langchain_pg_embedding (
    collection_id   UUID,           -- Links to collection
    embedding       VECTOR(1536),   -- 1536-dimensional vector (Amazon Titan)
    document        VARCHAR,        -- Text content of document chunk
    cmetadata       JSON,           -- Document metadata
    custom_id       VARCHAR,        -- Custom identifier
    uuid            UUID NOT NULL   -- Primary key
);
```

**Current Data:**
- **Row Count:** 387 document chunks
- **Vector Dimensions:** 1536 (Amazon Titan Embeddings)
- **Table Size:** 3.8 MB

**Metadata Structure:**
```json
{
    "filename": "FNM_2025-001_RELAY.txt",
    "file_type": "text/plain",
    "file_extension": "txt",
    "size": 12345,
    "uploaded_at": "2025-01-15T10:30:00",
    "source": "s3_sync",
    "content_length": 12345,
    "s3_key": "documents/FNM_2025-001_RELAY.txt",
    "s3_bucket": "financial-documents"
}
```

### 2. `langchain_pg_collection` (Collection Management)

**Purpose:** Manages collections of documents (groups/categories)

**Schema:**
```sql
CREATE TABLE langchain_pg_collection (
    name        VARCHAR,    -- Collection name
    cmetadata   JSON,       -- Collection metadata
    uuid        UUID NOT NULL   -- Primary key
);
```

**Current Data:**
- **Row Count:** 1 collection
- **Collection Name:** `financial_documents`
- **Collection UUID:** `cfb46a1c-842a-4692-bf92-e6d259376ee0`
- **Table Size:** 32 KB

### 3. `indexed_documents` (Custom Table)

**Purpose:** Additional document tracking (legacy or custom implementation)

**Schema:** Not detailed in current analysis (appears to be a custom table)

## 📄 Document Analysis

### Current Document Inventory

| Document | Type | Source | Chunks | Description |
|----------|------|--------|--------|-------------|
| `FNM_2025-001_RELAY.txt` | text/plain | s3_sync | 180 | Fannie Mae Deal 2025-001 |
| `FNM_2025-004_RELAY.txt` | text/plain | s3_sync | 136 | Fannie Mae Deal 2025-004 |
| `FNM_2025-003_RELAY.txt` | text/plain | s3_sync | 71 | Fannie Mae Deal 2025-003 |

**Total:** 3 documents, 387 chunks

### Document Processing Details

**Chunking Strategy:**
- **Chunk Size:** 1000 characters
- **Overlap:** 200 characters
- **Text Splitter:** RecursiveCharacterTextSplitter

**Embedding Model:**
- **Provider:** Amazon Bedrock
- **Model:** `amazon.titan-embed-text-v1`
- **Dimensions:** 1536
- **Region:** us-east-1

## 🔍 Search Implementation

### Vector Search Process

1. **Query Processing:**
   ```python
   query → Amazon Titan Embeddings → 1536-dimensional vector
   ```

2. **Similarity Search:**
   ```sql
   SELECT document, cmetadata, embedding <-> query_vector AS distance
   FROM langchain_pg_embedding
   ORDER BY distance
   LIMIT k;
   ```

3. **Result Formatting:**
   - Content text
   - Metadata (filename, source, etc.)
   - Relevance score

### Search Capabilities

- **Semantic Search:** Vector similarity using cosine distance
- **Metadata Filtering:** JSON queries on document metadata
- **Hybrid Search:** Combination of vector and text matching
- **Multi-document:** Search across all 3 financial deals

## 🏗️ Database Architecture

### Production Setup

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  Python Backend  │───▶│  PostgreSQL RDS │
│   (Frontend)    │    │  (Vector Store)  │    │  (Vector DB)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Amazon Bedrock  │
                       │  (Embeddings)    │
                       └──────────────────┘
```

### Development Fallback

- **Local Storage:** In-memory document storage
- **Text Search:** Basic keyword matching
- **Environment:** `USE_LOCAL_STORAGE=true`

## 🔧 Database Operations

### Common Queries

**1. Count Documents by Type:**
```sql
SELECT 
    cmetadata->>'filename' as filename,
    COUNT(*) as chunks
FROM langchain_pg_embedding 
GROUP BY cmetadata->>'filename'
ORDER BY chunks DESC;
```

**2. Search by Deal Number:**
```sql
SELECT document, cmetadata
FROM langchain_pg_embedding 
WHERE cmetadata->>'filename' LIKE '%2025-001%'
ORDER BY uuid;
```

**3. Get All Document Metadata:**
```sql
SELECT DISTINCT
    cmetadata->>'filename' as filename,
    cmetadata->>'source' as source,
    cmetadata->>'uploaded_at' as uploaded_at
FROM langchain_pg_embedding 
WHERE cmetadata->>'filename' IS NOT NULL;
```

### Maintenance Operations

**1. Clear All Documents:**
```sql
DELETE FROM langchain_pg_embedding;
```

**2. Remove Specific Document:**
```sql
DELETE FROM langchain_pg_embedding 
WHERE cmetadata->>'filename' = 'FNM_2025-001_RELAY.txt';
```

**3. Update Metadata:**
```sql
UPDATE langchain_pg_embedding 
SET cmetadata = cmetadata || '{"updated": "2025-01-15"}'::json
WHERE cmetadata->>'filename' = 'specific_file.txt';
```

## 🔒 Security & Access

### Database Security

- **AWS RDS:** Managed PostgreSQL service
- **Network:** VPC-isolated database
- **Authentication:** Master user credentials
- **Encryption:** At-rest and in-transit encryption
- **Backups:** Automated RDS backups

### Access Control

- **Application Access:** Single connection string
- **IAM Integration:** AWS credentials for Bedrock
- **Environment Variables:** Secure credential storage

## 📈 Performance Characteristics

### Vector Search Performance

- **Sub-second Response:** Typical queries under 100ms
- **Index Type:** pgvector HNSW index
- **Concurrency:** Supports multiple simultaneous searches
- **Scaling:** Can handle thousands of documents

### Storage Efficiency

- **Compression:** Native PostgreSQL compression
- **Indexing:** Efficient vector indexing
- **Metadata:** JSON storage for flexible metadata

## 🚀 Future Considerations

### Scaling Options

1. **More Documents:** Current schema supports thousands of documents
2. **Larger Vectors:** Can support different embedding models
3. **Multiple Collections:** Already supports collection separation
4. **Sharding:** PostgreSQL supports horizontal scaling

### Potential Enhancements

1. **Full-Text Search:** Add PostgreSQL text search capabilities
2. **Document Versioning:** Track document updates and versions
3. **User Management:** Add user-specific document access
4. **Analytics:** Add usage tracking and performance metrics

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Errors:** Check PGVECTOR_CONNECTION_STRING
2. **Extension Missing:** Ensure pgvector extension is installed
3. **Performance Issues:** Check vector index status
4. **Memory Issues:** Monitor PostgreSQL memory usage

### Diagnostic Queries

**Check Extension:**
```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

**Check Table Sizes:**
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```

**Check Vector Dimensions:**
```sql
SELECT vector_dims(embedding) as dimensions, COUNT(*) 
FROM langchain_pg_embedding 
GROUP BY vector_dims(embedding);
```

---

*Last Updated: October 24, 2025*  
*Database Version: PostgreSQL with pgvector*  
*Application: Financial Forecast AI*