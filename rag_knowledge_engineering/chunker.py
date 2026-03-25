"""Document chunking strategies for RAG systems."""

import re
from typing import List

from .analyzer import count_tokens
from .models import ChunkResult


def chunk_by_heading(text: str) -> ChunkResult:
    """
    Split document on H2 heading boundaries.

    Each H2 section becomes a separate chunk. This preserves semantic
    relationships within sections while isolating top-level operations.

    Args:
        text: Markdown document

    Returns:
        ChunkResult with chunks split at H2 boundaries
    """
    chunks = []
    chunk_boundaries = []
    current_chunk = []
    boundary_pos = 0

    for line in text.split('\n'):
        if re.match(r'^## ', line) and current_chunk:
            # Start new chunk
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
            chunk_boundaries.append(boundary_pos)
            current_chunk = [line]
            boundary_pos += len(chunk_text) + 1
        else:
            current_chunk.append(line)
            boundary_pos += len(line) + 1

    # Add final chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    total_tokens = sum(count_tokens(chunk) for chunk in chunks)
    avg_chunk_size = total_tokens // len(chunks) if chunks else 0

    return ChunkResult(
        chunks=chunks,
        chunk_boundaries=chunk_boundaries,
        total_chunks=len(chunks),
        average_chunk_size=avg_chunk_size,
    )


def chunk_by_tokens(text: str, max_tokens: int = 500) -> ChunkResult:
    """
    Split document into fixed-size token chunks.

    Creates chunks of approximately max_tokens size, splitting at
    paragraph boundaries when possible.

    Args:
        text: Markdown document
        max_tokens: Target tokens per chunk

    Returns:
        ChunkResult with fixed-size token chunks
    """
    chunks = []
    chunk_boundaries = []
    current_chunk = []
    current_tokens = 0

    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)

        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Start new chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
            chunk_boundaries.append(len(chunk_text))
            current_chunk = [paragraph]
            current_tokens = para_tokens
        else:
            current_chunk.append(paragraph)
            current_tokens += para_tokens

    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    total_tokens = sum(count_tokens(chunk) for chunk in chunks)
    avg_chunk_size = total_tokens // len(chunks) if chunks else 0

    return ChunkResult(
        chunks=chunks,
        chunk_boundaries=chunk_boundaries,
        total_chunks=len(chunks),
        average_chunk_size=avg_chunk_size,
    )


def chunk_semantic(text: str, max_tokens: int = 500) -> ChunkResult:
    """
    Split document using heading-aware semantic chunking.

    Respects heading hierarchies and keeps related content together.
    Chunks at H2 boundaries first, then subdivides large sections by tokens.

    Args:
        text: Markdown document
        max_tokens: Target tokens per chunk for subdivision

    Returns:
        ChunkResult with semantically coherent chunks
    """
    # First, split by H2 headings
    chunks = []
    chunk_boundaries = []
    current_section = []
    section_heading = None

    for line in text.split('\n'):
        if re.match(r'^## ', line):
            # Save previous section if it exists
            if current_section:
                section_text = '\n'.join(current_section)
                section_tokens = count_tokens(section_text)

                # Subdivide if too large
                if section_tokens > max_tokens:
                    subchunks = _subdivide_by_tokens(section_text, max_tokens)
                    chunks.extend(subchunks)
                else:
                    chunks.append(section_text)

            # Start new section
            section_heading = re.match(r'^## (.+)$', line).group(1)
            current_section = [line]
        else:
            current_section.append(line)

    # Add final section
    if current_section:
        section_text = '\n'.join(current_section)
        section_tokens = count_tokens(section_text)

        if section_tokens > max_tokens:
            subchunks = _subdivide_by_tokens(section_text, max_tokens)
            chunks.extend(subchunks)
        else:
            chunks.append(section_text)

    # Compute boundaries
    boundary = 0
    for chunk in chunks:
        boundary += len(chunk)
        chunk_boundaries.append(boundary)

    total_tokens = sum(count_tokens(chunk) for chunk in chunks)
    avg_chunk_size = total_tokens // len(chunks) if chunks else 0

    return ChunkResult(
        chunks=chunks,
        chunk_boundaries=chunk_boundaries,
        total_chunks=len(chunks),
        average_chunk_size=avg_chunk_size,
    )


def _subdivide_by_tokens(text: str, max_tokens: int) -> List[str]:
    """
    Subdivide text into token-bounded chunks.

    Helper function for semantic chunking.

    Args:
        text: Text to subdivide
        max_tokens: Target tokens per chunk

    Returns:
        List of chunks
    """
    chunks = []
    current_chunk = []
    current_tokens = 0

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)

        if current_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [paragraph]
            current_tokens = para_tokens
        else:
            current_chunk.append(paragraph)
            current_tokens += para_tokens

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def compare_chunking_strategies(text: str) -> None:
    """
    Compare retrieval quality across chunking strategies.

    Prints side-by-side comparison of heading, token, and semantic chunking.

    Args:
        text: Document to chunk
    """
    print("Chunking Strategy Comparison")
    print("=" * 60)

    # Chunk by heading
    by_heading = chunk_by_heading(text)
    print(f"\nH2 Boundary Chunking:")
    print(f"  Chunks: {by_heading.total_chunks}")
    print(f"  Avg size: {by_heading.average_chunk_size} tokens")

    # Chunk by tokens
    by_tokens = chunk_by_tokens(text, max_tokens=500)
    print(f"\nFixed Token Chunking (500 tokens):")
    print(f"  Chunks: {by_tokens.total_chunks}")
    print(f"  Avg size: {by_tokens.average_chunk_size} tokens")

    # Chunk semantic
    semantic = chunk_semantic(text, max_tokens=500)
    print(f"\nSemantic Chunking (H2 + 500 tokens):")
    print(f"  Chunks: {semantic.total_chunks}")
    print(f"  Avg size: {semantic.average_chunk_size} tokens")
