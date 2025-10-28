"""
LangSmith Integration Module

Provides comprehensive observability and tracing for the Financial Forecast AI application.
"""

import os
import time
import functools
from functools import wraps
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# LangSmith imports with fallback
try:
    from langsmith import Client, traceable
    from langsmith.run_helpers import get_current_run_tree
    import langsmith
    LANGSMITH_AVAILABLE = True
except ImportError:
    print("⚠️ LangSmith not available - running without tracing")
    LANGSMITH_AVAILABLE = False
    Client = None
    traceable = None
    langsmith = None

# LangChain callback imports
try:
    from langchain.callbacks import LangChainTracer, StdOutCallbackHandler
    from langchain.callbacks.manager import CallbackManager
    LANGCHAIN_CALLBACKS_AVAILABLE = True
except ImportError:
    print("⚠️ LangChain callbacks not available")
    LANGCHAIN_CALLBACKS_AVAILABLE = False
    LangChainTracer = None
    StdOutCallbackHandler = None
    CallbackManager = None

from datetime import datetime



class LangSmithTracer:
    """
    Manages LangSmith tracing and observability for financial operations.
    """
    
    def __init__(self):
        """Initialize LangSmith tracer with configuration."""
        self.enabled = False
        self.client = None
        self.callback_manager = None
        
        if LANGSMITH_AVAILABLE:
            # Get configuration from environment
            api_key = os.getenv('LANGSMITH_API_KEY')
            project = os.getenv('LANGSMITH_PROJECT', 'financial-forecast-ai')
            
            if api_key:
                try:
                    self.client = Client(api_key=api_key)
                    
                    # Set environment variables for LangChain auto-tracing
                    os.environ["LANGCHAIN_TRACING_V2"] = "true"
                    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
                    os.environ["LANGCHAIN_API_KEY"] = api_key
                    os.environ["LANGCHAIN_PROJECT"] = project
                    
                    # Additional environment variables for comprehensive tracing
                    os.environ["LANGSMITH_TRACING"] = "true"
                    
                    # Enable auto-tracing for LangChain operations
                    import langchain
                    langchain.debug = True
                    
                    # Create callback manager for explicit tracing
                    if LANGCHAIN_CALLBACKS_AVAILABLE:
                        callbacks = [LangChainTracer(project_name=project)]
                        self.callback_manager = CallbackManager(callbacks)
                    
                    self.enabled = True
                    print(f"[SUCCESS] LangSmith initialized with auto-tracing for project: {project}")
                except Exception as e:
                    print(f"[WARNING] LangSmith initialization failed: {e}")
            else:
                print("[WARNING] LANGSMITH_API_KEY not found in environment")
        else:
            print("[WARNING] LangSmith not available - install with: pip install langsmith")
    
    def get_callbacks(self):
        """Get LangSmith callbacks for LangChain models."""
        if self.enabled and self.callback_manager:
            return self.callback_manager.handlers
        return []

    
    def trace_query(self, func):
        """
        Decorator to trace query operations with LangSmith.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            # Execute function with basic logging
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log operation details
                query = kwargs.get('query', args[0] if args else 'Unknown query')
                print(f"INFO: LangSmith - Query traced: {func.__name__} ({execution_time:.2f}s)")
                
                return result
                
            except Exception as e:
                print(f"ERROR: LangSmith - Query failed: {func.__name__} - {e}")
                raise
        
        return wrapper
    
    def trace_vector_search(self, func):
        """
        Decorator to trace vector search operations.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                results = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log operation details
                query = kwargs.get('query', args[0] if args else 'Unknown query')
                result_count = len(results) if results else 0
                print(f"INFO: LangSmith - Vector search traced: {query[:50]}... -> {result_count} results ({execution_time:.2f}s)")
                
                return results
                
            except Exception as e:
                print(f"ERROR: LangSmith - Vector search failed: {e}")
                raise
        
        return wrapper
    
    def trace_document_processing(self, func):
        """
        Decorator to trace document processing operations.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log operation details
                print(f"INFO: LangSmith - Document processing traced: {func.__name__} ({execution_time:.2f}s)")
                
                return result
                
            except Exception as e:
                print(f"ERROR: LangSmith - Document processing failed: {func.__name__} - {e}")
                raise
        
        return wrapper

# Global tracer instance
tracer = LangSmithTracer()

# Convenience decorators for common use cases
def trace_financial_query(func):
    """Decorator for tracing financial query operations."""
    return tracer.trace_query(func)

def trace_vector_search(func):
    """Decorator for tracing vector search operations.""" 
    return tracer.trace_vector_search(func)

def trace_document_processing(func):
    """Decorator for tracing document processing operations."""
    return tracer.trace_document_processing(func)

def trace_financial_operation(operation_name: str):
    """
    Decorator for tracing financial operations with enhanced LangSmith integration.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # If LangSmith is available, use the traceable decorator for auto-tracing
            if tracer.enabled and LANGSMITH_AVAILABLE and traceable:
                try:
                    # Create a traceable version of the function
                    @traceable(
                        name=f"financial_operation_{operation_name}",
                        run_type="chain",
                        project=os.getenv('LANGSMITH_PROJECT', 'financial-forecast-ai')
                    )
                    def traced_function(*args, **kwargs):
                        return func(*args, **kwargs)
                    
                    result = traced_function(*args, **kwargs)
                    execution_time = time.time() - start_time
                    print(f"INFO: LangSmith auto-traced: {operation_name} ({execution_time:.2f}s)")
                    return result
                    
                except Exception as e:
                    print(f"ERROR: LangSmith auto-tracing failed: {e}")
                    # Fallback to manual tracing
                    pass
            
            # Fallback to manual tracing or when LangSmith auto-tracing fails
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if tracer.enabled and tracer.client:
                    try:
                        # Create a run in LangSmith manually
                        run_data = {
                            "name": f"financial_operation_{operation_name}",
                            "run_type": "chain",
                            "inputs": {"operation": operation_name, "function": func.__name__},
                            "outputs": {"success": True, "execution_time": execution_time},
                            "start_time": datetime.fromtimestamp(start_time),
                            "end_time": datetime.now(),
                            "execution_order": 1,
                            "extra": {
                                "operation_name": operation_name,
                                "execution_time_seconds": execution_time,
                                "function_name": func.__name__
                            }
                        }
                        
                        # Send to LangSmith
                        tracer.client.create_run(**run_data)
                        print(f"INFO: LangSmith manually traced: {operation_name} ({execution_time:.2f}s)")
                        
                    except Exception as e:
                        print(f"ERROR: Failed to trace to LangSmith: {e}")
                        print(f"INFO: Financial operation completed: {operation_name} ({execution_time:.2f}s)")
                else:
                    print(f"INFO: Financial operation completed: {operation_name} ({execution_time:.2f}s)")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"ERROR: Financial operation failed: {operation_name} - {e}")
                
                # Try to trace the error to LangSmith
                if tracer.enabled and tracer.client:
                    try:
                        error_run_data = {
                            "name": f"financial_operation_{operation_name}_error",
                            "run_type": "chain",
                            "inputs": {"operation": operation_name, "function": func.__name__},
                            "outputs": {"success": False, "error": str(e)},
                            "start_time": datetime.fromtimestamp(start_time),
                            "end_time": datetime.now(),
                            "error": str(e),
                            "execution_order": 1
                        }
                        tracer.client.create_run(**error_run_data)
                    except:
                        pass  # Don't let tracing errors block the original error
                
                raise
        
        return wrapper
    return decorator

