# 🏦 Financial Forecast AI - Document Analysis Prompts

This document contains a comprehensive collection of effective prompts for analyzing financial documents using the Financial Forecast AI application. These prompts are optimized for use with Amazon Titan Text models and the document processing capabilities.

## 📊 Document Analysis Prompts

### 🏦 Prepayment Analysis Prompts

#### For Mortgage Pool Documents
```
Analyze the prepayment trends in this mortgage pool data. Focus on seasonal patterns, interest rate sensitivity, and borrower characteristics that influence prepayment speeds.
```

#### For RMBS Prospectuses
```
Extract and analyze the prepayment assumptions from this RMBS prospectus. Identify the baseline CPR rates, stress scenarios, and any credit enhancement features.
```

#### For Historical Performance Data
```
Review the historical prepayment performance in these documents. Calculate the actual vs. projected prepayment speeds and identify any outlier periods.
```

#### For Prepayment Modeling
```
Build a prepayment forecast model using the data in these documents. Consider seasonal factors, burnout effects, and current market conditions.
```

#### For CPR Analysis
```
Calculate the Conditional Prepayment Rate (CPR) from the mortgage data in these documents. Provide monthly CPR trends and identify any acceleration or deceleration patterns.
```

### 📈 Risk Assessment Prompts

#### For Credit Risk Analysis
```
Perform a comprehensive credit risk assessment based on the uploaded financial statements. Focus on debt-to-income ratios, FICO score distributions, and geographic concentration risks.
```

#### For Interest Rate Risk
```
Analyze the interest rate sensitivity of these financial instruments. Calculate duration, convexity, and potential value-at-risk under different rate scenarios.
```

#### For Market Risk
```
Evaluate the market risk factors present in these documents. Identify correlation risks, liquidity concerns, and macroeconomic sensitivity factors.
```

#### For Concentration Risk
```
Assess concentration risks in the portfolio based on geographic distribution, borrower characteristics, and property types mentioned in these documents.
```

#### For Default Risk Analysis
```
Analyze the default risk indicators in these financial documents. Examine delinquency rates, loss severities, and recovery assumptions.
```

### 💰 Cash Flow Analysis Prompts

#### For Bond Analysis
```
Model the cash flow projections from these bond documents. Include principal amortization, interest payments, and any embedded options or call features.
```

#### For Structured Products
```
Analyze the waterfall structure and cash flow distribution priorities in these structured product documents. Identify subordination levels and credit support.
```

#### For Mortgage Cash Flows
```
Project the monthly cash flows from the mortgage pool data, including scheduled principal, prepayments, and interest collections.
```

#### For Yield Analysis
```
Calculate the yield-to-maturity, option-adjusted spread, and other yield metrics based on the pricing and cash flow data in these documents.
```

### 📋 Document Summarization Prompts

#### For Comprehensive Summary
```
Provide a comprehensive executive summary of all uploaded documents. Include key financial metrics, risk factors, investment highlights, and any regulatory considerations.
```

#### For Key Terms Extraction
```
Extract and summarize the key terms section from these offering documents. Focus on coupon rates, maturity dates, call provisions, and credit enhancements.
```

#### For Risk Factor Summary
```
Summarize all risk factors mentioned in these documents. Categorize them by type (credit, market, operational, regulatory) and assess their potential impact.
```

#### For Investment Highlights
```
Extract and summarize the investment highlights and value propositions from these financial documents.
```

### 🎯 Comparative Analysis Prompts

#### For Multiple Documents
```
Compare the risk-return profiles across all uploaded investment documents. Create a ranking based on yield, credit quality, and liquidity characteristics.
```

#### For Benchmark Analysis
```
Compare the performance metrics in these documents against industry benchmarks. Identify areas of outperformance and underperformance.
```

#### For Portfolio Comparison
```
Compare the characteristics of different mortgage pools or securities in the uploaded documents. Highlight key differences in credit quality, geography, and loan characteristics.
```

### 🔍 Specific Data Extraction Prompts

#### For Financial Metrics
```
Extract all financial ratios, yields, and performance metrics from the uploaded documents. Present them in a structured table format with source document references.
```

#### For Regulatory Information
```
Identify all regulatory requirements, compliance measures, and reporting obligations mentioned in these documents.
```

#### For Loan Characteristics
```
Extract loan-level characteristics from the mortgage data including loan-to-value ratios, FICO scores, property types, and geographic distribution.
```

#### For Servicer Information
```
Extract servicer-related information including servicer ratings, replacement triggers, and servicing fees from these documents.
```

### 📊 Modeling and Forecasting Prompts

#### For Scenario Analysis
```
Perform scenario analysis on these financial instruments under different economic conditions: base case, recession, and high inflation scenarios.
```

#### For Stress Testing
```
Conduct stress testing analysis using the data in these documents. Apply severe but plausible scenarios for interest rates, unemployment, and home prices.
```

