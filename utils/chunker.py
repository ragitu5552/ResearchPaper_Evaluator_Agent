import tiktoken

MAX_TOKENS = 15000  # conservative buffer below 16k hard limit


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def safe_chunk(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """
    Splits text into chunks that each fit within max_tokens.
    Returns a list of string chunks.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunks.append(enc.decode(chunk_tokens))

    return chunks


def truncate_to_limit(text: str, max_tokens: int = MAX_TOKENS) -> str:
    """
    Hard truncate if needed. Use for section content before passing to agents.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])
