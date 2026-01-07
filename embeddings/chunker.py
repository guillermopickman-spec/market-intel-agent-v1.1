def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Splits the text into larger chunks so the AI does not lose the thread.
    The 200-character overlap ensures the end of one chunk appears at the start of the next.
    """
    chunks = []
    start = 0

    if not text:
        return []

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # The next chunk starts slightly before the previous one ended
        start = end - overlap

    return chunks