import streamlit as st
import base64
import time
import os
from langchain_core.messages import HumanMessage, AIMessage
from rag_backend import get_rag_chain
from ingest import ingest_documents, DATA_DIR
from export import create_pdf  # <--- Handles PDF Generation

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="My Notebook UI",
    page_icon="📓"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    /* Main body background color and text color */
    body {
        background-color: #1a1c20;
        color: #e0e0e0;
    }

    /* Adjust Streamlit's main content padding */
    .block-container {
        padding-top: 2rem; 
        padding-bottom: 2rem; 
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Make columns expand evenly */
    [data-testid="stColumn"] {
        margin-right: 0.5rem;
    }
    [data-testid="stColumn"]:last-child {
        margin-right: 0;
    }
    
    /* Custom button styling */
    .stButton > button {
        background-color: #33363b;
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        background-color: #44484e;
        border-color: #555;
    }

    /* Deep Research Container */
    .deep-research-container {
        background-color: #2b3a2f;
        border: 1px solid #3c5440;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        color: #90ee90;
        font-size: 0.9em;
    }
    .deep-research-container span {
        color: #90ee90;
    }

    /* Search web container */
    .search-web-container {
        background-color: #2e3035;
        border: 1px solid #3c3e42;
        border-radius: 8px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .search-web-container .stTextInput input {
        background-color: #2e3035;
        border: none;
        color: #e0e0e0;
    }
    
    /* Studio card styling */
    .studio-card {
        background-color: #2e3035;
        border: 1px solid #3c3e42;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        min-height: 120px;
    }
    .studio-card-title {
        font-weight: bold;
        color: #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .studio-card-icon {
        font-size: 1.5em;
        margin-right: 0.5rem;
        color: #aaa;
    }
    .studio-card-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .studio-card-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .studio-card-buttons .stButton > button {
        background-color: #3f4247;
        border: none;
        padding: 0.3rem 0.6rem;
        font-size: 0.8em;
        color: #bbb;
    }
    .studio-card-buttons .stButton > button:hover {
        background-color: #4f5257;
    }
    
    /* Top bar styling */
    .top-bar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 1rem;
        background-color: #1a1c20;
        border-bottom: 1px solid #2e3035;
        margin-bottom: 1rem;
    }
    .top-bar-left, .top-bar-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .top-bar-button {
        background-color: #33363b !important;
        border: 1px solid #444 !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.9em !important;
    }
    .top-bar-icon {
        font-size: 1.5em;
        color: #aaa;
    }

    /* Chat message styling */
    .st-emotion-cache-1c7y2kd {
        background-color: #2e3035;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }

    /* Hiding the deploy button and hamburger menu for cleaner look */
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# --- Top Navigation Bar ---
st.markdown("""
<div class="top-bar-container">
    <div class="top-bar-left">
        <span class="top-bar-icon">◧</span>
        <h6>Untitled notebook</h6>
    </div>
    <div class="top-bar-right">
        <span class="top-bar-icon">⭳</span> 
<button class="top-bar-button">Share</button>
        <span class="top-bar-icon">⚙️</span> 
<button class="top-bar-button">Settings</button>
        <span class="top-bar-icon">👤</span> 
</div>
</div>
""", unsafe_allow_html=True)


# --- Main Three-Column Layout ---
col1, col2, col3 = st.columns([1, 2, 1]) 

# ==========================================
# COLUMN 1: SOURCES (Left 25%)
# ==========================================
with col1: 
    st.subheader("Sources")
    
    # 1. Functional File Uploader (Includes YAML)
    uploaded_files = st.file_uploader(
        "Add new sources (PDF, TXT, MD, JSON, PY, YAML)",
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

    # 2. Re-build Knowledge Base Button
    if st.button("Re-build Knowledge Base", use_container_width=True, type="primary"):
        with st.spinner("Ingesting documents..."):
            try:
                ingest_documents()
                get_rag_chain.clear()
                st.success("Updated!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # 3. Deep Research Static
    st.markdown("""
    <div class="deep-research-container">
        Try Advanced Search for an in-depth report and new sources!
    </div>
    """, unsafe_allow_html=True)
    
    # 4. Dynamic File List
    st.subheader("Current Knowledge Base")
    try:
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.pdf', '.txt', '.md', '.json', '.py', '.yaml', '.yml'))]
            if not files:
                st.markdown("<p style='color: #888; text-align: center;'>No sources found.</p>", unsafe_allow_html=True)
            else:
                for file_name in files:
                    st.markdown(f"📄 `{file_name}`")
        else:
             st.markdown("<p style='color: #888; text-align: center;'>No data folder found.</p>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error listing files: {e}")
    
    # 5. Search Web Static
    st.subheader("Search the web for new sources")
    st.markdown("""
    <div class="search-web-container">
        <label class="st-emotion-cache-nahz7x" for=":ra:">Web</label>
        <select class="st-emotion-cache-nahz7x">
            <option value="Web">Web</option>
        </select>
        <input type="text" placeholder="Search..." class="st-emotion-cache-nahz7x" style="flex: 1; padding: 0.5rem; background-color: #2e3035; border: none; color: #e0e0e0;"/>
        <button class="st-emotion-cache-nahz7x">➔</button>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# COLUMN 2: CHAT (Middle 50%)
# ==========================================
with col2: 
    st.subheader("Chat")

    # Initialize RAG Chain
    try:
        rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"Failed to load RAG chain. Is Ollama running?")
        st.stop()
        
    if rag_chain is None:
        st.info("Knowledge base is empty. Please upload documents on the left and click 'Re-build'.")
    
    # Initialize UI Messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize LangChain Chat History
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- CHAT CONTAINER ---
    with st.container(height=700, border=True):

        # Display Messages & PDF Buttons
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Add Download Button for Assistant responses
                if message["role"] == "assistant":
                    button_key = f"download_{i}"
                    try:
                        # Ensure we use the cleaned text version for PDF
                        pdf_data = create_pdf(message["content"])
                        
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_data,
                            file_name=f"generated_report_{i}.pdf",
                            mime="application/pdf",
                            key=button_key
                        )
                    except Exception as e:
                        # Silent fail for minor errors to avoid UI clutter
                        pass

        # Chat Input
        if prompt := st.chat_input("Draft a PRD or ask a question..."):
            # 1. Display user message immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Generate AI response with History
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        if rag_chain:
                            # Pass input AND history to the backend
                            response = rag_chain.invoke({
                                "input": prompt,
                                "chat_history": st.session_state.chat_history
                            })
                            
                            st.markdown(response)
                            
                            # 3. Update Stores
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                            # Update LangChain memory
                            st.session_state.chat_history.extend([
                                HumanMessage(content=prompt),
                                AIMessage(content=response)
                            ])
                            
                            # Rerun to show the download button
                            st.rerun()
                        else:
                            st.error("Please build the knowledge base first.")
                    except Exception as e:
                        st.error(f"Error: {e}")


# ==========================================
# COLUMN 3: STUDIO (Right 25%)
# ==========================================
with col3: 
    st.subheader("Studio")
    
    st.info("Tools to analyze and transform your documents.")

    # --- Tool 1: Gap Analysis (The New Feature) ---
    with st.expander("🕵️ Gap Analyzer", expanded=True):
        st.markdown("**Role:** Finds missing requirements.")
        
        # This button triggers the backend agent logic
        if st.button("Run Gap Analysis", type="primary", use_container_width=True):
            if rag_chain:
                with st.spinner("🔍 Comparing Specs vs. Code..."):
                    try:
                        # Call the new function in rag_backend.py
                        report = rag_chain.analyze_gaps()
                        
                        # Add the report to chat so user can see/download it
                        st.session_state.messages.append({"role": "assistant", "content": report})
                        st.session_state.chat_history.append(AIMessage(content=report))
                        
                        # Rerun to display the report in the center column
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            else:
                st.error("Please build knowledge base first.")

    # --- Tool 2: PDF Reports ---
    with st.expander("📊 Reports & Export", expanded=False):
        st.markdown("Export current chat to PDF.")
        # 'Clear History' helps reset context for a clean draft
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

    # --- Tool 3: Audio (Placeholder) ---
    with st.expander("🎤 Audio Overview", expanded=False):
        st.markdown("Generate a podcast-style summary.")
        st.button("Generate Audio (Coming Soon)", disabled=True, use_container_width=True)

    # --- Tool 4: Visuals (Placeholder) ---
    with st.expander("🗺️ Architecture Map", expanded=False):
        st.markdown("Visualize data flow.")
        st.button("Generate Diagram (Coming Soon)", disabled=True, use_container_width=True)