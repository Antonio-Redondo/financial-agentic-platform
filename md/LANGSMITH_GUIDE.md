# 🔍 LangSmith Integration Guide

## Overview
This guide covers the comprehensive LangSmith integration in the Financial Forecast AI application, providing observability, tracing, and performance monitoring for all AI operations.

## 🚀 **Quick Start**

### **Environment Setup**
```bash
# Required environment variables
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=financial-forecast-ai
```

### **Verification**
Check the app logs for successful initialization:
```
✅ LangSmith successfully initialized and connected
```

## 📊 **Features & Capabilities**

### **1. Comprehensive Financial Query Tracing**
- **Query Classification**: Automatically categorizes queries (deal_specific, document_analysis, general_analysis)
- **Deal Number Extraction**: Identifies and tracks specific deal numbers (2025-001, 2025-002, etc.)
- **Performance Metrics**: Response times, token usage, and success rates
- **Error Tracking**: Detailed error logs with context

### **2. Multi-Agent Workflow Monitoring**
- **Workflow Orchestration**: Tracks LangGraph multi-agent interactions
- **Agent Performance**: Individual agent response times and success rates
- **Decision Tracking**: Records which agents are selected and why
- **Fallback Monitoring**: Tracks when single-agent fallback is used

### **3. Document Processing Intelligence**
- **Chunking Analytics**: Document splitting strategy and chunk distribution
- **Vector Search Optimization**: Search query performance and relevance scores
- **Embedding Tracking**: Document indexing and retrieval patterns
- **Content Analysis**: Document type classification and processing efficiency

### **4. AWS Bedrock Integration Monitoring**
- **Model Performance**: Amazon Titan response times and token usage
- **Cost Tracking**: API call frequency and estimated costs
- **Error Handling**: Bedrock service errors and retry logic
- **Model Comparison**: Performance across different Bedrock models

## 🔧 **Implementation Details**

### **Core Integration Module**
Located in: `src/agents/langsmith_integration.py`

**Key Components:**
```python
class LangSmithManager:
    def trace_financial_query()      # Query-level tracing
    def trace_vector_search()        # Document search tracing
    def trace_document_chunking()    # Document processing
    def trace_bedrock_analysis()     # AWS Bedrock monitoring
    def trace_workflow_execution()   # Multi-agent workflows
    def trace_llm_response()         # LLM response analysis
```

### **Automatic Tracing Decorators**
```python
@trace_financial_operation("operation_name")
def your_function():
    # Automatically traced with performance metrics
    pass
```

### **Custom Metadata Tracking**
- **Financial Deal Context**: Deal numbers, document types, analysis complexity
- **User Interaction Patterns**: Query types, session duration, user preferences
- **System Performance**: Memory usage, database connections, processing time
- **Business Metrics**: Query success rates, user satisfaction indicators

## 📈 **Monitoring & Analytics**

### **Real-Time Dashboards**
Access via LangSmith UI: https://smith.langchain.com

**Key Metrics Tracked:**
1. **Query Performance**
   - Average response time: ~2-4 seconds
   - Success rate: >95%
   - Error rate tracking
   
2. **Document Analysis Efficiency**
   - Search relevance scores
   - Chunk retrieval accuracy
   - Document coverage metrics

3. **Multi-Agent Coordination**
   - Agent selection accuracy
   - Workflow completion rates
   - Inter-agent communication efficiency

4. **AWS Bedrock Utilization**
   - Token consumption patterns
   - Model response quality
   - Cost optimization opportunities

### **Alert Configuration**
Set up alerts for:
- Response time > 10 seconds
- Error rate > 5%
- Bedrock API failures
- Memory usage spikes

## 🎯 **Query Analysis Examples**

### **Deal-Specific Query Tracing**
```
Query: "Give me the pricing speed for deal 2025-002"
├── Query Type: deal_specific
├── Deal Numbers: ['2025-002']
├── Search Strategy: targeted_deal_search
├── Documents Found: 5 relevant chunks
├── Response Time: 2.3 seconds
└── Success: ✅
```

### **Comparative Analysis Tracing**
```
Query: "Which deal has the highest pricing speed?"
├── Query Type: comparative_analysis
├── Search Strategy: cross_deal_comparison
├── Deals Analyzed: ['2025-001', '2025-002', '2025-003', '2025-004']
├── Documents Searched: 15 chunks
├── Response Time: 4.1 seconds
└── Success: ✅
```

### **Document Processing Tracing**
```
Document: "FNM_2025-006_RELAY.txt"
├── File Size: 145KB
├── Chunks Created: 145
├── Embedding Generation: 12.5 seconds
├── Index Storage: PostgreSQL/pgvector
└── Processing: ✅ Complete
```

## 🔍 **Advanced Debugging**

