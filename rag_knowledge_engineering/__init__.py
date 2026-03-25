"""RAG Knowledge Engineering - Document optimization for retrieval systems."""

from .analyzer import compare_before_after, count_tokens, measure_retrieval_precision
from .chunker import chunk_by_heading, chunk_by_tokens, chunk_semantic
from .models import ChunkResult, ComparisonResult, OptimizedDocument, RetrievalMetrics, TokenComparison
from .optimizer import optimize_document, separate_appendix, add_quick_reference, promote_headings

__version__ = "0.1.0"
__author__ = "Grisha T."
__email__ = ""

__all__ = [
    # Optimizer functions
    "optimize_document",
    "promote_headings",
    "separate_appendix",
    "add_quick_reference",
    # Analyzer functions
    "count_tokens",
    "measure_retrieval_precision",
    "compare_before_after",
    # Chunker functions
    "chunk_by_heading",
    "chunk_by_tokens",
    "chunk_semantic",
    # Data models
    "OptimizedDocument",
    "ChunkResult",
    "RetrievalMetrics",
    "TokenComparison",
    "ComparisonResult",
]
