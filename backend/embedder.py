import json
import os
import numpy as np
import time
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

from opensearchpy import OpenSearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers as elastic_helpers
from opensearchpy import helpers as opensearch_helpers

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def load_mcp_data(json_path="data/mcpverse_data.json"):
    with open(json_path, "r") as f:
        return json.load(f)

def generate_embedding(text, model="text-embedding-ada-002"):
    try:
        response = client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def get_search_client():
    es_host = os.getenv("ELASTICSEARCH_HOST")
    es_key = os.getenv("ELASTICSEARCH_KEY")
    if es_host and es_key:
        return "elasticsearch", Elasticsearch(es_host, api_key=es_key)
    else:
        return "opensearch", OpenSearch(
            hosts=[{"host": os.getenv("OPENSEARCH_HOST", "localhost"), "port": int(os.getenv("OPENSEARCH_PORT", 9200))}],
            http_auth=(os.getenv("OPENSEARCH_USER", "admin"), os.getenv("OPENSEARCH_PASS", "admin")),
            use_ssl=True,
            verify_certs=True
        )

def create_index(client_type, client, index_name):
    if client.indices.exists(index=index_name):
        print(f"Deleting existing index: {index_name}")
        client.indices.delete(index=index_name)

    print(f"Creating index: {index_name}")
    if client_type == "elasticsearch":
        index_body = {
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "url": {"type": "keyword"},
                    "client_config": {"type": "object", "enabled": True},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
    else:
        index_body = {
            "settings": {
                "index.knn": True
            },
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "url": {"type": "keyword"},
                    "client_config": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    }
                }
            }
        }

    client.indices.create(index=index_name, body=index_body)

def index_documents(data, index_name="mcpverse", batch_size=10):
    client_type, client = get_search_client()
    create_index(client_type, client, index_name)

    actions = []
    MAX_CHARS = 24000

    for item in tqdm(data):
        content = f"{item['name']} {item.get('description', '')} {item.get('readme', '')}"
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS]

        embedding = generate_embedding(content)
        if not embedding:
            continue

        doc = {
            "_index": index_name,
            "_source": {
                "name": item["name"],
                "description": item.get("description", ""),
                "url": item["url"],
                "client_config": item.get("client_config", {}),
                "embedding": embedding
            }
        }
        actions.append(doc)

        if len(actions) >= batch_size:
            if client_type == "elasticsearch":
                elastic_helpers.bulk(client, actions, index=index_name, raise_on_error=False)
            else:
                opensearch_helpers.bulk(client, actions, index=index_name, raise_on_error=False)
            actions = []

    if actions:
        if client_type == "elasticsearch":
            elastic_helpers.bulk(client, actions, index=index_name, raise_on_error=False)
        else:
            opensearch_helpers.bulk(client, actions, index=index_name, raise_on_error=False)

    print("✅ Indexing completed.")

def search(query, index_name="mcpverse"):
    all_repos = load_mcp_data()
    if os.getenv("VECTOR_ENABLED") == "False":
        if not query:
            return all_repos

        query = query.lower()
        results = []
        for repo in all_repos:
            text = " ".join([
                repo.get('name', ''),
                repo.get('description', ''),
                repo.get('readme', '')
            ]).lower()
            if query in text:
                results.append(repo)
        return results
    else:
        client_type, client = get_search_client()

        embedding = generate_embedding(query)
        norm = np.linalg.norm(embedding)
        query_embedding = [v / norm for v in embedding]

        if client_type == "elasticsearch":
            search_query ={
                "size": 50,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "script_score": {
                                    "query": {
                                        "match_all": {}
                                    },
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                        "params": {
                                            "query_vector": query_embedding
                                        }
                                    }
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "name^2",
                                        "description",
                                        "readme"
                                    ],
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                }
            }
        elif client_type == "opensearch":
            search_query = {
                "size": 50,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": embedding,
                                        "k": 10
                                    }
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["name^2", "description", "readme"],
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                }
            }

        else:
            raise ValueError("Unsupported client type")

        res = client.search(index=index_name, body=search_query)
        return [hit["_source"] for hit in res["hits"]["hits"]]


def get_total_indexed_docs(index_name="mcpverse"):
    all_repos = load_mcp_data()
    if os.getenv("VECTOR_ENABLED") == "False":
        return len(all_repos)
    else:
        _, client = get_search_client()
        stats = client.count(index=index_name)
        return stats["count"]

def get_all_repos(index_name="mcpverse", size=100):
    all_repos = load_mcp_data()
    if os.getenv("VECTOR_ENABLED") == "False":
        return all_repos
    else:
        _, client = get_search_client()
        res = client.search(index=index_name, body={"size": size, "query": {"match_all": {}}})
        return [hit["_source"] for hit in res["hits"]["hits"]]

if __name__ == "__main__":
    start = time.time()
    data = load_mcp_data()
    index_documents(data)
    print(f"🔄 Done in {round(time.time() - start, 2)}s")