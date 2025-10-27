"""
Financial Workflow Orchestrator

Main workflow orchestrator that coordinates specialized agents with parallel execution
capabilities. Manages the multi-agent pipeline for comprehensive financial analysis
including document analysis, risk assessment, market analysis, and final recommendations.
"""

# Standard library imports
import asyncio
import json
import concurrent.futures
import threading
from datetime import datetime
from typing import Any, Annotated, Dict, List, TypedDict

# Third-party imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict

# Local imports
from .document_analysis_agent import DocumentAnalysisAgent
from .risk_assessment_agent import RiskAssessmentAgent
from .market_analysis_agent import MarketAnalysisAgent
from .recommendation_agent import RecommendationAgent
from ..vector_store import VectorStore


# Define WorkflowState for agent method signatures and workflow logic
class WorkflowState(TypedDict):
    query: str
    context_documents: list
    document_analysis: str
    risk_assessment: str
    market_analysis: str
    final_recommendation: str
    confidence_scores: dict
    agent_reasoning: dict
    current_step: str
    error_messages: list


class FinancialWorkflow:
    """LangGraph workflow orchestrator for multi-agent financial analysis with parallel execution"""

    WORKFLOW_STATES = [
        "document_analysis",
        "parallel_analysis",  # New parallel state
        "risk_assessment",
        "market_analysis", 
        "final_recommendations",
        END
    ]

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

        # Initialize specialized agents
        self.doc_agent = DocumentAnalysisAgent(vector_store)
        self.risk_agent = RiskAssessmentAgent()
        self.market_agent = MarketAnalysisAgent()
        self.recommendation_agent = RecommendationAgent()

        # Build the workflow graph with parallel execution
        self.workflow = self._build_parallel_workflow()

    @staticmethod
    def workflow_router(state: WorkflowState) -> str:
        """Enhanced router supporting parallel execution"""
        step = state.get("current_step", "document_analysis")
        
        if step == "document_analysis_complete":
            return "parallel_analysis"
        elif step == "parallel_analysis_complete":
            return "final_recommendations"
        elif step == "workflow_complete":
            return END
        else:
            return "document_analysis"

    def _parallel_analysis_coordinator(self, state: WorkflowState) -> WorkflowState:
        """Coordinate parallel execution of risk and market analysis"""
        try:
            print("🔄 Starting parallel analysis: Risk Assessment + Market Analysis")
            
            # Create thread-safe copies of state for each agent
            risk_state = state.copy()
            market_state = state.copy()
            
            # Use ThreadPoolExecutor for parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both analyses to run in parallel
                risk_future = executor.submit(self.risk_agent.assess_risk, risk_state)
                market_future = executor.submit(self.market_agent.analyze_market, market_state)
                
                # Wait for both to complete
                risk_result = risk_future.result(timeout=300)  # 5 minute timeout
                market_result = market_future.result(timeout=300)
                
                print("✅ Parallel analysis completed successfully")
            
            # Merge results back into main state
            state["risk_assessment"] = risk_result["risk_assessment"]
            state["market_analysis"] = market_result["market_analysis"]
            
            # Merge confidence scores
            state["confidence_scores"].update(risk_result.get("confidence_scores", {}))
            state["confidence_scores"].update(market_result.get("confidence_scores", {}))
            
            # Merge agent reasoning
            state["agent_reasoning"].update(risk_result.get("agent_reasoning", {}))
            state["agent_reasoning"].update(market_result.get("agent_reasoning", {}))
            
            # Merge any error messages
            state["error_messages"].extend(risk_result.get("error_messages", []))
            state["error_messages"].extend(market_result.get("error_messages", []))
            
            state["current_step"] = "parallel_analysis_complete"
            
        except concurrent.futures.TimeoutError:
            state["error_messages"].append("Parallel analysis timed out - proceeding with partial results")
            state["risk_assessment"] = state.get("risk_assessment", "Parallel analysis timeout")
            state["market_analysis"] = state.get("market_analysis", "Parallel analysis timeout")
            state["confidence_scores"]["risk_assessment"] = 0.3
            state["confidence_scores"]["market_analysis"] = 0.3
            state["current_step"] = "parallel_analysis_complete"
            
        except Exception as e:
            state["error_messages"].append(f"Parallel execution error: {str(e)}")
            # Fall back to sequential execution
            print(f"⚠️ Parallel execution failed, falling back to sequential: {e}")
            state = self.risk_agent.assess_risk(state)
            state = self.market_agent.analyze_market(state)
            state["current_step"] = "parallel_analysis_complete"
            
        return state

    def _build_parallel_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with parallel execution capabilities"""
        workflow = StateGraph(WorkflowState)
        
        # Add all nodes
        workflow.add_node("document_analysis", self.doc_agent.analyze_documents)
        workflow.add_node("parallel_analysis", self._parallel_analysis_coordinator)
        workflow.add_node("final_recommendations", self.recommendation_agent.generate_recommendations)
        workflow.add_node("router", self.workflow_router)

        # Set up the flow
        workflow.set_entry_point("router")
        
        # Router connections
        workflow.add_edge("router", "document_analysis")
        workflow.add_edge("document_analysis", "router")
        workflow.add_edge("parallel_analysis", "router")
        workflow.add_edge("final_recommendations", END)

        return workflow.compile()
    
    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow with parallel execution and context sufficiency checking"""
        
        # Initialize state
        initial_state = WorkflowState(
            query=query,
            context_documents=[],
            document_analysis="",
            risk_assessment="",
            market_analysis="",
            final_recommendation="",
            confidence_scores={},
            agent_reasoning={},
            current_step="starting",
            error_messages=[]
        )
        
        try:
            print(f"🚀 Starting multi-agent workflow with parallel execution for query: '{query}'")
            
            # Execute the workflow
            result = self.workflow.invoke(initial_state)
            
            # ENHANCED: Check context sufficiency and enhance if needed
            enhanced_result = self._enhance_workflow_context_if_needed(result, query)
            
            # Format the comprehensive response
            response = self._format_workflow_response(enhanced_result)
            
            return {
                "success": True,
                "response": response,
                "workflow_state": enhanced_result,
                "confidence": enhanced_result.get("confidence_scores", {}).get("overall", 0.5),
                "context_enhanced": enhanced_result != result
            }
            
        except Exception as e:
            print(f"❌ Workflow execution error: {str(e)}")
            return {
                "success": False,
                "response": f"Workflow execution error: {str(e)}",
                "workflow_state": initial_state,
                "confidence": 0.0,
                "context_enhanced": False
            }
    
    def _enhance_workflow_context_if_needed(self, result: WorkflowState, original_query: str) -> WorkflowState:
        """
        Check if workflow results show insufficient context and enhance if needed
        """
        print("🔍 Evaluating workflow context sufficiency...")
        
        # Collect all analysis text
        all_analysis = [
            result.get('document_analysis', ''),
            result.get('risk_assessment', ''),
            result.get('market_analysis', ''),
            result.get('final_recommendation', '')
        ]
        
        combined_analysis = ' '.join(all_analysis).lower()
        
        # Context sufficiency indicators
        insufficient_indicators = [
            "insufficient information",
            "no specific data",
            "cannot determine",
            "unable to provide",
            "limited information",
            "not enough detail",
            "requires additional data",
            "insufficient context"
        ]
        
        # Quality indicators
        quality_indicators = [
            "based on the analysis",
            "specific metrics show",
            "the data indicates",
            "according to the documents",
            "financial analysis reveals",
            "comprehensive assessment"
        ]
        
        insufficient_count = sum(1 for indicator in insufficient_indicators if indicator in combined_analysis)
        quality_count = sum(1 for indicator in quality_indicators if indicator in combined_analysis)
        
        analysis_length = len(combined_analysis)
        confidence_scores = result.get('confidence_scores', {})
        average_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.3
        
        # Calculate overall context quality
        context_quality_score = 0
        context_quality_score += quality_count * 2
        context_quality_score += min(analysis_length / 1000, 3)  # Length bonus (max 3)
        context_quality_score += average_confidence * 3  # Confidence bonus
        context_quality_score -= insufficient_count * 2  # Penalty for insufficient indicators
        
        print(f"📊 Workflow context quality score: {context_quality_score:.1f}/10")
        print(f"📊 Insufficient indicators: {insufficient_count}")
        print(f"📊 Quality indicators: {quality_count}")
        print(f"📊 Average confidence: {average_confidence:.2f}")
        print(f"📊 Total analysis length: {analysis_length} chars")
        
        # If context quality is poor, attempt enhancement
        if context_quality_score < 5.0 or insufficient_count > 2:
            print("🔄 Workflow context appears insufficient - attempting enhancement...")
            
            # Perform enhanced document search
            enhanced_documents = self._perform_enhanced_document_search(original_query, result)
            
            if enhanced_documents and len(enhanced_documents) > len(result.get('context_documents', [])):
                print(f"✅ Found {len(enhanced_documents)} enhanced documents for re-analysis")
                
                # Re-run document analysis with enhanced context
                enhanced_state = result.copy()
                enhanced_state['context_documents'] = enhanced_documents
                
                # Re-run document analysis agent with enhanced context
                enhanced_doc_analysis = self.doc_agent.analyze_documents(enhanced_state)
                
                # Check if enhanced analysis is actually better
                enhanced_analysis_text = enhanced_doc_analysis.get('document_analysis', '')
                enhanced_insufficient = sum(1 for indicator in insufficient_indicators 
                                          if indicator in enhanced_analysis_text.lower())
                enhanced_quality = sum(1 for indicator in quality_indicators 
                                     if indicator in enhanced_analysis_text.lower())
                
                if (enhanced_insufficient < insufficient_count or 
                    enhanced_quality > quality_count or 
                    len(enhanced_analysis_text) > analysis_length * 0.5):
                    
                    print("✅ Enhanced document analysis appears better - updating workflow result")
                    result.update(enhanced_doc_analysis)
                    result['agent_reasoning']['context_enhancement'] = "Applied enhanced document search due to insufficient initial context"
                else:
                    print("⚠️ Enhanced analysis not significantly better - keeping original")
            else:
                print("⚠️ Enhanced document search did not find additional relevant content")
        else:
            print("✅ Workflow context appears sufficient - no enhancement needed")
        
        return result
    
    def _perform_enhanced_document_search(self, query: str, current_state: WorkflowState) -> List:
        """
        Perform enhanced document search for workflow context enhancement
        """
        print("🔍 Performing enhanced document search for workflow...")
        
        enhanced_documents = []
        current_docs = current_state.get('context_documents', [])
        
        # Strategy 1: Extract deal numbers and search more broadly
        import re
        deal_pattern = r'(?:deal\s*)?20\d{2}-\d{3}'
        deal_matches = re.findall(deal_pattern, query.lower())
        
        if deal_matches:
            deal_number = deal_matches[0].replace("deal ", "").strip()
            
            # Broader deal searches
            enhanced_searches = [
                f"{deal_number}",
                f"FNM {deal_number}",
                f"FNMA {deal_number}",
                deal_number.replace("-", ""),
                f"2025-{deal_number.split('-')[1]}" if '-' in deal_number else deal_number
            ]
            
            for search_term in enhanced_searches:
                try:
                    results = self.vector_store.search_documents(search_term, k=10)
                    enhanced_documents.extend(results)
                    print(f"📍 Enhanced search '{search_term}': {len(results)} results")
                except Exception as e:
                    print(f"⚠️ Enhanced search failed for '{search_term}': {e}")
        
        # Strategy 2: Financial keyword expansion
        financial_keywords = self._extract_financial_keywords_for_workflow(query)
        for keyword in financial_keywords:
            try:
                results = self.vector_store.search_documents(keyword, k=5)
                enhanced_documents.extend(results)
                print(f"📍 Keyword search '{keyword}': {len(results)} results")
            except Exception as e:
                print(f"⚠️ Keyword search failed for '{keyword}': {e}")
        
        # Remove duplicates
        unique_documents = []
        seen_content = set()
        
        for doc in enhanced_documents:
            if isinstance(doc, dict) and 'content' in doc:
                content_hash = hash(doc['content'][:200])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_documents.append(doc)
        
        print(f"🔍 Enhanced document search: {len(enhanced_documents)} → {len(unique_documents)} unique documents")
        return unique_documents
    
    def _extract_financial_keywords_for_workflow(self, query: str) -> List[str]:
        """Extract financial keywords for workflow enhancement"""
        financial_terms = {
            'collateral': ['pool', 'asset', 'backing', 'underlying', 'mortgage'],
            'average life': ['WAL', 'weighted average life', 'duration', 'maturity', 'years'],
            'underwriter': ['bank', 'dealer', 'bookrunner', 'lead', 'manager'],
            'tranche': ['class', 'series', 'bond', 'note', 'security'],
            'pricing': ['yield', 'spread', 'rate', 'coupon', 'price'],
            'risk': ['credit', 'prepayment', 'interest rate', 'default', 'assessment'],
            'analysis': ['assessment', 'evaluation', 'review', 'forecast', 'projection']
        }
        
        keywords = []
        query_lower = query.lower()
        
        for main_term, related_terms in financial_terms.items():
            if main_term in query_lower:
                keywords.extend(related_terms[:3])  # Limit related terms
        
        # Add important words from query
        important_words = [word for word in query.split() 
                          if len(word) > 4 and word.lower() not in ['what', 'give', 'show', 'tell', 'about']]
        keywords.extend(important_words)
        
        return list(set(keywords))[:8]  # Limit total keywords
    
    def _format_workflow_response(self, state: WorkflowState) -> str:
        """Format the multi-agent workflow results into a comprehensive response"""
        
        confidence_scores = state.get("confidence_scores", {})
        overall_confidence = confidence_scores.get("overall", 0.5)
        
        response = f"""# 🏦 Multi-Agent Financial Analysis Results (Parallel Execution)

## 📊 Analysis Overview
**Query:** {state['query']}
**Overall Confidence:** {overall_confidence:.1%}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Execution Mode:** Parallel Risk + Market Analysis

---

## 📄 Document Analysis
**Confidence:** {confidence_scores.get('document_analysis', 0.5):.1%}

{state.get('document_analysis', 'No document analysis available')}

---

## ⚡ Parallel Analysis Results

### ⚠️ Risk Assessment  
**Confidence:** {confidence_scores.get('risk_assessment', 0.5):.1%}

{state.get('risk_assessment', 'No risk assessment available')}

### 📈 Market Analysis
**Confidence:** {confidence_scores.get('market_analysis', 0.5):.1%}

{state.get('market_analysis', 'No market analysis available')}

---

## 💡 Final Recommendations

{state.get('final_recommendation', 'No final recommendations available')}

---

## 🔍 Workflow Summary
"""
        
        # Add agent reasoning summary
        agent_reasoning = state.get("agent_reasoning", {})
        if agent_reasoning:
            response += "\n### Agent Contributions:\n"
            for agent, reasoning in agent_reasoning.items():
                response += f"- **{agent.replace('_', ' ').title()}:** {reasoning}\n"
        
        # Add error messages if any
        error_messages = state.get("error_messages", [])
        if error_messages:
            response += "\n### ⚠️ Workflow Warnings:\n"
            for error in error_messages:
                response += f"- {error}\n"
        
        # Add document sources
        context_docs = state.get("context_documents", [])
        if context_docs:
            response += f"\n### 📚 Source Documents ({len(context_docs)} documents analyzed):\n"
            for i, doc in enumerate(context_docs[:5], 1):  # Show top 5
                filename = doc.get('metadata', {}).get('filename', 'Unknown')
                relevance = doc.get('relevance_score', 0.0)
                response += f"{i}. **{filename}** (Relevance: {relevance:.1%})\n"
        
        return response

    def get_workflow_info(self) -> Dict[str, Any]:
        """Return workflow information for monitoring and debugging"""
        return {
            "workflow_name": "Financial Analysis Multi-Agent Workflow",
            "execution_mode": "Parallel (Risk + Market Analysis)",
            "agents": [
                self.doc_agent.get_agent_info(),
                self.risk_agent.get_agent_info(),
                self.market_agent.get_agent_info(),
                self.recommendation_agent.get_agent_info()
            ],
            "workflow_states": self.WORKFLOW_STATES,
            "parallel_stages": ["risk_assessment", "market_analysis"],
            "capabilities": [
                "Document analysis and extraction",
                "Parallel risk and market assessment",
                "Comprehensive financial recommendations",
                "Error handling and fallback mechanisms",
                "Confidence scoring and monitoring"
            ]
        }


def create_financial_workflow(vector_store: VectorStore) -> FinancialWorkflow:
    """Factory function to create a configured financial workflow with parallel execution"""
    return FinancialWorkflow(vector_store)