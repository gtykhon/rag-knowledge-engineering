"""Token counting and retrieval precision analysis."""

import re
from typing import List, Tuple

import tiktoken

from .models import ComparisonResult, RetrievalMetrics, TokenComparison


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model name for token counting (default: gpt-3.5-turbo)

    Returns:
        Token count
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base if model not found
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def _extract_text_sections(text: str) -> List[Tuple[str, str]]:
    """
    Extract sections from markdown by H2 headings.

    Returns:
        List of (heading, content) tuples
    """
    sections = []
    current_heading = "Preamble"
    current_content = []

    for line in text.split('\n'):
        if re.match(r'^## ', line):
            # Save previous section
            if current_content:
                sections.append((current_heading, '\n'.join(current_content)))
            current_heading = re.match(r'^## (.+)$', line).group(1)
            current_content = [line]
        else:
            current_content.append(line)

    # Save final section
    if current_content:
        sections.append((current_heading, '\n'.join(current_content)))

    return sections


def _compute_relevance_score(query: str, text: str) -> float:
    """
    Compute simple relevance score between query and text.

    Uses keyword overlap and proximity heuristics.

    Args:
        query: Query text
        text: Content to score

    Returns:
        Relevance score 0.0 to 1.0
    """
    query_words = set(query.lower().split())
    text_lower = text.lower()

    # Count keyword matches
    matches = sum(1 for word in query_words if word in text_lower)
    if not query_words:
        return 0.0

    # Bonus for exact phrase
    phrase_bonus = 1.0 if query.lower() in text_lower else 0.0

    return (matches / len(query_words)) * 0.8 + phrase_bonus * 0.2


def measure_retrieval_precision(
    query: str,
    document: str,
    chunk_size: int = 500,
) -> RetrievalMetrics:
    """
    Simulate RAG retrieval and measure precision.

    Chunks document, ranks by relevance to query, and measures
    what percentage of retrieved content is actually relevant.

    Args:
        query: Search query
        document: Document to retrieve from
        chunk_size: Max tokens per chunk (approximate)

    Returns:
        RetrievalMetrics for this query
    """
    # Split into sections
    sections = _extract_text_sections(document)

    # Score each section
    scored_sections = []
    for heading, content in sections:
        relevance = _compute_relevance_score(query, heading + " " + content)
        tokens = count_tokens(content)
        scored_sections.append((heading, content, relevance, tokens))

    # Rank by relevance and retrieve top chunks
    scored_sections.sort(key=lambda x: x[2], reverse=True)

    retrieved_chunks = []
    total_retrieved_tokens = 0
    token_budget = chunk_size * 3  # Retrieve up to 3 chunks

    for heading, content, relevance, tokens in scored_sections:
        if total_retrieved_tokens < token_budget:
            retrieved_chunks.append((len(retrieved_chunks), content, relevance))
            total_retrieved_tokens += tokens

    # Estimate relevant vs noise tokens
    # A chunk is "relevant" if its relevance score > 0.3
    relevant_token_count = sum(
        count_tokens(chunk[1]) for chunk in retrieved_chunks if chunk[2] > 0.3
    )
    noise_token_count = total_retrieved_tokens - relevant_token_count
    precision = relevant_token_count / total_retrieved_tokens if total_retrieved_tokens > 0 else 0.0

    return RetrievalMetrics(
        query=query,
        retrieved_chunks=retrieved_chunks,
        relevant_token_count=relevant_token_count,
        total_retrieved_tokens=total_retrieved_tokens,
        noise_token_count=noise_token_count,
        precision=precision,
        recall=min(precision, 0.95),  # Simplified recall estimate
    )


def compare_before_after(
    original: str,
    optimized: str,
    queries: List[str],
    document_name: str = "Document",
) -> ComparisonResult:
    """
    Compare retrieval precision before and after optimization.

    Args:
        original: Original markdown document
        optimized: Optimized markdown document
        queries: List of test queries
        document_name: Name for reporting

    Returns:
        ComparisonResult with side-by-side metrics
    """
    # Measure before optimization
    before_metrics = [measure_retrieval_precision(q, original) for q in queries]

    # Measure after optimization
    after_metrics = [measure_retrieval_precision(q, optimized) for q in queries]

    # Compute token comparison
    original_tokens = count_tokens(original)
    optimized_tokens = count_tokens(optimized)
    reduction = original_tokens - optimized_tokens
    reduction_pct = (reduction / original_tokens * 100) if original_tokens > 0 else 0

    token_comparison = TokenComparison(
        document_name=document_name,
        before_tokens=original_tokens,
        after_tokens=optimized_tokens,
        reduction_tokens=reduction,
        reduction_percentage=reduction_pct,
    )

    return ComparisonResult(
        original_doc=original,
        optimized_doc=optimized,
        queries=queries,
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        token_comparison=token_comparison,
    )
