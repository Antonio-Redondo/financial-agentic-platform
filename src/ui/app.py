import streamlit as st
import pandas as pd
import sys
import os
from dotenv import load_dotenv
import numpy as np
from datetime import datetime
import time

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.agents.financial_agent import FinancialAgent

load_dotenv()

# Enhanced page configuration
st.set_page_config(
    page_title="Financial Forecast AI | Prepayment Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
def load_custom_css():
    st.markdown("""
    <style>
    /* Main theme and background */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Metrics cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6;
    }
    
    .user-message {
        background-color: #eff6ff;
        border-left-color: #3b82f6;
    }
    
    .assistant-message {
        background-color: #f0fdf4;
        border-left-color: #10b981;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
    
    /* Upload area styling */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8fafc;
        margin-bottom: 1rem;
    }
    
    /* Analysis results styling */
    .analysis-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-success {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    .status-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: none;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def create_header():
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Financial Forecast AI</h1>
        <p>Advanced Prepayment Analytics & Risk Assessment Platform</p>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_dashboard():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Documents Processed",
            value=len(st.session_state.get("processed_docs", [])),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🤖 AI Model",
            value="Amazon Titan Text",
            delta="Reliable & Fast"
        )
    
    with col3:
        st.metric(
            label="💬 Messages",
            value=len(st.session_state.get("messages", [])),
            delta=None
        )
    
    with col4:
        st.metric(
            label="🎯 Status",
            value="Ready",
            delta=None
        )

def create_sidebar():
    with st.sidebar:
        st.markdown("### 📁 Document Management")
        
        # Upload section with better styling
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "📄 Upload Financial Documents",
            accept_multiple_files=True,
            type=["pdf", "docx", "doc", "txt", "rtf", "csv", "xlsx", "xls", "pptx", "ppt", "html", "htm", "xml", "json", "md"],
            help="Supported formats: PDF, Word (DOCX/DOC), Excel (XLSX/XLS), PowerPoint (PPTX/PPT), Text (TXT/RTF/MD), Web (HTML/XML), Data (CSV/JSON). Multiple files supported."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.markdown("#### 📋 Uploaded Files")
            for i, file in enumerate(uploaded_files):
                file_size = len(file.getvalue()) / 1024  # KB
                file_extension = file.name.split('.')[-1].upper()
                
                # Choose icon based on file type
                if file_extension in ['PDF']:
                    icon = "📕"
                elif file_extension in ['DOCX', 'DOC']:
                    icon = "📘"
                elif file_extension in ['XLSX', 'XLS', 'CSV']:
                    icon = "📊"
                elif file_extension in ['PPTX', 'PPT']:
                    icon = "📽️"
                elif file_extension in ['TXT', 'MD', 'RTF']:
                    icon = "📝"
                elif file_extension in ['HTML', 'HTM', 'XML']:
                    icon = "🌐"
                elif file_extension in ['JSON']:
                    icon = "📋"
                else:
                    icon = "📄"
                
                st.markdown(f"""
                <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 5px; margin: 0.25rem 0;">
                    {icon} {file.name}<br>
                    <small style="color: #6b7280;">Type: {file_extension} | Size: {file_size:.1f} KB</small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Process Documents", type="primary"):
                process_documents(uploaded_files)
        
        # Show processed documents status
        if st.session_state.get("processed_docs"):
            st.markdown("#### 📊 Processed Documents")
            for doc in st.session_state.processed_docs:
                icon = "✅" if doc.get("indexed", False) else "⚠️"
                chunks = doc.get("chunks_created", 0)
                file_ext = doc['name'].split('.')[-1].upper()
                
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 0.5rem; border-radius: 5px; margin: 0.25rem 0; border-left: 3px solid {'#10b981' if doc.get('indexed') else '#f59e0b'};">
                    {icon} {doc['name']}<br>
                    <small style="color: #6b7280;">
                        Type: {file_ext} | 
                        {'Indexed: ' + str(chunks) + ' chunks' if doc.get('indexed') else 'Not indexed'} | 
                        Size: {doc['size'] / 1024:.1f} KB | 
                        Content: {len(doc.get('content', '')):.0f} chars
                    </small>
                </div>
                """, unsafe_allow_html=True)
            
            # Add document search test
            if st.button("🔍 Test Document Search", help="Test if documents are searchable"):
                if st.session_state.agent and st.session_state.agent.vector_store:
                    try:
                        stats = st.session_state.agent.get_document_stats()
                        st.success(f"📊 Document Stats: {stats['total_chunks']} chunks from {stats['unique_documents']} documents in {stats['storage_type']} storage")
                        
                        # Show all documents info for debugging
                        if hasattr(st.session_state.agent.vector_store, 'get_all_documents_info'):
                            all_docs = st.session_state.agent.vector_store.get_all_documents_info()
                            if all_docs:
                                with st.expander("📋 All Stored Documents (Debug Info)"):
                                    for i, doc_info in enumerate(all_docs, 1):
                                        st.text(f"Document {i}:")
                                        st.text(f"  Filename: {doc_info.get('filename', 'unknown')}")
                                        st.text(f"  Content Length: {doc_info.get('content_length', 0)} chars")
                                        st.text(f"  Preview: {doc_info.get('content_preview', 'No preview')}")
                                        st.text("---")
                        
                        # Test search with user input
                        test_query = st.text_input("🔍 Test search query:", value="financial", help="Enter a word to search for in your documents")
                        if st.button("Search Documents"):
                            test_results = st.session_state.agent.vector_store.search_documents(test_query, k=5)
                            if test_results:
                                st.success(f"🔍 Search Test: Found {len(test_results)} relevant chunks for '{test_query}'")
                                with st.expander("Preview search results"):
                                    for i, result in enumerate(test_results, 1):
                                        st.text(f"Result {i} (Relevance: {result.get('relevance_score', 0):.2f}):")
                                        st.text(f"Source: {result.get('metadata', {}).get('filename', 'unknown')}")
                                        st.text(f"Content: {result.get('content', '')[:300]}...")
                                        st.text("---")
                            else:
                                st.warning(f"🔍 Search Test: No results found for '{test_query}' - documents may not contain this content")
                        
                    except Exception as e:
                        st.error(f"❌ Error testing document search: {str(e)}")
                else:
                    st.error("❌ Vector store not available")
        
        st.markdown("---")
        
        # Analysis options
        st.markdown("### ⚙️ Analysis Settings")
        
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Comprehensive", "Prepayment Focus", "Risk Assessment", "Market Analysis"],
            help="Choose the type of analysis to perform"
        )
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Minimum confidence level for predictions"
        )
        
        st.markdown("---")
        
        # Analysis info
        st.markdown("### ℹ️ Session Info")
        st.info("� Chat history is automatically saved and will persist throughout your session.")

def process_documents(uploaded_files):
    """Process uploaded documents and save to vector database"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Get the vector store from the agent
    vector_store = st.session_state.agent.vector_store if st.session_state.agent else None
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Processing {file.name}...")
        
        # Read file content based on file type
        try:
            content = ""
            file_extension = file.name.split('.')[-1].lower()
            
            if file.type == "application/pdf" or file_extension == "pdf":
                # PDF processing with pypdf
                try:
                    import pypdf
                    import io
                    
                    pdf_reader = pypdf.PdfReader(io.BytesIO(file.getvalue()))
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
                    
                    if not content.strip():
                        content = "PDF content could not be extracted (possibly scanned document)"
                except Exception as e:
                    content = f"Error processing PDF: {str(e)}"
                    
            elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"] or file_extension == "docx":
                # DOCX files
                try:
                    from docx import Document
                    import io
                    
                    doc = Document(io.BytesIO(file.getvalue()))
                    for paragraph in doc.paragraphs:
                        content += paragraph.text + "\n"
                    
                    # Also extract text from tables
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                content += cell.text + " "
                            content += "\n"
                    
                    if not content.strip():
                        content = "DOCX content could not be extracted"
                except Exception as e:
                    content = f"Error processing DOCX: {str(e)}"
                    
            elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"] or file_extension in ["xlsx", "xls"]:
                # Excel files
                try:
                    import pandas as pd
                    import io
                    
                    # Read all sheets
                    df_dict = pd.read_excel(io.BytesIO(file.getvalue()), sheet_name=None)
                    for sheet_name, df in df_dict.items():
                        content += f"Sheet: {sheet_name}\n"
                        content += df.to_string(index=False) + "\n\n"
                        
                except Exception as e:
                    content = f"Error processing Excel file: {str(e)}"
                    
            elif file.type in ["application/vnd.openxmlformats-officedocument.presentationml.presentation"] or file_extension in ["pptx", "ppt"]:
                # PowerPoint files
                try:
                    from pptx import Presentation
                    import io
                    
                    prs = Presentation(io.BytesIO(file.getvalue()))
                    for slide_num, slide in enumerate(prs.slides, 1):
                        content += f"Slide {slide_num}:\n"
                        for shape in slide.shapes:
                            if hasattr(shape, "text"):
                                content += shape.text + "\n"
                        content += "\n"
                        
                except Exception as e:
                    content = f"Error processing PowerPoint file: {str(e)}"
                    
            elif file.type == "text/csv" or file_extension == "csv":
                # CSV files
                try:
                    import pandas as pd
                    import io
                    
                    df = pd.read_csv(io.BytesIO(file.getvalue()))
                    content = f"CSV Data ({len(df)} rows):\n"
                    content += df.to_string(index=False)
                    
                except Exception as e:
                    content = f"Error processing CSV: {str(e)}"
                    
            elif file.type == "application/json" or file_extension == "json":
                # JSON files
                try:
                    import json
                    
                    json_data = json.loads(file.getvalue().decode('utf-8'))
                    content = "JSON Content:\n" + json.dumps(json_data, indent=2)
                    
                except Exception as e:
                    content = f"Error processing JSON: {str(e)}"
                    
            elif file.type in ["text/html", "application/xml"] or file_extension in ["html", "htm", "xml"]:
                # HTML/XML files
                try:
                    from bs4 import BeautifulSoup
                    
                    html_content = file.getvalue().decode('utf-8')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    content = soup.get_text()
                    
                except Exception as e:
                    content = f"Error processing HTML/XML: {str(e)}"
                    
            elif file_extension == "md":
                # Markdown files
                try:
                    import markdown
                    
                    md_content = file.getvalue().decode('utf-8')
                    html = markdown.markdown(md_content)
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    content = soup.get_text()
                    
                except Exception as e:
                    content = f"Error processing Markdown: {str(e)}"
                    
            elif file_extension == "rtf":
                # RTF files (basic extraction)
                try:
                    rtf_content = file.getvalue().decode('utf-8', errors='ignore')
                    # Basic RTF text extraction (removes most RTF codes)
                    import re
                    content = re.sub(r'\\[a-z]+\d*\s?', ' ', rtf_content)
                    content = re.sub(r'[{}]', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                except Exception as e:
                    content = f"Error processing RTF: {str(e)}"
                    
            else:
                # Default: treat as text file
                try:
                    content = file.getvalue().decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = file.getvalue().decode('latin-1')
                    except Exception as e:
                        content = f"Could not decode file content: {str(e)}"
            
            # Create metadata for the document
            file_extension = file.name.split('.')[-1].lower()
            metadata = {
                "filename": file.name,
                "file_type": file.type,
                "file_extension": file_extension,
                "size": len(file.getvalue()),
                "uploaded_at": datetime.now().isoformat(),
                "source": "user_upload",
                "content_length": len(content)
            }
            
            # Index document into vector store (chunks automatically)
            if vector_store:
                status_text.text(f"Indexing {file.name} into vector database...")
                vector_store.index_document(content, metadata)
                status_msg = f"✅ {file.name} indexed into vector database"
            else:
                status_msg = f"⚠️ {file.name} processed but vector store unavailable"
            
            # Add to processed documents session state (with summary)
            if "processed_docs" not in st.session_state:
                st.session_state.processed_docs = []
            
            st.session_state.processed_docs.append({
                "name": file.name,
                "size": len(file.getvalue()),
                "processed_at": datetime.now(),
                "content": content[:500] + "..." if len(content) > 500 else content,
                "indexed": vector_store is not None,
                "chunks_created": len(vector_store.text_splitter.split_text(content)) if vector_store else 0
            })
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            st.success(status_msg)
            
        except Exception as e:
            error_msg = f"❌ Error processing {file.name}: {str(e)}"
            st.error(error_msg)
            print(error_msg)
    
    status_text.text("✅ All documents processed and indexed successfully!")
    time.sleep(2)
    status_text.empty()
    progress_bar.empty()

def create_chat_interface():
    """Enhanced chat interface with input at top"""
    st.markdown("### 💬 AI Financial Analyst")
    
    # Create a container for the input that stays at the top
    input_container = st.container()
    
    with input_container:
        st.markdown("#### ✍️ Ask Your Question")
        # Chat input at the top - always visible
        prompt = st.chat_input("Type your question here...", key="chat_input_top")
    
    # Separator
    st.markdown("---")
    
    # Process input immediately if provided
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Process the query and get response
        try:
            with st.spinner("� Analyzing your query..."):
                # Get response from agent
                response = st.session_state.agent.process_query(prompt)
                
                # Format response with additional insights
                formatted_response = f"""**Analysis Complete** ✅
                
{response.get("output", "No response generated")}

---
*Analysis completed at {datetime.now().strftime("%H:%M:%S")} with {response.get("confidence", 0.9):.0%} confidence*"""
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                
                # Show additional visualizations if data is present
                if "data" in response and response["data"]:
                    create_data_visualization(response["data"])
                    
        except Exception as e:
            error_response = f"❌ I encountered an error while processing your request: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_response})
        
        # Rerun to show the new messages
        st.rerun()
    
    # Show conversation history below the input
    if st.session_state.messages:
        st.markdown("#### 🔄 Latest Conversation")
        
        # Show the last user message and AI response pair
        messages_to_show = st.session_state.messages[-2:] if len(st.session_state.messages) >= 2 else st.session_state.messages[-1:]
        
        for message in messages_to_show:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        st.markdown("---")
        
        # Show full conversation history in an expander
        if len(st.session_state.messages) > 2:
            with st.expander(f"📜 Full Conversation History ({len(st.session_state.messages)} messages)", expanded=False):
                for message in st.session_state.messages[:-2]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
    else:
        st.info("👋 Welcome! Ask me anything about financial analysis and prepayment forecasting.")


def create_data_visualization(data):
    """Create visualizations for analysis data using Streamlit built-in charts"""
    if isinstance(data, dict) and data:
        st.markdown("### 📊 Analysis Results")
        
        # Display the actual data provided by the AI model
        if "chart_data" in data:
            st.markdown("#### 📈 Analysis Chart")
            chart_df = pd.DataFrame(data["chart_data"])
            st.line_chart(chart_df)
        
        if "metrics" in data:
            st.markdown("#### 📋 Key Metrics")
            metrics_df = pd.DataFrame(data["metrics"])
            st.table(metrics_df)
        
        if "summary" in data:
            st.markdown("#### 📄 Summary")
            st.write(data["summary"])
    
    elif isinstance(data, list) and data:
        st.markdown("### 📊 Analysis Results")
        st.markdown("#### 📋 Analysis Data")
        df = pd.DataFrame(data)
        st.table(df)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = FinancialAgent()
            print("✅ FinancialAgent initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            st.session_state.agent = None
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = []
    if "conversation_count" not in st.session_state:
        st.session_state.conversation_count = 0

def main():
    """Main application function"""
    load_custom_css()
    initialize_session_state()
    
    # Create header
    create_header()
    
    # Create metrics dashboard
    create_metrics_dashboard()
    
    # Create main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        create_chat_interface()
    
    with col2:
        create_sidebar()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 1rem;">
        <small>🏦 Financial Forecast AI | Powered by Amazon Titan | Built with Streamlit</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()