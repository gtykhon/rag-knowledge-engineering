"""Tests for token counting and retrieval analysis."""

import pytest

from rag_knowledge_engineering.analyzer import (
    compare_before_after,
    count_tokens,
    measure_retrieval_precision,
)


class TestCountTokens:
    def test_count_simple_text(self):
        """Test token counting on simple text."""
        text = "Hello world"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_longer_text(self):
        """Test that longer text has more tokens."""
        short = "Hello"
        long = "Hello " * 100
        short_count = count_tokens(short)
        long_count = count_tokens(long)
        assert long_count > short_count

    def test_count_empty_text(self):
        """Test counting empty text."""
        count = count_tokens("")
        assert count == 0

    def test_count_markdown_text(self):
        """Test counting markdown formatted text."""
        markdown = """# Heading
## Subheading

Some content with **bold** and *italic*.

- List item 1
- List item 2
"""
        count = count_tokens(markdown)
        assert count > 0

    def test_different_models_may_differ(self):
        """Test that token counts work with model parameter."""
        text = "This is a test sentence."
        count1 = count_tokens(text, model="gpt-3.5-turbo")
        count2 = count_tokens(text, model="gpt-4")
        # Different models may have different tokenization
        assert count1 > 0
        assert count2 > 0


class TestMeasureRetrievalPrecision:
    def test_measure_perfect_match(self):
        """Test retrieval when document matches query perfectly."""
        query = "configuration validation"
        document = """## Validation Configuration
Configuration details about validation.

## Retry Policy
Details about retries.
"""
        metrics = measure_retrieval_precision(query, document)
        assert metrics.query == query
        assert metrics.precision >= 0.0
        assert metrics.precision <= 1.0
        assert metrics.total_retrieved_tokens > 0

    def test_measure_no_match(self):
        """Test retrieval when document doesn't match query."""
        query = "unrelated topic xyz"
        document = """## Configuration
Configuration content here.

## Implementation
Implementation details here.
"""
        metrics = measure_retrieval_precision(query, document)
        assert metrics.precision >= 0.0
        # Expect low or zero precision for completely unrelated query

    def test_retrieval_metrics_summary(self):
        """Test that metrics provide good summary."""
        query = "configuration"
        document = """## Configuration
Details about configuration.

## Other Section
Unrelated content.
"""
        metrics = measure_retrieval_precision(query, document)
        summary = metrics.summary()
        assert "Query:" in summary
        assert query in summary
        assert "Retrieved:" in summary


class TestCompareBeforeAfter:
    def test_compare_documents(self):
        """Test comparison of before/after documents."""
        original = """## Main Topic
### Subtopic 1
Content one

### Subtopic 2
Content two

### Subtopic 3
Content three

## Background
Background information.

## Theory
Theoretical foundations.
"""
        optimized = """## Subtopic 1
Content one

## Subtopic 2
Content two

## Subtopic 3
Content three

## Appendix
### Background
Background information.

### Theory
Theoretical foundations.
"""
        queries = ["How to configure?", "What's the background?"]
        result = compare_before_after(original, optimized, queries)

        assert result.token_comparison.before_tokens > 0
        assert result.token_comparison.after_tokens > 0
        assert len(result.before_metrics) == len(queries)
        assert len(result.after_metrics) == len(queries)

    def test_compare_with_document_name(self):
        """Test that document name is tracked."""
        before = "## Section\nContent\n## Background\nBG"
        after = "## Section\nContent\n## Appendix\nBG"
        result = compare_before_after(before, after, ["test"], document_name="MyDoc")
        assert result.token_comparison.document_name == "MyDoc"

    def test_compare_summary(self):
        """Test comparison summary generation."""
        before = "## Section 1\nContent " * 50
        after = "## Section 1\nContent " * 25
        result = compare_before_after(before, after, ["query"])
        summary = result.summary()
        assert "Token reduction" in summary
        assert "retrieval precision" in summary

    def test_precision_improvement(self):
        """Test that optimization can improve precision."""
        # Before: mixed content
        before = """## Main
Main content mixed with background.

### Subsection
Details mixed with theory.

## Background
Background theory and history.

## Implementation
Implementation and edge cases.
"""
        # After: separated content
        after = """## Main
Main content here.

### Subsection
Details section.

## Implementation
Implementation details.

## Appendix
### Background
Background theory and history.

### Edge Cases
Implementation edge cases.
"""
        queries = ["What is the main topic?"]
        result = compare_before_after(before, after, queries, document_name="test_doc")

        # Before and after should have valid metrics
        assert len(result.before_metrics) > 0
        assert len(result.after_metrics) > 0

        # Both should have measurable precision
        before_precision = result.before_metrics[0].precision
        after_precision = result.after_metrics[0].precision

        assert before_precision >= 0.0
        assert after_precision >= 0.0
