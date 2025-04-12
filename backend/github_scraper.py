import time
from datetime import datetime, timedelta
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_THREADS = 10
COLLECTION_KEYWORDS = ["awesome", "list", "collection", "curated", "resources"]

def wait_if_rate_limited(github):
    rate_limit = github.get_rate_limit().core
    if rate_limit.remaining == 0:
        wait_time = int(rate_limit.reset.timestamp() - time.time()) + 5
        print(f"🛑 Rate limit exceeded. Waiting {wait_time} seconds...")
        time.sleep(wait_time)

def is_collection_repo(repo):
    text = (repo.name + " " + (repo.description or "")).lower()
    return any(keyword in text for keyword in COLLECTION_KEYWORDS)

def is_link_heavy_readme(repo):
    try:
        readme = repo.get_readme()
        content = base64.b64decode(readme.content).decode("utf-8")
        github_links = content.count("https://github.com/")
        return github_links > 5
    except Exception:
        return False

def is_valid_mcp_repo(repo):
    if is_collection_repo(repo):
        return False
    return True

def validate_repos_parallel(repos):
    valid_repos = {}

    def validate(repo):
        if is_valid_mcp_repo(repo):
            return repo.full_name, repo
        return None

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(validate, repo): repo for repo in repos}
        for future in as_completed(futures):
            result = future.result()
            if result:
                key, repo = result
                valid_repos[key] = repo

    return valid_repos

def fetch_repos_in_range(github, start_date, end_date, collected):
    # if len(collected) >= 100:
    #     return
    query = f'mcp server in:description created:{start_date.date()}..{end_date.date()}'
    print(f"🔍 Query: {query}")

    # wait_if_rate_limited(github)
    result = github.search_repositories(query=query, sort="stars", order="desc")
    count = result.totalCount
    print(f"→ Found {count} repos between {start_date.date()} and {end_date.date()}")

    if count == 0:
        return

    if count >= 1000:
        # Split range recursively
        mid_date = start_date + (end_date - start_date) / 2
        fetch_repos_in_range(github, start_date, mid_date, collected)
        fetch_repos_in_range(github, mid_date + timedelta(days=1), end_date, collected)
    else:
        repos_to_validate = [repo for repo in result if repo.full_name not in collected]
        valid = validate_repos_parallel(repos_to_validate)
        collected.update(valid)

def search_mcp_repos(github):
    collected = {}
    start_date = datetime(2023, 1, 1)
    end_date = datetime.today()

    fetch_repos_in_range(github, start_date, end_date, collected)
    return list(collected.values())