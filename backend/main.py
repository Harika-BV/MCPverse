import os
import json
from github import Github
from dotenv import load_dotenv
from pathlib import Path
from github_scraper import search_mcp_repos
from config_extractor import extract_client_config_from_readme

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Initialize GitHub client
g = Github(GITHUB_TOKEN)

# Create data folder if not exists
data_path = Path("data")
data_path.mkdir(exist_ok=True)

print("🔍 Searching for MCP-related repositories...")
repos = search_mcp_repos(g)

print(f"📦 Found {len(repos)} repositories. Processing...")
repo_data = []

for repo in repos:
    try:
        readme = repo.get_readme().decoded_content.decode("utf-8")
        config = extract_client_config_from_readme(readme)

        repo_data.append({
            "name": repo.full_name,
            "url": repo.html_url,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "topics": repo.get_topics(),
            "readme": readme,
            "client_config": config,
            "last_updated": repo.updated_at.isoformat(),
        })
    except Exception as e:
        print(f"⚠️ Error processing {repo.full_name}: {e}")

# Save to JSON
output_file = data_path / "mcpverse_data.json"
with open(output_file, "w") as f:
    json.dump(repo_data, f, indent=2)

print(f"✅ Done. Saved to {output_file}")