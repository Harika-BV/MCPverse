import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json, os
from backend.embedder import search_opensearch, get_total_indexed_docs, get_all_repos

st.set_page_config(page_title="MCPverse", layout="wide")

def load_data():
    return get_all_repos(size=200)  # or any number you prefer

repos = load_data()
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
search = st.text_input("Search repositories...")

# ---------- Filtered Results ----------
# filtered = [r for r in repos if search.lower() in r["name"].lower() or search.lower() in r.get("description", "").lower()]
filtered = search_opensearch(search)

# ---------- Display Cards ----------
for i in range(0, len(filtered), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j < len(filtered):
            repo = filtered[i + j]

            toggle_key = f"toggle-{repo['name']}"
            button_key = f"btn-{repo['name']}"

            if toggle_key not in st.session_state:
                st.session_state[toggle_key] = False

            with cols[j]:
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

                # Config toggle button
                if st.button("⚙️ Client config", key=button_key):
                    st.session_state[toggle_key] = not st.session_state[toggle_key]

                # Show config if toggled
                if st.session_state[toggle_key]:
                    if repo.get("client_config"):
                        st.code(json.dumps(repo["client_config"], indent=2), language="json")
                    else:
                        st.info("No client config available.")
    st.markdown("---")
    # Inject custom CSS for sticky footer
st.markdown("""
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f3f6fc;
            color: #333;
            text-align: center;
            padding: 10px;
            font-size: 0.9rem;
            border-top: 1px solid #ddd;
            z-index: 100;
        }
    </style>
    <div class="footer">
        ℹ️ All data shown here is scraped from public GitHub repositories.  
        🛠️ Developed with ❤️ by <a href="https://github.com/Harika-BV" target="_blank">Harika B V</a>
    </div>
""", unsafe_allow_html=True)
