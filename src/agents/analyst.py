# Standard library imports
import os
import time
from typing import Dict

# Third-party imports will be imported inline where needed to avoid unnecessary loading

class FinancialAnalyst:
    def __init__(self):
        self.llm = None
        self._initialize_llm()
        
        # Import LangSmith integration for tracing
        try:
            from .langsmith_integration import langsmith_manager
            self.langsmith = langsmith_manager
        except ImportError:
            self.langsmith = None
        
    def _initialize_llm(self):
        """Initialize Amazon Titan for superior financial analysis"""
        try:
            print("🚀 Initializing Amazon Titan Text...")
            from langchain_community.chat_models import BedrockChat
            
           
            self.llm = BedrockChat(
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
        
    def analyze(self, text: str) -> Dict:
        """Advanced financial analysis using Amazon Titan with comprehensive tracing"""
        
        # Start timing for performance tracking
        start_time = time.time()
        
        if self.llm is None:
            error_result = {
                "analysis": "❌ Unable to connect to Amazon Titan via AWS Bedrock. Please check your AWS configuration and ensure Titan models are available in your region.",
                "confidence": 0.0
            }
            
            # Trace the error
            if self.langsmith:
                self.langsmith.trace_bedrock_analysis(
                    analysis_type="financial_analysis_error",
                    input_data={"query": text[:200]},
                    analysis_results=error_result,
                    model_id="amazon.titan-tg1-large",
                    processing_steps=["model_initialization_failed"],
                    latency_ms=(time.time() - start_time) * 1000,
                    metadata={"error": "bedrock_unavailable"}
                )
            
            return error_result
        
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
            
            # Trace the chat interaction start
            chat_start_time = time.time()
            
            # Use the chat model interface with proper message format
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=prompt)
            
            # Trace Bedrock chat interaction
            if self.langsmith:
                self.langsmith.trace_bedrock_chat(
                    system_prompt="You are a senior financial analyst and quantitative expert...",
                    user_message=text,
                    model_id="amazon.titan-tg1-large",
                    inference_params={
                        "temperature": 0.8,
                        "maxTokenCount": 4000,
                        "topP": 0.9
                    },
                    metadata={
                        "analysis_type": "financial_analysis",
                        "prompt_template": "enhanced_financial_prompt"
                    }
                )
            
            # Make the actual Bedrock call
            response = self.llm.invoke([message])
            chat_latency = (time.time() - chat_start_time) * 1000
            
            # Extract content from the response
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Prepare result
            result = {
                "analysis": response_content,
                "confidence": 1.0  # Using real model - no synthetic confidence scoring
            }
            
            # Calculate total processing time
            total_latency = (time.time() - start_time) * 1000
            
            # Trace the complete Bedrock chat with response
            if self.langsmith:
                self.langsmith.trace_bedrock_chat(
                    system_prompt="You are a senior financial analyst and quantitative expert...",
                    user_message=text,
                    assistant_response=response_content,
                    model_id="amazon.titan-tg1-large",
                    inference_params={
                        "temperature": 0.8,
                        "maxTokenCount": 4000,
                        "topP": 0.9
                    },
                    latency_ms=chat_latency,
                    token_usage={
                        "input_tokens": len(prompt.split()),
                        "output_tokens": len(response_content.split()),
                        "total_tokens": len(prompt.split()) + len(response_content.split())
                    },
                    metadata={
                        "analysis_type": "financial_analysis",
                        "prompt_template": "enhanced_financial_prompt",
                        "response_length": len(response_content)
                    }
                )
                
                # Trace the analysis operation
                self.langsmith.trace_bedrock_analysis(
                    analysis_type="comprehensive_financial_analysis",
                    input_data={
                        "user_query": text,
                        "prompt_length": len(prompt),
                        "analysis_scope": ["quantitative", "market_insights", "risk_assessment", "recommendations"]
                    },
                    analysis_results={
                        "analysis_content": response_content[:500] + "..." if len(response_content) > 500 else response_content,
                        "analysis_sections": self._extract_analysis_sections(response_content),
                        "confidence": 1.0
                    },
                    model_id="amazon.titan-tg1-large",
                    processing_steps=[
                        "prompt_construction",
                        "bedrock_invocation", 
                        "response_processing",
                        "content_extraction"
                    ],
                    confidence_scores={
                        "model_confidence": 1.0,
                        "content_quality": self._assess_content_quality(response_content),
                        "completeness": self._assess_completeness(response_content)
                    },
                    latency_ms=total_latency,
                    metadata={
                        "titan_model": "amazon.titan-tg1-large",
                        "inference_success": True,
                        "response_type": "structured_analysis"
                    }
                )
            
            return result
            
        except Exception as e:
            error_latency = (time.time() - start_time) * 1000
            error_msg = f"❌ Error with Amazon Titan financial analysis: {str(e)}"
            print(error_msg)
            
            error_result = {
                "analysis": f"I encountered an error while processing your financial analysis request: {str(e)}. This may be due to model availability or AWS configuration. Please verify that Amazon Titan is accessible in your AWS region.",
                "confidence": 0.0
            }
            
            # Trace the error
            if self.langsmith:
                self.langsmith.trace_bedrock_analysis(
                    analysis_type="financial_analysis_error",
                    input_data={"query": text[:200]},
                    analysis_results=error_result,
                    model_id="amazon.titan-tg1-large",
                    processing_steps=["prompt_construction", "bedrock_invocation_failed"],
                    confidence_scores={"error_occurred": True},
                    latency_ms=error_latency,
                    metadata={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "inference_success": False
                    }
                )
            
            return error_result
    
    def _extract_analysis_sections(self, content: str) -> Dict:
        """Extract analysis sections for better tracing"""
        try:
            sections = {}
            
            # Look for common section indicators
            if "QUANTITATIVE ANALYSIS" in content.upper():
                sections["has_quantitative"] = True
            if "MARKET INSIGHTS" in content.upper():
                sections["has_market_insights"] = True
            if "RISK ASSESSMENT" in content.upper():
                sections["has_risk_assessment"] = True
            if "STRATEGIC RECOMMENDATIONS" in content.upper() or "RECOMMENDATIONS" in content.upper():
                sections["has_recommendations"] = True
                
            sections["total_sections"] = len([k for k in sections.keys() if sections[k]])
            return sections
            
        except Exception:
            return {"extraction_failed": True}
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess content quality for tracing"""
        try:
            quality_score = 0.5  # Base score
            
            # Check for financial terms
            financial_terms = ["analysis", "risk", "return", "investment", "portfolio", "market", "financial"]
            term_count = sum(1 for term in financial_terms if term in content.lower())
            quality_score += min(term_count * 0.1, 0.3)
            
            # Check for numerical content
            import re
            numbers = re.findall(r'\d+\.?\d*%?', content)
            if len(numbers) > 5:
                quality_score += 0.2
                
            return min(quality_score, 1.0)
            
        except Exception:
            return 0.5
    
    def _assess_completeness(self, content: str) -> float:
        """Assess response completeness for tracing"""
        try:
            completeness = 0.3  # Base score
            
            # Check length
            if len(content) > 500:
                completeness += 0.3
            if len(content) > 1000:
                completeness += 0.2
                
            # Check for structured content
            if any(marker in content for marker in ["•", "1.", "2.", "-"]):
                completeness += 0.2
                
            return min(completeness, 1.0)
            
        except Exception:
            return 0.5
