from qdrant_client import QdrantClient

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL)

# Wypisz dostępne kolekcje
collections = [col.name for col in client.get_collections().collections]
print("Kolekcje:", collections)

if not collections:
    print("Brak kolekcji w Qdrant! Najpierw uruchom skrypt embeddingowy, aby utworzyć i załadować dane.")
else:
    for collection_name in collections:
        print(f"\n--- Kolekcja: {collection_name} ---")
        try:
            result = client.scroll(collection_name=collection_name, limit=5, with_payload=True)
            points = result[1]
            if points:
                for point in points:
                    if hasattr(point, "payload"):
                        print(point.payload)
                    else:
                        print(f"Rekord bez payloadu: {point}")
            else:
                print("Brak rekordów w tej kolekcji.")
        except Exception as e:
            print(f"Błąd podczas pobierania kolekcji '{collection_name}': {e}")
