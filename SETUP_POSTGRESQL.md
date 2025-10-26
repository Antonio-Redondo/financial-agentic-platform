# Setting Up PostgreSQL for Financial Forecast App

## Summary of Changes Made

✅ **Removed all local storage functionality** - The app now only uses PostgreSQL with pgvector extension
✅ **Simplified vector store** - Removed complex TF-IDF and local relevance scoring 
✅ **Database-only approach** - All document storage and search now happens in PostgreSQL

## Required Setup

### 1. **Set PostgreSQL Connection String**

The app now **requires** a PostgreSQL database with pgvector extension. Set the environment variable:

```bash
# Windows PowerShell
$env:PGVECTOR_CONNECTION_STRING = "postgresql://username:password@host:port/database"

# Example for local PostgreSQL:
$env:PGVECTOR_CONNECTION_STRING = "postgresql://postgres:mypassword@localhost:5432/financial_docs"
```

### 2. **Database Requirements**

Your PostgreSQL database must have:
- ✅ **pgvector extension** installed
- ✅ **Tables created** for vector storage (automatically created on first run)
- ✅ **Proper permissions** for the user account

### 3. **Environment Variables Needed**

```bash
# Required
$env:PGVECTOR_CONNECTION_STRING = "postgresql://username:password@host:port/database"

# Required for AWS Bedrock
$env:AWS_REGION = "us-east-1" 
$env:AWS_ACCESS_KEY_ID = "your_key"
$env:AWS_SECRET_ACCESS_KEY = "your_secret"
```

## Benefits of This Change

### ✅ **Consistent Storage**
- All documents stored in PostgreSQL
- No data loss between app restarts
- Proper ACID transactions

### ✅ **Better Performance** 
- Native vector similarity search
- Optimized database queries
- Scalable to large document collections

### ✅ **Production Ready**
- No temporary local storage
- Database-backed persistence
- Multi-user support ready

### ✅ **Simplified Architecture**
- Removed complex local relevance algorithms
- Uses proven PostgreSQL vector search
- Easier to maintain and debug

## Why You Weren't Getting Expected Results

The previous issue was likely because:

1. **Mixed storage modes** - App was sometimes using local storage, sometimes PostgreSQL
2. **Complex relevance scoring** - Local TF-IDF methods weren't being applied consistently  
3. **Debug output missing** - Local storage debug prints weren't showing in PostgreSQL mode
4. **Inconsistent indexing** - Documents might have been in local storage but not in database

## Next Steps

1. **Set up PostgreSQL** with pgvector extension
2. **Configure environment variables** as shown above
3. **Restart the app** - it will now only use PostgreSQL
4. **Re-upload documents** to ensure they're properly indexed in the database
5. **Test deal-specific queries** - should now work consistently

The app will now give you **consistent, database-backed results** for all your deal-specific queries!