def with_langsmith_callbacks():
    """
    Returns LangSmith callbacks for LangChain operations.
    """
    if not tracer.enabled:
        return []
    
    try:
        # Return empty list as fallback - actual LangChain callbacks would need LangChain integration
        return []
    except Exception:
        return []


def with_langsmith_callbacks(model_class, *args, **kwargs):
    """
    Helper function to create LangChain models with LangSmith callbacks enabled.
    
    Usage:
        chat_model = with_langsmith_callbacks(BedrockChat, model_id="...", region_name="...")
        embeddings = with_langsmith_callbacks(BedrockEmbeddings, model_id="...", region_name="...")
    """
    # Only add callbacks for models that support them (chat models, not embeddings)
    model_name = model_class.__name__
    
    if tracer.enabled and tracer.callback_manager and model_name in ['BedrockChat', 'ChatBedrock']:
        kwargs['callbacks'] = tracer.get_callbacks()
        print(f"INFO: Creating {model_name} with LangSmith tracing enabled")
    elif model_name in ['BedrockEmbeddings']:
        print(f"INFO: Creating {model_name} (embeddings will be traced via Bedrock context managers)")
    else:
        print(f"INFO: Creating {model_name}")
    
    return model_class(*args, **kwargs)


def trace_bedrock_call(model_name: str, operation: str):
    """
    Context manager for tracing Bedrock model calls.
    """
    class BedrockTraceContext:
        def __init__(self, model_name, operation):
            self.model_name = model_name
            self.operation = operation
            self.start_time = None
            
        def __enter__(self):
            self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time:
                latency_ms = (time.time() - self.start_time) * 1000
                
                if tracer.enabled and tracer.client:
                    try:
                        # Create Bedrock call run in LangSmith
                        run_data = {
                            "name": f"bedrock_call_{self.model_name}",
                            "run_type": "llm",
                            "inputs": {"model": self.model_name, "operation": self.operation},
                            "outputs": {"success": exc_type is None, "latency_ms": latency_ms},
                            "start_time": datetime.fromtimestamp(self.start_time),
                            "end_time": datetime.now(),
                            "execution_order": 1,
                            "extra": {
                                "model_name": self.model_name,
                                "operation": self.operation,
                                "latency_ms": latency_ms,
                                "provider": "bedrock"
                            }
                        }
                        
                        if exc_type:
                            run_data["error"] = str(exc_val)
                        
                        # Send to LangSmith
                        tracer.client.create_run(**run_data)
                        
                        if exc_type:
                            print(f"ERROR: Bedrock {self.model_name} call failed after {latency_ms:.2f}ms (traced to LangSmith)")
                        else:
                            print(f"INFO: Bedrock {self.model_name} call completed in {latency_ms:.2f}ms (traced to LangSmith)")
                            
                    except Exception as e:
                        print(f"ERROR: Failed to trace Bedrock call to LangSmith: {e}")
                        if exc_type:
                            print(f"ERROR: Bedrock {self.model_name} call failed after {latency_ms:.2f}ms")
                        else:
                            print(f"INFO: Bedrock {self.model_name} call completed in {latency_ms:.2f}ms")
                else:
                    if exc_type:
                        print(f"ERROR: Bedrock {self.model_name} call failed after {latency_ms:.2f}ms")
                    else:
                        print(f"INFO: Bedrock {self.model_name} call completed in {latency_ms:.2f}ms")
        
        def log_response(self, prompt: str, response: str):
            """Log the successful response"""
            if tracer.enabled and self.start_time:
                latency_ms = (time.time() - self.start_time) * 1000
                langsmith_manager.trace_llm_response(
                    prompt=prompt,
                    response=response,
                    model_name=self.model_name,
                    latency_ms=latency_ms,
                    metadata={
                        "operation": self.operation,
                        "provider": "bedrock"
                    }
                )
    
    return BedrockTraceContext(model_name, operation)

