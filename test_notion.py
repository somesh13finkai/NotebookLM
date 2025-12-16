import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_connection():
    token = os.getenv("NOTION_TOKEN")
    page_id = os.getenv("ROOT_PAGE_ID")

    print("--- 🕵️ Notion Connection Test ---")
    
    # Check 1: Are keys present?
    if not token:
        print("❌ Error: NOTION_TOKEN is missing from .env")
        return
    if not page_id:
        print("❌ Error: ROOT_PAGE_ID is missing from .env")
        return

    print(f"🔑 Token found: ...{token[-5:]}")
    print(f"📄 Page ID: {page_id}")

    # Check 2: specific API call
    client = Client(auth=token)

    try:
        print("\n📡 Attempting to contact Notion API...")
        response = client.pages.retrieve(page_id)
        
        # Success!
        title_prop = response["properties"]["title"]["title"]
        page_title = title_prop[0]["plain_text"] if title_prop else "Untitled"
        
        print(f"✅ SUCCESS! Connected to page: '{page_title}'")
        print("Your integration is working perfectly.")

    except Exception as e:
        # Failure Analysis
        error_msg = str(e)
        print("\n❌ CONNECTION FAILED")
        
        if "404" in error_msg:
            print("👉 Cause: Page not found or Access Denied.")
            print("   Fix: Go to the page in Notion -> Click '...' -> 'Connect to' -> Select your bot.")
        elif "401" in error_msg:
            print("👉 Cause: Invalid Token.")
            print("   Fix: Check your NOTION_TOKEN in .env. It should start with 'secret_'.")
        else:
            print(f"👉 Error details: {error_msg}")

if __name__ == "__main__":
    test_connection()