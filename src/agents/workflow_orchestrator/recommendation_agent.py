"""
Recommendation Agent

Final synthesis agent that combines document analysis, risk assessment, and market analysis
into actionable investment recommendations and strategic guidance. Provides executive
summary, quantitative projections, and implementation roadmap.
"""

# Standard library imports
from typing import Dict, Any
from datetime import datetime

# Local imports
from ..analyst import FinancialAnalyst


class RecommendationAgent:
    """Final agent that synthesizes all analyses into actionable recommendations"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        self.agent_name = "Recommendation Agent"
        
    def generate_recommendations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all analyses into final recommendations"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis", "")
            risk_assessment = state.get("risk_assessment", "")
            market_analysis = state.get("market_analysis", "")
            
            synthesis_prompt = f"""You are a Senior Financial Strategist synthesizing multi-agent analysis for final recommendations.
            
            USER QUERY: {query}
            
            📄 **DOCUMENT ANALYSIS:**
            {doc_analysis}
            
            ⚠️ **RISK ASSESSMENT:**
            {risk_assessment}
            
            📊 **MARKET ANALYSIS:**
            {market_analysis}
            
            Based on this comprehensive multi-agent analysis, provide:
            
            🎯 **EXECUTIVE SUMMARY:**
            - Key findings synthesis from all analytical dimensions
            - Overall investment thesis and strategic positioning
            - Critical risk factors and opportunity highlights
            - Confidence assessment across analytical components
            - Key assumptions and limitations
            
            💡 **STRATEGIC RECOMMENDATIONS:**
            - Primary investment/operational recommendations with rationale
            - Risk-return optimization strategies
            - Portfolio positioning and allocation guidance
            - Timing considerations and market entry/exit points
            - Alternative scenarios and contingency planning
            
            📈 **QUANTITATIVE PROJECTIONS:**
            - Prepayment speed forecasts with confidence intervals
            - Return expectations across multiple scenarios
            - Duration and convexity projections
            - Sensitivity analyses for key variables
            - Monte Carlo simulation insights (if applicable)
            - Stress test results and breakeven analyses
            
            🚨 **RISK MANAGEMENT FRAMEWORK:**
            - Top 3 risk monitoring priorities with metrics
            - Recommended hedging strategies and instruments
            - Position sizing and concentration limits
            - Early warning indicators and trigger points
            - Stress testing protocols and frequency
            - Risk reporting and governance recommendations
            
            ⏰ **IMPLEMENTATION ROADMAP:**
            - **Immediate Actions (0-30 days):**
              * Critical decisions and approvals needed
              * Initial position establishment or adjustments
              * Risk monitoring implementation
              * Data gathering and analysis setup
            
            - **Short-term Initiatives (1-6 months):**
              * Portfolio optimization execution
              * Hedging program implementation
              * Performance monitoring and reporting
              * Market condition reassessment points
            
            - **Long-term Strategic Goals (6+ months):**
              * Strategic positioning objectives
              * Portfolio evolution and growth targets
              * Risk framework maturation
              * Market opportunity capture
            
            📊 **SUCCESS METRICS AND KPIs:**
            - Primary performance indicators to track
            - Risk metrics and acceptable ranges
            - Market benchmark comparisons
            - Review and reassessment schedules
            - Decision criteria for strategy adjustments
            
            🔄 **MONITORING AND REVIEW FRAMEWORK:**
            - Monthly review agenda and metrics
            - Quarterly strategic reassessment
            - Annual strategy review and updates
            - Market condition change triggers
            - Performance attribution analysis
            
            Format as a comprehensive financial recommendation with clear action items,
            specific metrics, and implementation timelines. Include confidence levels
            for all major recommendations and identify key decision dependencies."""
            
            result = self.analyst.analyze(synthesis_prompt)
            
            # Calculate overall confidence
            confidence_scores = state["confidence_scores"]
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
            
            # Update state
            state["final_recommendation"] = result.get("analysis", "")
            state["confidence_scores"]["overall"] = overall_confidence
            state["agent_reasoning"]["final_synthesis"] = "Synthesized multi-agent analysis into actionable recommendations"
            state["current_step"] = "workflow_complete"
            
            print(f"✅ {self.agent_name}: Final recommendations completed (Overall confidence: {overall_confidence:.1%})")
            
        except Exception as e:
            error_msg = f"Recommendation Generation Error: {str(e)}"
            state["error_messages"].append(error_msg)
            state["final_recommendation"] = "Error generating final recommendations - please review individual agent outputs"
            state["confidence_scores"]["overall"] = 0.3
            print(f"❌ {self.agent_name}: {error_msg}")
            
        return state
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for monitoring and debugging"""
        return {
            "name": self.agent_name,
            "purpose": "Strategic synthesis and actionable recommendations",
            "capabilities": [
                "Multi-agent analysis synthesis",
                "Strategic recommendation development",
                "Quantitative projection integration",
                "Risk management framework design",
                "Implementation roadmap creation",
                "Success metrics definition"
            ],
            "output": "Comprehensive strategic recommendations with implementation plan"
        }