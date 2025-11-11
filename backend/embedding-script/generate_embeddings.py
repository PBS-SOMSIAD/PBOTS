import os
from qdrant_client import QdrantClient
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "documents"
DATA_DIR = "data"


def generate_database():
    try:
        doc_converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")

        documents, metadatas = [], []

        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".pdf"):
                file_path = os.path.join(DATA_DIR, filename)
                print(f"Processing file: {file_path}")
                result = doc_converter.convert(file_path)

                for chunk in HybridChunker().chunk(result.document):
                    documents.append(chunk.text)
                    metadatas.append(chunk.meta.export_json_dict())

        db_client.add(
            collection_name=COLLECTION_NAME,
            documents=documents,
            metadata=metadatas,
            batch_size=64,
        )

        print(f"Database generation successful. Total document count: {len(documents)}")
    except Exception as e:
        print(f"Failed to generate database: {str(e)}")


if __name__ == "__main__":
    generate_database()