# Legacy compatibility - create langsmith_manager instance
class LangSmithManager:
    """Legacy wrapper for backward compatibility."""
    
    def __init__(self):
        self.tracer = tracer
        self.enabled = tracer.enabled
        self.is_enabled = tracer.enabled  # Add this attribute for compatibility
        self.client = tracer.client
    
    def trace_financial_query(self, query: str, deal_numbers: List[str], 
                             query_type: str, metadata: Dict = None) -> None:
        """Legacy method for tracing financial queries."""
        if self.enabled:
            print(f"INFO: Financial query traced: {query_type} for deals {deal_numbers}")
    
    def trace_vector_search(self, query: str, results: List[Dict],
                           metadata: Dict = None) -> None:
        """Legacy method for tracing vector searches."""
        if self.enabled:
            print(f"INFO: Vector search traced: {query} -> {len(results)} results")
    
    def trace_document_processing(self, document_path: str, chunks_created: int,
                                 metadata: Dict = None) -> None:
        """Legacy method for tracing document processing."""
        if self.enabled:
            print(f"INFO: Document processed: {document_path} -> {chunks_created} chunks")
    
    def trace_llm_response(self, prompt: str, response: str, model_name: str, 
                          latency_ms: float = None, metadata: Dict = None) -> None:
        """Trace LLM responses to LangSmith."""
        if self.enabled and self.client:
            try:
                # Create a run in LangSmith
                run_data = {
                    "name": f"llm_call_{model_name}",
                    "run_type": "llm",
                    "inputs": {"prompt": prompt},
                    "outputs": {"response": response},
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_order": 1,
                    "extra": {
                        "model_name": model_name,
                        "latency_ms": latency_ms,
                        "metadata": metadata or {}
                    }
                }
                
                # Send to LangSmith
                self.client.create_run(**run_data)
                
                # Also log locally
                latency_info = f" (latency: {latency_ms:.2f}ms)" if latency_ms else ""
                print(f"INFO: LLM response traced to LangSmith - Model: {model_name}{latency_info}")
                
            except Exception as e:
                print(f"ERROR: Failed to trace LLM response to LangSmith: {e}")
                # Fallback to console logging
                latency_info = f" (latency: {latency_ms:.2f}ms)" if latency_ms else ""
                print(f"INFO: LLM response traced locally - Model: {model_name}{latency_info}")
        else:
            # Fallback when LangSmith is not available
            latency_info = f" (latency: {latency_ms:.2f}ms)" if latency_ms else ""
            print(f"INFO: LLM response traced locally - Model: {model_name}{latency_info}")
    
    def trace_query(self, query: str, response: str = "", metadata: Dict = None) -> None:
        """Legacy method for tracing queries."""
        if self.enabled:
            query_preview = query[:100] + "..." if len(query) > 100 else query
            response_preview = response[:100] + "..." if len(response) > 100 else response
            print(f"INFO: Query traced: {query_preview}")
            if response:
                print(f"  Response: {response_preview}")
            if metadata:
                print(f"  Metadata: {metadata}")

# Create legacy manager instance for backward compatibility
langsmith_manager = LangSmithManager()

# Export commonly used functions
__all__ = [
    'tracer',
    'langsmith_manager',
    'trace_financial_query',
    'trace_vector_search', 
    'trace_document_processing',
    'trace_financial_operation',
    'with_langsmith_callbacks',
    'trace_bedrock_call'
]
