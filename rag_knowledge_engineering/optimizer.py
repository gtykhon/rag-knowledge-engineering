"""Document restructuring transformations for RAG optimization."""

import re
from typing import List, Tuple

from .models import OptimizedDocument


def promote_headings(text: str) -> Tuple[str, int]:
    """
    Promote nested H3/H4/H5 headings to H2 level.

    This flattens hierarchy so that heading-based chunking creates
    independent, retrievable units instead of nested subtrees.

    Args:
        text: Markdown text with nested headings

    Returns:
        Tuple of (transformed_text, count_of_headings_promoted)
    """
    lines = text.split('\n')
    promoted_count = 0
    result = []

    for line in lines:
        # Match H3, H4, H5 headings
        match = re.match(r'^(#{3,5})\s+(.+)$', line)

        if match:
            promoted_count += 1
            # Replace with H2
            result.append(f"## {match.group(2)}")
        else:
            result.append(line)

    return '\n'.join(result), promoted_count


def separate_appendix(text: str) -> Tuple[str, int]:
    """
    Move research evidence, theory, and background sections to appendix.

    Identifies sections matching patterns like "Background", "Theory",
    "Research", "Implementation Details", "Edge Cases" and moves them
    to an "Appendix" section at the end.

    Args:
        text: Markdown text with mixed content

    Returns:
        Tuple of (transformed_text, count_of_sections_moved)
    """
    appendix_patterns = [
        r'^## Background',
        r'^## Theory',
        r'^## Research',
        r'^## Implementation Details',
        r'^## Edge Cases',
        r'^## Proof',
        r'^## Citations',
        r'^## Reference',
        r'^## Historical Context',
    ]

    lines = text.split('\n')
    main_section = []
    appendix_section = []
    moved_count = 0
    current_section = None

    for i, line in enumerate(lines):
        # Check if this line starts an appendix pattern
        is_appendix = any(re.match(pattern, line) for pattern in appendix_patterns)

        if is_appendix:
            moved_count += 1
            current_section = 'appendix'
            appendix_section.append(line)
        elif line.startswith('## ') and current_section == 'appendix':
            # New H2 section after appendix started - likely back to main content
            # For safety, only move if explicitly in patterns
            main_section.append(line)
            current_section = 'main'
        elif current_section == 'appendix' or (current_section is None and is_appendix):
            appendix_section.append(line)
        else:
            main_section.append(line)
            if not line.strip():  # Reset on blank lines if no section
                if current_section is None:
                    current_section = 'main'

    # Build final document
    result = main_section

    if appendix_section:
        # Clean up trailing whitespace
        while result and not result[-1].strip():
            result.pop()

        result.append('\n## Appendix\n')
        result.extend(appendix_section)

    return '\n'.join(result), moved_count


def add_quick_reference(text: str, sections: List[str] | None = None) -> Tuple[str, int]:
    """
    Add quick-reference summaries at the top of sections.

    Creates compact H3 "Quick Reference" sections with operation lists
    for each major H2 section identified.

    Args:
        text: Markdown text
        sections: List of section names to add references to (default: auto-detect)

    Returns:
        Tuple of (transformed_text, count_of_references_added)
    """
    lines = text.split('\n')
    result = []
    quick_refs_added = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Detect H2 section headers
        if re.match(r'^## .+$', line):
            section_title = re.match(r'^## (.+)$', line).group(1)

            # Skip if already has quick reference
            if i + 1 < len(lines) and '### Quick Reference' in lines[i + 1]:
                i += 1
                continue

            # Only add for specified sections or all if not specified
            if sections is None or section_title in sections:
                # Look ahead to find operation headings (H3s)
                operations = []
                j = i + 1
                while j < len(lines) and not re.match(r'^## ', lines[j]):
                    if re.match(r'^### (.+)$', lines[j]):
                        op_match = re.match(r'^### (.+)$', lines[j])
                        operations.append(op_match.group(1))
                    j += 1

                if operations:
                    # Add quick reference
                    result.append('')
                    result.append('### Quick Reference')
                    result.append('')
                    for op in operations[:5]:  # Limit to 5 operations
                        result.append(f'- {op}')
                    result.append('')
                    quick_refs_added += 1

        i += 1

    return '\n'.join(result), quick_refs_added


def optimize_document(
    text: str,
    apply_heading_promotion: bool = True,
    apply_appendix_separation: bool = True,
    apply_quick_reference: bool = True,
) -> OptimizedDocument:
    """
    Apply all optimization strategies to a document.

    Each transformation is composable and can be applied independently.

    Args:
        text: Original markdown text
        apply_heading_promotion: Promote H3/H4/H5 to H2
        apply_appendix_separation: Move research/theory to appendix
        apply_quick_reference: Add quick-reference summaries

    Returns:
        OptimizedDocument with before/after metrics and transformations applied
    """
    from .analyzer import count_tokens

    original_token_count = count_tokens(text)
    optimized_text = text
    transformations_applied = []
    promoted_headings_count = 0
    appendix_moved_count = 0
    quick_refs_added = 0

    # Apply heading promotion
    if apply_heading_promotion:
        optimized_text, promoted_headings_count = promote_headings(optimized_text)
        transformations_applied.append("heading_promotion")

    # Apply appendix separation
    if apply_appendix_separation:
        optimized_text, appendix_moved_count = separate_appendix(optimized_text)
        transformations_applied.append("appendix_separation")

    # Apply quick reference
    if apply_quick_reference:
        optimized_text, quick_refs_added = add_quick_reference(optimized_text)
        transformations_applied.append("quick_reference")

    optimized_token_count = count_tokens(optimized_text)
    reduction = original_token_count - optimized_token_count
    reduction_percentage = (reduction / original_token_count * 100) if original_token_count > 0 else 0

    return OptimizedDocument(
        original_text=text,
        optimized_text=optimized_text,
        original_token_count=original_token_count,
        optimized_token_count=optimized_token_count,
        reduction_percentage=reduction_percentage,
        transformations_applied=transformations_applied,
        promoted_headings=promoted_headings_count,
        appendix_moved_sections=appendix_moved_count,
        quick_references_added=quick_refs_added,
    )
