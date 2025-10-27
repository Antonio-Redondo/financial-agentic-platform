"""
LangSmith Integration Module
Provides comprehensive observability and monitoring for the Financial Forecast AI App
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangSmithManager:
    """
    LangSmith integration manager with graceful fallback
    Handles tracing, analytics, and feedback collection
    """
    
    def __init__(self):
        self.is_enabled = False
        self.api_available = False
        self.client = None
        self.project_name = "financial-forecast-ai-app"
        self._initialize_langsmith()
    
    def _initialize_langsmith(self):
        """Initialize LangSmith with proper error handling"""
        try:
            # Load environment variables from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass  # dotenv not available, continue with existing env vars
            
            # Check if LangSmith environment variables are set
            api_key = os.getenv("LANGCHAIN_API_KEY")
            tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
            
            if not api_key or not tracing_enabled:
                logger.info(f"LangSmith not configured - API Key: {'✓' if api_key else '✗'}, Tracing: {'✓' if tracing_enabled else '✗'}")
                logger.info("Using local logging fallback")
                return
            
            # Disable LangSmith auto-tracing to prevent conflicts
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            
            # Try to import and initialize LangSmith
            from langsmith import Client
            
            self.client = Client()
            
            # Test connection with a simple API call but don't fail on 403
            try:
                # Try to get project info to test connection
                projects = list(self.client.list_projects(limit=1))
                self.api_available = True
                self.is_enabled = True
                logger.info("✅ LangSmith successfully initialized and connected")
                
            except Exception as api_error:
                if "403" in str(api_error) or "Forbidden" in str(api_error):
                    logger.warning(f"LangSmith API access restricted (403 Forbidden) - using local mode")
                else:
                    logger.warning(f"LangSmith API connection failed: {api_error}")
                # Keep client for local operations but mark API as unavailable
                self.api_available = False
                self.is_enabled = True  # Still enable for local tracing
                
        except ImportError:
            logger.warning("LangSmith SDK not installed - install with: pip install langsmith")
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
            self.is_enabled = False
    
    def trace_query(self, query: str, response: str = "", metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace a query-response pair with graceful fallback"""
        if not self.is_enabled:
            return None
            
        try:
            # Always log locally
            logger.info(f"Query traced: {query[:100]}...")
            
            if self.api_available and self.client:
                # Try to trace to LangSmith
                run_id = self._create_langsmith_run(
                    name="financial_query",
                    inputs={"query": query},
                    outputs={"response": response},
                    run_type="llm",
                    metadata=metadata or {}
                )
                return run_id
            else:
                # Fallback to local tracing
                return self._local_trace("query", {
                    "query": query,
                    "response": response,
                    "metadata": metadata or {}
                })
                
        except Exception as e:
            logger.error(f"Failed to trace query: {e}")
            return None
    
    def trace_vector_search(self, query: str, results: List[Dict], metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace vector search operations"""
        if not self.is_enabled:
            return None
            
        try:
            logger.info(f"Vector search traced: {query[:100]}... ({len(results)} results)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="vector_search",
                    inputs={"query": query},
                    outputs={"results_count": len(results), "results": results[:3]},
                    run_type="retriever",
                    metadata=metadata or {}
                )
            else:
                return self._local_trace("search", {
                    "query": query,
                    "results_count": len(results),
                    "results": results[:3] if results else [],
                    "metadata": metadata or {}
                })
                
        except Exception as e:
            logger.error(f"Failed to trace vector search: {e}")
            return None
    
    def trace_llm_response(self, prompt: str = None, query: str = None, response: str = "", 
                          model_name: str = "amazon-titan", latency_ms: float = 0, 
                          metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace LLM response operations"""
        if not self.is_enabled:
            return None
            
        try:
            # Support both 'prompt' and 'query' parameters for backward compatibility
            input_text = prompt or query or ""
            
            logger.info(f"LLM response traced: {model_name} ({latency_ms:.1f}ms)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="llm_response",
                    inputs={"prompt": input_text},
                    outputs={"response": response},
                    run_type="llm",
                    metadata={
                        "model": model_name,
                        "latency_ms": latency_ms,
                        "response_length": len(response) if response else 0,
                        **(metadata or {})
                    }
                )
            else:
                return self._local_trace("llm", {
                    "input": input_text,
                    "response": response,
                    "model_name": model_name,
                    "latency_ms": latency_ms,
                    "metadata": metadata or {}
                })
                
        except Exception as e:
            logger.error(f"Failed to trace LLM response: {e}")
            return None
    
    def trace_bedrock_chat(self, messages: List[Dict] = None, system_prompt: str = "", 
                          user_message: str = "", assistant_response: str = "",
                          model_id: str = "amazon.titan-text-express-v1", 
                          inference_params: Dict = None, latency_ms: float = 0,
                          token_usage: Dict = None, metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace Bedrock chat operations with comprehensive details"""
        if not self.is_enabled:
            return None
            
        try:
            # Prepare input data
            chat_input = {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "messages": messages or [],
                "model_id": model_id,
                "inference_params": inference_params or {}
            }
            
            # Prepare output data
            chat_output = {
                "assistant_response": assistant_response,
                "response_length": len(assistant_response) if assistant_response else 0,
                "token_usage": token_usage or {},
                "latency_ms": latency_ms
            }
            
            # Enhanced metadata
            enhanced_metadata = {
                "service": "amazon_bedrock",
                "model_family": "titan" if "titan" in model_id else "unknown",
                "interaction_type": "chat",
                "timestamp": datetime.now().isoformat(),
                "message_count": len(messages) if messages else 1,
                **(metadata or {})
            }
            
            logger.info(f"Bedrock chat traced: {model_id} ({latency_ms:.1f}ms)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="bedrock_chat",
                    inputs=chat_input,
                    outputs=chat_output,
                    run_type="llm",
                    metadata=enhanced_metadata
                )
            else:
                return self._local_trace("bedrock_chat", {
                    **chat_input,
                    **chat_output,
                    "metadata": enhanced_metadata
                })
                
        except Exception as e:
            logger.error(f"Failed to trace Bedrock chat: {e}")
            return None
    
    def trace_bedrock_analysis(self, analysis_type: str, input_data: Dict, 
                              analysis_results: Dict, model_id: str = "amazon.titan-text-express-v1",
                              processing_steps: List[str] = None, confidence_scores: Dict = None,
                              latency_ms: float = 0, metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace Bedrock analysis operations (financial analysis, document analysis, etc.)"""
        if not self.is_enabled:
            return None
            
        try:
            # Prepare analysis input
            analysis_input = {
                "analysis_type": analysis_type,
                "input_data": input_data,
                "model_id": model_id,
                "processing_steps": processing_steps or []
            }
            
            # Prepare analysis output
            analysis_output = {
                "analysis_results": analysis_results,
                "confidence_scores": confidence_scores or {},
                "result_summary": self._summarize_analysis_results(analysis_results),
                "latency_ms": latency_ms
            }
            
            # Enhanced metadata for analysis
            enhanced_metadata = {
                "service": "amazon_bedrock",
                "operation": "analysis",
                "analysis_type": analysis_type,
                "model_family": "titan" if "titan" in model_id else "unknown",
                "timestamp": datetime.now().isoformat(),
                "steps_count": len(processing_steps) if processing_steps else 0,
                **(metadata or {})
            }
            
            logger.info(f"Bedrock analysis traced: {analysis_type} with {model_id} ({latency_ms:.1f}ms)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="bedrock_analysis",
                    inputs=analysis_input,
                    outputs=analysis_output,
                    run_type="chain",
                    metadata=enhanced_metadata
                )
            else:
                return self._local_trace("bedrock_analysis", {
                    **analysis_input,
                    **analysis_output,
                    "metadata": enhanced_metadata
                })
                
        except Exception as e:
            logger.error(f"Failed to trace Bedrock analysis: {e}")
            return None
    
    def trace_bedrock_streaming(self, stream_id: str, model_id: str, 
                               chunks_received: int = 0, total_tokens: int = 0,
                               stream_duration_ms: float = 0, final_response: str = "",
                               metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace Bedrock streaming operations"""
        if not self.is_enabled:
            return None
            
        try:
            stream_input = {
                "stream_id": stream_id,
                "model_id": model_id,
                "streaming_enabled": True
            }
            
            stream_output = {
                "chunks_received": chunks_received,
                "total_tokens": total_tokens,
                "stream_duration_ms": stream_duration_ms,
                "final_response": final_response,
                "response_length": len(final_response) if final_response else 0
            }
            
            enhanced_metadata = {
                "service": "amazon_bedrock",
                "operation": "streaming",
                "model_family": "titan" if "titan" in model_id else "unknown",
                "timestamp": datetime.now().isoformat(),
                "avg_chunk_time": stream_duration_ms / chunks_received if chunks_received > 0 else 0,
                **(metadata or {})
            }
            
            logger.info(f"Bedrock streaming traced: {chunks_received} chunks in {stream_duration_ms:.1f}ms")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="bedrock_streaming",
                    inputs=stream_input,
                    outputs=stream_output,
                    run_type="llm",
                    metadata=enhanced_metadata
                )
            else:
                return self._local_trace("bedrock_streaming", {
                    **stream_input,
                    **stream_output,
                    "metadata": enhanced_metadata
                })
                
        except Exception as e:
            logger.error(f"Failed to trace Bedrock streaming: {e}")
            return None
    
    def trace_bedrock_embeddings(self, texts: List[str], model_id: str = "amazon.titan-embed-text-v1",
                                embeddings: List[List[float]] = None, processing_time_ms: float = 0,
                                metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace Bedrock embeddings operations"""
        if not self.is_enabled:
            return None
            
        try:
            embeddings_input = {
                "texts": [text[:100] + "..." if len(text) > 100 else text for text in texts],
                "model_id": model_id,
                "text_count": len(texts),
                "total_characters": sum(len(text) for text in texts)
            }
            
            embeddings_output = {
                "embeddings_generated": len(embeddings) if embeddings else 0,
                "embedding_dimensions": len(embeddings[0]) if embeddings and len(embeddings) > 0 else 0,
                "processing_time_ms": processing_time_ms
            }
            
            enhanced_metadata = {
                "service": "amazon_bedrock",
                "operation": "embeddings",
                "model_family": "titan-embed",
                "timestamp": datetime.now().isoformat(),
                "avg_text_length": sum(len(text) for text in texts) / len(texts) if texts else 0,
                **(metadata or {})
            }
            
            logger.info(f"Bedrock embeddings traced: {len(texts)} texts with {model_id} ({processing_time_ms:.1f}ms)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="bedrock_embeddings",
                    inputs=embeddings_input,
                    outputs=embeddings_output,
                    run_type="embedding",
                    metadata=enhanced_metadata
                )
            else:
                return self._local_trace("bedrock_embeddings", {
                    **embeddings_input,
                    **embeddings_output,
                    "metadata": enhanced_metadata
                })
                
        except Exception as e:
            logger.error(f"Failed to trace Bedrock embeddings: {e}")
            return None
    
    def _summarize_analysis_results(self, results: Dict) -> Dict:
        """Create a summary of analysis results for better tracing"""
        try:
            summary = {
                "keys_count": len(results.keys()) if isinstance(results, dict) else 0,
                "has_recommendations": "recommendations" in str(results).lower(),
                "has_risks": "risk" in str(results).lower(),
                "has_metrics": any(key in str(results).lower() for key in ["metric", "score", "rating", "percentage"]),
                "result_type": type(results).__name__
            }
            
            # Add specific analysis indicators
            if isinstance(results, dict):
                for key in results.keys():
                    if "error" in key.lower():
                        summary["has_errors"] = True
                    if "confidence" in key.lower():
                        summary["has_confidence"] = True
                    if "deal" in key.lower():
                        summary["deal_related"] = True
            
            return summary
        except Exception:
            return {"summary_failed": True}
    
    def trace_financial_query(self, query: str, deal_numbers: List[str] = None, 
                             query_type: str = "general", metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace financial query operations"""
        if not self.is_enabled:
            return None
            
        try:
            logger.info(f"Financial query traced: {query_type} for deals {deal_numbers}")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="financial_query",
                    inputs={"query": query, "deal_numbers": deal_numbers or []},
                    outputs={"query_type": query_type},
                    run_type="chain",
                    metadata=metadata or {}
                )
            else:
                return self._local_trace("financial_query", {
                    "query": query,
                    "deal_numbers": deal_numbers or [],
                    "query_type": query_type,
                    "metadata": metadata or {}
                })
                
        except Exception as e:
            logger.error(f"Failed to trace financial query: {e}")
            return None
    
    def trace_document_chunking(self, document_name: str, chunk_count: int, 
                               processing_time: float = 0, metadata: Optional[Dict] = None) -> Optional[str]:
        """Trace document chunking operations"""
        if not self.is_enabled:
            return None
            
        try:
            logger.info(f"Document chunking traced: {document_name} ({chunk_count} chunks)")
            
            if self.api_available and self.client:
                return self._create_langsmith_run(
                    name="document_chunking",
                    inputs={"document_name": document_name},
                    outputs={"chunk_count": chunk_count, "processing_time": processing_time},
                    run_type="tool",
                    metadata=metadata or {}
                )
            else:
                return self._local_trace("document_chunking", {
                    "document_name": document_name,
                    "chunk_count": chunk_count,
                    "processing_time": processing_time,
                    "metadata": metadata or {}
                })
                
        except Exception as e:
            logger.error(f"Failed to trace document chunking: {e}")
            return None
    
    def _create_langsmith_run(self, name: str, inputs: Dict, outputs: Dict, 
                             run_type: str, metadata: Dict) -> Optional[str]:
        """Create a LangSmith run with error handling"""
        try:
            if not self.client or not self.api_available:
                return None
                
            run = self.client.create_run(
                name=name,
                inputs=inputs,
                outputs=outputs,
                run_type=run_type,
                project_name=self.project_name,
                extra=metadata,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            return str(run.id) if run else None
            
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                # Suppress 403 errors - they're expected
                if self.api_available:  # Only log once when first detected
                    logger.warning("LangSmith API access restricted - switching to local mode")
                    self.api_available = False
            else:
                logger.warning(f"LangSmith API call failed: {e}")
            # Mark API as unavailable for future calls
            self.api_available = False
            return None
    
    def _local_trace(self, operation: str, data: Dict) -> str:
        """Fallback local tracing when LangSmith API is unavailable"""
        try:
            # Create traces directory if it doesn't exist
            traces_dir = "traces"
            os.makedirs(traces_dir, exist_ok=True)
            
            trace_id = f"{operation}_{int(time.time() * 1000)}"
            trace_data = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                **data
            }
            
            filename = f"{traces_dir}/trace_{trace_id}.json"
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)
                
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed local tracing: {e}")
            return None
    
    def get_project_analytics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get project analytics with fallback to local data"""
        try:
            if self.api_available and self.client:
                # Try to get LangSmith analytics
                try:
                    runs = list(self.client.list_runs(
                        project_name=self.project_name,
                        limit=100
                    ))
                    
                    total_runs = len(runs)
                    successful_runs = len([r for r in runs if not r.error])
                    failed_runs = total_runs - successful_runs
                    
                    # Calculate average latency
                    latencies = [
                        (r.end_time - r.start_time).total_seconds() * 1000 
                        for r in runs if r.start_time and r.end_time
                    ]
                    avg_latency = sum(latencies) / len(latencies) if latencies else 0
                    
                    return {
                        "status": "connected",
                        "total_runs": total_runs,
                        "successful_runs": successful_runs,
                        "failed_runs": failed_runs,
                        "avg_latency": round(avg_latency, 2),
                        "recent_queries": [
                            {
                                "query": str(r.inputs.get("query", ""))[:100] if r.inputs else "",
                                "timestamp": r.start_time.isoformat() if r.start_time else ""
                            }
                            for r in runs[:10]
                        ],
                        "error_types": {},
                        "days_back": days_back
                    }
                    
                except Exception as api_error:
                    logger.warning(f"LangSmith analytics API failed: {api_error}")
                    self.api_available = False
            
            # Fallback to local analytics
            return self._get_local_analytics(days_back)
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e), "status": "error"}
    
    def _get_local_analytics(self, days_back: int) -> Dict[str, Any]:
        """Get analytics from local trace files"""
        try:
            traces_dir = "traces"
            if not os.path.exists(traces_dir):
                return {"status": "no_data", "total_runs": 0}
            
            trace_files = [f for f in os.listdir(traces_dir) if f.endswith('.json')]
            
            analytics = {
                "status": "local_only",
                "total_runs": len(trace_files),
                "successful_runs": len(trace_files),  # Assume success if stored
                "failed_runs": 0,
                "avg_latency": 0,
                "recent_queries": [],
                "error_types": {},
                "days_back": days_back
            }
            
            # Analyze recent traces
            for trace_file in trace_files[-10:]:  # Last 10 traces
                try:
                    with open(os.path.join(traces_dir, trace_file), 'r') as f:
                        trace_data = json.load(f)
                    
                    if trace_data.get("operation") in ["query", "financial_query"]:
                        analytics["recent_queries"].append({
                            "query": trace_data.get("query", "")[:100],
                            "timestamp": trace_data.get("timestamp")
                        })
                except Exception:
                    continue
            
            return analytics
            
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def log_user_feedback(self, query: str, response: str, rating: int, 
                         comments: str = "", run_id: Optional[str] = None) -> bool:
        """Log user feedback with graceful fallback"""
        try:
            logger.info(f"User feedback logged: rating={rating}")
            
            if self.api_available and self.client and run_id:
                # Try to log to LangSmith
                try:
                    self.client.create_feedback(
                        run_id=run_id,
                        key="user_rating",
                        score=rating,
                        comment=comments
                    )
                    return True
                except Exception as api_error:
                    logger.warning(f"LangSmith feedback API failed: {api_error}")
            
            # Fallback to local logging
            self._local_trace("feedback", {
                "query": query,
                "response": response[:200] + "..." if len(response) > 200 else response,
                "rating": rating,
                "comments": comments,
                "run_id": run_id
            })
            return True
            
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current LangSmith status"""
        return {
            "enabled": self.is_enabled,
            "api_available": self.api_available,
            "project": self.project_name,
            "client_connected": self.client is not None,
            "tracer_available": self.is_enabled
        }


# Simple decorator functions for LangSmith tracing
def trace_financial_operation(operation_name: str):
    """Decorator to trace financial operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                logger.info(f"{operation_name} completed in {latency_ms:.1f}ms")
                return result
            except Exception as e:
                logger.error(f"{operation_name} failed: {e}")
                raise
        return wrapper
    return decorator


def with_langsmith_callbacks():
    """Get LangSmith callbacks for LangChain integration"""
    try:
        from langchain.callbacks.manager import get_openai_callback
        from langsmith.run_helpers import traceable
        
        # Return LangSmith-compatible callbacks
        return []  # LangSmith auto-instruments LangChain when LANGCHAIN_TRACING_V2=true
        
    except ImportError:
        logger.warning("LangChain callbacks not available")
        return []


# Global instance
langsmith_manager = LangSmithManager()