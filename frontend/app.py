import streamlit as st
import requests
import json, os

st.set_page_config(page_title="MCPverse", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    if os.getenv("ENV") == "local":
        with open("../backend/data/mcpverse_data.json", "r") as f:
            return json.load(f)
    else:
        url = "https://raw.githubusercontent.com/Harika-BV/mcpverse/main/backend/data/mcpverse_data.json"
        response = requests.get(url)
        return response.json()

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
st.title("🔍 MCPverse — Discover MCP Servers")
search = st.text_input("Search repositories...")

# ---------- Filtered Results ----------
filtered = [r for r in repos if search.lower() in r["name"].lower() or search.lower() in r.get("description", "").lower()]

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