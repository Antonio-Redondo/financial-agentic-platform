"""
Simple logging module to replace LangSmith integration
Provides basic tracing and analytics using built-in Python logging
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTracer:
    """Simple tracing without external dependencies"""
    
    def __init__(self):
        self.is_enabled = True
        self.traces_dir = "traces"
        os.makedirs(self.traces_dir, exist_ok=True)
    
    def trace_query(self, query: str, response: str = "", metadata: Optional[Dict] = None) -> str:
        """Trace a query-response pair"""
        if not self.is_enabled:
            return None
            
        try:
            trace_id = f"query_{int(time.time() * 1000)}"
            
            trace_data = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "metadata": metadata or {},
                "operation": "financial_query"
            }
            
            # Log to console
            logger.info(f"Query traced: {query[:100]}...")
            
            # Save to file
            filename = f"{self.traces_dir}/trace_{trace_id}.json"
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)
                
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to trace query: {e}")
            return None
    
    def trace_vector_search(self, query: str, results: List[Dict], metadata: Optional[Dict] = None) -> str:
        """Trace vector search operations"""
        if not self.is_enabled:
            return None
            
        try:
            trace_id = f"search_{int(time.time() * 1000)}"
            
            trace_data = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "results_count": len(results),
                "results": results[:3] if results else [],  # Store first 3 results
                "metadata": metadata or {},
                "operation": "vector_search"
            }
            
            logger.info(f"Vector search traced: {query[:100]}... ({len(results)} results)")
            
            filename = f"{self.traces_dir}/trace_{trace_id}.json"
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)
            
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to trace vector search: {e}")
            return None
    
    def trace_llm_response(self, prompt: str = None, query: str = None, response: str = "", 
                          model_name: str = "unknown", latency_ms: float = 0, metadata: Optional[Dict] = None) -> str:
        """Trace LLM response operations"""
        if not self.is_enabled:
            return None
            
        try:
            # Support both 'prompt' and 'query' parameters for backward compatibility
            input_text = prompt or query or ""
            
            trace_id = f"llm_{int(time.time() * 1000)}"
            
            trace_data = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "input": input_text,
                "response": response,
                "model_name": model_name,
                "latency_ms": latency_ms,
                "response_length": len(response) if response else 0,
                "metadata": metadata or {},
                "operation": "llm_response"
            }
            
            logger.info(f"LLM response traced: {model_name} ({latency_ms:.1f}ms)")
            
            filename = f"{self.traces_dir}/trace_{trace_id}.json"
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)
            
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to trace LLM response: {e}")
            return None
    
    def trace_financial_query(self, query: str, deal_numbers: List[str] = None, 
                             query_type: str = "general", metadata: Optional[Dict] = None) -> str:
        """Trace financial query operations"""
        if not self.is_enabled:
            return None
            
        try:
            trace_id = f"financial_query_{int(time.time() * 1000)}"
            
            trace_data = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "deal_numbers": deal_numbers or [],
                "query_type": query_type,
                "metadata": metadata or {},
                "operation": "financial_query"
            }
            
            logger.info(f"Financial query traced: {query_type} for deals {deal_numbers}")
            
            filename = f"{self.traces_dir}/trace_{trace_id}.json"
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)
            
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to trace financial query: {e}")
            return None
    
    def get_project_analytics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get basic analytics from local traces"""
        try:
            if not os.path.exists(self.traces_dir):
                return {"status": "no_data", "total_runs": 0}
            
            trace_files = [f for f in os.listdir(self.traces_dir) if f.endswith('.json')]
            
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
                    with open(os.path.join(self.traces_dir, trace_file), 'r') as f:
                        trace_data = json.load(f)
                    
                    if trace_data.get("operation") == "financial_query":
                        analytics["recent_queries"].append({
                            "query": trace_data.get("query", "")[:100],
                            "timestamp": trace_data.get("timestamp")
                        })
                except Exception:
                    continue
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e), "status": "error"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current tracer status"""
        return {
            "enabled": self.is_enabled,
            "api_available": False,  # No external API
            "project": "local-tracing",
            "client_connected": True,
            "tracer_available": True
        }


# Simple decorator functions to replace LangSmith decorators
def trace_financial_operation(operation_name: str):
    """Decorator to trace financial operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                logger.info(f"{operation_name} completed in {(time.time() - start_time)*1000:.1f}ms")
                return result
            except Exception as e:
                logger.error(f"{operation_name} failed: {e}")
                raise
        return wrapper
    return decorator


def with_langsmith_callbacks():
    """Get callbacks (returns empty list since we're not using LangChain callbacks)"""
    return []


# Global instance
simple_tracer = SimpleTracer()

# Alias for backward compatibility
langsmith_manager = simple_tracer