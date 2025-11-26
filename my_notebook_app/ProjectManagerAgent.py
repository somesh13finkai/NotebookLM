import streamlit as st
import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# --- Configuration ---
VECTOR_STORE_DIR = "vector_store/faiss_index"
LLM_MODEL = "llama3.1:8b" 
EMBEDDING_MODEL = "mxbai-embed-large"
STATUS_FILE_PATH = "data/06_project_status_matrix.md"

class ProjectManagerAgent:
    def __init__(self, llm, retriever, status_content):
        self.llm = llm
        self.retriever = retriever
        self.status_content = status_content

    def invoke(self, inputs):
        # ... (Your existing invoke method for Drafting - Keep this as is) ...
        user_query = inputs.get("input", "")
        chat_history = inputs.get("chat_history", [])
        
        docs = self.retriever.invoke(user_query)
        retrieved_context = "\n\n".join([f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}" for d in docs])
        
        drafting_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are the Technical Lead. You prevent redundant work.

            === PROJECT STATUS (SOURCE OF TRUTH) ===
            {status_context}
            ========================================

            RETRIEVED CONTEXT:
            {context}
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """
            {query}
            
            ---
            🛑 **STRICT INSTRUCTIONS:**
            1. **COMPLETED FEATURE CHECK:** If "✅ COMPLETE", REFUSE to draft.
            2. **NEW FEATURE DRAFTING:** Draft using Node/React/Postgres.
            """)
        ])
        chain = drafting_prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "status_context": self.status_content,
            "context": retrieved_context,
            "chat_history": chat_history,
            "query": user_query
        })

    # --- NEW: GAP ANALYSIS FUNCTION ---
    def analyze_gaps(self):
        """
        Scans the codebase/specs to find missing implementation details.
        """
        # We retrieve broad context about architecture and requirements
        docs = self.retriever.invoke("System Architecture Requirements vs Implementation Status")
        context_text = "\n\n".join([f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}" for d in docs])
        
        gap_prompt = ChatPromptTemplate.from_template("""
        You are a QA Architect and "Gap Analysis" Agent.
        
        YOUR TASK: 
        Compare the "Requirements" (Architecture/Specs) against the "Implementation Status" (Matrix/Code) in the context below.
        
        CONTEXT:
        {context}
        
        PROJECT STATUS:
        {status}
        
        OUTPUT REPORT FORMAT:
        1. **🔴 Critical Gaps:** (Features defined in specs but marked 'PENDING' or missing in code)
        2. **⚠️ Inconsistencies:** (e.g., Spec says 'UUID' but code implies 'Integer', or 'Auth' is done but 'User Profile' is missing)
        3. **✅ Alignment:** (Major modules that match perfectly)
        
        Be specific. Cite the files where you found the info.
        """)
        
        chain = gap_prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "context": context_text,
            "status": self.status_content
        })

@st.cache_resource
def get_rag_chain():
    # ... (Keep existing initialization logic) ...
    try:
        llm = ChatOllama(model=LLM_MODEL, temperature=0.0, keep_alive="5m") 
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        if not os.path.exists(VECTOR_STORE_DIR):
             return None
             
        vector_store = FAISS.load_local(
            VECTOR_STORE_DIR, 
            embeddings,
            allow_dangerous_deserialization=True
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 15}) # Increased k for deeper analysis

        status_content = "Status Matrix not found."
        if os.path.exists(STATUS_FILE_PATH):
            with open(STATUS_FILE_PATH, "r") as f:
                status_content = f.read()

        return ProjectManagerAgent(llm, retriever, status_content)

    except Exception as e:
        print(f"Error initializing Agent: {e}")
        return None