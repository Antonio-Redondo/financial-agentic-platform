# Optimized Prompts for Financial Deal Analysis

## Overview
This document provides carefully crafted prompts designed to extract accurate and comprehensive information from financial deal documents (2025-001, 2025-003, 2025-004, etc.) stored in the vector database. These prompts are optimized for the AI Financial Analyst's search and analysis capabilities.

## 🎯 **Deal-Specific Identification Prompts**

### **Basic Deal Information**
```
"Show me the key details for deal 2025-001 including issuer, deal size, and pricing date"
"What is the CUSIP number and settlement date for deal 2025-003?"
"Extract the underwriter information and pricing speed for deal 2025-004" - Good
"List all tranches and their characteristics for deal 2025-001"

give me the underwriter for deal 2025-002 - Good
```

### **Pricing and Speed Analysis**
```
"What is the exact pricing speed for deal 2025-003 and how does it compare to market standards?"
"Give me the pricing speed for deal 2025-004 with underwriter Bank of America - show the specific percentage"
"Compare the pricing speeds across deals 2025-001, 2025-003, and 2025-004"
"Extract the final pricing terms and any speed adjustments for deal 2025-001"
```

## 📊 **Data-Driven Analysis Prompts**

### **Collateral Pool Analysis**
```
"Analyze the collateral pools for deal 2025-003: agency type, mortgage characteristics, WAC, age, and face amount" - Very good
"What are the geographic concentrations in deal 2025-004's collateral pools?"
"Compare collateral quality metrics between deals 2025-001 and 2025-003"
"Extract the pool factor and prepayment history for deal 2025-004's underlying assets" - Good 
```

### **Tranche Structure Deep Dive**
```
"Show detailed tranche structure for deal 2025-001 including CUSIP, coupon rates, and credit enhancement levels"
"Which tranches in deal 2025-003 have the highest prepayment risk and why?"
"Extract the subordination levels and credit support for each tranche in deal 2025-004"
"Compare the senior/subordinate structure across deals 2025-001, 2025-003, and 2025-004" very good
```

