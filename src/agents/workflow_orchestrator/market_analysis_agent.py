"""
Market Analysis Agent

Specialized agent for market analysis and economic factors evaluation.
Focuses on mortgage markets, macroeconomic trends, prepayment analysis,
and market outlook for financial forecasting.
"""

# Standard library imports
from typing import Dict, Any

# Third-party imports
from langsmith import traceable

# Local imports
from ..analyst import FinancialAnalyst


class MarketAnalysisAgent:
    """Specialized agent for market analysis and economic factors"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        self.agent_name = "Market Analysis Agent"
        
    @traceable(name="market_analysis_agent", tags=["agent", "market-analysis", "economic-factors"])
    def analyze_market(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions and economic factors"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis_result", "")
            risk_assessment = state.get("risk_assessment", "")
            
            market_prompt = f"""You are a Market Analysis Specialist focusing on mortgage markets and macroeconomic factors.
            
            USER QUERY: {query}
            
            DOCUMENT ANALYSIS CONTEXT:
            {doc_analysis}
            
            RISK ASSESSMENT CONTEXT:
            {risk_assessment}
            
            Provide comprehensive market analysis including:
            
            📊 **CURRENT MARKET CONDITIONS:**
            - Interest rate environment and yield curve analysis
            - Mortgage market dynamics and issuance trends
            - Housing market indicators (prices, sales, inventory)
            - Economic growth factors and GDP trends
            - Inflation expectations and monetary policy impacts
            - Credit market conditions and spreads
            
            📈 **PREPAYMENT ANALYSIS:**
            - Current prepayment speeds (CPR/PSA) and trends
            - Seasonal patterns and historical variations
            - Economic drivers of prepayment behavior
            - Refinancing incentives analysis and rate sensitivity
            - Geographic and demographic prepayment patterns
            - Impact of government programs on prepayment
            
            🌍 **MACROECONOMIC FACTORS:**
            - Federal Reserve policy impacts and forward guidance
            - Inflation expectations and real rate environment
            - Employment and income trends affecting borrowers
            - Regional economic variations and local factors
            - International economic influences
            - Fiscal policy impacts on housing and credit
            
            🏠 **HOUSING MARKET DYNAMICS:**
            - Home price appreciation trends and forecasts
            - Housing supply and demand fundamentals
            - First-time buyer activity and demographics
            - Construction activity and permits
            - Affordability metrics and trends
            - Regional market variations and hotspots
            
            💹 **FINANCIAL MARKET CONTEXT:**
            - Credit spread environments and trends
            - Investor demand for mortgage securities
            - Bank and non-bank lending capacity
            - Regulatory environment and policy changes
            - Competition in mortgage origination
            - Secondary market liquidity conditions
            
            🔮 **MARKET OUTLOOK AND FORECASTS:**
            - Short-term (3-6 months) market projections
            - Medium-term (1-2 years) economic forecasts
            - Key market risk scenarios and probabilities
            - Opportunity identification and timing
            - Critical inflection points and catalysts
            - Policy risk assessments
            
            Include specific market data, quantitative trends, and probability-weighted projections where available.
            Provide confidence intervals for major forecasts and identify key uncertainty factors."""
            
            result = self.analyst.analyze(market_prompt)
            
            # Update state
            state["market_analysis"] = result.get("analysis", "")
            state["confidence_scores"]["market_analysis"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["market_analysis"] = "Market conditions analysis with focus on prepayment and economic factors"
            state["current_step"] = "market_analysis_complete"
            
            print(f"✅ {self.agent_name}: Market analysis completed")
            
        except Exception as e:
            error_msg = f"Market Analysis Error: {str(e)}"
            state["error_messages"].append(error_msg)
            state["market_analysis"] = "Error in market analysis - using historical averages"
            state["confidence_scores"]["market_analysis"] = 0.3
            print(f"❌ {self.agent_name}: {error_msg}")
            
        return state
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for monitoring and debugging"""
        return {
            "name": self.agent_name,
            "purpose": "Market conditions and macroeconomic analysis",
            "capabilities": [
                "Interest rate environment analysis",
                "Prepayment behavior modeling",
                "Macroeconomic trend evaluation",
                "Housing market dynamics",
                "Financial market context",
                "Market outlook forecasting"
            ],
            "output": "Comprehensive market analysis with economic forecasts"
        }