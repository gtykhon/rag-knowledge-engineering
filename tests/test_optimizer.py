"""Tests for optimizer transformations."""

import pytest

from rag_knowledge_engineering.optimizer import (
    add_quick_reference,
    optimize_document,
    promote_headings,
    separate_appendix,
)


class TestPromoteHeadings:
    def test_promote_h3_to_h2(self):
        """Test that H3 headings are promoted to H2."""
        text = """## Main Section
### Subsection
Content here
"""
        result, count = promote_headings(text)
        assert "## Subsection" in result
        assert "### Subsection" not in result
        assert count == 1

    def test_promote_multiple_nested_headings(self):
        """Test promotion of H3, H4, H5."""
        text = """## Main
### Sub3
#### Sub4
##### Sub5
Content
"""
        result, count = promote_headings(text)
        # All nested headings should be promoted
        assert result.count("## ") == 4
        assert "### " not in result
        assert "#### " not in result
        assert "##### " not in result
        assert count == 3

    def test_preserve_h2_headings(self):
        """Test that H2 headings are preserved."""
        text = """## Heading 1
Content
## Heading 2
More content
"""
        result, count = promote_headings(text)
        assert "## Heading 1" in result
        assert "## Heading 2" in result
        assert count == 0


class TestSeparateAppendix:
    def test_move_background_section(self):
        """Test that Background section is moved to appendix."""
        text = """## Main Content
Content here

## Background
Background information
"""
        result, count = separate_appendix(text)
        assert "## Appendix" in result
        assert result.index("## Appendix") < result.index("## Background")
        assert count == 1

    def test_move_multiple_appendix_sections(self):
        """Test moving multiple appendix-type sections."""
        text = """## Main Content
Main stuff

## Theory
Theory stuff

## Research
Research stuff

## Main Again
More main
"""
        result, count = separate_appendix(text)
        # Should move Theory and Research, but Main Again stays in main
        assert count >= 2

    def test_no_move_when_no_appendix_patterns(self):
        """Test that normal sections are not moved."""
        text = """## Introduction
Intro

## Implementation
Implementation details
"""
        result, count = separate_appendix(text)
        assert count == 0
        assert "## Appendix" not in result


class TestAddQuickReference:
    def test_add_quick_reference_to_section(self):
        """Test that quick reference is added to sections."""
        text = """## Configuration
### Validation
Validation content
### Retry Policy
Retry content
"""
        result, count = add_quick_reference(text)
        assert "### Quick Reference" in result
        assert count == 1

    def test_quick_reference_lists_operations(self):
        """Test that quick reference lists H3 operations."""
        text = """## Config
### Setting A
Content A
### Setting B
Content B
### Setting C
Content C
"""
        result, count = add_quick_reference(text)
        assert "- Setting A" in result
        assert "- Setting B" in result
        assert "- Setting C" in result

    def test_skip_existing_quick_reference(self):
        """Test that existing quick references are not duplicated."""
        text = """## Config
### Quick Reference
- Existing
### Setting
Content
"""
        result, count = add_quick_reference(text)
        # Should not add duplicate
        assert result.count("### Quick Reference") == 1

    def test_limit_quick_reference_operations(self):
        """Test that quick reference limits to 5 operations."""
        operations = "\n".join([f"### Op{i}\nContent" for i in range(10)])
        text = f"## Section\n{operations}"
        result, count = add_quick_reference(text)
        # Count the operations listed in quick reference
        quick_ref_section = result.split("## Section")[1]
        operation_lines = [l for l in quick_ref_section.split('\n') if l.startswith('- Op')]
        assert len(operation_lines) <= 5


class TestOptimizeDocument:
    def test_optimize_applies_all_transformations(self):
        """Test that optimize_document applies all transformations."""
        text = """## Section
### Subsection
Content

## Background
Background info
"""
        result = optimize_document(text)
        assert "heading_promotion" in result.transformations_applied
        assert "appendix_separation" in result.transformations_applied
        assert "quick_reference" in result.transformations_applied

    def test_optimize_reduces_tokens(self):
        """Test that optimization reduces token count."""
        text = """## Complex Section
### Detailed Subsection One
This is detailed content about subsection one that explains concepts in depth.

### Detailed Subsection Two
This is detailed content about subsection two with more explanation.

### Detailed Subsection Three
Even more detailed content with background information.

## Background Material
This section contains background research and theoretical foundations that explains the history and context.

## Implementation Details
Additional implementation details and edge cases to consider when implementing this solution.
"""
        result = optimize_document(text)
        assert result.optimized_token_count < result.original_token_count
        assert result.reduction_percentage > 0

    def test_optimize_selective_transformations(self):
        """Test applying only specific transformations."""
        text = """## Main
### Sub
Content

## Background
Background
"""
        result = optimize_document(
            text,
            apply_heading_promotion=True,
            apply_appendix_separation=False,
            apply_quick_reference=False,
        )
        assert "heading_promotion" in result.transformations_applied
        assert "appendix_separation" not in result.transformations_applied

    def test_optimize_document_summary(self):
        """Test that OptimizedDocument provides good summary."""
        text = """## Main
### Sub
Content

## Background
Background
"""
        result = optimize_document(text)
        summary = result.summary()
        assert "Token reduction" in summary
        assert "Transformations" in summary
        assert "%" in summary

    def test_preserve_content_integrity(self):
        """Test that optimization preserves main content."""
        main_content = "Important configuration details here"
        text = f"""## Configuration
{main_content}

### Subsection
More details

## Background
Historical context here
"""
        result = optimize_document(text)
        assert main_content in result.optimized_text
