# 🔬 LangSmith Integration Guide

## Overview
Your Financial Forecast AI application is now integrated with **LangSmith** for comprehensive observability, monitoring, and debugging of AI operations. LangSmith provides detailed insights into:

- 📊 **Query Analytics** - Track all user queries and responses
- 🔍 **Vector Search Performance** - Monitor document retrieval effectiveness  
- 🤖 **LLM Response Quality** - Analyze AI model performance and latency
- 💰 **Financial Query Patterns** - Understand deal-specific analysis usage
- 📄 **Document Processing** - Track chunking and indexing operations
- 💬 **User Feedback** - Collect and analyze user satisfaction ratings

## 🚀 Quick Start

### 1. Verify Configuration
Your `.env` file should contain:
```bash
# LangSmith Configuration for Observability and Monitoring
LANGCHAIN_API_KEY=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
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=financial-forecast-ai-app
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 2. Test Integration
Run the test script to verify everything is working:
```bash
python test_langsmith_integration.py
```

### 3. Start the Application
```bash
streamlit run src/ui/app.py --server.port 8510
```

## 📊 How to Use LangSmith

### **In the Application Dashboard**

1. **Check Connection Status**
   - Look for "🟢 LangSmith API Connected" in the sidebar
   - If you see "🟡 LangSmith API Unavailable (Local Mode)", traces are saved locally

2. **View Real-Time Analytics**
   - Scroll to "🔬 LangSmith Analytics" section in the sidebar
   - Monitor total runs, success rates, and average latency
   - View recent queries and their performance

3. **Access Full Dashboard**
   - Click "🔗 View Full Dashboard" to open LangSmith web interface
   - Analyze detailed traces and performance metrics

### **LangSmith Web Dashboard**

1. **Visit**: https://smith.langchain.com/
2. **Select Project**: `financial-forecast-ai-app`
3. **Explore Features**:
   - 📈 **Traces Tab**: See all operations with detailed timing
   - 📊 **Analytics Tab**: View performance trends and metrics  
   - 🔍 **Search**: Filter by operation type, time range, or metadata
   - 💬 **Feedback**: Review user ratings and comments

## 🔧 Integration Features

### **Automatic Tracing**
Every operation is automatically traced:

- **Financial Queries**: `"Who is the underwriter for deal 2025-001?"`
- **Vector Searches**: Document retrieval with relevance scores
- **LLM Responses**: AI model calls with input/output and latency
- **Document Processing**: PDF chunking and indexing operations
- **User Interactions**: Query patterns and response quality

### **Error Monitoring**  
- All errors are automatically logged to LangSmith
- View error details in the LangSmith dashboard
- Track error frequency and patterns
- Get alerts for critical issues

### **User Feedback Collection**
After each query, users can:
- Rate response quality (1-5 stars)
- Provide detailed comments
- Feedback is automatically linked to the specific trace

## 📈 LangSmith Dashboard Features

### **Traces View**
- **Timeline**: See all operations in chronological order
- **Details**: Click any trace to see inputs, outputs, and metadata
- **Performance**: View latency, token usage, and cost metrics
- **Debugging**: Inspect errors and failed operations

### **Analytics Dashboard**
- **Usage Metrics**: Total runs, success rates, error rates
- **Performance Trends**: Latency and throughput over time
- **User Patterns**: Most common queries and usage peaks
- **Model Performance**: Compare different AI model responses

### **Search and Filtering**
- **Time Range**: Filter by specific dates or time periods
- **Operation Type**: View only queries, searches, or LLM calls
- **Deal Numbers**: Filter by specific financial deals
- **Success/Error**: Show only successful or failed operations

## 🛠 Advanced Usage

### **Custom Metadata**
Every trace includes rich metadata:
```python
langsmith_manager.trace_financial_query(
    query="Underwriter analysis",
    deal_numbers=["2025-001", "2025-003"],
    query_type="underwriter_lookup",
    metadata={
        "user_id": "analyst_001",
        "confidence": 0.95,
        "search_strategy": "enhanced"
    }
)
```

### **Feedback Integration**
```python
langsmith_manager.log_user_feedback(
    query="Risk assessment request",
    response="Detailed risk analysis...",
    rating=5,
    comments="Excellent accuracy and comprehensive analysis",
    run_id="trace_12345"
)
```

## 🎯 Best Practices

1. **Monitor Regularly**: Check the LangSmith dashboard daily for insights
2. **Review Feedback**: Use user ratings to improve response quality
3. **Analyze Patterns**: Identify common queries to optimize performance  
4. **Set Alerts**: Configure LangSmith alerts for critical issues
5. **Track Metrics**: Monitor latency and success rates over time

## 🔄 Fallback Behavior

If LangSmith API is unavailable, the system automatically:
- ✅ Continues normal operation without interruption
- 📁 Saves traces locally in the `traces/` folder
- 📊 Provides local analytics in the dashboard
- 🔄 Switches back to LangSmith when API is restored

## 🚨 Troubleshooting

### **LangSmith Not Enabled**
```
✅ Check LANGCHAIN_API_KEY is set in .env
✅ Verify LANGCHAIN_TRACING_V2=true
✅ Ensure internet connection for API access
```

### **API Connection Failed**  
```
✅ Verify API key is valid and active
✅ Check firewall/proxy settings
✅ Try accessing https://smith.langchain.com manually
```

### **No Traces Appearing**
```
✅ Restart the application after configuring
✅ Check the traces/ folder for local backups
✅ Verify project name matches: financial-forecast-ai-app
```

## 📚 Resources

- **LangSmith Documentation**: https://docs.smith.langchain.com/
- **API Reference**: https://api.python.langchain.com/en/latest/langsmith_api_reference.html
- **Community Support**: https://github.com/langchain-ai/langsmith-sdk

---

**🎉 Your Financial Forecast AI is now fully observable with LangSmith!**

Monitor performance, collect feedback, and optimize your AI operations with comprehensive tracing and analytics.