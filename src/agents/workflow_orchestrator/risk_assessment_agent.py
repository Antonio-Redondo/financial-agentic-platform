"""
Risk Assessment Agent

Specialized agent for comprehensive financial risk assessment including credit risk,
market risk, operational risk, and risk mitigation strategies. Provides quantitative
risk metrics and probability assessments for financial forecasting.
"""

# Standard library imports
from typing import Dict, Any

# Local imports
from ..analyst import FinancialAnalyst


class RiskAssessmentAgent:
    """Specialized agent for financial risk assessment"""
    
    def __init__(self):
        self.analyst = FinancialAnalyst()
        self.agent_name = "Risk Assessment Agent"
        
    def assess_risk(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        try:
            query = state["query"]
            doc_analysis = state.get("document_analysis", "")
            
            risk_prompt = f"""You are a Risk Assessment Specialist for financial forecasting and mortgage-backed securities.
            
            USER QUERY: {query}
            
            DOCUMENT ANALYSIS CONTEXT:
            {doc_analysis}
            
            Provide a comprehensive risk assessment covering:
            
            🔴 **CREDIT RISK ANALYSIS:**
            - Default probability assessments and modeling
            - Credit quality indicators (FICO scores, LTV ratios, DTI)
            - Portfolio concentration risks by geography/property type
            - Borrower profile analysis and demographics
            - Historical loss rates and charge-off patterns
            - Credit enhancement adequacy evaluation
            
            📈 **MARKET RISK EVALUATION:**
            - Interest rate sensitivity and duration analysis
            - Prepayment risk factors and speed volatility
            - Market volatility impacts on valuations
            - Economic scenario analysis (base/stress/optimistic)
            - Liquidity risk in secondary markets
            - Correlation risks with other asset classes
            
            ⚠️ **OPERATIONAL RISK FACTORS:**
            - Model risk considerations and validation
            - Data quality risks and measurement errors
            - Regulatory compliance risks and changes
            - Operational process risks and controls
            - Counterparty risks (servicers, trustees)
            - Technology and cybersecurity risks
            
            🎯 **RISK MITIGATION STRATEGIES:**
            - Recommended hedging approaches and instruments
            - Portfolio optimization suggestions for risk reduction
            - Risk monitoring frameworks and early warning indicators
            - Stress testing recommendations and scenarios
            - Capital allocation and reserve requirements
            - Risk transfer mechanisms (insurance, derivatives)
            
            📊 **QUANTITATIVE RISK METRICS:**
            - Value at Risk (VaR) estimates with confidence intervals
            - Expected loss calculations and scenarios
            - Risk-adjusted return metrics
            - Sensitivity analyses for key risk factors
            - Monte Carlo simulation recommendations
            
            Provide specific risk metrics, probability ranges, and quantitative assessments where possible.
            Include confidence levels for all major risk assessments."""
            
            result = self.analyst.analyze(risk_prompt)
            
            # Update state
            state["risk_assessment"] = result.get("analysis", "")
            state["confidence_scores"]["risk_assessment"] = result.get("confidence", 0.8)
            state["agent_reasoning"]["risk_assessment"] = "Comprehensive risk analysis across credit, market, and operational factors"
            state["current_step"] = "risk_assessment_complete"
            
            print(f"✅ {self.agent_name}: Risk assessment completed")
            
        except Exception as e:
            error_msg = f"Risk Assessment Error: {str(e)}"
            state["error_messages"].append(error_msg)
            state["risk_assessment"] = "Error in risk assessment - using conservative assumptions"
            state["confidence_scores"]["risk_assessment"] = 0.3
            print(f"❌ {self.agent_name}: {error_msg}")
            
        return state
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for monitoring and debugging"""
        return {
            "name": self.agent_name,
            "purpose": "Comprehensive financial risk assessment and mitigation",
            "capabilities": [
                "Credit risk modeling",
                "Market risk analysis",
                "Operational risk evaluation",
                "Risk mitigation strategies",
                "Quantitative risk metrics",
                "Scenario stress testing"
            ],
            "output": "Multi-dimensional risk assessment with quantitative metrics"
        }