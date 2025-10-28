# Standard library imports
import os
import re
import time
from typing import Dict, List

# Third-party imports
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from .langsmith_integration import langsmith_manager, trace_financial_operation, trace_bedrock_call, with_langsmith_callbacks


class FinancialDocumentSplitter:
    """Smart splitter for financial documents that preserves section structure"""
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def split_text(self, text: str) -> List[str]:
        """Split financial document while preserving logical sections"""
        chunks = []
        
        # Define section patterns based on the document format
        section_patterns = [
            r"###############\s+DEAL INFORMATION\s+###############",
            r"###############\s+COLLATERAL INFORMATION\s+###############", 
            r"###############\s+TRANCHE INFORMATION\s+###############",
            r"###############\s+REREMIC INFORMATION\s+###############",
            r"###############\s+RECOMBINABLE INFORMATION\s+###############"
        ]
        
        # Split by major sections first
        sections = self._split_by_sections(text, section_patterns)
        
        for section in sections:
            # For each section, create smart chunks
            section_chunks = self._create_section_chunks(section)
            chunks.extend(section_chunks)
            
        return chunks
    
    def _split_by_sections(self, text: str, patterns: List[str]) -> List[str]:
        """Split text by major section headers"""
        sections = []
        current_pos = 0
        
        for pattern in patterns:
            match = re.search(pattern, text[current_pos:], re.IGNORECASE)
            if match:
                # Add previous section if exists
                if current_pos > 0:
                    section_content = text[current_pos:current_pos + match.start()].strip()
                    if section_content:
                        sections.append(section_content)
                
                # Find start of current section
                section_start = current_pos + match.start()
                
                # Find next section or end of document
                next_section_pos = len(text)
                for next_pattern in patterns:
                    if next_pattern != pattern:
                        next_match = re.search(next_pattern, text[section_start + len(match.group()):], re.IGNORECASE)
                        if next_match:
                            next_section_pos = min(next_section_pos, section_start + len(match.group()) + next_match.start())
                
                # Extract complete section
                section_content = text[section_start:next_section_pos].strip()
                if section_content:
                    sections.append(section_content)
                
                current_pos = next_section_pos
        
        # Add remaining content
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                sections.append(remaining)
                
        return sections if sections else [text]
    
    def _create_section_chunks(self, section: str) -> List[str]:
        """Create smart chunks within a section"""
        chunks = []
        
        # Check if this is the Deal Information section (most important for queries)
        if "DEAL INFORMATION" in section.upper():
            # Keep deal header together - this is critical for tranche count queries
            chunks.append(section)
            return chunks
        
        # Check if this is Tranche Information section
        elif "TRANCHE INFORMATION" in section.upper():
            # Split by individual tranches (each starts with TRANCHE_NUMBER)
            tranche_chunks = self._split_tranche_section(section)
            chunks.extend(tranche_chunks)
            return chunks
        
        # For other sections, use size-based chunking with preservation
        elif len(section) <= self.chunk_size:
            # Section fits in one chunk
            chunks.append(section)
        else:
            # Need to split section, but preserve structure
            subsection_chunks = self._split_preserving_structure(section)
            chunks.extend(subsection_chunks)
            
        return chunks
    
    def _split_tranche_section(self, section: str) -> List[str]:
        """Split tranche section by individual tranches"""
        chunks = []
        
        # Find all tranche starts
        tranche_pattern = r"\nTRANCHE_NUMBER\s+:\s+\d+"
        matches = list(re.finditer(tranche_pattern, section))
        
        if not matches:
            # No tranches found, return as single chunk
            return [section]
        
        # Add section header to first chunk
        section_lines = section.split('\n')
        header_lines = []
        for line in section_lines:
            if 'TRANCHE INFORMATION' in line or line.startswith('#'):
                header_lines.append(line)
            else:
                break
        
        # Process each tranche
        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(section)
            
            tranche_content = section[start_pos:end_pos].strip()
            
            # Add header to first tranche chunk for context
            if i == 0 and header_lines:
                tranche_content = '\n'.join(header_lines) + '\n' + tranche_content
                
            # If tranche is too large, split it further
            if len(tranche_content) > self.chunk_size:
                sub_chunks = self._split_preserving_structure(tranche_content)
                chunks.extend(sub_chunks)
            else:
                chunks.append(tranche_content)
                
        return chunks
    
    def _split_preserving_structure(self, text: str) -> List[str]:
        """Split text while preserving line structure"""
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # If adding this line would exceed chunk size and we have content
            if current_size + line_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap (last few lines)
                overlap_lines = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk
                current_chunk = overlap_lines + [line]
                current_size = sum(len(l) + 1 for l in current_chunk)
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
            
        return chunks


