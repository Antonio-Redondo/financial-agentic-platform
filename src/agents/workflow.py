"""
LangGraph Multi-Agent Workflow for Financial Analysis
Orchestrates specialized agents for comprehensive financial forecasting
"""
import asyncio
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime
import json

# Import our existing agents
from .analyst import FinancialAnalyst
from .vector_store import VectorStore


class WorkflowState(TypedDict):
    """State shared across all agents in the workflow"""
    query: str
    context_documents: List[Dict]
    document_analysis: str
    risk_assessment: str
    market_analysis: str
    final_recommendation: str
    confidence_scores: Dict[str, float]
    agent_reasoning: Dict[str, str]
    current_step: str
    error_messages: List[str]


class DocumentAnalysisAgent:
    """Specialized agent for document analysis and information extraction"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.analyst = FinancialAnalyst()
        
    def analyze_documents(self, state: WorkflowState) -> WorkflowState:
        """Analyze documents and extract key financial information"""
        try:
            query = state["query"]
            
            # Search for relevant documents
            relevant_docs = self.vector_store.search_documents(query, k=5)
            
            # Create specialized prompt for document analysis
            doc_context = "\n".join([f"Document: {doc.get('filename', 'Unknown')}\nContent: {doc.get('content', '')}" 
                                   for doc in relevant_docs])
            
            analysis_prompt = f"""You are a Document Analysis Specialist for financial documents. 
            
            USER QUERY: {query}
            
            RELEVANT DOCUMENTS:
            {doc_context}
            
            Provide a comprehensive document analysis focusing on:
            1. Key financial metrics and data points
            2. Document type and reliability assessment
            3. Relevant historical data and trends
            4. Data quality and completeness evaluation
            5. Key insights for financial forecasting
            
            Be specific and quantitative where possible."""
            
            result = self.analyst.analyze(analysis_prompt)
            
            # Update state
            state["context_documents"] = relevant_docs
            state["document_analysis"] = result.get("analysis", "")
            state["confidence_scores"]["document_analysis"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["document_analysis"] = "Analyzed documents for key financial indicators and data quality"
            state["current_step"] = "document_analysis_complete"
            
        except Exception as e:
            state["error_messages"].append(f"Document Analysis Error: {str(e)}")
            state["document_analysis"] = "Error in document analysis - proceeding with limited context"
            state["confidence_scores"]["document_analysis"] = 0.3
            
        return state


class RiskAssessmentAgent:
    """Specialized agent for financial risk assessment"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        
    def assess_risk(self, state: WorkflowState) -> WorkflowState:
        """Perform comprehensive risk assessment"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis", "")
            
            risk_prompt = f"""You are a Risk Assessment Specialist for financial forecasting and mortgage-backed securities.
            
            USER QUERY: {query}
            
            DOCUMENT ANALYSIS CONTEXT:
            {doc_analysis}
            
            Provide a comprehensive risk assessment covering:
            
            🔴 CREDIT RISK ANALYSIS:
            - Default probability assessments
            - Credit quality indicators
            - Portfolio concentration risks
            - Borrower profile analysis
            
            📈 MARKET RISK EVALUATION:
            - Interest rate sensitivity
            - Prepayment risk factors
            - Market volatility impacts
            - Economic scenario analysis
            
            ⚠️ OPERATIONAL RISK FACTORS:
            - Model risk considerations
            - Data quality risks
            - Regulatory compliance risks
            - Operational process risks
            
            🎯 RISK MITIGATION STRATEGIES:
            - Recommended hedging approaches
            - Portfolio optimization suggestions
            - Risk monitoring frameworks
            - Stress testing recommendations
            
            Provide specific risk metrics, probability ranges, and quantitative assessments where possible."""
            
            result = self.analyst.analyze(risk_prompt)
            
            # Update state
            state["risk_assessment"] = result.get("analysis", "")
            state["confidence_scores"]["risk_assessment"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["risk_assessment"] = "Comprehensive risk analysis across credit, market, and operational factors"
            state["current_step"] = "risk_assessment_complete"
            
        except Exception as e:
            state["error_messages"].append(f"Risk Assessment Error: {str(e)}")
            state["risk_assessment"] = "Error in risk assessment - using conservative assumptions"
            state["confidence_scores"]["risk_assessment"] = 0.3
            
        return state


class MarketAnalysisAgent:
    """Specialized agent for market analysis and economic factors"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        
    def analyze_market(self, state: WorkflowState) -> WorkflowState:
        """Analyze market conditions and economic factors"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis", "")
            risk_assessment = state.get("risk_assessment", "")
            
            market_prompt = f"""You are a Market Analysis Specialist focusing on mortgage markets and economic factors.
            
            USER QUERY: {query}
            
            DOCUMENT ANALYSIS CONTEXT:
            {doc_analysis}
            
            RISK ASSESSMENT CONTEXT:
            {risk_assessment}
            
            Provide comprehensive market analysis including:
            
            📊 CURRENT MARKET CONDITIONS:
            - Interest rate environment and trends
            - Mortgage market dynamics
            - Housing market indicators
            - Economic growth factors
            
            📈 PREPAYMENT ANALYSIS:
            - Current prepayment speeds (CPR/PSA)
            - Seasonal patterns and trends
            - Economic drivers of prepayment
            - Refinancing incentives analysis
            
            🌍 MACROECONOMIC FACTORS:
            - Federal Reserve policy impacts
            - Inflation expectations
            - Employment and income trends
            - Regional economic variations
            
            🔮 MARKET OUTLOOK:
            - Short-term (3-6 months) projections
            - Medium-term (1-2 years) forecasts
            - Key market risk scenarios
            - Opportunity identification
            
            Include specific market data, trends, and quantitative projections where available."""
            
            result = self.analyst.analyze(market_prompt)
            
            # Update state
            state["market_analysis"] = result.get("analysis", "")
            state["confidence_scores"]["market_analysis"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["market_analysis"] = "Market conditions analysis with focus on prepayment and economic factors"
            state["current_step"] = "market_analysis_complete"
            
        except Exception as e:
            state["error_messages"].append(f"Market Analysis Error: {str(e)}")
            state["market_analysis"] = "Error in market analysis - using historical averages"
            state["confidence_scores"]["market_analysis"] = 0.3
            
        return state


class RecommendationAgent:
    """Final agent that synthesizes all analyses into actionable recommendations"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        
    def generate_recommendations(self, state: WorkflowState) -> WorkflowState:
        """Synthesize all analyses into final recommendations"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis", "")
            risk_assessment = state.get("risk_assessment", "")
            market_analysis = state.get("market_analysis", "")
            
            synthesis_prompt = f"""You are a Senior Financial Strategist synthesizing multi-agent analysis for final recommendations.
            
            USER QUERY: {query}
            
            📄 DOCUMENT ANALYSIS:
            {doc_analysis}
            
            ⚠️ RISK ASSESSMENT:
            {risk_assessment}
            
            📊 MARKET ANALYSIS:
            {market_analysis}
            
            Based on this comprehensive multi-agent analysis, provide:
            
            🎯 EXECUTIVE SUMMARY:
            - Key findings synthesis
            - Overall confidence assessment
            - Critical risk factors
            - Market opportunity highlights
            
            💡 STRATEGIC RECOMMENDATIONS:
            - Primary investment/operational recommendations
            - Risk mitigation priorities
            - Portfolio optimization strategies
            - Timing considerations
            
            📈 QUANTITATIVE PROJECTIONS:
            - Prepayment speed forecasts (if applicable)
            - Return expectations with confidence intervals
            - Key sensitivity analyses
            - Scenario-based outcomes
            
            🚨 RISK MANAGEMENT:
            - Top 3 risk monitoring priorities
            - Recommended hedging strategies
            - Stress testing suggestions
            - Warning indicators to watch
            
            ⏰ IMPLEMENTATION ROADMAP:
            - Immediate actions (0-30 days)
            - Short-term initiatives (1-6 months)
            - Long-term strategic goals (6+ months)
            - Success metrics and KPIs
            
            Format as a comprehensive financial recommendation with clear action items."""
            
            result = self.analyst.analyze(synthesis_prompt)
            
            # Calculate overall confidence
            confidence_scores = state["confidence_scores"]
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
            
            # Update state
            state["final_recommendation"] = result.get("analysis", "")
            state["confidence_scores"]["overall"] = overall_confidence
            state["agent_reasoning"]["final_synthesis"] = "Synthesized multi-agent analysis into actionable recommendations"
            state["current_step"] = "workflow_complete"
            
        except Exception as e:
            state["error_messages"].append(f"Recommendation Generation Error: {str(e)}")
            state["final_recommendation"] = "Error generating final recommendations - please review individual agent outputs"
            state["confidence_scores"]["overall"] = 0.3
            
        return state


class FinancialWorkflow:
    """LangGraph workflow orchestrator for multi-agent financial analysis"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
        # Initialize specialized agents
        self.doc_agent = DocumentAnalysisAgent(vector_store)
        self.risk_agent = RiskAssessmentAgent()
        self.market_agent = MarketAnalysisAgent()
        self.recommendation_agent = RecommendationAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("document_analysis", self.doc_agent.analyze_documents)
        workflow.add_node("risk_assessment", self.risk_agent.assess_risk)
        workflow.add_node("market_analysis", self.market_agent.analyze_market)
        workflow.add_node("final_recommendations", self.recommendation_agent.generate_recommendations)
        
        # Define the workflow sequence
        workflow.set_entry_point("document_analysis")
        workflow.add_edge("document_analysis", "risk_assessment")
        workflow.add_edge("risk_assessment", "market_analysis")
        workflow.add_edge("market_analysis", "final_recommendations")
        workflow.add_edge("final_recommendations", END)
        
        # Compile the workflow
        return workflow.compile()
    
    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow"""
        
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
            # Execute the workflow
            result = self.workflow.invoke(initial_state)
            
            # Format the comprehensive response
            response = self._format_workflow_response(result)
            
            return {
                "success": True,
                "response": response,
                "workflow_state": result,
                "confidence": result.get("confidence_scores", {}).get("overall", 0.5)
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Workflow execution error: {str(e)}",
                "workflow_state": initial_state,
                "confidence": 0.0
            }
    
    def _format_workflow_response(self, state: WorkflowState) -> str:
        """Format the multi-agent workflow results into a comprehensive response"""
        
        confidence_scores = state.get("confidence_scores", {})
        overall_confidence = confidence_scores.get("overall", 0.5)
        
        response = f"""# 🏦 Multi-Agent Financial Analysis Results

## 📊 Analysis Overview
**Query:** {state['query']}
**Overall Confidence:** {overall_confidence:.1%}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📄 Document Analysis
**Confidence:** {confidence_scores.get('document_analysis', 0.5):.1%}

{state.get('document_analysis', 'No document analysis available')}

---

## ⚠️ Risk Assessment  
**Confidence:** {confidence_scores.get('risk_assessment', 0.5):.1%}

{state.get('risk_assessment', 'No risk assessment available')}

---

## 📈 Market Analysis
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
                relevance = doc.get('relevance', 0.0)
                response += f"{i}. **{filename}** (Relevance: {relevance:.1%})\n"
        
        return response


def create_financial_workflow(vector_store: VectorStore) -> FinancialWorkflow:
    """Factory function to create a configured financial workflow"""
    return FinancialWorkflow(vector_store)