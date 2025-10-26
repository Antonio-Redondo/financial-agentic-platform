"""
Workflow Orchestrator Package

This package contains specialized agents for multi-agent financial analysis workflow:
- DocumentAnalysisAgent: Document extraction and analysis
- RiskAssessmentAgent: Comprehensive risk evaluation
- MarketAnalysisAgent: Market conditions and economic analysis
- RecommendationAgent: Final synthesis and recommendations
- FinancialWorkflow: Orchestrator with parallel execution capabilities
"""

from .document_analysis_agent import DocumentAnalysisAgent
from .risk_assessment_agent import RiskAssessmentAgent
from .market_analysis_agent import MarketAnalysisAgent
from .recommendation_agent import RecommendationAgent
from .financial_workflow import FinancialWorkflow, create_financial_workflow

__all__ = [
    'DocumentAnalysisAgent',
    'RiskAssessmentAgent', 
    'MarketAnalysisAgent',
    'RecommendationAgent',
    'FinancialWorkflow',
    'create_financial_workflow'
]