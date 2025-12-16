import sys
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Configuration ---
VECTOR_STORE_DIR = "vector_store/faiss_index"
LLM_MODEL = "llama3.2:3b"
# UPDATED MODEL: Switched from 'nomic-embed-text'
EMBEDDING_MODEL = "mxbai-embed-large" 
#
# Make sure you have pulled this model! Run in your terminal:
# ollama pull mxbai-embed-large
#

def get_rag_chain():
    """
    Initializes and returns a RAG (Retrieval-Augmented Generation) chain.
    """
    try:
        # 1. Load the LLM
        # This connects to your local Ollama server
        llm = ChatOllama(model=LLM_MODEL, temperature=0.3)
        
        # 2. Load the Vector Store
        # This loads the FAISS index from your local disk
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_store = FAISS.load_local(
            VECTOR_STORE_DIR, 
            embeddings,
            allow_dangerous_deserialization=True # Required by FAISS
        )
        retriever = vector_store.as_retriever()
        
        # 3. Create the Prompt Template
        template = """
        You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know.
        Use three sentences maximum and keep the answer concise.

        Question: {question}

        Context: {context}

        Answer:
        """
        prompt = ChatPromptTemplate.from_template(template)

        # 4. Create the RAG Chain
        # This chain pipes together all the steps
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain

    except FileNotFoundError:
        print(f"Error: Vector store not found at '{VECTOR_STORE_DIR}'")
        print("Please run 'python3 ingest.py' first to create the vector store.")
        return None
    except Exception as e:
        print(f"Error initializing RAG chain: {e}")
        print("\n--- Troubleshooting ---")
        print("1. Is Ollama running? (Run `ollama serve` in your terminal if not)")
        print(f"2. Did you pull the models? (Run `ollama pull {LLM_MODEL}` and `ollama pull {EMBEDDING_MODEL}`)")
        print("3. Did you run `ingest.py`? (The folder 'vector_store/faiss_index' must exist and contain a FAISS index)")
        print("-----------------------")
        return None

def main():
    """
    Main function to run the CLI chat client.
    """
    print("\n--- Local RAG CLI ---")
    print("Loading RAG chain...")
    
    rag_chain = get_rag_chain()
    
    if rag_chain is None:
        sys.exit(1) # Exit if chain failed to load

    print(f"Ready! Using LLM: '{LLM_MODEL}' and Vector Store: '{VECTOR_STORE_DIR}'")
    print("Type 'exit' or 'quit' to end.\n")

    while True:
        try:
            # 1. Get user input
            query = input("Ask a question about your documents:\n> ")

            if query.lower() in ['exit', 'quit']:
                print("Exiting...")
                break
            
            if not query.strip():
                continue

            # 2. Invoke the RAG chain
            print("\nThinking...")
            response = rag_chain.invoke(query)
            
            # 3. Print the response
            print(f"\nAnswer:\n{response}\n")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()