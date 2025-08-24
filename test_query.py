from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

query_text = "Jak zalogować się do USOS?"
vector = model.encode(query_text).tolist()

result = client.search(
    collection_name="faq",
    query_vector=vector,
    limit=3
)
for point in result:
    print(point.payload)
