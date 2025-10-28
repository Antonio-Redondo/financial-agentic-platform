
# Standard library imports
import os
from datetime import datetime
from typing import Dict, List
import time

# Third-party imports
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
from langchain.schema import BaseMessage
from langchain_community.chat_models import BedrockChat
from langchain_core.messages import HumanMessage, AIMessage

# Local imports
from .analyst import FinancialAnalyst
from .vector_store import VectorStore
from .workflow_orchestrator import create_financial_workflow
from .langsmith_integration import langsmith_manager, trace_financial_operation, with_langsmith_callbacks, trace_bedrock_call

load_dotenv()

class FinancialAgent:
    def __init__(self):
        self.analyst = FinancialAnalyst()
        self.vector_store = VectorStore()
        
        # Initialize LangChain memory systems
        self._initialize_langchain_memory()
        
        # Keep custom context for backwards compatibility and enhanced features
        self.conversation_history = []
        self.conversation_context = {}
        self.max_context_messages = 10  # Keep last 10 exchanges for context
        
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
    
    def _initialize_langchain_memory(self):
        """Initialize LangChain memory components"""
        try:
            # Initialize Bedrock chat model for memory operations with LangSmith tracing
            self.chat_model = with_langsmith_callbacks(
                BedrockChat,
                model_id="amazon.titan-text-express-v1",
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            
            # Initialize ConversationBufferWindowMemory (keeps last N exchanges)
            self.buffer_memory = ConversationBufferWindowMemory(
                k=5,  # Keep last 5 conversation exchanges
                return_messages=True,
                memory_key="chat_history"
            )
            
            # Initialize ConversationSummaryBufferMemory (summarizes old conversations)
            self.summary_memory = ConversationSummaryBufferMemory(
                llm=self.chat_model,
                max_token_limit=2000,  # Summarize when conversation exceeds 2000 tokens
                return_messages=True,
                memory_key="conversation_summary"
            )
            
            print("✅ LangChain memory systems initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize LangChain memory: {e}")
            print("🔄 Falling back to custom memory only")
            self.buffer_memory = None
            self.summary_memory = None
            self.chat_model = None
    
    def _traced_chat_call(self, messages: List, operation_name: str = "chat_call") -> str:
        """Make a traced call to the Bedrock chat model"""
        if not self.chat_model:
            return "Chat model not available"
        
        start_time = time.time()
        try:
            with trace_bedrock_call("amazon.titan-text-express-v1", operation_name):
                response = self.chat_model.invoke(messages)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract content
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Trace the call
            langsmith_manager.trace_llm_response(
                prompt=str(messages),
                response=response_content,
                model_name="amazon.titan-text-express-v1",
                latency_ms=latency_ms,
                metadata={
                    "component": "financial_agent",
                    "operation": operation_name,
                    "message_count": len(messages)
                }
            )
            
            return response_content
            
        except Exception as e:
            print(f"Error in traced chat call: {e}")
            return f"Error: {e}"
        
    @trace_financial_operation("search_and_analyze")
    def search_and_analyze(self, query: str) -> str:
        """Search documents and analyze the results using multi-agent workflow when possible"""
        start_time = time.time()
        
        # Log query to LangSmith
        langsmith_manager.trace_query(
            query=query,
            response="",  # Will be updated after response
            metadata={"agent_mode": "multi" if self.use_multi_agent else "single", "query_type": "search_and_analyze"}
        )
        
        print(f"🔍 Processing query: {query}")
        
        # Use multi-agent workflow if available
        if self.use_multi_agent and self.workflow:
            try:
                print("🤖 Using LangGraph multi-agent workflow")
                workflow_result = self.workflow.execute_workflow(query)
                
                if workflow_result.get("success", False):
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # Log successful workflow to LangSmith
                    langsmith_manager.trace_llm_response(
                        prompt=query,
                        response=workflow_result.get("response", ""),
                        model_name="multi-agent-workflow",
                        latency_ms=latency_ms
                    )
                    
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
        
        # Detect deal-specific queries for more targeted search
        import re
        deal_pattern = r'(?:deal\s*)?20\d{2}-\d{3}'
        deal_matches = re.findall(deal_pattern, query.lower())
        is_deal_specific = bool(deal_matches)
        
        # Search for relevant documents with more results - be more aggressive
        search_limit = 7 if is_content_request else 5
        
        print(f"📊 Document search - is_content_request: {is_content_request}, search_limit: {search_limit}, is_deal_specific: {is_deal_specific}")
        if deal_matches:
            print(f"🎯 Deal-specific query detected for: {deal_matches}")
        
        try:
            # For deal-specific queries, use more targeted search approach
            if is_deal_specific and deal_matches:
                deal_number = deal_matches[0].replace("deal ", "").strip()
                print(f"🎯 Deal-specific query detected for: {deal_number}")
                
                # SUPER STRICT APPROACH: Search specifically for the deal number first
                deal_only_results = self.vector_store.search_documents(f"DEAL_NUMBER {deal_number}", k=10)
                print(f"🔍 Strict deal search for 'DEAL_NUMBER {deal_number}': {len(deal_only_results)} documents found")
                
                # ENHANCED: If asking about deal-level attributes, search specifically for header information
                deal_level_keywords = ['underwriter', 'issuer', 'trustee', 'pricing', 'settlement', 'date', 'speed', 'size']
                if any(word in query.lower() for word in deal_level_keywords):
                    # Use search strategies that actually work for finding the header
                    header_searches = [
                        f"BANK_OF_AMERICA",  # Direct search for known underwriter
                        f"DEAL INFORMATION",  # Header section search
                        f"UNDERWRITER",       # Field-specific search
                        f"FNM_{deal_number}"  # Filename-based search
                    ]
                    
                    header_results = []
                    for search_term in header_searches:
                        search_results = self.vector_store.search_documents(search_term, k=5)
                        # Filter to only include results from the correct deal
                        deal_specific_results = []
                        for result in search_results:
                            filename = result.get('metadata', {}).get('filename', '')
                            content = result.get('content', '')
                            # Include if it's from the right deal and contains header info
                            if deal_number in filename and ('DEAL INFORMATION' in content.upper() or 'UNDERWRITER' in content.upper()):
                                deal_specific_results.append(result)
                        header_results.extend(deal_specific_results)
                        print(f"🔍 Header search '{search_term}': {len(deal_specific_results)} deal-specific documents found")
                    
                    # Add header results to the mix (avoiding duplicates)
                    existing_ids = {id(r) for r in deal_only_results}
                    added_count = 0
                    for header_result in header_results:
                        if id(header_result) not in existing_ids:
                            deal_only_results.append(header_result)
                            added_count += 1
                            content = header_result.get('content', '')
                            if 'UNDERWRITER' in content.upper():
                                print(f"📊 Added UNDERWRITER header chunk for deal {deal_number}")
                    
                    print(f"📈 Total header chunks added: {added_count}")
                
                # ENHANCED: If asking about tranches, also search specifically for header information
                elif any(word in query.lower() for word in ['tranche', 'tranches', 'count', 'number', 'how many']):
                    header_results = self.vector_store.search_documents(f"DEAL_NUMBER {deal_number} NUMBER_OF_TRANCHES", k=5)
                    print(f"🔍 Header search for tranche count: {len(header_results)} documents found")
                    
                    # Add header results to the mix (avoiding duplicates)
                    existing_ids = {id(r) for r in deal_only_results}
                    for header_result in header_results:
                        if id(header_result) not in existing_ids:
                            deal_only_results.append(header_result)
                            print(f"📊 Added header chunk for tranche count analysis")
                
                # Alternative search with just the deal number
                if not deal_only_results:
                    deal_only_results = self.vector_store.search_documents(deal_number, k=10)
                    print(f"🔍 Fallback deal search for '{deal_number}': {len(deal_only_results)} documents found")
                
                # CRITICAL: Filter to ONLY include results that actually contain this exact deal
                strict_filtered_results = []
                for result in deal_only_results:
                    content = result.get('content', '').lower()
                    filename = result.get('metadata', {}).get('filename', '')
                    
                    # Check if this result is from the correct deal file
                    if deal_number in filename.lower():
                        strict_filtered_results.append(result)
                        print(f"✅ Including result from {filename} - filename contains deal {deal_number}")
                    elif f"deal_number                       :  {deal_number}" in content:
                        strict_filtered_results.append(result)
                        print(f"✅ Including result from {filename} - contains exact deal header for {deal_number}")
                    else:
                        print(f"❌ REJECTING result from {filename} - doesn't match deal {deal_number}")
                
                # Now search within these filtered results for the actual query
                if strict_filtered_results:
                    # Search within the deal-specific content for the query terms
                    query_terms = query.lower().replace(f"deal {deal_number}", "").replace(deal_number, "").strip()
                    if not query_terms:
                        query_terms = "information"  # Default if no specific terms
                    
                    print(f"🔍 Searching within deal {deal_number} content for: '{query_terms}'")
                    
                    # Score results based on query relevance within the correct deal
                    scored_results = []
                    for result in strict_filtered_results:
                        content = result.get('content', '').lower()
                        score = 0
                        
                        # Base scoring for query terms
                        for term in query_terms.split():
                            if term in content:
                                score += content.count(term)
                        
                        # ENHANCED: Boost score for header information when asking about tranches
                        if any(word in query.lower() for word in ['tranche', 'tranches', 'count', 'number', 'how many']):
                            if 'number_of_tranches' in content:
                                score += 1000  # Very high boost for the actual tranche count
                                print(f"🎯 BOOSTED score for header chunk with NUMBER_OF_TRANCHES")
                            elif 'deal_number' in content and deal_number in content:
                                score += 100   # Moderate boost for deal header chunks
                        
                        result['query_relevance_score'] = score
                        # Preserve the original similarity_score from vector search
                        if 'similarity_score' not in result:
                            result['similarity_score'] = result.get('similarity_score', 0.0)
                        scored_results.append(result)
                    
                    # Sort by query relevance within the correct deal
                    scored_results.sort(key=lambda x: x.get('query_relevance_score', 0), reverse=True)
                    search_results = scored_results[:search_limit]
                    
                    print(f"🎯 Final results: {len(search_results)} documents from deal {deal_number} only")
                    for i, result in enumerate(search_results):
                        filename = result.get('metadata', {}).get('filename', 'unknown')
                        score = result.get('query_relevance_score', 0)
                        print(f"  Result {i+1}: {filename} (query_score: {score})")
                else:
                    print(f"⚠️ No documents found specifically for deal {deal_number}")
                    search_results = []
            else:
                # Regular search for non-deal-specific queries
                search_results = self.vector_store.search_documents(query, k=search_limit)
            print(f"🔍 Initial search results: {len(search_results)} documents found")
            
            # If no results found, try alternative search approaches
            if not search_results:
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
                print(f"  Result {i+1}: {result.get('metadata', {}).get('filename', 'unknown')} (score: {result.get('similarity_score', 0):.2f})")
                
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
                    relevance = result.get('similarity_score', 0)
                    
                    context += f"📄 SOURCE: {filename} (Relevance: {relevance:.2f})\n"
                    context += f"CONTENT: {result['content']}\n"
                    context += "-" * 50 + "\n\n"
                    print(f"✅ Including content from {filename} (relevance: {relevance:.2f})")
                else:
                    context += f"Document {i}:\n{str(result)}\n\n"
        else:
            # Check if there are any documents in the system via PostgreSQL
            context = "⚠️ No relevant content found in the uploaded documents for this query."
            print(f"⚠️ No relevant content found for query: '{query}'")
        
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
            analysis_query = f"""
You are a senior financial analyst. The user has uploaded documents to the system, but no specific content was found relevant to this query: "{query}"

USER QUERY: {query}

INSTRUCTIONS:
- Acknowledge that the user has uploaded documents but this specific query didn't match content in those documents
- Provide general financial analysis and insights related to the query
- Suggest more specific questions that might find relevant content in their uploaded documents
- Focus on delivering expert financial knowledge while noting the document search didn't find matches

Provide comprehensive financial analysis addressing the question with your financial expertise.
            """
        
        # Get analysis from the financial analyst
        analysis_result = self.analyst.analyze(analysis_query)
        return analysis_result.get("analysis", "No analysis available.")
    
    @trace_financial_operation("process_query")
    def process_query(self, query: str) -> Dict:
        """Process a user query using multi-agent or single-agent approach with context"""
        start_time = time.time()
        
        try:
            # Enhance query with conversation context (custom + LangChain memory)
            enhanced_query = self._build_contextual_query_enhanced(query)
            
            # Check for complex analysis keywords that benefit from multi-agent approach
            complex_keywords = ['risk', 'market', 'forecast', 'analysis', 'assessment', 'recommendation', 'strategy', 'prepayment', 'portfolio']
            is_complex_query = any(keyword in enhanced_query.lower() for keyword in complex_keywords)
            
            # Log query processing to LangSmith
            deal_numbers = self._extract_deal_numbers(query)
            query_type = "complex" if is_complex_query else "simple"
            
            langsmith_manager.trace_financial_query(
                query=query,
                deal_numbers=deal_numbers,
                query_type=query_type,
                metadata={
                    "enhanced_query": enhanced_query,
                    "context_enhanced": enhanced_query != query,
                    "complex_analysis": is_complex_query
                }
            )
            
            # Use the enhanced query for processing
            query_to_process = enhanced_query
            
            if self.use_multi_agent and self.workflow and is_complex_query:
                print("🎯 Complex query detected - using multi-agent workflow")
                workflow_result = self.workflow.execute_workflow(query_to_process)
                
                if workflow_result.get("success", False):
                    response = workflow_result.get("response", "No response generated")
                    
                    # Log successful response to LangSmith
                    latency_ms = (time.time() - start_time) * 1000
                    langsmith_manager.trace_llm_response(
                        prompt=query_to_process,
                        response=response,
                        model_name="multi-agent-workflow",
                        latency_ms=latency_ms
                    )
                    
                    # Add conversation context to memory (both custom and LangChain)
                    self.add_to_conversation_history(query, response)
                    
                    return {
                        "output": response,
                        "workflow_used": "multi-agent",
                        "confidence": workflow_result.get("confidence", 0.5),
                        "context_used": enhanced_query != query
                    }
                else:
                    print("🔄 Multi-agent failed, falling back to single-agent")
            
            # Use single-agent approach for simple queries or as fallback
            analysis_result = self.search_and_analyze(query_to_process)
            
            # Log single-agent response to LangSmith
            latency_ms = (time.time() - start_time) * 1000
            langsmith_manager.trace_llm_response(
                prompt=query_to_process,
                response=analysis_result,
                model_name="single-agent-financial",
                latency_ms=latency_ms
            )
            
            # Add conversation context to memory
            self.add_to_conversation_history(query, analysis_result)
            
            return {
                "output": analysis_result,
                "workflow_used": "single-agent",
                "confidence": 0.8,
                "context_used": enhanced_query != query
            }
                
        except Exception as e:
            # Log error to LangSmith
            latency_ms = (time.time() - start_time) * 1000
            langsmith_manager.trace_llm_response(
                prompt=query,
                response=f"Error: {str(e)}",
                model_name="error-handler",
                latency_ms=latency_ms
            )
            
            # Fallback response in case of errors
            return {
                "output": f"I'm currently experiencing technical difficulties. Please try again later. Error: {str(e)}",
                "workflow_used": "error",
                "confidence": 0.0
            }
    
    def add_to_langchain_memory(self, user_message: str, ai_response: str):
        """Add conversation to LangChain memory systems"""
        try:
            if self.buffer_memory:
                # Add to buffer memory
                self.buffer_memory.chat_memory.add_user_message(user_message)
                self.buffer_memory.chat_memory.add_ai_message(ai_response)
            
            if self.summary_memory:
                # Add to summary memory
                self.summary_memory.chat_memory.add_user_message(user_message)
                self.summary_memory.chat_memory.add_ai_message(ai_response)
                
        except Exception as e:
            print(f"⚠️ Error adding to LangChain memory: {e}")
    
    def get_langchain_conversation_context(self) -> str:
        """Get conversation context from LangChain memory systems"""
        context_parts = []
        
        try:
            # Get recent conversation from buffer memory
            if self.buffer_memory:
                buffer_context = self.buffer_memory.load_memory_variables({})
                if "chat_history" in buffer_context and buffer_context["chat_history"]:
                    # Convert messages to readable format
                    recent_messages = buffer_context["chat_history"][-4:]  # Last 2 exchanges
                    for msg in recent_messages:
                        if hasattr(msg, 'content'):
                            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                            context_parts.append(f"{role}: {content_preview}")
            
            # Get summary from summary memory
            if self.summary_memory:
                summary_context = self.summary_memory.load_memory_variables({})
                if "conversation_summary" in summary_context and summary_context["conversation_summary"]:
                    summary = summary_context["conversation_summary"]
                    if isinstance(summary, str) and summary.strip():
                        context_parts.append(f"Summary: {summary[:150]}...")
                        
        except Exception as e:
            print(f"⚠️ Error getting LangChain context: {e}")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def get_langchain_memory_stats(self) -> Dict:
        """Get statistics about LangChain memory usage"""
        stats = {
            "buffer_memory_enabled": self.buffer_memory is not None,
            "summary_memory_enabled": self.summary_memory is not None,
            "buffer_messages": 0,
            "summary_available": False
        }
        
        try:
            if self.buffer_memory:
                buffer_vars = self.buffer_memory.load_memory_variables({})
                if "chat_history" in buffer_vars:
                    stats["buffer_messages"] = len(buffer_vars["chat_history"])
            
            if self.summary_memory:
                summary_vars = self.summary_memory.load_memory_variables({})
                stats["summary_available"] = bool(summary_vars.get("conversation_summary"))
                
        except Exception as e:
            print(f"⚠️ Error getting memory stats: {e}")
        
        return stats
    
    def _build_contextual_query_enhanced(self, query: str) -> str:
        """Enhanced query building with LangChain memory integration"""
        # Start with custom context
        enhanced_query = self._build_contextual_query(query)
        
        # Add LangChain memory context if available
        langchain_context = self.get_langchain_conversation_context()
        if langchain_context and enhanced_query == query:  # Only if custom context didn't enhance it
            # Check if query needs context enhancement
            import re
            context_needed_patterns = [
                r'\bit\b', r'\bthis\b', r'\bthat\b', r'\bthey\b', r'\bthem\b',
                r'\bcompare\s+(?:to|with|against)\s*$',
                r'\bwhat\s+about\b', r'\bhow\s+about\b'
            ]
            
            needs_context = any(re.search(pattern, query.lower()) for pattern in context_needed_patterns)
            if needs_context:
                enhanced_query = f"{query} (Context: {langchain_context})"
                print(f"🧠 Enhanced query with LangChain memory: {enhanced_query[:100]}...")
        
        return enhanced_query
    
    def clear_langchain_memory(self):
        """Clear all LangChain memory"""
        try:
            if self.buffer_memory:
                self.buffer_memory.clear()
            if self.summary_memory:
                self.summary_memory.clear()
            print("✅ LangChain memory cleared")
        except Exception as e:
            print(f"⚠️ Error clearing LangChain memory: {e}")
    
    def _extract_deal_numbers(self, query: str) -> List[str]:
        """Extract deal numbers from query"""
        import re
        deal_pattern = r'(?:deal\s*)?20\d{2}-\d{3}'
        deals = re.findall(deal_pattern, query.lower())
        return [deal.replace("deal ", "").strip() for deal in deals]
    
    def create_agent(self):
        """For compatibility - returns self"""
        return self
            
    def get_document_stats(self) -> Dict:
        """Get statistics about indexed documents"""
        # For PostgreSQL vector store, return basic stats
        total_chunks = "unknown (PostgreSQL)"
        unique_docs = "unknown (PostgreSQL)"
            
        return {
            "total_chunks": total_chunks,
            "unique_documents": unique_docs,
            "storage_type": "postgresql"
        }
    
    def add_to_conversation_history(self, user_message: str, ai_response: str):
        """Add a conversation exchange to history and update context"""
        # Add to custom conversation history
        self.conversation_history.append({
            "user": user_message,
            "assistant": ai_response,
            "timestamp": str(datetime.now())
        })
        
        # Keep only recent conversations to prevent context overflow
        if len(self.conversation_history) > self.max_context_messages:
            self.conversation_history = self.conversation_history[-self.max_context_messages:]
        
        # Add to LangChain memory systems
        self.add_to_langchain_memory(user_message, ai_response)
        
        # Update conversation context with key information
        self._update_conversation_context(user_message, ai_response)
    
    def _update_conversation_context(self, user_message: str, ai_response: str):
        """Extract and store key context from the conversation"""
        import re
        
        # Extract deal numbers mentioned
        deal_pattern = r'(?:deal\s*)?20\d{2}-\d{3}'
        deals_mentioned = re.findall(deal_pattern, user_message.lower() + " " + ai_response.lower())
        
        if deals_mentioned:
            if "recent_deals" not in self.conversation_context:
                self.conversation_context["recent_deals"] = []
            
            # Add unique deals to context
            for deal in deals_mentioned:
                deal_clean = deal.replace("deal ", "").strip()
                if deal_clean not in self.conversation_context["recent_deals"]:
                    self.conversation_context["recent_deals"].append(deal_clean)
            
            # Keep only last 5 deals mentioned
            self.conversation_context["recent_deals"] = self.conversation_context["recent_deals"][-5:]
        
        # Extract current topic/focus
        topic_keywords = {
            "pricing": ["pricing", "price", "speed", "rate"],
            "risk": ["risk", "credit", "prepayment", "default"],
            "structure": ["tranche", "structure", "subordination", "enhancement"],
            "metrics": ["WAC", "WAM", "yield", "duration", "balance"],
            "comparison": ["compare", "versus", "against", "relative"]
        }
        
        message_lower = user_message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                self.conversation_context["current_topic"] = topic
                break
    
    def _build_contextual_query(self, query: str) -> str:
        """Enhance query with conversation context when needed"""
        import re
        
        # Check if query needs context (contains pronouns or references)
        context_needed_patterns = [
            r'\bit\b', r'\bthis\b', r'\bthat\b', r'\bthey\b', r'\bthem\b',
            r'\bcompare\s+(?:to|with|against)\s*$',
            r'\bwhat\s+about\b', r'\bhow\s+about\b',
            r'\band\s+the\b', r'\bfor\s+the\s+same\b'
        ]
        
        needs_context = any(re.search(pattern, query.lower()) for pattern in context_needed_patterns)
        
        if not needs_context:
            return query
        
        # Build contextual enhancement
        context_additions = []
        
        # Add recent deals if context is needed
        if "recent_deals" in self.conversation_context and self.conversation_context["recent_deals"]:
            recent_deals = self.conversation_context["recent_deals"]
            if len(recent_deals) == 1:
                context_additions.append(f"for deal {recent_deals[0]}")
            else:
                context_additions.append(f"for deals {', '.join(recent_deals)}")
        
        # Add topic context
        if "current_topic" in self.conversation_context:
            topic = self.conversation_context["current_topic"]
            if topic not in query.lower():
                topic_context = {
                    "pricing": "pricing and speed information",
                    "risk": "risk assessment details",
                    "structure": "structural features and tranches",
                    "metrics": "financial metrics and calculations",
                    "comparison": "comparative analysis"
                }
                if topic in topic_context:
                    context_additions.append(f"focusing on {topic_context[topic]}")
        
        # Enhance the query
        if context_additions:
            enhanced_query = f"{query} {' '.join(context_additions)}"
            print(f"🔍 Enhanced query with context: {enhanced_query}")
            return enhanced_query
        
        return query
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the recent conversation for context"""
        if not self.conversation_history:
            return ""
        
        summary_parts = []
        
        # Recent conversation context
        if len(self.conversation_history) >= 2:
            last_exchange = self.conversation_history[-1]
            summary_parts.append(f"Previous question: {last_exchange['user'][:100]}...")
        
        # Context information
        if self.conversation_context:
            if "recent_deals" in self.conversation_context:
                deals = self.conversation_context["recent_deals"]
                summary_parts.append(f"Recent deals discussed: {', '.join(deals)}")
            
            if "current_topic" in self.conversation_context:
                topic = self.conversation_context["current_topic"]
                summary_parts.append(f"Current focus: {topic}")
        
        return " | ".join(summary_parts) if summary_parts else ""
    
    def invoke(self, input_data: Dict) -> Dict:
        """For compatibility with AgentExecutor interface"""
        query = input_data.get("input", "")
        return self.process_query(query)