import os
import json
import streamlit as st
from operator import itemgetter
from dotenv import load_dotenv

# --- LangChain Imports (Updated for Cloud/v0.3) ---
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- STORAGE FIX: These moved in new LangChain versions ---
from langchain.storage import EncoderBackedStore
from langchain_community.storage import LocalFileStore

from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# --- Configuration ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

VECTOR_STORE_DIR = "vector_store"
DOCSTORE_DIR = "docstore_data"
FAISS_INDEX_NAME = "faiss_index"
EMBEDDING_MODEL = "models/text-embedding-004"
LLM_MODEL = "gemini-1.5-flash" 

# --- 1. JSON Serializers (MUST MATCH INGEST.PY EXACTLY) ---
def serialize_document(doc: Document) -> bytes:
    return json.dumps({
        "page_content": doc.page_content,
        "metadata": doc.metadata,
    }).encode("utf-8")

def deserialize_document(data: bytes) -> Document:
    obj = json.loads(data.decode("utf-8"))
    return Document(
        page_content=obj["page_content"],
        metadata=obj["metadata"],
    )

# --- 2. The Wrapper Class ---
# This fixes the "RunnableSequence object has no field" error
class RAGApplication:
    def __init__(self, retrieval_chain, retriever, llm):
        self.chain = retrieval_chain
        self.retriever = retriever
        self.llm = llm

    def invoke(self, input_dict):
        return self.chain.invoke(input_dict)

    def analyze_gaps(self):
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
            
        docs = self.retriever.invoke("project requirements specifications vs implementation details")
        context_text = format_docs(docs)
        
        gap_prompt = f"""
        You are a QA Architect. Analyze the technical context below.
        Task: Identify promises made in 'Overview' vs implementation in 'Technical Details'.
        
        Context:
        {context_text[:12000]} 
        
        Output a bulleted list of "Gaps Detected":
        """
        return self.llm.invoke(gap_prompt).content

@st.cache_resource
def get_rag_chain():
    # 1. Safety Check
    if not os.path.exists(VECTOR_STORE_DIR) or not os.path.exists(DOCSTORE_DIR):
        # We don't return None here immediately to avoid crashing app on first load if empty
        # But generally, ingestion should have happened.
        pass

    # 2. Initialize Embeddings
    if "GOOGLE_API_KEY" not in os.environ:
        st.error("❌ GOOGLE_API_KEY not found. Check your .env (or Secrets on Cloud).")
        return None
        
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    try:
        # 3. Load Vector Store
        vectorstore = FAISS.load_local(
            VECTOR_STORE_DIR, 
            embeddings, 
            index_name=FAISS_INDEX_NAME,
            allow_dangerous_deserialization=True
        )
        
        # 4. Load Doc Store
        fs_store = LocalFileStore(DOCSTORE_DIR)
        store = EncoderBackedStore(
            store=fs_store,
            key_encoder=lambda k: str(k),
            value_serializer=serialize_document,
            value_deserializer=deserialize_document
        )
        
    except Exception as e:
        st.error(f"❌ Failed to load knowledge base: {e}")
        return None

    # 5. Reconstruct Retriever
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )

    # 6. Initialize LLM (Gemini)
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL, 
        temperature=0.3,
        max_output_tokens=2048
    )

    # 7. Define Prompts
    contextualize_q_system_prompt = """Given a chat history and the latest user question 
    which might reference context in the chat history, formulate a standalone question 
    which can be understood without the chat history. Do NOT answer the question, 
    just reformulate it if needed and otherwise return it as is."""

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    qa_system_prompt = """You are a Senior Technical Assistant. 
    Use the following pieces of retrieved context to answer the question.
    
    The context is formatted in Markdown. Pay attention to Headers (#, ##) to understand the topic.
    
    Context:
    {context}
    
    If you don't know the answer, just say that you don't know. 
    Keep the answer technical and concise."""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    # 8. Build the Chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    history_aware_retriever = (
        contextualize_q_prompt 
        | llm 
        | StrOutputParser() 
        | retriever
    )

    # Dictionary input wrapper using itemgetter
    rag_chain_runnable = (
        {
            "context": history_aware_retriever | format_docs, 
            "input": itemgetter("input"), 
            "chat_history": itemgetter("chat_history")
        }
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    # 9. Return the Wrapper
    return RAGApplication(rag_chain_runnable, retriever, llm)