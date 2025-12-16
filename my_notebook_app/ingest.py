import os
import sys
import shutil
import pickle
import json
from dotenv import load_dotenv

# --- LangChain Imports ---
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.storage import LocalFileStore, EncoderBackedStore
from langchain.retrievers import ParentDocumentRetriever
from langchain_core.documents import Document

# --- Notion Import ---
from notion_client import Client as NotionClient

# --- Configuration ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

DATA_DIR = "data"
VECTOR_STORE_DIR = "vector_store"
DOCSTORE_DIR = "docstore_data"
FAISS_INDEX_NAME = "faiss_index"
EMBEDDING_MODEL = "models/text-embedding-004"

# --- 1. Serializers (Must match Backend) ---
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

# --- 2. Local Document Loading ---
def load_local_documents(data_dir):
    print(f"📂 Scanning '{data_dir}' for local files...")
    documents = []
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        return documents

    try:
        txt_loader = DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader)
        documents.extend(txt_loader.load())
    except Exception: pass

    try:
        pdf_loader = DirectoryLoader(data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
        documents.extend(pdf_loader.load())
    except Exception: pass
        
    return documents

# --- 3. Notion Logic (The "Greedy" Update) ---
def extract_text_from_block(block):
    """
    Extracts text from almost any block type (Paragraph, Code, Quote, etc).
    """
    block_type = block.get("type")
    content = ""
    
    # 1. Standard Text Blocks (Paragraphs, Headings, Lists, Toggles, Quotes, Callouts)
    if block_type in [
        "paragraph", "heading_1", "heading_2", "heading_3", 
        "bulleted_list_item", "numbered_list_item", "to_do", 
        "toggle", "quote", "callout"
    ]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        text = "".join([t.get("plain_text", "") for t in rich_text])
        if text:
            content = text + "\n"

    # 2. Code Blocks (Crucial for your use case)
    elif block_type == "code":
        rich_text = block.get("code", {}).get("rich_text", [])
        code = "".join([t.get("plain_text", "") for t in rich_text])
        if code:
            content = f"\n```\n{code}\n```\n"

    return content

def fetch_page_content(client, page_id):
    """Recursively fetches blocks from a page to build text content."""
    content_parts = []
    has_more = True
    start_cursor = None

    while has_more:
        try:
            response = client.blocks.children.list(block_id=page_id, start_cursor=start_cursor)
            blocks = response.get("results", [])
            
            for block in blocks:
                text = extract_text_from_block(block)
                if text:
                    content_parts.append(text)
            
            has_more = response.get("has_more")
            start_cursor = response.get("next_cursor")
        except Exception as e:
            print(f"   ⚠️ Error fetching blocks for page {page_id}: {e}")
            has_more = False
        
    return "\n".join(content_parts)

def load_notion_documents():
    token = os.getenv("NOTION_TOKEN")
    root_page_id = os.getenv("NOTION_PAGE_ID")

    if not token or not root_page_id:
        print("⚠️ Skipped Notion: Missing credentials in .env")
        return []

    print(f"🔍 Scanning Notion from Root ID: {root_page_id}...")
    client = NotionClient(auth=token)
    docs = []
    
    # Queue: [ID, Title]
    pages_to_visit = [(root_page_id, "Root Page")]
    visited_pages = set()

    while pages_to_visit:
        current_id, current_title = pages_to_visit.pop(0)
        
        if current_id in visited_pages: continue
        visited_pages.add(current_id)

        try:
            # A. Fetch Page Title
            page_obj = client.pages.retrieve(page_id=current_id)
            title = current_title
            props = page_obj.get("properties", {})
            for p in props.values():
                if p["type"] == "title" and p.get("title"):
                    title = "".join([t.get("plain_text", "") for t in p.get("title")])
            
            print(f"   -> Processing: {title}")

            # B. Fetch ALL Content (including Code Blocks now)
            page_text = fetch_page_content(client, current_id)
            
            if page_text.strip():
                docs.append(Document(page_content=page_text, metadata={"source": title, "type": "notion"}))

            # C. Find Child Pages (Recursion)
            has_more = True
            cursor = None
            while has_more:
                children = client.blocks.children.list(block_id=current_id, start_cursor=cursor)
                for block in children["results"]:
                    if block["type"] == "child_page":
                        child_id = block["id"]
                        child_title = block.get("child_page", {}).get("title", "Untitled")
                        pages_to_visit.append((child_id, child_title))
                has_more = children.get("has_more")
                cursor = children.get("next_cursor")

        except Exception as e:
            print(f"   ❌ Error processing page {current_id}: {e}")

    print(f"✅ Loaded {len(docs)} Notion pages.")
    return docs

# --- 4. Main Ingestion Logic ---
def ingest_documents():
    local_docs = load_local_documents(DATA_DIR)
    notion_docs = load_notion_documents()
    all_docs = local_docs + notion_docs
    
    if not all_docs:
        print("❌ No documents found.")
        return

    print(f"📦 Total Documents: {len(all_docs)}")

    if "GOOGLE_API_KEY" not in os.environ:
        print("❌ Error: GOOGLE_API_KEY missing.")
        return
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # Clean previous store
    if os.path.exists(DOCSTORE_DIR):
        shutil.rmtree(DOCSTORE_DIR)
    os.makedirs(DOCSTORE_DIR)

    fs_store = LocalFileStore(DOCSTORE_DIR)
    store = EncoderBackedStore(
        store=fs_store,
        key_encoder=lambda k: str(k),
        value_serializer=serialize_document,
        value_deserializer=deserialize_document,
    )

    vectorstore = FAISS.from_texts(["init"], embeddings)
    
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=RecursiveCharacterTextSplitter(chunk_size=400),
        parent_splitter=RecursiveCharacterTextSplitter(chunk_size=2000),
    )

    print("⏳ Processing documents...")
    try:
        retriever.add_documents(all_docs, ids=None)
        vectorstore.save_local(VECTOR_STORE_DIR, FAISS_INDEX_NAME)
        print("✅ Ingestion Complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ingest_documents()