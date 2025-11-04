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
from langsmith import traceable

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
    document_analysis_result: str
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

    @traceable(name="parallel_analysis_coordinator", tags=["parallel", "risk-assessment", "market-analysis"])
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

        # Set up the flow with conditional routing
        workflow.set_entry_point("document_analysis")
        
        # Use conditional edges for proper routing
        workflow.add_conditional_edges(
            "document_analysis",
            self.workflow_router,
            {
                "parallel_analysis": "parallel_analysis",
                "final_recommendations": "final_recommendations",
                "document_analysis": "document_analysis",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "parallel_analysis", 
            self.workflow_router,
            {
                "parallel_analysis": "parallel_analysis",
                "final_recommendations": "final_recommendations", 
                "document_analysis": "document_analysis",
                END: END
            }
        )
        
        workflow.add_edge("final_recommendations", END)

        return workflow.compile()
    
    @traceable(name="multi_agent_workflow", tags=["workflow", "multi-agent", "financial-analysis"])
    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow with parallel execution"""
        
        # Initialize state
        initial_state = WorkflowState(
            query=query,
            context_documents=[],
            document_analysis_result="",
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
            
            # Execute the workflow with tracing
            result = self.workflow.invoke(initial_state)
            
            # Calculate overall confidence
            confidence_scores = result.get("confidence_scores", {})
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
            result["confidence_scores"]["overall"] = overall_confidence
            
            # Format the comprehensive response
            response = self._format_workflow_response(result)
            
            print(f"✅ Multi-agent workflow completed successfully (confidence: {overall_confidence:.1%})")
            
            return {
                "success": True,
                "response": response,
                "workflow_state": result,
                "confidence": overall_confidence,
                "execution_mode": "multi-agent",
                "agents_executed": list(result.get("agent_reasoning", {}).keys())
            }
            
        except Exception as e:
            print(f"❌ Multi-agent workflow failed: {str(e)}")
            return {
                "success": False,
                "response": f"Workflow execution error: {str(e)}",
                "workflow_state": initial_state,
                "confidence": 0.0,
                "execution_mode": "multi-agent-failed",
                "error": str(e)
            }
    
    def _format_workflow_response(self, state: WorkflowState) -> str:
        """Format the multi-agent workflow results into a comprehensive response"""
        
        confidence_scores = state.get("confidence_scores", {})
        overall_confidence = confidence_scores.get("overall", 0.5)
        
        response = f"""## 🤖 Multi-Agent Analysis

**Query:** {state['query']}
**Confidence:** {overall_confidence:.1%} | **Date:** {datetime.now().strftime('%m/%d %H:%M')}

### 💡 Executive Summary
{state.get('final_recommendation', 'No recommendations available')}

### � Analysis Details
**Document Analysis:** {state.get('document_analysis_result', 'Not available')[:200]}{'...' if len(state.get('document_analysis_result', '')) > 200 else ''}

**Risk Assessment:** {state.get('risk_assessment', 'Not available')[:200]}{'...' if len(state.get('risk_assessment', '')) > 200 else ''}

**Market Analysis:** {state.get('market_analysis', 'Not available')[:200]}{'...' if len(state.get('market_analysis', '')) > 200 else ''}

### � Agent Insights"""
        
        # Add agent reasoning summary in consolidated format
        agent_reasoning = state.get("agent_reasoning", {})
        if agent_reasoning:
            for agent, reasoning in agent_reasoning.items():
                agent_name = agent.replace('_', ' ').title()
                response += f"\n• **{agent_name}:** {reasoning[:120]}{'...' if len(reasoning) > 120 else ''}"
        
        # Add confidence scores in compact format
        confidence_scores = state.get("confidence_scores", {})
        if confidence_scores:
            response += f"\n\n**Confidence Metrics:** "
            metrics = [f"{metric.replace('_', ' ').title()}: {score:.0%}" for metric, score in confidence_scores.items()]
            response += " | ".join(metrics)
        
        # Add error messages if any (compact)
        error_messages = state.get("error_messages", [])
        if error_messages:
            response += f"\n\n**Warnings:** {'; '.join(error_messages[:2])}"
        
        # Add top source documents in compact format
        context_docs = state.get("context_documents", [])
        if context_docs:
            response += f"\n\n**Sources:** "
            sources = [f"{doc.get('metadata', {}).get('filename', 'Unknown')} ({doc.get('similarity_score', 0.0):.0%})" for doc in context_docs[:3]]
            response += " | ".join(sources)
        
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