### **Trace Inspection**
1. **Access LangSmith UI**
2. **Filter by Project**: "financial-forecast-ai"
3. **Search by Metadata**:
   - `deal_number`: "2025-002"
   - `query_type`: "deal_specific"
   - `agent_mode`: "multi_agent"

### **Performance Analysis**
```python
# Example trace metadata structure
{
    "query": "user_query_here",
    "deal_numbers": ["2025-001"],
    "query_type": "deal_specific",
    "has_document_context": true,
    "search_results_count": 5,
    "agent_mode": "single_agent_fallback",
    "response_time_ms": 2300,
    "tokens_used": 1250,
    "success": true
}
```

### **Error Investigation**
Common error patterns and solutions:
1. **Bedrock Throttling**: Implement exponential backoff
2. **Vector Search Timeout**: Optimize search parameters
3. **Memory Issues**: Monitor chunk size and batch processing
4. **Authentication Failures**: Verify AWS credentials and LangSmith API key

## 📋 **Best Practices**

### **1. Trace Organization**
- Use descriptive operation names
- Include relevant business context
- Tag traces with deal numbers and document types
- Maintain consistent metadata schema

### **2. Performance Optimization**
- Monitor trace overhead (should be <5% of total time)
- Batch trace submissions when possible
- Use appropriate sampling rates for high-volume operations
- Regular cleanup of old traces

### **3. Security Considerations**
- Never trace sensitive financial data directly
- Use anonymized identifiers where possible
- Implement trace data retention policies
- Regular audit of traced information

### **4. Cost Management**
- Monitor LangSmith usage and costs
- Set up appropriate retention periods
- Use sampling for high-frequency operations
- Regular review of tracing strategy

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. LangSmith Not Connecting**
```bash
# Check environment variables
echo $LANGCHAIN_API_KEY
echo $LANGCHAIN_PROJECT

# Verify network connectivity
curl -H "Authorization: Bearer $LANGCHAIN_API_KEY" https://api.smith.langchain.com/runs
```

**2. Missing Traces**
- Verify `LANGCHAIN_TRACING_V2=true`
- Check for network connectivity issues
- Ensure proper error handling in traced functions
- Verify project name matches LangSmith configuration

**3. Performance Impact**
- Monitor trace submission timing
- Consider asynchronous tracing for high-frequency operations
- Optimize metadata payload size
- Use sampling for performance-critical paths

**4. Metadata Not Appearing**
- Verify metadata dictionary structure
- Check for serialization issues with complex objects
- Ensure metadata keys follow LangSmith conventions
- Test with simple metadata first

## 📊 **Integration Benefits**

### **Operational Excellence**
- **Real-time Monitoring**: Instant visibility into system performance
- **Error Detection**: Proactive identification of issues
- **Performance Optimization**: Data-driven optimization opportunities
- **Quality Assurance**: Continuous monitoring of response quality

### **Business Intelligence**
- **User Behavior Analysis**: Understanding query patterns and preferences
- **Financial Analysis Patterns**: Most requested deals and metrics
- **System Utilization**: Peak usage times and resource requirements
- **Success Metrics**: Query resolution rates and user satisfaction

### **Development Acceleration**
- **Debugging Efficiency**: Rapid issue identification and resolution
- **Feature Validation**: A/B testing of new features and algorithms
- **Performance Benchmarking**: Baseline establishment and improvement tracking
- **Quality Gates**: Automated quality checks and alerts

## 🚀 **Advanced Features**

### **Custom Evaluators**
```python
# Financial accuracy evaluator
def evaluate_deal_response(run, example):
    expected_deal = example.outputs["deal_number"]
    actual_response = run.outputs["response"]
    return {"deal_accuracy": expected_deal in actual_response}
```

### **Batch Processing Monitoring**
Track document batch uploads and processing:
- S3 sync operations
- Bulk document indexing
- Batch analysis jobs

### **Multi-Model Comparison**
Compare performance across:
- Amazon Titan variants
- Different embedding models
- Various chunking strategies
- Alternative search algorithms

### **Custom Dashboards**
Create specialized dashboards for:
- Financial deal analysis performance
- Document processing efficiency
- User query patterns
- System health metrics

## 📞 **Support & Resources**

### **Documentation Links**
- [LangSmith Official Docs](https://docs.smith.langchain.com/)
- [Python SDK Reference](https://python.langchain.com/docs/langsmith/)
- [Tracing Guide](https://docs.smith.langchain.com/tracing)

### **Internal Resources**
- Configuration: `src/agents/langsmith_integration.py`
- Environment Setup: `.env` file
- Deployment: Docker configuration includes LangSmith

### **Getting Help**
1. Check application logs for LangSmith initialization
2. Verify environment variables and API connectivity
3. Review trace data in LangSmith UI
4. Consult internal documentation and code comments

---

*This guide covers the comprehensive LangSmith integration providing full observability into the Financial Forecast AI application's performance, user interactions, and system health.*
