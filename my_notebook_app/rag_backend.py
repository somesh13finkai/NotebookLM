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
        user_query = inputs.get("input", "")
        chat_history = inputs.get("chat_history", [])

        # Retrieve Context
        docs = self.retriever.invoke(user_query)
        retrieved_context = "\n\n".join([f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}" for d in docs])
        
        # --- UPDATED PROMPT: STRICT REFUSAL MODE ---
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
            
            1. **COMPLETED FEATURE CHECK:**
               Look at the "PROJECT STATUS" block above. 
               If the user asks for a feature that is marked "✅ COMPLETE" (like Authentication/Auth), you **MUST REFUSE** to draft a plan.
               
               **Output EXACTLY this for completed features:**
               "🚨 **STATUS ALERT:** [Feature Name] is already marked as COMPLETE.
               **Existing Implementation:** [Summarize what exists in the Context]"
               
               (Do NOT generate a "Database Schema" or "API Endpoints" section for completed features).

            2. **NEW FEATURE DRAFTING:**
               Only if the feature is NOT complete, draft the TRD using:
               - Backend: Node.js + Express
               - Database: PostgreSQL
               - Frontend: React + Tailwind
            """)
        ])
        
        chain = drafting_prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "status_context": self.status_content,
            "context": retrieved_context,
            "chat_history": chat_history,
            "query": user_query
        })

@st.cache_resource
def get_rag_chain():
    try:
        llm = ChatOllama(model=LLM_MODEL, temperature=0.0, keep_alive="5m") # Temp 0.0 for maximum strictness
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        if not os.path.exists(VECTOR_STORE_DIR):
             return None
             
        vector_store = FAISS.load_local(
            VECTOR_STORE_DIR, 
            embeddings,
            allow_dangerous_deserialization=True
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 10})

        status_content = "Status Matrix not found."
        if os.path.exists(STATUS_FILE_PATH):
            with open(STATUS_FILE_PATH, "r") as f:
                status_content = f.read()

        return ProjectManagerAgent(llm, retriever, status_content)

    except Exception as e:
        print(f"Error initializing Agent: {e}")
        return None