class VectorStore:
    def __init__(self):
        # Use amazon.titan-embed-text-v2:0 (Titan Text Embeddings V2)
        # This is the latest v2 embedding model from Amazon
        try:
            self.embeddings = with_langsmith_callbacks(
                BedrockEmbeddings,
                model_id="amazon.titan-embed-text-v2:0",
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            # Test the dimensions with Bedrock tracing
            with trace_bedrock_call("amazon.titan-embed-text-v2:0", "embedding_test"):
                test_embed = self.embeddings.embed_query("test")
            print(f"[INFO] Embedding dimensions: {len(test_embed)}")
        except Exception as e:
            print(f"[ERROR] Embedding initialization failed: {e}")
            raise
        
        # Initialize PGVector with connection string from environment
        connection_string = os.getenv("PGVECTOR_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("[ERROR] PGVECTOR_CONNECTION_STRING environment variable is required")
        
        try:
            self.vector_store = PGVector(
                connection_string=connection_string,
                embedding_function=self.embeddings,
                collection_name="financial_documents"
            )
            print("[SUCCESS] Successfully connected to PostgreSQL vector store")
        except Exception as e:
            if "already defined" in str(e):
                # Try to connect to existing store
                print("[WARNING] Vector store tables already exist, connecting to existing store...")
                try:
                    # Use from_existing_index to connect to existing tables
                    self.vector_store = PGVector.from_existing_index(
                        embedding=self.embeddings,
                        connection_string=connection_string,
                        collection_name="financial_documents"
                    )
                    print("[SUCCESS] Successfully connected to existing vector store")
                except Exception as e2:
                    raise Exception(f"[ERROR] Failed to connect to existing vector store: {str(e2)}")
            else:
                raise Exception(f"[ERROR] Error initializing vector store: {str(e)}")
        
        # Smart financial document splitter instead of generic text splitter
        self.financial_splitter = FinancialDocumentSplitter(
            chunk_size=1200,
            chunk_overlap=100
        )
        
    @trace_financial_operation("document_indexing")
    def index_document(self, document: str, metadata: Dict = None) -> None:
        """Index a document into the vector store using smart financial chunking"""
        start_time = time.time()
        print(f"[INFO] Indexing document with smart financial chunking...")
        
        # Split document into intelligent chunks
        chunking_start_time = time.time()
        chunks = self.financial_splitter.split_text(document)
        chunking_latency = (time.time() - chunking_start_time) * 1000
        
        print(f"[INFO] Created {len(chunks)} smart chunks from document")
        
        # Debug: Show chunk info for verification
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            chunk_preview = chunk[:150].replace('\n', ' ')
            print(f"  Chunk {i+1}: {chunk_preview}... ({len(chunk)} chars)")
        
        # Add chunks to PGVector store
        indexing_start_time = time.time()
        self.vector_store.add_texts(
            texts=chunks,
            metadatas=[metadata] * len(chunks) if metadata else None
        )
        indexing_latency = (time.time() - indexing_start_time) * 1000
        
        total_latency = (time.time() - start_time) * 1000
        
        # Log document processing to LangSmith
        langsmith_manager.trace_document_processing(
            document_path=metadata.get("source", "unknown") if metadata else "unknown",
            chunks_created=len(chunks),
            metadata={
                "component": "vector_store",
                "document_length": len(document),
                "avg_chunk_size": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
                "chunking_latency_ms": chunking_latency,
                "indexing_latency_ms": indexing_latency,
                "total_latency_ms": total_latency,
                "embedding_model": "amazon.titan-embed-text-v2:0"
            }
        )
        
        print(f"[SUCCESS] Successfully indexed {len(chunks)} chunks")
        
    @trace_financial_operation("document_search")
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant documents using PostgreSQL vector similarity"""
        start_time = time.time()
        
        # Trace the embedding call with Bedrock context
        embedding_start_time = time.time()
        with trace_bedrock_call("amazon.titan-embed-text-v2:0", "document_search"):
            docs = self.vector_store.similarity_search_with_score(
                query=query,
                k=k
            )
        embedding_latency = (time.time() - embedding_start_time) * 1000
        
        # Format results with enhanced tracing
        results = []
        for doc, score in docs:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            }
            results.append(result)
            
            # Log individual result details for debugging
            print(f"[DEBUG] Search result - Score: {score:.6f}, Content length: {len(doc.page_content)}")
        
        search_latency = (time.time() - start_time) * 1000
        
        # Log vector search to LangSmith with enhanced debugging
        langsmith_manager.trace_vector_search(
            query=query,
            results=[{"doc_id": i, "score": r["similarity_score"]} for i, r in enumerate(results)],
            metadata={
                "component": "vector_store",
                "embedding_model": "amazon.titan-embed-text-v2:0",
                "k": k,
                "total_results": len(results),
                "avg_similarity_score": sum(r["similarity_score"] for r in results) / len(results) if results else 0,
                "min_similarity_score": min(r["similarity_score"] for r in results) if results else 0,
                "max_similarity_score": max(r["similarity_score"] for r in results) if results else 0,
                "embedding_latency_ms": embedding_latency,
                "total_latency_ms": search_latency,
                "query_length": len(query),
                "best_match_content_preview": results[0]["content"][:200] if results else "No results"
            }
        )
        
        return results
    
    def get_all_documents_info(self) -> List[Dict]:
        """Get information about all stored documents for debugging"""
        return [{"info": "Using PostgreSQL storage - cannot easily list all documents"}]