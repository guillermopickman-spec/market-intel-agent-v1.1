import logging
from typing import Optional, List, Tuple, cast
from chromadb.api.types import Embedding
from chroma.collection import get_collection
from embeddings.model import get_embedding_model
from services.llm.factory import LLMFactory  # Use factory instead of direct import
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def ask_document_question(question: str, conversation_id: Optional[int] = None) -> Tuple[str, List[str]]:
    """
    RAG Chain: 
    1. Generate Embeddings (MiniLM via Hugging Face).
    2. Search ChromaDB for relevant context.
    3. Synthesize the final answer using the configured LLM (Gemini or HF).
    """
    model = get_embedding_model()
    collection = get_collection()
    
    # 1. Generate Embeddings for the search
    raw_embeddings = model.embed([question])
    
    if not raw_embeddings or len(raw_embeddings) == 0:
        logger.error(f"RAG Failure: No embeddings for: {question}")
        raise HTTPException(
            status_code=504, 
            detail="The Intelligence Service failed to load. Please try again."
        )

    # 2. Query Vector Store (ChromaDB)
    try:
        query_vector = cast(List[Embedding], [[float(val) for val in raw_embeddings[0]]])
        search_params = {"query_embeddings": query_vector, "n_results": 7}
        
        if conversation_id:
            search_params["where"] = {"conversation_id": int(conversation_id)}
        
        results = collection.query(**search_params)
        
        documents_list = results.get('documents') or []
        metadatas_list = results.get('metadatas') or []
        
        context = ""
        sources = []

        if documents_list and len(documents_list) > 0:
            context = "\n---\n".join(documents_list[0])
            if metadatas_list:
                sources = list(set([str(m.get('title', 'Market Report')) for m in metadatas_list[0] if m]))
        else:
            context = "No relevant audit data found for this query."

        # 3. Final Synthesis using the Factory
        prompt = (
            f"You are a professional market analyst. Based ONLY on the following context, "
            f"answer the user question in detail. If the information is not present, say so.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            f"ANSWER:"
        )
        
        # This will automatically pick Gemini if set in .env
        llm_client = LLMFactory.get_client()
        response_content = llm_client.generate(prompt)
        
        return response_content, sources

    except Exception as e:
        logger.error(f"❌ Critical Error in RAG Chain: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intelligence Synthesis Error: {str(e)}")