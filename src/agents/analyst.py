# Standard library imports
import os
import time
from typing import Dict

# Import LangSmith tracing
# Local imports
from .langsmith_integration import langsmith_manager, trace_financial_operation, trace_bedrock_call, with_langsmith_callbacks

# Third-party imports will be imported inline where needed to avoid unnecessary loading

class FinancialAnalyst:
    def __init__(self):
        self.llm = None
        self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize Amazon Titan for superior financial analysis"""
        try:
            print("🚀 Initializing Amazon Titan Text...")
            from langchain_community.chat_models import BedrockChat
            
           
            self.llm = with_langsmith_callbacks(
                BedrockChat,
                model_id="amazon.titan-tg1-large",
                model_kwargs={
                     "temperature": 0.8,     # Controls randomness
                     "maxTokenCount": 4000,  # Max response length
                     "topP": 0.9            # Nucleus sampling (top 90%)
                }
            )
            print("✅ Amazon Titan Text ready for financial analysis!")
        except Exception as e:
            print(f"❌ Failed to initialize Amazon Titan: {str(e)}")
            print("Please ensure your AWS credentials have access to Amazon Titan models in Bedrock")
            self.llm = None
        
    @trace_financial_operation("financial_analysis")
    def analyze(self, text: str) -> Dict:
        """Advanced financial analysis using Amazon Titan"""
        
        start_time = time.time()
        
        if self.llm is None:
            return {
                "analysis": "❌ Unable to connect to Amazon Titan via AWS Bedrock. Please check your AWS configuration and ensure Titan models are available in your region.",
                "confidence": 0.0
            }
        
        try:
            # Enhanced prompt optimized for Amazon Titan's financial analysis capabilities
            prompt = f"""You are a senior financial analyst and quantitative expert specializing in mortgage-backed securities, prepayment modeling, and financial risk assessment. You have deep expertise in:

- Mortgage prepayment analysis (CPR, PSA, SMM models)
- Interest rate risk and duration analysis  
- Credit risk assessment and portfolio optimization
- Financial modeling and quantitative analysis
- Regulatory compliance (Basel III, Dodd-Frank, etc.)
- Market risk and stress testing methodologies

USER REQUEST: {text}

Please provide a comprehensive financial analysis that includes:

🔢 QUANTITATIVE ANALYSIS:
- Relevant financial metrics, ratios, and calculations
- Numerical estimates with supporting methodology
- Statistical insights and probability assessments
- Risk-adjusted returns and performance measures

📊 MARKET INSIGHTS:
- Current market conditions and trends
- Historical context and comparative analysis
- Economic factors and their impact
- Industry benchmarks and best practices

⚠️ RISK ASSESSMENT:
- Identification of key risk factors
- Risk mitigation strategies and recommendations
- Scenario analysis and stress testing insights
- Regulatory and compliance considerations

💡 STRATEGIC RECOMMENDATIONS:
- Actionable investment or operational recommendations
- Portfolio optimization suggestions
- Implementation strategies and timelines
- Performance monitoring and success metrics

Format your response professionally with clear sections, bullet points where appropriate, and specific numerical estimates. Draw from established financial principles, industry standards, and quantitative methodologies.

IMPORTANT: Provide detailed, substantive analysis using your extensive financial knowledge and current market understanding. Focus on delivering actionable, expert-level insights with concrete recommendations and quantitative assessments where applicable."""
            
            # Use the chat model interface with proper message format
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=prompt)
            
            # Trace the LLM call with Bedrock context
            llm_start_time = time.time()
            with trace_bedrock_call("amazon.titan-tg1-large", "financial_analysis"):
                response = self.llm.invoke([message])
            llm_latency = (time.time() - llm_start_time) * 1000
            
            # Extract content from the response
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Log the LLM response to LangSmith
            langsmith_manager.trace_llm_response(
                prompt=prompt,
                response=response_content,
                model_name="amazon.titan-tg1-large",
                latency_ms=llm_latency,
                metadata={
                    "component": "financial_analyst",
                    "operation": "financial_analysis",
                    "input_length": len(text),
                    "output_length": len(response_content)
                }
            )
            
            total_latency = (time.time() - start_time) * 1000
            
            return {
                "analysis": response_content,
                "confidence": 1.0,  # Using real model - no synthetic confidence scoring
                "latency_ms": total_latency
            }
            
        except Exception as e:
            error_msg = f"❌ Error with Amazon Titan financial analysis: {str(e)}"
            print(error_msg)
            
            return {
                "analysis": f"I encountered an error while processing your financial analysis request: {str(e)}. This may be due to model availability or AWS configuration. Please verify that Amazon Titan is accessible in your AWS region.",
                "confidence": 0.0
            }
