"""
Application Initialization Service
Handles S3 document loading and knowledge base setup on application startup
"""
import os
import time
from typing import Dict, Optional
from .s3_loader import S3DocumentLoader
from .document_manager import DocumentManager


class AppInitializationService:
    """Service to initialize the application with S3 documents"""
    
    def __init__(self, vector_store=None):
        """
        Initialize the service
        
        Args:
            vector_store: VectorStore instance for document indexing
        """
        self.vector_store = vector_store
        self.document_manager = DocumentManager(vector_store)
        
        # S3 configuration
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")
        self.s3_prefix = os.getenv("S3_DOCUMENTS_PREFIX", "documents/")
        self.auto_load_enabled = os.getenv("S3_AUTO_LOAD_ENABLED", "false").lower() == "true"
        
        self.s3_loader = None
        if self.s3_bucket and self.auto_load_enabled:
            try:
                self.s3_loader = S3DocumentLoader(self.s3_bucket, self.s3_prefix)
            except Exception as e:
                print(f"⚠️ S3 loader initialization failed: {str(e)}")
                self.s3_loader = None
    
    def is_s3_enabled(self) -> bool:
        """Check if S3 auto-loading is enabled and configured"""
        return (
            self.auto_load_enabled and 
            self.s3_bucket and 
            self.s3_loader is not None
        )
    
    def get_initialization_status(self) -> Dict:
        """Get the current initialization configuration status"""
        return {
            "s3_enabled": self.is_s3_enabled(),
            "s3_bucket": self.s3_bucket,
            "s3_prefix": self.s3_prefix,
            "auto_load_enabled": self.auto_load_enabled,
            "vector_store_available": self.vector_store is not None,
            "use_local_storage": os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"
        }
    
    def initialize_knowledge_base(self, show_progress: bool = True) -> Dict:
        """
        Initialize the knowledge base with S3 documents
        
        Args:
            show_progress: Whether to show progress information
            
        Returns:
            Dictionary with initialization results
        """
        start_time = time.time()
        
        if show_progress:
            print("🚀 Initializing Financial Forecast AI Knowledge Base...")
        
        # Check configuration
        if not self.is_s3_enabled():
            message = "S3 auto-loading not enabled or configured"
            if show_progress:
                print(f"ℹ️ {message}")
            
            return {
                "success": True,
                "message": message,
                "s3_enabled": False,
                "documents_processed": 0,
                "processing_time": time.time() - start_time
            }
        
        if not self.vector_store:
            message = "Vector store not available for indexing"
            if show_progress:
                print(f"❌ {message}")
            
            return {
                "success": False,
                "message": message,
                "s3_enabled": True,
                "documents_processed": 0,
                "processing_time": time.time() - start_time
            }
        
        try:
            if show_progress:
                print(f"📁 Loading documents from S3 bucket: {self.s3_bucket}")
                print(f"📂 Document prefix: {self.s3_prefix}")
            
            # Load and process documents from S3
            s3_documents = self.s3_loader.load_and_process_documents()
            
            if not s3_documents:
                message = "No documents found in S3 bucket"
                if show_progress:
                    print(f"📭 {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "s3_enabled": True,
                    "documents_processed": 0,
                    "processing_time": time.time() - start_time
                }
            
            # Process documents through the document manager
            if show_progress:
                print(f"🔄 Processing {len(s3_documents)} documents...")
            
            processing_results = self.document_manager.process_documents_batch(s3_documents)
            
            # Calculate timing
            processing_time = time.time() - start_time
            
            if show_progress:
                print(f"⏱️ Processing completed in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "message": f"Successfully processed {processing_results['new_documents']} new documents",
                "s3_enabled": True,
                "documents_processed": processing_results['new_documents'],
                "total_documents": processing_results['total_documents'],
                "skipped_duplicates": processing_results['skipped_duplicates'],
                "processing_errors": processing_results['processing_errors'],
                "processing_time": processing_time,
                "processed_documents": processing_results['processed_documents']
            }
            
        except Exception as e:
            error_message = f"Error during knowledge base initialization: {str(e)}"
            if show_progress:
                print(f"❌ {error_message}")
            
            return {
                "success": False,
                "message": error_message,
                "s3_enabled": True,
                "documents_processed": 0,
                "processing_time": time.time() - start_time
            }
    
    def get_knowledge_base_summary(self) -> Dict:
        """Get summary of the current knowledge base"""
        return self.document_manager.get_indexed_documents_summary()
    
    def refresh_knowledge_base(self) -> Dict:
        """Refresh the knowledge base by re-checking S3 for new documents"""
        if not self.is_s3_enabled():
            return {
                "success": False,
                "message": "S3 auto-loading not enabled"
            }
        
        print("🔄 Refreshing knowledge base from S3...")
        return self.initialize_knowledge_base(show_progress=True)