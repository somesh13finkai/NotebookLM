import streamlit as st
import base64

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="My Notebook UI",  # CHANGED
    page_icon="📓"
)

# --- Custom CSS for better visual fidelity ---
st.markdown("""
    <style>
    /* Main body background color and text color */
    body {
        background-color: #1a1c20; /* Darker background */
        color: #e0e0e0; /* Light gray text */
    }

    /* Adjust Streamlit's main content padding to be more compact */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Make columns expand evenly */
    [data-testid="stColumn"] {
        flex: 1 !important;
        margin-right: 0.5rem; /* Small gap between columns */
    }
    [data-testid="stColumn"]:last-child {
        margin-right: 0;
    }
    
    /* Custom button styling for "Add sources" and "Upload a source" */
    .stButton > button {
        background-color: #33363b; /* Darker button background */
        color: #e0e0e0; /* Light text */
        border: 1px solid #444; /* Subtle border */
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        background-color: #44484e; /* Slightly lighter on hover */
        border-color: #555;
    }

    /* Style for the "Try Deep Research" button/container */
    .deep-research-container {
        background-color: #2b3a2f; /* Dark green background */
        border: 1px solid #3c5440; /* Darker green border */
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        color: #90ee90; /* Light green text */
        font-size: 0.9em;
    }
    .deep-research-container span {
        color: #90ee90; /* Ensure span text is also light green */
    }

    /* Style for the "Search the web" container */
    .search-web-container {
        background-color: #2e3035; /* Dark gray */
        border: 1px solid #3c3e42;
        border-radius: 8px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Input field styling inside search web container */
    .search-web-container .stTextInput input {
        background-color: #2e3035;
        border: none;
        color: #e0e0e0;
    }
    .search-web-container .stSelectbox [data-testid="stSelectboxSingleValue"] {
        background-color: #2e3035;
        border: none;
        color: #e0e0e0;
    }
    .search-web-container .stSelectbox [data-testid="stSelectboxContainer"] {
        background-color: #2e3035;
        border: 1px solid #444;
        border-radius: 8px;
    }

    /* Studio card styling */
    .studio-card {
        background-color: #2e3035; /* Dark gray */
        border: 1px solid #3c3e42;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        min-height: 120px; /* Ensure consistent height for visual balance */
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
        background-color: #1a1c20; /* Same as body to blend in */
        border-bottom: 1px solid #2e3035;
        margin-bottom: 1rem;
    }
    .top-bar-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .top-bar-right {
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
    .top-bar-button:hover {
        background-color: #44484e !important;
    }
    .top-bar-icon {
        font-size: 1.5em;
        color: #aaa;
    }

    /* Style for the central upload area */
    .upload-area-center {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: calc(100vh - 200px); /* Adjust based on header/footer */
        text-align: center;
        color: #aaa;
        background-color: #2e3035;
        border: 2px dashed #444;
        border-radius: 12px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        padding: 2rem;
    }
    .upload-area-center .stButton > button {
        background-color: #33363b;
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        margin-top: 1rem;
    }
    .upload-area-center .stButton > button:hover {
        background-color: #44484e;
    }
    .upload-icon {
        font-size: 3em;
        margin-bottom: 1rem;
        color: #666;
    }
    
    /* Footer-like input bar */
    .bottom-input-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1a1c20;
        padding: 0.5rem 1rem;
        border-top: 1px solid #2e3035;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        z-index: 1000;
    }
    .bottom-input-bar .stTextInput > div > div > input {
        background-color: #2e3035;
        border: 1px solid #444;
        border-radius: 20px;
        color: #e0e0e0;
        padding: 0.5rem 1rem;
    }
    .bottom-input-bar .stTextInput > div > div {
        flex: 1; /* Allow input to take available space */
    }
    .bottom-input-bar .stButton > button {
        background: none;
        border: none;
        color: #888;
        font-size: 1.5em;
        padding: 0.2rem;
    }
    .bottom-input-bar .stButton > button:hover {
        color: #e0e0e0;
        background: none;
    }
    
    /* Saved sources bottom area */
    .saved-sources-bottom {
        text-align: center;
        margin-top: 1rem;
        color: #aaa;
        font-size: 0.8em;
    }
    .saved-sources-bottom .stFileUploader {
        margin-top: 0.5rem;
    }

    /* Small font size for captions */
    .st-emotion-cache-nahz7x p { /* Targeting p tags in captions */
        font-size: 0.85em;
        color: #aaa;
    }
    .st-emotion-cache-nahz7x h6 { /* Targeting h6 for smaller headers */
        font-size: 1.0em;
        color: #e0e0e0;
    }

    /* General text color adjustments for default Streamlit components */
    .stMarkdown, .stText, .stAlert, .stLabel {
        color: #e0e0e0;
    }
    
    /* Ensure Streamlit containers with borders respect padding */
    .st-emotion-cache-fofvrt { /* Target the container with border */
        padding: 1rem;
    }
    
    /* Adjusting the size and alignment of the header "Untitled notebook" */
    h1.st-emotion-cache-nahz7x {
        font-size: 1.8em;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        color: #e0e0e0;
    }
    
    /* Adjusting the top margin of the columns to align with the main content below the header */
    .st-emotion-cache-zq5w6s { /* Target the div that wraps st.columns */
        margin-top: 0;
    }

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
col1, col2, col3 = st.columns([1, 2, 1]) # Adjust ratios if needed

with col1: # Left Column: Sources
    st.subheader("Sources")
    
    # Add sources button
    st.button("➕ Add sources", use_container_width=True)
    
    # Try Advanced Search container (CHANGED)
    st.markdown("""
    <div class="deep-research-container">
        Try Advanced Search for an in-depth report and new sources!
    </div>
    """, unsafe_allow_html=True)
    
    # Search the web for new sources
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
    
    # Saved sources will appear here
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #aaa; font-size: 0.85em;">
        <span style="font-size: 3em;">⑃</span><br>
        Saved sources will appear here<br>
        Click Add source above to add PDFs, websites,<br>
        text, videos, or audio files. Or import a file directly<br>
        from Google Drive.
    </div>
    """, unsafe_allow_html=True)


