Local RAG Backend Setup Guide

This guide explains how to set up and run the local RAG (Retrieval-Augmented Generation) pipeline.

Step 1: Install Ollama (Local LLM Server)

This is the "server wrapper" for your local LLaMA models.

Go to ollama.com and download the application for your OS (macOS,
Windows, or Linux).

Install it. After installation, Ollama runs as a background service.

Step 2: Download the LLMs

You need two models: one for "chat" (generation) and one for "embeddings" (retrieval).

Open your terminal and run:

# 1. Pull the main chat model (a light, powerful 3B model)
ollama pull llama3.2:3b

# 2. Pull the embedding model (specialized for RAG)
ollama pull nomic-embed-text


Step 3: Install Python Libraries

Install all the required Python packages from your requirements.txt file.

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install libraries
pip install -r requirements.txt


Step 4: Add Your Documents

Place one or more PDF files you want to "chat" with into the /data folder.

my_notebook_app/
└── data/
    └── my_project_brief.pdf
    └── another_report.pdf


Step 5: Run the Ingestion Script

This script reads your documents, creates embeddings, and saves them to the local vector store. You only need to run this once (or again if you add/change documents).

python ingest.py


Expected Output:
You will see progress bars and a final message:
Successfully saved vector store to 'vector_store/faiss_index'

Step 6: Test the RAG Flow (Run the CLI)

Now you can run the CLI tool to chat with your documents.

python query.py


Expected Output:
The script will load the models and then prompt you for a question.

--- Local RAG CLI ---
Loading RAG chain...
Ready! Using LLM: 'llama3.2:3b' and Vector Store: 'vector_store/faiss_index'
Type 'exit' or 'quit' to end.

Ask a question about your documents:
>


Next Steps

You now have a fully functional backend RAG pipeline. The next logical step would be to take the logic from query.py and integrate it into your src/core/chat_logic.py file so your Streamlit UI (from app.py and src/components/) can call it.