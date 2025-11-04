"""
Document Analysis Agent

Specialized agent for document analysis and information extraction from financial documents.
Focuses on extracting key financial metrics, assessing data quality, and providing
comprehensive document analysis for financial forecasting.
"""

# Standard library imports
from typing import Dict, Any

# Third-party imports
from langsmith import traceable

# Local imports
from ..analyst import FinancialAnalyst
from ..vector_store import VectorStore


class DocumentAnalysisAgent:
    """Specialized agent for document analysis and information extraction"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.analyst = FinancialAnalyst()
        self.agent_name = "Document Analysis Agent"
        
    @traceable(name="document_analysis_agent", tags=["agent", "document-analysis", "financial-data"])
    def analyze_documents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze documents and extract key financial information"""
        try:
            query = state["query"]
            
            # Search for relevant documents
            relevant_docs = self.vector_store.search_documents(query, k=5)
            
            # Create specialized prompt for document analysis
            doc_context = "\n".join([
                f"Document: {doc.get('metadata', {}).get('filename', 'Unknown')}\n"
                f"Content: {doc.get('content', '')}" 
                for doc in relevant_docs
            ])
            
            analysis_prompt = f"""You are a Document Analysis Specialist for financial documents. 
            
            USER QUERY: {query}
            
            RELEVANT DOCUMENTS:
            {doc_context}
            
            Provide a comprehensive document analysis focusing on:
            
            📄 **DOCUMENT OVERVIEW:**
            1. Document types and sources identified
            2. Data coverage and time periods
            3. Document reliability assessment
            4. Key sections and exhibits analyzed
            
            💰 **KEY FINANCIAL METRICS:**
            1. Primary financial data points extracted
            2. Deal structures and characteristics
            3. Pricing information and terms
            4. Performance metrics and ratios
            
            📊 **DATA QUALITY ASSESSMENT:**
            1. Completeness of information
            2. Data consistency and accuracy
            3. Missing or incomplete data points
            4. Reliability confidence levels
            
            🔍 **INSIGHTS FOR FORECASTING:**
            1. Historical trends identified
            2. Key variables for modeling
            3. Risk indicators present
            4. Market context and comparables
            
            Be specific and quantitative where possible. Include exact figures, dates, and percentages."""
            
            result = self.analyst.analyze(analysis_prompt)
            
            # Update state
            state["context_documents"] = relevant_docs
            state["document_analysis_result"] = result.get("analysis", "")
            state["confidence_scores"]["document_analysis"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["document_analysis"] = "Analyzed documents for key financial indicators and data quality"
            state["current_step"] = "document_analysis_complete"
            
            print(f"✅ {self.agent_name}: Document analysis completed with {len(relevant_docs)} documents")
            
        except Exception as e:
            error_msg = f"Document Analysis Error: {str(e)}"
            state["error_messages"].append(error_msg)
            state["document_analysis_result"] = "Error in document analysis - proceeding with limited context"
            state["confidence_scores"]["document_analysis"] = 0.3
            print(f"❌ {self.agent_name}: {error_msg}")
            
        return state
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for monitoring and debugging"""
        return {
            "name": self.agent_name,
            "purpose": "Document extraction and financial data analysis",
            "capabilities": [
                "Financial document parsing",
                "Data quality assessment", 
                "Key metrics extraction",
                "Historical trend identification"
            ],
            "output": "Comprehensive document analysis with financial insights"
        }