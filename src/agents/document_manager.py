"""
Document Manager for Financial Forecast AI
Manages document storage and knowledge base updates (unified with UI uploads)
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class DocumentManager:
    """Manages documents in the knowledge base (same behavior as UI uploads)"""
    
    def __init__(self, vector_store=None):
        """
        Initialize document manager
        
        Args:
            vector_store: VectorStore instance for indexing documents
        """
        self.vector_store = vector_store
        self.use_local_storage = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"
        
        # Database connection string for vector store queries
        self.connection_string = os.getenv("PGVECTOR_CONNECTION_STRING")
    def get_indexed_documents_summary(self) -> Dict:
        """Get summary of all indexed documents from vector store"""
        if self.use_local_storage:
            # For local storage, we can't easily count vector store documents
            # Just return basic info
            return {
                "total_documents": 0,
                "storage_type": "local",
                "documents": []
            }
        
        if not self.connection_string:
            return {"total_documents": 0, "storage_type": "none", "documents": []}
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT cmetadata->>'filename' as filename,
                       cmetadata->>'source' as source,
                       cmetadata->>'content_length' as content_length,
                       cmetadata->>'uploaded_at' as uploaded_at,
                       COUNT(*) as chunks_count
                FROM langchain_pg_embedding 
                WHERE cmetadata->>'filename' IS NOT NULL
                GROUP BY cmetadata->>'filename', cmetadata->>'source', 
                         cmetadata->>'content_length', cmetadata->>'uploaded_at'
                ORDER BY cmetadata->>'uploaded_at' DESC
            """)
            
            documents = [dict(row) for row in cur.fetchall()]
            
            # Get unique documents count
            cur.execute("""
                SELECT COUNT(DISTINCT cmetadata->>'filename') as total
                FROM langchain_pg_embedding 
                WHERE cmetadata->>'filename' IS NOT NULL
            """)
            total = cur.fetchone()['total']
            
            cur.close()
            conn.close()
            
            return {
                "total_documents": total,
                "storage_type": "postgresql_vector_store",
                "documents": documents
            }
            
        except Exception as e:
            print(f"❌ Error getting indexed documents summary: {str(e)}")
            return {"total_documents": 0, "storage_type": "error", "documents": []}
    
    def process_documents_batch(self, documents: List[Dict]) -> Dict:
        """
        Process a batch of documents exactly like UI uploads
        (No deduplication - just index everything directly into vector store)
        
        Args:
            documents: List of documents with 'content' and 'metadata' keys
            
        Returns:
            Dictionary with processing results
        """
        if not documents:
            return {
                "total_documents": 0,
                "new_documents": 0,
                "skipped_duplicates": 0,
                "processing_errors": 0,
                "processed_documents": []
            }
        
        results = {
            "total_documents": len(documents),
            "new_documents": 0,
            "skipped_duplicates": 0,
            "processing_errors": 0,
            "processed_documents": []
        }
        
        print(f"📊 Processing {len(documents)} documents (same as UI uploads)...")
        
        for doc in documents:
            try:
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                filename = metadata.get('filename', 'unknown')
                
                # Create metadata exactly like UI uploads
                ui_style_metadata = {
                    "filename": filename,
                    "file_type": metadata.get('content_type', 'unknown'),
                    "file_extension": filename.split('.')[-1].lower() if '.' in filename else 'unknown',
                    "size": len(content),
                    "uploaded_at": datetime.now().isoformat(),
                    "source": "s3_sync",  # Mark as S3 source
                    "content_length": len(content),
                    # Keep S3-specific metadata as well
                    "s3_key": metadata.get('s3_key'),
                    "s3_bucket": metadata.get('s3_bucket')
                }
                
                # Index the document directly (same as UI uploads)
                if self.vector_store:
                    print(f"📄 Indexing: {filename}")
                    
                    # Index document into vector store (chunks automatically)
                    self.vector_store.index_document(content, ui_style_metadata)
                    
                    # Get chunks count for reporting
                    chunks = self.vector_store.text_splitter.split_text(content)
                    chunks_count = len(chunks)
                    
                    results["new_documents"] += 1
                    results["processed_documents"].append({
                        "filename": filename,
                        "chunks": chunks_count,
                        "size": len(content),
                        "source": "s3_sync"
                    })
                    
                    print(f"✅ Indexed: {filename} ({chunks_count} chunks)")
                    
                else:
                    print(f"⚠️ No vector store available for indexing {filename}")
                    results["processing_errors"] += 1
                
            except Exception as e:
                print(f"❌ Error processing document {filename}: {str(e)}")
                results["processing_errors"] += 1
                continue
        
        print(f"""
🎉 Batch processing complete (UI upload style):
   📄 Total documents: {results['total_documents']}
   ✅ Documents indexed: {results['new_documents']}
   ❌ Processing errors: {results['processing_errors']}
        """)
        
        return results
    
    def cleanup_orphaned_records(self) -> int:
        """Clean up orphaned vector store entries (placeholder - same as UI uploads)"""
        print("🧹 No cleanup needed - same behavior as UI uploads")
        return 0