import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json
from backend.embedder import get_total_indexed_docs, get_all_repos, search_opensearch

st.set_page_config(page_title="MCPverse", layout="wide")

# Load all data at once if not already loaded in session state
if "all_repos" not in st.session_state:
    st.session_state.all_repos = get_all_repos(size=200)  # Load all repos once into session state

# Initialize session state for loaded_repos if not already initialized
if "loaded_repos" not in st.session_state:
    st.session_state.loaded_repos = st.session_state.all_repos[:10]  # Initially load first 10 repos

# Initialize session state for offset if not already initialized
if "offset" not in st.session_state:
    st.session_state.offset = 10  # Start from the next batch

# Load repositories based on offset (for "Load more" functionality)
repos_per_page = 10
repos = st.session_state.loaded_repos

# ---------- CSS Styling ----------
st.markdown("""
    <style>
        .repo-container {
            background: #f0f8ff;
            border-radius: 12px;
            border: 1px solid #c3dafe;
            padding: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        }
        .repo-card {
            margin-bottom: 0.5rem;
        }
        .chip {
            display: inline-block;
            background-color: #bbdefb;
            color: #0d47a1;
            padding: 4px 10px;
            margin: 4px 6px 0 0;
            border-radius: 20px;
            font-size: 0.8em;
        }
        a {
            text-decoration: none;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Title & Search ----------
total = get_total_indexed_docs()
st.title(f"🔍 MCPverse — Discover MCP Servers ({total} indexed)")

# Input for search
search = st.text_input("Search repositories...")

# Filtered results based on search (use cached repos)
filtered = search_opensearch(search) if search else repos

# ---------- Display Cards in Two Columns ----------
cols = st.columns(2)  # Create two columns for layout
for i, repo in enumerate(filtered):
    col = cols[i % 2]  # Alternate between the two columns
    with col:
        # Render Repo Card
        st.markdown(f"""
            <div class="repo-container">
                <div class="repo-card">
                    <h4>🔹 <a href="{repo['url']}" target="_blank">{repo['name']}</a></h4>
                    <p>{repo.get("description", "No description")}</p>
                    <p>{" ".join([f"<span class='chip'>{t}</span>" for t in repo.get("topics", [])])}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Client config section (if available)
        if repo.get("client_config"):
            with st.expander("⚙️ Client config", expanded=False):
                st.code(json.dumps(repo["client_config"], indent=2), language="json")
        else:
            with st.expander("Client config not available", expanded=False):
                st.write("No client config available.")

# Check if there's more data to load and show the "Load more" button accordingly
if st.session_state.offset < len(st.session_state.all_repos):
    load_more_button = st.button("Load more...")

    # If "Load more" is clicked, load the next batch of repos and append it to the existing list
    if load_more_button:
        new_repos = st.session_state.all_repos[st.session_state.offset: st.session_state.offset + repos_per_page]
        st.session_state.loaded_repos.extend(new_repos)  # Add new repos to the loaded list
        st.session_state.offset += repos_per_page  # Increase offset for the next batch
        # Refresh the page to reflect the new data
        st.rerun()