with col2: # Middle Column: Chat / Main Content
    st.subheader("Chat") # Using subheader to match visual size
    
    # Central upload area
    st.markdown("""
    <div class="upload-area-center">
        <span class="upload-icon">⬆️</span>
        <p>Add a source to get started</p>
        <button>Upload a source</button>
    </div>
    """, unsafe_allow_html=True)
    
    # Bottom input bar for the middle column
    st.markdown("""
    <div class="bottom-input-bar">
        <span style="font-size:1.5em; color:#888;">📎</span>
        <input type="text" placeholder="Upload a source to get started" style="flex: 1; padding: 0.5rem 1rem; background-color: #2e3035; border: 1px solid #444; border-radius: 20px; color: #e0e0e0;">
        <span style="font-size:1.5em; color:#888;">💬</span>
        <span style="font-size:1.5em; color:#888;">➡️</span>
    </div>
    """, unsafe_allow_html=True)
    
    # REMOVED the disclaimer text that was here
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem; color: #aaa; font-size: 0.75em; padding-bottom: 2rem;">
        &nbsp;
    </div>
    """, unsafe_allow_html=True)



with col3: # Right Column: Studio
    st.subheader("Studio")
    
    # Top text
    st.markdown("""
    <p style="font-size: 0.8em; color: #aaa;">Studio output will be saved here.<br>After adding sources, click to add Audio Overview,<br>Study Guide, Mind Map, and more!</p>
    """, unsafe_allow_html=True)
    
    # Audio Overview Card
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">🎤</span>
            <div>
                <div class="studio-card-title">Audio Overview</div>
                <p style="font-size: 0.7em; color: #888;">Create an Audio Overview in: हिन्दी, বাংলা, ગુજરાતી, తెలుగు, മലയാളം, मराठी, ಕನ್ನಡ, ଓଡ଼ିଆ, ਪੰਜਾਬੀ, English</p>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Video Overview Card
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">🎥</span>
            <div>
                <div class="studio-card-title">Video Overview</div>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mind Map Card (CHANGED ICON)
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">🗺️</span>
            <div>
                <div class="studio-card-title">Mind Map</div>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reports Card
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">📊</span>
            <div>
                <div class="studio-card-title">Reports</div>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Flashcards Card
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">📇</span>
            <div>
                <div class="studio-card-title">Flashcards</div>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quiz Card
    st.markdown("""
    <div class="studio-card">
        <div class="studio-card-content">
            <span class="studio-card-icon">❓</span>
            <div>
                <div class="studio-card-title">Quiz</div>
            </div>
        </div>
        <div class="studio-card-buttons">
            <button>⚲</button>
            <button>✎</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add Note button at the very bottom of the Studio column
    st.button("Add note", use_container_width=True, type="primary")