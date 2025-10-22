from typing import Dict, List
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class VectorStore:
    def __init__(self):
        self.use_local_storage = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"
        
        if not self.use_local_storage:
            self.embeddings = BedrockEmbeddings(
                model_id="amazon.titan-embed-text-v1",
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            
            # Initialize PGVector with connection string from environment
            connection_string = os.getenv("PGVECTOR_CONNECTION_STRING")
            if connection_string:
                try:
                    self.vector_store = PGVector(
                        connection_string=connection_string,
                        embedding_function=self.embeddings,
                        collection_name="financial_documents"
                    )
                except Exception as e:
                    if "already defined" in str(e):
                        # Try to connect to existing store
                        print("⚠️ Vector store tables already exist, connecting to existing store...")
                        try:
                            # Use from_existing_index to connect to existing tables
                            self.vector_store = PGVector.from_existing_index(
                                embedding=self.embeddings,
                                connection_string=connection_string,
                                collection_name="financial_documents"
                            )
                            print("✅ Successfully connected to existing vector store")
                        except Exception as e2:
                            print(f"❌ Failed to connect to existing vector store: {str(e2)}")
                            print("⚠️ Falling back to local storage")
                            self.vector_store = None
                            self.use_local_storage = True
                    else:
                        print(f"❌ Error initializing vector store: {str(e)}")
                        self.vector_store = None
                        self.use_local_storage = True
            else:
                self.vector_store = None
                print("Warning: No database connection string found. Using local storage.")
                self.use_local_storage = True
        
        if self.use_local_storage:
            # Use in-memory storage for development
            self.documents = []
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def index_document(self, document: str, metadata: Dict = None) -> None:
        """Index a document into the vector store"""
        # Split document into chunks
        chunks = self.text_splitter.split_text(document)
        
        if self.use_local_storage:
            # Store in memory for development
            for chunk in chunks:
                self.documents.append({
                    "content": chunk,
                    "metadata": metadata or {}
                })
        else:
            # Add chunks to vector store
            if self.vector_store:
                self.vector_store.add_texts(
                    texts=chunks,
                    metadatas=[metadata] * len(chunks) if metadata else None
                )
        
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant documents with improved matching"""
        if self.use_local_storage:
            print(f"🔍 Local search for: '{query}' in {len(self.documents)} documents")
            
            # Enhanced text matching for local storage
            results = []
            query_lower = query.lower()
            query_words = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
            
            for doc in self.documents:
                content_lower = doc["content"].lower()
                
                # Check for exact phrase match (high relevance)
                if query_lower in content_lower:
                    relevance = 1.0
                    results.append({
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "relevance_score": relevance
                    })
                    continue
                
                # Check for individual word matches
                word_matches = sum(1 for word in query_words if word in content_lower)
                if word_matches > 0:
                    relevance = word_matches / len(query_words) if query_words else 0.0
                    # Boost relevance for more matches
                    relevance = min(0.95, relevance + (word_matches * 0.1))
                    
                    results.append({
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "relevance_score": relevance
                    })
            
            # If no matches with words, try partial matches
            if not results and query_words:
                for doc in self.documents:
                    content_lower = doc["content"].lower()
                    partial_matches = sum(1 for word in query_words 
                                        for content_word in content_lower.split() 
                                        if word in content_word or content_word in word)
                    if partial_matches > 0:
                        relevance = (partial_matches * 0.3) / len(query_words)
                        results.append({
                            "content": doc["content"],
                            "metadata": doc["metadata"],
                            "relevance_score": relevance
                        })
            
            # Sort by relevance and return top k results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            print(f"📊 Found {len(results)} matching documents")
            return results[:k]
        else:
            # Perform similarity search with vector store
            if self.vector_store:
                docs = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
                
                # Format results
                results = []
                for doc, score in docs:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": float(score)
                    })
                
                return results
            else:
                return []
    
    def get_all_documents_info(self) -> List[Dict]:
        """Get information about all stored documents for debugging"""
        if self.use_local_storage:
            return [{
                "filename": doc.get("metadata", {}).get("filename", "unknown"),
                "content_length": len(doc.get("content", "")),
                "content_preview": doc.get("content", "")[:200] + "...",
                "metadata": doc.get("metadata", {})
            } for doc in self.documents]
        else:
            return [{"info": "Using PostgreSQL storage - cannot easily list all documents"}]
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate a basic relevance score based on keyword matching"""
        query_words = query.split()
        matches = sum(1 for word in query_words if word in content)
        return matches / len(query_words) if query_words else 0.0