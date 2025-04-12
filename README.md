# 🚀 MCPverse

*MCPverse* is a semantic search engine for discovering **Model Configuration Protocol (MCP)** servers across GitHub. It indexes public MCP repositories and enables powerful natural language search using vector embeddings and OpenSearch.

---
### 📡 Live Demo
Try out the hosted version of MCPverse here:
👉 https://mcpverse.streamlit.app

---

## ✨ Features

- 🔍 Semantic search using OpenAI embeddings (`text-embedding-ada-002`)
- 📚 Indexes name, description, and README content
- ⚙️ Client configuration preview (where available)
- 🎨 Interactive UI using Streamlit

---

## 📦 Project Structure

```
.
├── backend
│   ├── fetch_repos.py      # Get MCP server repos from Github
│   ├── extract_config.py   # Logic to extract MCP client config from README
│   ├── embedder.py         # OpenAI + OpenSearch indexing and search logic
|   ├── github_scraper.py   # Using Github API to search on MCP servers 
│   └── data/
│       └── mcpverse_data.json  
├── frontend
│   └── app.py               # Streamlit app
├── requirements.txt
├── README.md
├── .env
├── .gitignore
```

---

## 🛠️ Local Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Harika-BV/MCPverse.git
cd MCPverse
```

---

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Create a `.env` file in the root:

```
GITHUB_TOKEN=your-github-token
ENV=local
OPENAI_API_KEY=your-openai-key
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=admin
```

> 💡 You can also connect to your hosted OpenSearch or Elasticsearch cluster.

---

### 4. Start OpenSearch Locally (Optional)

If you're running OpenSearch locally, use Docker:

```bash
docker run -d --name opensearch -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  opensearchproject/opensearch:2.11.1
```

---

### 5. Index MCP Repositories

```bash
cd backend
python embedder.py
```

This will:
- Load the GitHub MCP repo data (from mcpverse_data.json)
- Generate OpenAI embeddings
- Index them into OpenSearch

---

### 6. Run the Streamlit App

```bash
cd frontend
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧑‍💻 Maintainer

Built with ❤️ by [Harika B V](https://github.com/Harika-BV)

---

## ⚠️ Disclaimer

All repositories and data are publicly available on GitHub.  
MCPverse is a community project and is not affiliated with any third-party MCP maintainers.
