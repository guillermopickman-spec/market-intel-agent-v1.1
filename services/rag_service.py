from chroma.collection import get_collection
from embeddings.model import get_embedding_model

def search_rag(query: str, conversation_id: int, n_results: int = 3):
    """
    1. Converts query to vector.
    2. Searches ChromaDB for chunks belonging to the specific conversation.
    3. Returns the combined text.
    """
    model = get_embedding_model()
    collection = get_collection()
    
    # Generate vector for the user's question
    query_vectors = model.embed([query])
    
    if not query_vectors:
        return ""

    # Search ChromaDB
    # We use a filter to ensure the AI only sees data from THIS conversation
    results = collection.query(
        query_embeddings=[query_vectors[0]],
        n_results=n_results,
        where={"conversation_id": int(conversation_id)}
    )
    
    # Flatten the list of documents into a single string of context
    documents_list = results.get('documents', [[]])
    documents = documents_list[0] if documents_list else []
    context = "\n\n---\n\n".join(documents)
    
    return context