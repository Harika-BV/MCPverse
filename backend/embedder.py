import json
import os
import time
from opensearchpy import OpenSearch, helpers
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch import helpers as elastic_helpers

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Load JSON data
def load_mcp_data(json_path="data/mcpverse_data.json"):
    with open(json_path, "r") as f:
        return json.load(f)

# Generate Ada embeddings
def generate_embedding(text, model="text-embedding-ada-002"):
    try:   
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )

        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

# Setup OpenSearch connection
def get_opensearch_client():
    host = os.getenv("OPENSEARCH_HOST", "localhost")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    user = os.getenv("OPENSEARCH_USER", "admin")
    password = os.getenv("OPENSEARCH_PASS", "admin")
    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
    ELASTICSEARCH_KEY = os.getenv("ELASTICSEARCH_KEY")
    if ELASTICSEARCH_HOST:
        return Elasticsearch(
            ELASTICSEARCH_HOST,
            api_key=ELASTICSEARCH_KEY
        )
    
    else:
        return OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(user, password),
            use_ssl=False,
            verify_certs=False
        )


# Create index if not exists
def create_index(client, index_name):
    if os.getenv("ELASTICSEARCH_HOST"):
        index_body = {
                "mappings": {
                    "properties": {
                         "name": {"type": "text"},
                        "description": {"type": "text"},
                        "url": {"type": "keyword"},
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
        index_body ={
                "settings": {
                    "index.knn": True
                },
                "mappings": {
                    "properties": {
                        "name": {"type": "text"},
                        "description": {"type": "text"},
                        "url": {"type": "keyword"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536
                        }
                    }
                }
            }
        
    if client.indices.exists(index=index_name):
        print(f"Deleting existing index: {index_name}")
        client.indices.delete(index=index_name)

    # Create index
    print(f"Creating index: {index_name}")
    client.indices.create(index=index_name, body=index_body)

# Prepare and index documents in bulk
def index_documents(data, index_name="mcpverse", batch_size=10):
    opensearch_client = get_opensearch_client()
    create_index(opensearch_client, index_name)

    actions = []

    for item in tqdm(data):
        content = f"{item['name']} {item.get('description', '')} {item.get('readme', '')}"
        embedding = generate_embedding(content)
        if not embedding:
            continue

        doc = {
            "_index": index_name,
            "_source": {
                "name": item["name"],
                "description": item.get("description", ""),
                "url": item["url"],
                "embedding": embedding,
            }
        }
        actions.append(doc)

        # Send in batches
        if len(actions) >= batch_size:
            elastic_helpers.bulk(opensearch_client, actions, index=index_name)
            actions = []

    # Index remaining
    if actions:
        elastic_helpers.bulk(opensearch_client, actions, index=index_name)

    print("✅ Indexing completed.")

def search_opensearch(query, index_name="mcpverse"):
    opensearch_client = get_opensearch_client()

    embedding = client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    ).data[0].embedding

    hybrid_query = {
            "size": 10,
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


    response = opensearch_client.search(index=index_name, body=hybrid_query)
    hits = response["hits"]["hits"]
    return [hit["_source"] for hit in hits]

def get_total_indexed_docs(index_name="mcpverse"):
    client = get_opensearch_client()
    stats = client.count(index=index_name)
    return stats["count"]

def get_all_repos(index_name="mcpverse", size=100):
    client = get_opensearch_client()
    response = client.search(
        index=index_name,
        body={
            "size": size,
            "query": {"match_all": {}}
        }
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]


# Run
if __name__ == "__main__":
    start = time.time()
    data = load_mcp_data()
    index_documents(data)
    print(f"🔄 Done in {round(time.time() - start, 2)}s")
