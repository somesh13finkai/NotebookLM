import streamlit as st
import time
import os
from dotenv import load_dotenv # Ensure .env is loaded
from langchain_core.messages import HumanMessage, AIMessage
from rag_backend import get_rag_chain
from ingest import ingest_documents, DATA_DIR
from export import create_pdf 




st.markdown(
    """
    <style>
    /* Limit chat input width to center (chat) column */
    div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 0.75rem;
        left: 30%;
        right: 30%;
        z-index: 999;
        background-color: var(--background-color);
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
    }

    /* Prevent overlap with last messages */
    .block-container {
        padding-bottom: 6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)






# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="My Notebook UI",
    page_icon="📓"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    body { background-color: #1a1c20; color: #e0e0e0; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton > button { background-color: #33363b; color: #e0e0e0; border: 1px solid #444; border-radius: 8px; }
    .stButton > button:hover { background-color: #44484e; border-color: #555; }
    
    /* Notion Status Badge */
    .notion-badge {
        padding: 0.5rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .notion-active { background-color: #2b3a2f; border: 1px solid #3c5440; color: #90ee90; }
    .notion-inactive { background-color: #3a2b2b; border: 1px solid #543c3c; color: #ee9090; }

    /* Chat message styling */
    .st-emotion-cache-1c7y2kd { background-color: #2e3035; border-radius: 8px; }
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Top Bar ---
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 1rem; background-color:#1a1c20; border-bottom:1px solid #2e3035; margin-bottom:1rem;">
    <div style="display:flex; gap:1rem; align-items:center;">
        <span style="font-size:1.5em; color:#aaa;">◧</span>
        <h6 style="margin:0; color:#e0e0e0;">Untitled notebook</h6>
    </div>
    <div style="display:flex; gap:1rem;">
        <button style="background:#333; color:#ccc; border:1px solid #444; padding:0.3rem 0.8rem; border-radius:4px;">Share</button>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1]) 

# ==========================================
# COLUMN 1: SOURCES
# ==========================================
with col1: 
    st.subheader("Sources")
    
    # --- 1. Notion Status Indicator (NEW) ---
    notion_token = os.getenv("NOTION_TOKEN")
    root_page_id = os.getenv("ROOT_PAGE_ID")
    
    if notion_token and root_page_id:
        st.markdown(f"""
        <div class="notion-badge notion-active">
            <span>✅</span> 
            <div>
                <strong>Notion Connected</strong><br>
                <span style="font-size:0.8em; opacity:0.8;">Page ID: ...{root_page_id[-6:]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="notion-badge notion-inactive">
            <span>⚠️</span> 
            <div>
                <strong>Notion Disconnected</strong><br>
                <span style="font-size:0.8em; opacity:0.8;">Check .env for keys</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 2. File Uploader ---
    uploaded_files = st.file_uploader(
        "Add local files",
        type=["pdf", "txt", "md", "json", "py", "yaml", "yml"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        saved_files = []
        os.makedirs(DATA_DIR, exist_ok=True) 
        for file in uploaded_files:
            file_path = os.path.join(DATA_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            saved_files.append(file.name)
        if saved_files:
            st.toast(f"Saved {len(saved_files)} files.")

    # --- 3. Re-build Button ---
    if st.button("Re-build Knowledge Base", use_container_width=True, type="primary"):
        with st.spinner("Ingesting Notion & Local Docs..."):
            try:
                ingest_documents()
                get_rag_chain.clear() # Clear cache to force reload
                st.success("Knowledge Base Updated!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

    

# ==========================================
# COLUMN 2: CHAT
# ==========================================
with col2: 
    st.subheader("Chat")

    # Initialize RAG Chain
    try:
        rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()
        
    if rag_chain is None:
        st.info("⚠️ Knowledge base is empty. Please upload docs or connect Notion.")
    
    # Initialize State
    if "messages" not in st.session_state: st.session_state.messages = []
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    # Chat Container
    with st.container(height=700, border=True):
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    # PDF Download Logic
                    try:
                        pdf_data = create_pdf(message["content"])
                        st.download_button("📄 Download PDF", pdf_data, f"report_{i}.pdf", "application/pdf", key=f"dl_{i}")
                    except: pass

        if prompt := st.chat_input("Ask about your project docs..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing Knowledge Base..."):
                    if rag_chain:
                        response = rag_chain.invoke({
                            "input": prompt,
                            "chat_history": st.session_state.chat_history
                        })
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.session_state.chat_history.extend([HumanMessage(content=prompt), AIMessage(content=response)])
                        st.rerun()
                    else:
                        st.error("Please build the knowledge base first.")

# ==========================================
# COLUMN 3: STUDIO
# ==========================================
with col3: 
    st.subheader("Studio")
    
    with st.expander("🕵️ Gap Analyzer", expanded=True):
        st.markdown("Compare code vs. docs.")
        if st.button("Run Gap Analysis", type="primary", use_container_width=True):
            if rag_chain and hasattr(rag_chain, 'analyze_gaps'):
                with st.spinner("Analyzing..."):
                    report = rag_chain.analyze_gaps()
                    st.session_state.messages.append({"role": "assistant", "content": report})
                    st.session_state.chat_history.append(AIMessage(content=report))
                    st.rerun()
            else:
                st.error("Gap Analysis not available.")

    with st.expander("📊 Utils", expanded=False):
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()