#### For Sensitivity Analysis
```
Perform sensitivity analysis on key variables affecting the performance of these financial instruments. Focus on interest rate changes and prepayment speed variations.
```

#### For Monte Carlo Analysis
```
If sufficient data is available, outline the parameters needed for Monte Carlo simulation of these financial instruments.
```

### 🎨 Advanced Analysis Prompts

#### For Portfolio Optimization
```
Analyze the portfolio allocation implications of these investments. Consider correlation benefits, concentration limits, and risk-adjusted returns.
```

#### For ESG Analysis
```
Evaluate the ESG (Environmental, Social, Governance) factors and sustainability metrics mentioned in these financial documents.
```

#### For Liquidity Analysis
```
Assess the liquidity characteristics of these financial instruments based on market depth, trading volume, and structural features mentioned in the documents.
```

#### For Credit Enhancement Analysis
```
Analyze the credit enhancement mechanisms (overcollateralization, subordination, insurance) described in these structured finance documents.
```

### 📈 Performance Analysis Prompts

#### For Historical Performance
```
Analyze the historical performance data in these documents. Calculate key performance indicators and identify trends over time.
```

#### For Vintage Analysis
```
Perform vintage analysis on the loan data to identify performance differences across origination periods.
```

#### For Delinquency Analysis
```
Analyze delinquency and default patterns in the historical data. Identify seasonal effects and early warning indicators.
```

### 🔧 Technical Analysis Prompts

#### For Data Quality Assessment
```
Assess the quality and completeness of data in these documents. Identify any gaps, inconsistencies, or data quality issues.
```

#### For Methodology Review
```
Review and summarize the methodologies used for valuation, risk assessment, and performance measurement in these documents.
```

#### For Assumptions Analysis
```
Extract and analyze all key assumptions used in financial models and projections within these documents.
```

## 💡 Best Practices for Prompts

### ✅ Do:
- Be specific about the type of analysis you want
- Mention specific financial metrics or ratios of interest
- Reference document types (prospectus, financial statement, etc.)
- Ask for structured outputs (tables, bullet points, summaries)
- Include time horizons for projections
- Specify risk scenarios or stress tests
- Use financial terminology accurately
- Request source references for extracted data

### ❌ Don't:
- Use vague terms like "analyze everything"
- Ask for information not present in the documents
- Request real-time market data (the AI works with uploaded docs only)
- Expect predictions beyond what data supports
- Ask for investment advice or recommendations
- Use overly complex compound questions
- Request proprietary or confidential calculations without context

## 🔧 Example Workflow Prompts

### Step 1 - Initial Assessment
```
Provide an overview of the document types uploaded and their primary purposes. Identify any missing information needed for complete analysis.
```

### Step 2 - Document Classification
```
Classify each uploaded document by type (prospectus, financial statement, performance report, etc.) and summarize the key information contained in each.
```

### Step 3 - Data Extraction
```
Extract all numerical data, financial metrics, and key terms from the documents. Organize the information in a structured format.
```

### Step 4 - Risk Assessment
```
Assess the key risk factors identified in the analysis. Rank them by potential impact and likelihood based on the information in the documents.
```

### Step 5 - Performance Analysis
```
Analyze the performance metrics and trends identified in the documents. Calculate relevant ratios and identify areas of concern or strength.
```

### Step 6 - Summary and Insights
```
Summarize the key findings and provide actionable insights based on the document analysis. Include any recommendations for further investigation.
```

## 📝 Prompt Templates

### Template for New Document Types
```
Analyze the [DOCUMENT_TYPE] focusing on [SPECIFIC_AREA]. Extract [SPECIFIC_METRICS] and provide insights on [ANALYSIS_FOCUS]. Present results in [FORMAT_PREFERENCE].
```

### Template for Comparative Analysis
```
Compare [METRIC/CHARACTERISTIC] across the uploaded [DOCUMENT_TYPES]. Highlight key differences and similarities, and rank by [RANKING_CRITERIA].
```

### Template for Risk Analysis
```
Evaluate [RISK_TYPE] in these documents. Identify risk factors, quantify where possible, and assess potential impact on [INVESTMENT/PORTFOLIO].
```

## 🎯 Domain-Specific Prompts

### For CMBS Analysis
```
Analyze the commercial mortgage-backed securities data focusing on property types, geographic concentration, and debt service coverage ratios.
```

### For ABS Analysis
```
Examine the asset-backed securities structure including underlying asset characteristics, credit enhancement levels, and payment waterfalls.
```

### For CLO Analysis
```
Analyze the collateralized loan obligation structure focusing on portfolio diversity, manager track record, and coverage tests.
```

### For Municipal Bonds
```
Evaluate the municipal bond documents focusing on credit quality, revenue sources, and covenant protections.
```

---

*This document is designed to help users get the most accurate and useful analysis from the Financial Forecast AI application. These prompts are continuously updated based on user feedback and model improvements.*