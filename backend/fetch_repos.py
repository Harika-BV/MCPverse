import os
import json
import time
import base64
from github import Github
from dotenv import load_dotenv
from pathlib import Path
from github_scraper import search_mcp_repos
from config_extractor import extract_client_config_from_readme
from concurrent.futures import ThreadPoolExecutor, as_completed
from github.GithubException import GithubException, RateLimitExceededException

MAX_THREADS = 10  # Tune based on your machine

start_time = time.time()

# Load environment variables
load_dotenv()
GH_API_KEY = os.getenv("GH_API_KEY")

# Initialize GitHub client
g = Github(GH_API_KEY)

# Create data folder if not exists
data_path = Path("data")
data_path.mkdir(exist_ok=True)

print("🔍 Searching for MCP-related repositories...")
repos = search_mcp_repos(g)

print(f"📦 Found {len(repos)} repositories. Processing...")
repo_data = []

def get_repo_readme(repo):
    try:
        readme = repo.get_readme()
        content = base64.b64decode(readme.content).decode("utf-8")
        return content
    except RateLimitExceededException:
        print("🛑 Rate limit hit while fetching README. Waiting...")
        time.sleep(5)
        return None
    except GithubException as e:
        if e.status == 404:
            print(f"ℹ️ No README found for {repo.full_name}")
        elif e.status == 403:
            print(f"⚠️ Access denied or abuse detection for {repo.full_name}")
        else:
            print(f"⚠️ GithubException for {repo.full_name}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error for {repo.full_name}: {e}")
        return None


def process_repo(repo):
    try:
        time.sleep(5)
        if not repo.private:
            try:
                readme = get_repo_readme(repo)
                config = extract_client_config_from_readme(readme)
            except:
                readme = None
                config = None
            if readme:
                return {
                    "name": repo.full_name,
                    "url": repo.html_url,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "topics": repo.get_topics(),
                    "readme": readme,
                    "client_config": config,
                    "last_updated": repo.updated_at.isoformat(),
                }
    except Exception as e:
        print(f"⚠️ Error processing {repo.full_name}: {e}")
        return None
    
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(process_repo, repo) for repo in repos]
    for future in as_completed(futures):
        result = future.result()
        if result:
            repo_data.append(result)

# Save to JSON
output_file = data_path / "mcpverse_data.json"
with open(output_file, "w") as f:
    json.dump(repo_data, f, indent=2)

print(f"✅ Done. Saved to {output_file}")
end_time = time.time()
elapsed = end_time - start_time
print(f"⏱️ Total time taken: {elapsed:.2f} seconds")

print("Total count ", len(repo_data))