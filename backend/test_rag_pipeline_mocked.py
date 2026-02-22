"""
Mocked end-to-end RAG pipeline test.
This avoids loading heavy models by injecting fake modules for:
- multimedia_rag.ingestion.embedder
- multimedia_rag.ingestion.mongo_store
- multimedia_rag.query.search

It then imports `multimedia_rag.query.pipeline.run_query` and runs it with a sample query.
"""
import os
import sys
import types

# Set OpenAI env (use your env or .env in real runs)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['OPENAI_MODEL'] = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# ---------------------------------------------------------------------------
# Inject fake embedder module to avoid SentenceTransformer import
# ---------------------------------------------------------------------------
fake_embedder = types.ModuleType("multimedia_rag.ingestion.embedder")

EMBED_DIM = 384

def generate_embedding(text: str):
    # deterministic simple embedding for testing
    return [0.0] * EMBED_DIM

fake_embedder.generate_embedding = generate_embedding
sys.modules['multimedia_rag.ingestion.embedder'] = fake_embedder

# ---------------------------------------------------------------------------
# Inject fake mongo_store module to avoid MongoDB access
# ---------------------------------------------------------------------------
fake_mongo = types.ModuleType("multimedia_rag.ingestion.mongo_store")

def get_frame_metadata(frame_id):
    return {
        "gps_lat": 51.0,
        "gps_lng": -0.1,
        "confidence": 0.95,
        "reid_group": "group-1"
    }

def get_frame_embedding_doc(frame_id):
    return {
        "_id": frame_id,
        "cam_id": "cam-1",
        "timestamp": 42,
        "caption": "Person wearing blue jacket",
        "frame_image": b"\x89PNG..."
    }

fake_mongo.get_frame_metadata = get_frame_metadata
fake_mongo.get_frame_embedding_doc = get_frame_embedding_doc
def ensure_text_index():
    # no-op for mocked DB
    return None

class _FakeCollection:
    def find(self, *args, **kwargs):
        return []

class _FakeDB(dict):
    def __getitem__(self, name):
        return _FakeCollection()

def get_db():
    return _FakeDB()

fake_mongo.ensure_text_index = ensure_text_index
fake_mongo.get_db = get_db
sys.modules['multimedia_rag.ingestion.mongo_store'] = fake_mongo

# ---------------------------------------------------------------------------
# Inject fake search module to return pre-canned vector search results
# ---------------------------------------------------------------------------
fake_search = types.ModuleType('multimedia_rag.query.search')

def vector_search(query_embedding, top_k=10):
    # Return a few fake hits with _id matching what get_frame_embedding_doc expects
    return [
        {"_id": "frame-1", "score": 0.9, "gdrive_url": None},
        {"_id": "frame-2", "score": 0.75, "gdrive_url": None}
    ]

fake_search.vector_search = vector_search
def multi_search(user_query, top_k=25):
    return vector_search(None, top_k=top_k)

fake_search.multi_search = multi_search
sys.modules['multimedia_rag.query.search'] = fake_search

# ---------------------------------------------------------------------------
# Now import the pipeline and run a test query
# ---------------------------------------------------------------------------
print('\n== Mocked RAG Pipeline Test ==')
try:
    # Import the pipeline after injecting fakes
    from multimedia_rag.query.pipeline import run_query

    query = "Find a person in a blue jacket"
    print(f"Running pipeline.run_query('{query}') (mocked)...")
    output = run_query(query)

    print('\n--- Pipeline Output Summary ---')
    print(f"Query: {output.get('query')}")
    print(f"Total results: {output.get('total')}")
    print(f"Timeline length: {len(output.get('timeline', []))}")
    print('Sample result keys:', list(output.get('results', [])[0].keys()) if output.get('results') else 'none')
    print('\nFull output (truncated):')
    import json
    print(json.dumps(output, indent=2)[:2000])

    print('\n✓ Mocked pipeline run completed successfully')
    sys.exit(0)

except Exception as e:
    print('\n✗ Mocked pipeline run failed:')
    import traceback
    traceback.print_exc()
    sys.exit(2)
