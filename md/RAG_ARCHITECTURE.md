# RAG Architecture in Financial Forecast AI

## Overview
The Financial Forecast AI application implements RAG (Retrieval Augmented Generation) in three main phases:

1. **Indexing Phase (Document Processing)**
2. **Retrieval Phase (Context Search)**
3. **Generation Phase (Analysis & Response)**

## Detailed Architecture

```
┌─── Indexing Phase ────────────────────────────────────┐
│                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌────────┐  │
│  │  Document    │    │    Text      │    │  Text  │  │
│  │  Loading     │ -> │  Chunking    │ -> │ Vector │  │
│  │  (PyPDF)     │    │  (1K chunks) │    │ Store  │  │
│  └──────────────┘    └──────────────┘    └────────┘  │
│                                              │        │
└──────────────────────────────────────────────┼────────┘
                                               │
┌─── Retrieval Phase ───────────────────────────────────┐
│                                               ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌────────┐  │
│  │   Query      │    │   Vector     │    │ Vector │  │
│  │ Embedding    │ -> │  Similarity  │ <- │  DB    │  │
│  │ Generation   │    │   Search     │    │(pgvec) │  │
│  └──────────────┘    └──────────────┘    └────────┘  │
│                            │                          │
└────────────────────────────┼──────────────────────────┘
                             │
┌─── Generation Phase ───────┼──────────────────────────┐
│                           ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌────────┐  │
│  │  Context     │    │    LLM       │    │Response│  │
│  │  Assembly    │ -> │  Generation  │ -> │Delivery│  │
│  │              │    │  (Claude)    │    │        │  │
│  └──────────────┘    └──────────────┘    └────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘

```

## Phase Descriptions

### 1. Indexing Phase
```python
# Document Processing (src/core/vector_store.py)
class VectorStore:
    def create_vector_store(self, documents_path):
        # Load PDFs
        loader = DirectoryLoader(documents_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        texts = text_splitter.split_documents(documents)
        
        # Create embeddings and store in pgvector
        vector_store = PGVector.from_documents(
            embedding=self.embeddings,
            documents=texts,
            connection_string=self.connection_string
        )
```

### 2. Retrieval Phase
```python
# Context Retrieval (src/core/vector_store.py)
def search_documents(self, query, k=5):
    vector_store = PGVector(
        embedding_function=self.embeddings,
        connection_string=self.connection_string
    )
    # Perform similarity search
    return vector_store.similarity_search(query, k=k)
```

### 3. Generation Phase
```python
# Response Generation (src/core/analyst.py)
class FinancialAnalyst:
    def create_analysis_chain(self, context):
        template = """You are an expert financial analyst. Use the following context 
        from financial documents to answer questions about prepayment speeds and rates.

        Context: {context}
        Chat History: {chat_history}
        Question: {question}

        Provide a detailed analysis based on the context provided."""
        
        prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=template
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory
        )
```

## Data Flow

1. **Document Ingestion**:
   - PDF documents (prospectus reports, relay files) are uploaded
   - Documents are split into chunks of 1000 tokens with 100 token overlap
   - Each chunk is embedded using AWS Bedrock embeddings
   - Vectors are stored in PostgreSQL using pgvector extension

2. **Query Processing**:
   - User questions are embedded using the same embedding model
   - Vector similarity search finds relevant document chunks
   - Top k (default=5) most relevant chunks are retrieved

3. **Response Generation**:
   - Retrieved contexts are assembled into a prompt
   - Chat history is included for conversation coherence
   - AWS Bedrock Claude model generates detailed analysis
   - Response is formatted and delivered through Streamlit UI

## Key Components

1. **Vector Store (PostgreSQL + pgvector)**:
   - Stores document embeddings
   - Enables efficient similarity search
   - Maintains document-vector relationships

2. **AWS Bedrock Integration**:
   - Claude Sonnet model for analysis
   - Embedding model for vector creation
   - Handles both document and query embedding

3. **Agent System**:
   - Orchestrates the RAG workflow
   - Manages conversation context
   - Coordinates between components

4. **User Interface**:
   - Streamlit-based web interface
   - Real-time document processing
   - Interactive chat functionality

## Performance Optimizations

1. **Chunking Strategy**:
   - 1000-token chunks balance context and relevance
   - 100-token overlap maintains contextual coherence
   - Recursive splitting preserves document structure

2. **Vector Search**:
   - pgvector index for fast similarity search
   - Configurable k for result precision
   - Cosine similarity metric for matching

3. **Response Generation**:
   - Context window optimization
   - Chat history management
   - Temperature control for response consistency

## Monitoring and Logging

- Vector store operations logging
- Query performance metrics
- Response generation timing
- Error tracking and handling

## Security Considerations

- AWS IAM role-based access
- Database connection security
- Document access controls
- API endpoint protection