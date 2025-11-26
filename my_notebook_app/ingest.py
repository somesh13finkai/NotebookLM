import os
import sys
import time
from langchain_community.document_loaders import (
    PyPDFLoader, 
    DirectoryLoader, 
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# --- Configuration ---
DATA_DIR = "data"
VECTOR_STORE_DIR = "vector_store/faiss_index"
EMBEDDING_MODEL = "mxbai-embed-large" 

def load_all_documents(data_dir):
    """
    Loads all supported documents (PDF, TXT, MD, JSON, PY, YAML) from the data directory.
    """
    print("Loading documents...")
    
    # Loader for PDFs
    pdf_loader = DirectoryLoader(
        data_dir, 
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader,
        show_progress=True,
        use_multithreading=True
    )
    
    # Loader for TXT, MD, PY, JSON files
    # We use TextLoader for all these code/text formats
    text_loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )
    
    md_loader = DirectoryLoader(
        data_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )

    json_loader = DirectoryLoader(
        data_dir,
        glob="**/*.json",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )
    
    py_loader = DirectoryLoader(
        data_dir,
        glob="**/*.py",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )

    # UPDATED: YAML Loaders
    yaml_loader = DirectoryLoader(
        data_dir,
        glob="**/*.yaml",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )
    
    yml_loader = DirectoryLoader(
        data_dir,
        glob="**/*.yml",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )

    # Load all documents
    docs = []
    # Add the new loaders to the list
    for loader in [pdf_loader, text_loader, md_loader, json_loader, py_loader, yaml_loader, yml_loader]:
        try:
            loaded_docs = loader.load()
            if loaded_docs:
                docs.extend(loaded_docs)
                print(f"Loaded {len(loaded_docs)} files from {loader}")
        except Exception as e:
            print(f"Error with loader {loader}: {e}")
    
    return docs

def ingest_documents():
    """
    Ingests documents from the DATA_DIR, splits them,
    creates embeddings, and saves them to a FAISS vector store.
    """
    print("Starting document ingestion...")
    
    # 1. Load documents
    try:
        documents = load_all_documents(DATA_DIR)
        if not documents:
            print(f"No supported documents found in '{DATA_DIR}' directory.")
            return
        
        print(f"Total loaded pages/files: {len(documents)}")

    except Exception as e:
        print(f"Error loading documents: {e}")
        return

    # 2. Split documents into chunks
    # Large chunk size (2000) to keep API specs and Code context intact
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, 
        chunk_overlap=300,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    if not chunks:
        print("Error splitting documents into chunks.")
        return
        
    print(f"Split documents into {len(chunks)} chunks.")

    # 3. Create embeddings and save to FAISS (IN BATCHES)
    print("Creating embeddings and saving to FAISS vector store...")
    
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        batch_size = 64
        
        print(f"Processing first batch (1 to {min(batch_size, len(chunks))})...")
        if not chunks:
            print("No chunks to process.")
            return

        db = FAISS.from_documents(chunks[:batch_size], embeddings)
        
        for i in range(batch_size, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            print(f"Processing batch ({i+1} to {min(i + batch_size, len(chunks))})...")
            db.add_documents(batch)
            time.sleep(0.5) 
            
        # 4. Save the vector store
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        db.save_local(VECTOR_STORE_DIR)
        print(f"Successfully saved vector store to '{VECTOR_STORE_DIR}'")

    except Exception as e:
        print(f"Error during embedding or saving vector store: {e}")
        print(f"Please ensure Ollama is running and you have pulled the '{EMBEDDING_MODEL}' model.")

if __name__ == "__main__":
    ingest_documents()