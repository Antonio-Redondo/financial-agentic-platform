

# 🐍 Python File Explanations (Visual Table)

This table visually maps each Python file in the `src/` directory and its subfolders to its main responsibility in the Financial Forecast AI Application.

---

| 📁 **File Location**                | 📝 **Description**                                                                                       |
|:------------------------------------|:--------------------------------------------------------------------------------------------------------|
| 🧠 **src/agents/financial_agent.py**   | Main orchestrator for financial analysis. Handles user queries, coordinates multi-agent workflows, and falls back to single-agent logic if needed. |
| 🔄 **src/agents/workflow.py**          | Defines the LangGraph-based multi-agent workflow, including agent classes for document analysis, risk assessment, market analysis, and recommendations. |
| 📊 **src/agents/analyst.py**           | Implements the `FinancialAnalyst` class, which uses Amazon Titan (Bedrock) for advanced financial analysis and LLM-based responses. |
| 🗄️ **src/agents/vector_store.py**      | Manages document storage and retrieval. Handles both in-memory (development) and PostgreSQL/pgvector (production) storage for document embeddings and metadata. |
| 📦 **src/agents/document_manager.py**  | Manages document ingestion, indexing, and summary reporting. Handles both local and database-backed document management. |
| 🚀 **src/agents/app_initialization.py**| Service for initializing the application, including S3 document loading and knowledge base setup at startup. |
| ☁️ **src/agents/s3_loader.py**         | Handles loading documents from AWS S3 buckets for ingestion into the knowledge base. |
| 📦 **src/agents/__init__.py**          | Marks the folder as a Python package. |
| 💬 **src/ui/app.py**                   | Streamlit UI for the application. Provides the chat interface, document upload, and visualization of results. |
| 📦 **src/ui/__init__.py**              | Marks the folder as a Python package. |
| 📦 **src/__init__.py**                 | Marks the folder as a Python package. |

---

**Legend:**
- 🧠 Core backend logic, multi-agent orchestration, and document management
- 💬 User interface and visualization
- 📦 Python package marker files
- ☁️ S3 integration
- 🚀 App initialization
- 🗄️ Vector storage
- 🔄 Workflow logic
- 📊 Financial analysis

All files are designed to work together in a modular, clean-architecture style.
