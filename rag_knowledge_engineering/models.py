"""Data models for RAG knowledge engineering."""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class OptimizedDocument:
    """Result of document optimization process."""

    original_text: str
    optimized_text: str
    original_token_count: int
    optimized_token_count: int
    reduction_percentage: float
    transformations_applied: List[str]
    promoted_headings: int
    appendix_moved_sections: int
    quick_references_added: int

    def summary(self) -> str:
        """Return human-readable optimization summary."""
        return (
            f"Token reduction: {self.original_token_count} → "
            f"{self.optimized_token_count} ({self.reduction_percentage:.1f}%)\n"
            f"Transformations: {', '.join(self.transformations_applied)}\n"
            f"Promoted headings: {self.promoted_headings}\n"
            f"Appendix sections: {self.appendix_moved_sections}\n"
            f"Quick references: {self.quick_references_added}"
        )


@dataclass
class ChunkResult:
    """Result of document chunking."""

    chunks: List[str]
    chunk_boundaries: List[int]
    total_chunks: int
    average_chunk_size: int

    def get_chunk(self, index: int) -> str:
        """Get chunk by index."""
        if 0 <= index < len(self.chunks):
            return self.chunks[index]
        raise IndexError(f"Chunk index {index} out of range [0, {len(self.chunks)-1}]")


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval evaluation."""

    query: str
    retrieved_chunks: List[Tuple[int, str, float]]  # (index, text, relevance_score)
    relevant_token_count: int
    total_retrieved_tokens: int
    noise_token_count: int
    precision: float  # relevant / total
    recall: float  # coverage indicator

    def summary(self) -> str:
        """Return human-readable retrieval summary."""
        return (
            f"Query: '{self.query}'\n"
            f"Retrieved: {self.total_retrieved_tokens} tokens ({len(self.retrieved_chunks)} chunks)\n"
            f"Relevant: {self.relevant_token_count} tokens ({self.precision:.1%})\n"
            f"Noise: {self.noise_token_count} tokens ({1-self.precision:.1%})"
        )


@dataclass
class TokenComparison:
    """Before/after token comparison for a single document."""

    document_name: str
    before_tokens: int
    after_tokens: int
    reduction_tokens: int
    reduction_percentage: float

    def to_table_row(self) -> Tuple[str, int, int, int, str]:
        """Return tuple for table formatting."""
        return (
            self.document_name,
            self.before_tokens,
            self.after_tokens,
            self.reduction_tokens,
            f"{self.reduction_percentage:.1f}%"
        )


@dataclass
class ComparisonResult:
    """Complete before/after comparison for multiple queries."""

    original_doc: str
    optimized_doc: str
    queries: List[str]
    before_metrics: List[RetrievalMetrics]
    after_metrics: List[RetrievalMetrics]
    token_comparison: TokenComparison

    def summary(self) -> str:
        """Return comprehensive comparison summary."""
        lines = [
            f"Document Comparison: {self.token_comparison.document_name}",
            f"{'='*60}",
            f"Token reduction: {self.token_comparison.before_tokens} → "
            f"{self.token_comparison.after_tokens} "
            f"({self.token_comparison.reduction_percentage:.1f}%)",
            "",
            "Before optimization:",
        ]

        before_avg_precision = sum(m.precision for m in self.before_metrics) / len(self.before_metrics)
        lines.append(f"  Average retrieval precision: {before_avg_precision:.1%}")

        lines.append("\nAfter optimization:")
        after_avg_precision = sum(m.precision for m in self.after_metrics) / len(self.after_metrics)
        lines.append(f"  Average retrieval precision: {after_avg_precision:.1%}")
        lines.append(f"  Improvement: +{(after_avg_precision - before_avg_precision):.1%}")

        return "\n".join(lines)
