from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from .analyst import FinancialAnalyst
from .vector_store import VectorStore
from .workflow import create_financial_workflow

load_dotenv()

class FinancialAgent:
    def __init__(self):
        self.analyst = FinancialAnalyst()
        self.vector_store = VectorStore()
        
        # Initialize LangGraph multi-agent workflow
        try:
            self.workflow = create_financial_workflow(self.vector_store)
            self.use_multi_agent = True
            print("✅ Multi-agent LangGraph workflow initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize multi-agent workflow: {e}")
            print("🔄 Falling back to single-agent mode")
            self.workflow = None
            self.use_multi_agent = False
        
    def search_and_analyze(self, query: str) -> str:
        """Search documents and analyze the results using multi-agent workflow when possible"""
        print(f"🔍 Processing query: {query}")
        
        # Use multi-agent workflow if available
        if self.use_multi_agent and self.workflow:
            try:
                print("🤖 Using LangGraph multi-agent workflow")
                workflow_result = self.workflow.execute_workflow(query)
                
                if workflow_result.get("success", False):
                    print(f"✅ Multi-agent workflow completed successfully (confidence: {workflow_result.get('confidence', 0):.1%})")
                    return workflow_result.get("response", "No response generated")
                else:
                    print(f"❌ Multi-agent workflow failed: {workflow_result.get('response', 'Unknown error')}")
                    print("🔄 Falling back to single-agent mode")
                    
            except Exception as e:
                print(f"❌ Multi-agent workflow error: {e}")
                print("🔄 Falling back to single-agent mode")
        
        # Fallback to original single-agent logic
        print("🔄 Using single-agent mode")
        return self._single_agent_analysis(query)
    
    def _single_agent_analysis(self, query: str) -> str:
        """Original single-agent analysis logic (fallback)"""
        print(f"🔍 Processing query: {query}")
        
        # Determine if user is asking for document content specifically
        content_keywords = ['content', 'document', 'text', 'show me', 'what does', 'extract', 'summary', 'details', 'analyze', 'analysis', 'financial', 'data', 'report', 'findings']
        is_content_request = any(keyword in query.lower() for keyword in content_keywords)
        
        # Search for relevant documents with more results - be more aggressive
        search_limit = 7 if is_content_request else 5
        
        print(f"📊 Document search - is_content_request: {is_content_request}, search_limit: {search_limit}")
        
        try:
            # Check if we have documents in the vector store
            if self.vector_store.use_local_storage:
                total_docs = len(self.vector_store.documents)
                print(f"📁 Total documents in local storage: {total_docs}")
                if total_docs > 0:
                    print("📄 Sample document metadata:")
                    for i, doc in enumerate(self.vector_store.documents[:3]):
                        print(f"  Doc {i+1}: {doc.get('metadata', {}).get('filename', 'unknown')} - {len(doc.get('content', ''))} chars")
            
            search_results = self.vector_store.search_documents(query, k=search_limit)
            print(f"🔍 Initial search results: {len(search_results)} documents found")
            
            # If no results found, try broader financial terms
            if not search_results and self.vector_store.use_local_storage and len(self.vector_store.documents) > 0:
                print("🔄 No initial results, trying broader search...")
                broader_terms = ["financial", "revenue", "profit", "analysis", "data", "report", "summary", "total", "amount", "year", "quarter", "percent", "%"]
                for term in broader_terms:
                    if term.lower() in query.lower():
                        continue  # Skip if already searched
                    broader_results = self.vector_store.search_documents(term, k=3)
                    if broader_results:
                        search_results.extend(broader_results)
                        print(f"🔍 Found {len(broader_results)} results with broader term '{term}'")
                        break
            
            # Remove duplicates and limit results
            seen_content = set()
            unique_results = []
            for result in search_results:
                content_hash = hash(result.get('content', '')[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            search_results = unique_results[:search_limit]
            
            for i, result in enumerate(search_results):
                print(f"  Result {i+1}: {result.get('metadata', {}).get('filename', 'unknown')} (score: {result.get('relevance_score', 0):.2f})")
                
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            # If vector store isn't working, proceed without search results
            search_results = []
        
        # Combine search results into context
        context = ""
        if search_results:
            context = "=== RELEVANT DOCUMENT CONTENT ===\n\n"
            for i, result in enumerate(search_results, 1):
                if isinstance(result, dict) and 'content' in result:
                    metadata = result.get('metadata', {})
                    filename = metadata.get('filename', f'Document {i}')
                    relevance = result.get('relevance_score', 0)
                    
                    context += f"📄 SOURCE: {filename} (Relevance: {relevance:.2f})\n"
                    context += f"CONTENT: {result['content']}\n"
                    context += "-" * 50 + "\n\n"
                    print(f"✅ Including content from {filename} (relevance: {relevance:.2f})")
                else:
                    context += f"Document {i}:\n{str(result)}\n\n"
        else:
            # Check if there are any documents in the system
            total_docs = len(self.vector_store.documents) if self.vector_store.use_local_storage else "unknown"
            if total_docs == 0:
                context = "⚠️ No documents have been uploaded to the system yet. Please upload documents to get specific content-based responses."
                print("⚠️ No documents in system")
            else:
                context = f"⚠️ No relevant content found in the {total_docs} uploaded documents for this query."
                print(f"⚠️ No relevant content found in {total_docs} documents for query: '{query}'")
        
        # Create enhanced analysis prompt optimized for Amazon Titan's capabilities
        if search_results and context and "RELEVANT DOCUMENT CONTENT" in context:
            # For queries with document content available, be assertive about using it
            analysis_query = f"""
You are a senior financial analyst with access to specific document content. The user has uploaded financial documents and is asking for analysis based on those documents.

USER QUERY: {query}

{context}

CRITICAL INSTRUCTIONS:
- You HAVE access to the document content provided above
- You MUST base your response on the actual document content provided
- DO NOT say you don't have access to documents - you do have access via the content above
- Extract specific data, numbers, and insights from the provided document content
- Provide detailed financial analysis using the actual data from the documents
- Quote specific sections when relevant
- If asked for summaries, summarize the actual content provided above

Your response should demonstrate expertise by analyzing the specific financial data, metrics, and information contained in the provided document content. Be specific and detailed in your analysis.
            """
        else:
            # For queries without specific document content
            total_docs = len(self.vector_store.documents) if self.vector_store.use_local_storage else 0
            if total_docs > 0:
                analysis_query = f"""
You are a senior financial analyst. The user has uploaded {total_docs} documents to the system, but no specific content was found relevant to this query: "{query}"

USER QUERY: {query}

INSTRUCTIONS:
- Acknowledge that the user has uploaded documents but this specific query didn't match content in those documents
- Provide general financial analysis and insights related to the query
- Suggest more specific questions that might find relevant content in their uploaded documents
- Focus on delivering expert financial knowledge while noting the document search didn't find matches

Provide comprehensive financial analysis addressing the question with your financial expertise.
            """
            else:
                analysis_query = f"""
You are a senior financial analyst providing expert financial insights.

USER QUERY: {query}

INSTRUCTIONS:
- No documents have been uploaded to the system yet
- Provide comprehensive financial analysis based on your expertise
- Include relevant financial principles, methodologies, and best practices
- Suggest what types of documents would be helpful for more specific analysis

Deliver expert-level financial insights addressing the user's question.
            """
        
        # Get analysis from the financial analyst
        analysis_result = self.analyst.analyze(analysis_query)
        return analysis_result.get("analysis", "No analysis available.")
    
    def process_query(self, query: str) -> Dict:
        """Process a user query using multi-agent or single-agent approach"""
        try:
            # Check for complex analysis keywords that benefit from multi-agent approach
            complex_keywords = ['risk', 'market', 'forecast', 'analysis', 'assessment', 'recommendation', 'strategy', 'prepayment', 'portfolio']
            is_complex_query = any(keyword in query.lower() for keyword in complex_keywords)
            
            if self.use_multi_agent and self.workflow and is_complex_query:
                print("🎯 Complex query detected - using multi-agent workflow")
                workflow_result = self.workflow.execute_workflow(query)
                
                if workflow_result.get("success", False):
                    return {
                        "output": workflow_result.get("response", "No response generated"),
                        "workflow_used": "multi-agent",
                        "confidence": workflow_result.get("confidence", 0.5)
                    }
                else:
                    print("🔄 Multi-agent failed, falling back to single-agent")
            
            # Use single-agent approach for simple queries or as fallback
            analysis_result = self.search_and_analyze(query)
            
            return {
                "output": analysis_result,
                "workflow_used": "single-agent",
                "confidence": 0.8
            }
                
        except Exception as e:
            # Fallback response in case of errors
            return {
                "output": f"I'm currently experiencing technical difficulties. Please try again later. Error: {str(e)}",
                "workflow_used": "error",
                "confidence": 0.0
            }
    
    def create_agent(self):
        """For compatibility - returns self"""
        return self
            
    def get_document_stats(self) -> Dict:
        """Get statistics about indexed documents"""
        if self.vector_store.use_local_storage:
            total_chunks = len(self.vector_store.documents)
            unique_docs = len(set(doc['metadata'].get('filename', 'unknown') 
                                for doc in self.vector_store.documents))
        else:
            # For PGVector, we'd need to query the database
            total_chunks = "unknown"
            unique_docs = "unknown"
            
        return {
            "total_chunks": total_chunks,
            "unique_documents": unique_docs,
            "storage_type": "local" if self.vector_store.use_local_storage else "postgresql"
        }
    
    def invoke(self, input_data: Dict) -> Dict:
        """For compatibility with AgentExecutor interface"""
        query = input_data.get("input", "")
        return self.process_query(query)