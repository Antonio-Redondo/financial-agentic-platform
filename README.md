# 🏦 Financial Forecast AI

> **Advanced Prepayment Analytics & Risk Assessment Platform**  
> *Powered by Amazon Titan Models & RAG Architecture*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![AWS](https://img.shields.io/badge/AWS-Bedrock-orange?style=for-the-badge&logo=amazon-aws)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

</div>

---

## 🆕 Recent Updates (October 2025)

### ✨ Major Enhancements & New Features
- **🔍 Amazon Titan Text Embeddings v2**: Upgraded to `amazon.titan-embed-text-v2:0` with 1024-dimensional vectors for superior semantic search
- **🎯 LangSmith Integration**: Comprehensive observability with auto-tracing, run tracking, and detailed performance monitoring
- **🧠 Conversation Memory**: Bidirectional synchronization between Streamlit UI and LangChain memory for contextual follow-up queries
- **📊 Enhanced Vector Search**: Improved relevance scoring with similarity scores in 0.70-0.80 range for high-quality results
- **🔄 Real-time Tracing**: All operations (vector search, financial queries, Bedrock analysis, LLM responses) traced to LangSmith
- **💭 Context-Aware Queries**: Smart detection of references like "it", "this", "as well" to maintain conversation flow
- **🎨 Modern Chat Interface**: Enhanced Streamlit UI with improved message handling and user experience

### 🔧 Technical Improvements
- **Multi-agent workflow** implemented using LangGraph for advanced orchestration
- **Amazon Bedrock (Titan) LLM** with enhanced callback integration for better tracing
- **PostgreSQL/pgvector** optimized for 1024-dimensional embeddings with debug logging
- **S3 integration** for document ingestion and batch processing
- **Comprehensive error handling** with detailed logging and user feedback
- **Memory persistence** across app restarts with session state synchronization

### 📁 File Structure & Documentation
- Enhanced `langsmith_integration.py` with traceable decorators and auto-tracing
- Improved `financial_agent.py` with contextual query enhancement patterns
- Updated `vector_store.py` with Titan v2 embeddings and enhanced debugging
- Enhanced `app.py` with bidirectional conversation memory synchronization
- See `src/PYEXPLANATION.md` for a visual, up-to-date mapping of all Python files and their responsibilities

### 🛠️ Development Environment
- All `__pycache__` folders and `.pyc` files are safe to delete and are not required for deployment
- Enhanced development workflow with comprehensive logging and tracing capabilities

---

## ✨ Key Features

```
🧠 AI-Powered Analysis     📄 Multi-Format Support     💬 Enhanced Chat Interface
├─ Amazon Titan v2 Models ├─ PDF Documents            ├─ Conversation Memory
├─ RAG Architecture       ├─ Excel Spreadsheets       ├─ Context-Aware Queries
├─ Financial Expertise    ├─ Word Documents           ├─ Smart Follow-ups
└─ Real-time Processing   └─ PowerPoint & More        └─ Modern UI Design

🔍 Vector Search          ⚡ Performance               🛡️ Security & Observability
├─ Titan Embeddings v2    ├─ Sub-second Responses     ├─ AWS IAM Integration
├─ 1024-Dim Vectors       ├─ High Relevance Scores    ├─ LangSmith Tracing
├─ Contextual Retrieval   ├─ Scalable Architecture    ├─ Comprehensive Monitoring
└─ Intelligent Ranking    └─ Local Development        └─ Error Tracking
```

## 📋 Prerequisites

<table>
<tr>
<td width="50%">

**🐍 Development Environment**
- Python 3.11+ 
- Git for version control
- VS Code (recommended)
- Virtual environment support

</td>
<td width="50%">

**☁️ AWS Services**
- AWS Account with Bedrock access
- IAM permissions configured
- Optional: PostgreSQL with pgvector
- AWS CLI configured

</td>
</tr>
</table>

## 🚀 Quick Start Guide

### 1️⃣ **Clone & Setup**

```bash
# Clone the repository
git clone https://github.com/Antonio-Redondo/financial-forecast-ai.git
cd financial-forecast-ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
```

### 2️⃣ **Install Dependencies**

```bash
# Install all required packages
pip install -r requirements.txt

# Additional document processing libraries (auto-installed)
pip install openpyxl xlrd beautifulsoup4 python-pptx markdown
```

### 3️⃣ **Environment Configuration**

Create a `.env` file in the project root:

```env
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# LangSmith Configuration (Optional - for advanced tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=financial-forecast-ai

# Database Configuration (Optional - uses local storage by default)
POSTGRES_CONNECTION=your_postgres_endpoint
PGVECTOR_CONNECTION_STRING=postgresql://user:pass@host:5432/db

# Development Mode (Recommended for local testing)
USE_LOCAL_STORAGE=true
```

### 4️⃣ **Launch Application**

```bash
# Start the Financial Forecast AI
streamlit run src/ui/app.py --server.port 8516

# 🌐 Open in browser: http://localhost:8516
```

## 💻 How to Use

<div align="center">

### 📱 **Modern Chat Interface with Conversation Memory**

</div>

```
┌─────────────────────────────────────────────────────────────────┐
│  💭 Ask Your Financial Question                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 💡 Ask about deal 2025-003 pricing speed...             │   │
│  │                                                         │   │
│  │ 💬 Follow up: "Give me the bond value as well"         │   │
│  │    ↳ 🧠 AI remembers context from previous messages    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  📊 Analyze Trends    ⚠️ Risk Assessment    📋 Summarize Docs   │
│  🔍 LangSmith Traces  💭 Memory Context     🎯 Smart Follow-ups │
└─────────────────────────────────────────────────────────────────┘
```

### 🎯 **Step-by-Step Workflow**

| Step | Action | Description |
|------|--------|-------------|
| **1** | 📁 **Upload Documents** | Drag & drop PDF, Excel, Word, PowerPoint files |
| **2** | 🔄 **Auto-Processing** | AI extracts and indexes content with Titan v2 embeddings |
| **3** | 💬 **Ask Questions** | Use natural language with conversation memory support |
| **4** | 🧠 **AI Analysis** | Amazon Titan models analyze with RAG retrieval & LangSmith tracing |
| **5** | 📊 **View Results** | Get detailed insights with high relevance scores (0.70-0.80) |
| **6** | 🔄 **Follow-up** | Ask contextual questions - AI remembers previous conversation |

### 📄 **Supported Document Formats**

```
📕 PDF Files          📊 Spreadsheets       📝 Text Documents     🌐 Web Formats
├─ Financial Reports  ├─ Excel (.xlsx/.xls) ├─ Word (.docx/.doc)  ├─ HTML/XML
├─ Prospectuses       ├─ CSV Data           ├─ Plain Text (.txt)  ├─ JSON Data
├─ Research Papers    └─ Data Tables        ├─ Rich Text (.rtf)   └─ Markdown
└─ Legal Documents                          └─ Markdown (.md)

📽️ Presentations
├─ PowerPoint (.pptx/.ppt)
└─ Slide Content Extraction
```

## 🔧 AWS Bedrock Configuration

<div align="center">

### 🚀 **3-Step Setup Process**

</div>

```
Step 1: IAM Setup    →    Step 2: Model Access    →    Step 3: Verification
┌─────────────────┐       ┌─────────────────────┐       ┌─────────────────┐
│ 👤 Create User  │  ───► │ 🧠 Request Models   │  ───► │ ✅ Test & Verify │
│ 🔑 Add Policies │       │ 📝 Use Case Form    │       │ 🎯 Ready to Use │
│ 💾 Get Creds    │       │ ⏰ Wait Approval    │       │ 🔄 Start App     │
└─────────────────┘       └─────────────────────┘       └─────────────────┘
```

### 🎯 **Option A: Quick Setup (Recommended)**

1. **Deploy Complete Infrastructure** *(Automated)*
   ```bash
   # Creates VPC, database, IAM permissions - everything needed
   aws cloudformation create-stack \
     --stack-name financial-forecast-complete \
     --template-body file://infra/cloudformation.yaml \
     --capabilities CAPABILITY_IAM \
     --parameters ParameterKey=Environment,ParameterValue=dev \
                  ParameterKey=UserName,ParameterValue=Antonio
   ```

2. **Request Model Access** *(Manual)*
   ```
   🌐 Go to: AWS Console → Bedrock → Model Access
   📍 Region: us-east-1
   🎯 Model: Amazon Titan Text Large
   📝 Use Case: Financial analysis and prepayment forecasting
   ⏰ Wait: ~15 minutes for approval
   ```

### 🛠️ **Option B: Manual Setup**

<details>
<summary><b>🔧 Click to expand manual configuration steps</b></summary>

#### **Step 1: Create IAM Policy**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **Step 2: Attach to User**
```bash
# Create user and attach policy
aws iam create-user --user-name FinancialForecastUser
aws iam attach-user-policy --user-name FinancialForecastUser --policy-arn YOUR_POLICY_ARN
aws iam create-access-key --user-name FinancialForecastUser
```

</details>

### ✅ **Verification Checklist**

| ✓ | Component | Status | Command |
|---|-----------|---------|---------|
| □ | **AWS CLI** | Configured | `aws sts get-caller-identity` |
| □ | **Credentials** | Valid | Check `.env` file |
| □ | **Region** | us-east-1 | `aws configure get region` |
| □ | **Bedrock Models** | Available | `aws bedrock list-foundation-models` |
| □ | **Titan v2 Access** | Enabled | Check amazon.titan-embed-text-v2:0 |
| □ | **LangSmith** | Optional | Set LANGCHAIN_TRACING_V2=true |
| □ | **Permissions** | Working | Launch app and test |

### 🔍 **Troubleshooting Guide**

```
❌ Error: "ResourceNotFoundException"
   └─ Solution: Request model access in Bedrock console

❌ Error: "AccessDenied" 
   └─ Solution: Check IAM permissions and policies

❌ Error: "Invalid credentials"
   └─ Solution: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

❌ Error: "Region not supported"
   └─ Solution: Use us-east-1 region for Bedrock
```

## ☁️ AWS Infrastructure Deployment

<div align="center">

### 🏗️ **Two Deployment Options**

</div>

```
🏠 Local Development              🏭 Full AWS Deployment
┌─────────────────────────┐      ┌─────────────────────────┐
│ ✅ Streamlit Server     │      │ 🚀 Container Platform   │
│ ✅ Local File Storage   │      │ 🗄️ RDS PostgreSQL      │
│ ✅ AWS Bedrock API      │      │ 🔒 VPC Network          │
│ ✅ IAM Permissions      │      │ ⚖️ Load Balancer        │
│ 💰 Low Cost            │      │ 📈 Auto Scaling         │
│ 🚀 Fast Setup          │      │ 🛡️ Production Security  │
└─────────────────────────┘      └─────────────────────────┘
```

### 🚀 **Complete Infrastructure Deployment** *(Production)*

```bash
# 1️⃣ Deploy unified infrastructure (VPC + Database + IAM)
aws cloudformation create-stack \
  --stack-name financial-forecast-complete \
  --template-body file://infra/cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=Environment,ParameterValue=dev \
               ParameterKey=UserName,ParameterValue=Antonio

# 2️⃣ Wait for deployment completion
aws cloudformation wait stack-create-complete \
  --stack-name financial-forecast-complete

# 3️⃣ Get database connection details
aws cloudformation describe-stacks \
  --stack-name financial-forecast-complete \
  --query "Stacks[0].Outputs"
```

### 🏠 **Local Development Mode** *(Current & Recommended)*

```bash
# ✅ Current setup - just run the app locally!
streamlit run src/ui/app.py --server.port 8516

# 🌐 Access: http://localhost:8516
```

<div align="center">

**📝 Infrastructure**: The application uses a **single consolidated CloudFormation template** for all AWS resources.  
**🚀 Development**: Run locally with file-based storage, deploy to AWS for production.

</div>

### 📊 **Deployment Comparison**

| Feature | 🏠 Local Dev | 🏭 AWS Production |
|---------|--------------|-------------------|
| **Setup Time** | ⚡ 5 minutes | ⏰ 30 minutes |
| **Cost** | 💰 $0.02/query | 💰💰 $50+/month |
| **Scalability** | 👤 Single user | 👥 Multi-user |
| **Database** | 📁 Local files | 🗄️ PostgreSQL |
| **Security** | 🔐 Basic | 🛡️ Enterprise |
| **Maintenance** | ✅ None | 🔧 Regular |

### 🔄 **Current Architecture**

```
Local Machine                    AWS Services
┌─────────────────┐             ┌─────────────────┐
│ 🖥️ Streamlit App │ ────────── │ 🧠 Bedrock API  │
│ 📁 File Storage  │             │ 🤖 Titan Models │
│ 🐍 Python Code  │             │ 🔑 IAM Access   │
└─────────────────┘             └─────────────────┘
```

## 🏗️ Project Architecture

### 📂 **Directory Structure**

```
financial-forecast-ai/
├── 📁 src/                          # Source code
│   ├── 🤖 agents/                   # AI Agent System
│   │   ├── financial_agent.py       # Main orchestrator with memory
│   │   ├── analyst.py              # Amazon Titan interface
│   │   ├── vector_store.py         # Titan v2 embeddings (1024-dim)
│   │   └── langsmith_integration.py # Comprehensive tracing & observability
│   ├── 🔧 core/                    # Core business logic  
│   └── 🎨 ui/                      # Enhanced Streamlit interface
│       └── app.py                  # Chat UI with conversation memory
├── 🏗️ infra/                       # AWS Infrastructure
│   ├── cloudformation.yaml        # Complete deployment template
│   └── README.md                  # Infrastructure guide
├── 📋 requirements.txt             # Python dependencies
├── 🔧 .env                        # Environment config (AWS + LangSmith)
├── 🐳 Dockerfile                  # Container setup
└── 📖 README.md                   # This documentation
```

### 🎯 **Component Overview**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🧠 FINANCIAL FORECAST AI SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  🎨 UI Layer              🤖 Agent Layer             ☁️ AWS Services            │
│  ┌─────────────────┐     ┌─────────────────────┐    ┌─────────────────────┐    │
│  │ • Streamlit UI  │────▶│ • Financial Agent   │───▶│ • Amazon Bedrock    │    │
│  │ • Chat Memory   │     │ • AI Analyst        │    │ • Titan v2 Models   │    │
│  │ • File Upload   │     │ • Vector Store      │    │ • PostgreSQL + RDS │    │
│  │ • Visualizations│     │ • RAG Pipeline      │    │ • LangSmith Tracing │    │
│  └─────────────────┘     └─────────────────────┘    └─────────────────────┘    │
│                                     │                           │               │
│                                     ▼                           ▼               │
│                            🔍 Conversation Memory      📊 Comprehensive         │
│                            • Context Preservation      • Auto-tracing          │
│                            • Follow-up Queries         • Performance Monitoring│
│                            • Session Synchronization   • Error Tracking        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 🔄 **Data Flow**

```
📄 Document Upload → 🔍 Processing → 🧠 AI Analysis → 💡 Insights → 🔍 Tracing

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 📁 Files    │───▶│ ✂️ Chunking │───▶│ 🔢 Vectors  │───▶│ 💾 Storage  │
│ Multi-format│    │ Text Split  │    │ Titan v2    │    │ Local/Cloud │
└─────────────┘    └─────────────┘    │ 1024-dim    │    └─────────────┘
                                      └─────────────┘           │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│ 💬 Response │◀───│ 🧠 AI Model │◀───│ 🔍 Retrieval│◀──────────┘
│ + Memory    │    │ Titan Text  │    │ 0.70-0.80   │
└─────────────┘    │ + Tracing   │    │ Similarity  │
                   └─────────────┘    └─────────────┘
                           │                   │
                   ┌─────────────┐    ┌─────────────┐
                   │ 📊 LangSmith│    │ 💭 Context  │
                   │ Monitoring  │    │ Memory      │
                   └─────────────┘    └─────────────┘
```

### 🛠️ **Technology Stack**

<table>
<tr>
<td width="25%"><b>🎨 Frontend</b></td>
<td width="25%"><b>🤖 AI/ML</b></td>
<td width="25%"><b>💾 Data</b></td>
<td width="25%"><b>☁️ Infrastructure</b></td>
</tr>
<tr>
<td>

- Streamlit
- CSS/HTML
- JavaScript
- Responsive UI
- Conversation Memory

</td>
<td>

- AWS Bedrock
- Amazon Titan v2
- LangChain
- LangGraph
- LangSmith

</td>
<td>

- PostgreSQL
- pgvector
- Local Storage
- Vector Search
- 1024-dim Embeddings

</td>
<td>

- AWS VPC
- CloudFormation
- IAM Roles
- Docker Ready
- Observability

</td>
</tr>
</table>

### 🧪 **Testing Enhanced Features**

**🔍 Conversation Memory Test:**
```
1. Ask: "Give me the pricing speed for deal 2025-003"
2. Follow up: "Give me the bond value as well"
   ↳ 🧠 AI should remember the deal context automatically

3. Ask: "What about the settlement date?"
   ↳ 💭 Should continue with deal 2025-003 context
```

**📊 LangSmith Tracing:**
- All operations automatically traced when LANGCHAIN_TRACING_V2=true
- View traces at: https://smith.langchain.com/
- Monitor performance, relevance scores, and conversation flow

**🎯 Vector Search Quality:**
- Similarity scores typically range 0.70-0.80 for relevant documents
- Enhanced with Amazon Titan Text Embeddings v2 (1024 dimensions)
- Debug logging shows relevance scoring in console

---

## 🎯 Key Use Cases

<div align="center">

### 💼 **Financial Analysis Scenarios**

</div>

| 🎯 Use Case | 📄 Input | 🔍 Analysis | 💡 Output |
|-------------|----------|-------------|-----------|
| **Prepayment Risk** | Mortgage pool data | Historical trends + AI modeling | Risk scores & forecasts with 0.70+ relevance |
| **Credit Assessment** | Financial statements | Multi-factor analysis + memory context | Credit ratings & recommendations |
| **Yield Analysis** | Bond prospectuses | Cash flow modeling + Titan v2 embeddings | Expected returns & duration |
| **Market Research** | Industry reports | Competitive analysis + conversation history | Market insights & opportunities |
| **Compliance Check** | Regulatory docs | Rule interpretation + LangSmith tracing | Compliance status & gaps |
| **Investment Decision** | Due diligence files | Comprehensive review + contextual follow-ups | Investment recommendations |

---

## 🤝 Contributing

<div align="center">

**🌟 We welcome contributions to improve Financial Forecast AI!**

</div>

### 🚀 **Development Workflow**

```bash
# 1️⃣ Fork & Clone
git clone https://github.com/yourusername/financial-forecast-ai.git
cd financial-forecast-ai

# 2️⃣ Create Feature Branch
git checkout -b feature/your-feature-name

# 3️⃣ Make Changes & Test
streamlit run src/ui/app.py --server.port 8516

# 4️⃣ Commit & Push
git add .
git commit -m "✨ Add your feature description"
git push origin feature/your-feature-name

# 5️⃣ Create Pull Request
# Visit GitHub and create a PR with description
```

### 📋 **Contribution Areas**

- 🐛 **Bug Fixes**: Improve stability and reliability
- ✨ **Features**: New AI capabilities or UI enhancements
- 📚 **Documentation**: Better guides and examples
- 🔧 **Infrastructure**: AWS deployment improvements
- 🧪 **Testing**: Unit tests and integration tests
- 🎨 **UI/UX**: Enhanced user interface design

---

## 📜 License & Credits

<div align="center">

**📄 License**: MIT License - see [LICENSE](LICENSE) file for details

**🏦 Financial Forecast AI** - *Built with ❤️ for the financial community*

---

<table>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/Powered%20by-Amazon%20Titan-FF9900?style=for-the-badge&logo=amazon-aws" />
</td>
<td align="center">
<img src="https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit" />
</td>
<td align="center">
<img src="https://img.shields.io/badge/Vector%20DB-PostgreSQL-316192?style=for-the-badge&logo=postgresql" />
</td>
</tr>
</table>

**⭐ Star this repo if you find it useful!** | **🐛 Report issues** | **💡 Suggest features**

</div>