### **Financial Metrics Extraction**
```
"Extract all key financial metrics for deal 2025-003: WAC, WAM, original balance, current balance"
"What are the yield and duration characteristics for deal 2025-004's Class A tranches?"`- Good
"Show me the credit enhancement percentages and overcollateralization ratios for deal 2025-001"
"Extract the pool statistics: loan count, average loan size, and FICO scores for deal 2025-003"
```

## 🔍 **Risk Assessment Prompts**

### **Credit Risk Analysis**
```
"Provide a comprehensive credit risk assessment for deal 2025-004 based on borrower profiles and loan characteristics" - Good
"What are the key credit risk factors in deal 2025-003's collateral pool?" - Good
"Analyze the geographic and property type concentrations that could impact deal 2025-001"
"Extract delinquency rates and loss projections for deal 2025-004" - Good
give me the underwriter for deal 2025-001 - Good
```

### **Prepayment Risk Evaluation**
```
"Forecast prepayment speeds (CPR/PSA) for deal 2025-003 and explain the methodology"
"What factors in deal 2025-004 could lead to faster or slower prepayments?"
"Compare the prepayment protection features across deals 2025-001, 2025-003, and 2025-004"
"Extract historical prepayment data and projections for deal 2025-001's underlying pools"
```

### **Market Risk Factors**
```
"How do current interest rate conditions affect deal 2025-004's performance outlook?"
"Analyze the impact of housing market trends on deal 2025-003's collateral value"
"What macroeconomic factors pose the greatest risk to deal 2025-001?"
"Extract duration and convexity measures for deal 2025-004's tranches"
```

## 💡 **Investment Analysis Prompts**

### **Performance Projections**
```
"Based on deal 2025-003's structure and market conditions, project expected returns for the next 12 months"
"What are the key performance indicators to monitor for deal 2025-004?"
"Extract yield-to-maturity and total return projections for deal 2025-001's senior tranches"
"Compare the risk-adjusted returns across deals 2025-001, 2025-003, and 2025-004"
```

### **Recommendation Prompts**
```
"Based on deal 2025-004's characteristics, provide investment recommendations for different risk profiles"
"Which tranches in deal 2025-003 offer the best risk-reward ratio and why?"
"Extract the key strengths and weaknesses of deal 2025-001 for portfolio consideration"
"Recommend optimal holding periods for different tranches in deal 2025-004"
```

## 🔧 **Comparative Analysis Prompts**

### **Cross-Deal Comparisons**
```
"Compare the overall credit quality between deals 2025-001, 2025-003, and 2025-004"
"Which deal among 2025-001, 2025-003, and 2025-004 has the most attractive pricing?"
"Extract and compare the structural features across all three deals"
"Rank deals 2025-001, 2025-003, and 2025-004 by credit enhancement levels"
```

### **Market Positioning**
```
"How does deal 2025-003 compare to similar transactions in the current market?"
"Extract deal 2025-004's competitive advantages relative to recent issuances"
"What makes deal 2025-001 unique compared to other FNMA transactions?"
```

## 📋 **Document Verification Prompts**

### **Data Completeness Checks**
```
"Assess the completeness of documentation for deal 2025-003 - identify any missing data points"
"Extract the data quality indicators and reliability metrics for deal 2025-004"
"What additional information would be needed for a complete analysis of deal 2025-001?"
"Verify that all required disclosures are present in deal 2025-003's documentation"
```

### **Regulatory Compliance**
```
"Extract regulatory compliance information and ratings for deal 2025-004"
"What are the reporting requirements and frequency for deal 2025-003?"
"Identify any regulatory changes that could impact deal 2025-001's performance"
```

## 🎯 **Prompt Optimization Tips**

### **Best Practices for Accurate Results:**

1. **Be Specific with Deal Numbers**
   - Always include the exact deal identifier (e.g., "2025-003", not just "2025")
   - Use consistent formatting for deal references

2. **Request Specific Data Points**
   - Ask for exact figures, percentages, and dates
   - Request specific document sections or exhibits when relevant

3. **Use Financial Terminology**
   - Include industry-standard terms (WAC, WAM, CUSIP, PSA, CPR)
   - Reference specific tranche classes when analyzing structures

4. **Context for Comparisons**
   - When comparing deals, specify the comparison criteria
   - Request ranking or prioritization when analyzing multiple options

5. **Time-Sensitive Queries**
   - Include relevant time periods for projections
   - Specify current market conditions when asking for analysis

### **Query Structure for Best Results:**
```
"For deal [DEAL_NUMBER], extract [SPECIFIC_DATA] from [DOCUMENT_SECTION/TYPE] and [ACTION_REQUESTED]"

Example:
"For deal 2025-004, extract the pricing speed and underwriter details from the term sheet and compare to market standards"
```

### **Multi-Part Analysis Prompts:**
```
"Analyze deal 2025-003 in three parts:
1. Extract key structural features and credit enhancement
2. Assess prepayment and credit risks
3. Provide investment recommendations with specific rationale"
```

## 📊 **Expected Data Points by Deal**

### **Deal 2025-001:**
- Focus on: FNMA structure, traditional features, standard credit enhancement
- Key metrics: WAC, WAM, pool factor, geographic distribution
- Risk factors: Standard mortgage credit risk, prepayment variability

### **Deal 2025-003:**
- Focus on: Wells Fargo underwriting, specific structural features
- Key metrics: Enhanced credit support, unique tranche characteristics
- Risk factors: Concentrated exposures, market timing considerations

### **Deal 2025-004:**
- Focus on: Bank of America underwriting, pricing speed advantages
- Key metrics: Competitive pricing, optimized structure
- Risk factors: Market conditions impact, interest rate sensitivity

## 🚀 **Advanced Analysis Prompts**

### **Scenario Analysis**
```
"For deal 2025-004, model performance under three scenarios: base case, stress, and optimistic market conditions"
"Extract sensitivity analysis for deal 2025-003 showing impact of ±2% interest rate changes"
"What are the break-even points for different tranches in deal 2025-001?"
```

### **Portfolio Integration**
```
"How would adding deal 2025-003 to a portfolio impact overall duration and credit risk?"
"Extract correlation analysis between deal 2025-004 and existing portfolio holdings"
"What diversification benefits does deal 2025-001 provide?"
```

These optimized prompts are designed to work with the AI Financial Analyst's sophisticated search and analysis capabilities, ensuring users receive accurate, comprehensive, and actionable insights from their financial deal documentation.