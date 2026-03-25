"""Benchmarking tool for RAG optimization."""

import os
from pathlib import Path
from typing import List

from .analyzer import compare_before_after, count_tokens
from .models import TokenComparison
from .optimizer import optimize_document


def find_before_after_pairs(examples_dir: str = "examples") -> List[tuple]:
    """
    Find before/after markdown file pairs in examples directory.

    Looks for files matching pattern: before_*.md and after_*.md

    Args:
        examples_dir: Directory containing example files

    Returns:
        List of (before_path, after_path, name) tuples
    """
    examples_path = Path(examples_dir)
    if not examples_path.exists():
        return []

    pairs = []
    before_files = sorted(examples_path.glob("before_*.md"))

    for before_file in before_files:
        name = before_file.name.replace("before_", "").replace(".md", "")
        after_file = examples_path / f"after_{name}.md"

        if after_file.exists():
            pairs.append((str(before_file), str(after_file), name))

    return pairs


def benchmark_examples(examples_dir: str = "examples") -> None:
    """
    Run benchmarks on all before/after examples.

    Prints comparison table with token reductions.

    Args:
        examples_dir: Directory containing example files
    """
    pairs = find_before_after_pairs(examples_dir)

    if not pairs:
        print(f"No before/after pairs found in {examples_dir}/")
        print("Expected files: before_*.md and after_*.md")
        return

    print("RAG Optimization Benchmark Results")
    print("=" * 80)
    print(f"{'Document':<30} {'Before':<12} {'After':<12} {'Reduction':<15} {'%':<8}")
    print("-" * 80)

    comparisons = []

    for before_path, after_path, name in pairs:
        with open(before_path, 'r') as f:
            before_text = f.read()

        with open(after_path, 'r') as f:
            after_text = f.read()

        before_tokens = count_tokens(before_text)
        after_tokens = count_tokens(after_text)
        reduction = before_tokens - after_tokens
        reduction_pct = (reduction / before_tokens * 100) if before_tokens > 0 else 0

        comparison = TokenComparison(
            document_name=name,
            before_tokens=before_tokens,
            after_tokens=after_tokens,
            reduction_tokens=reduction,
            reduction_percentage=reduction_pct,
        )
        comparisons.append(comparison)

        row = comparison.to_table_row()
        print(f"{row[0]:<30} {row[1]:<12} {row[2]:<12} {row[3]:<15} {row[4]:<8}")

    # Print summary
    print("-" * 80)

    if comparisons:
        total_before = sum(c.before_tokens for c in comparisons)
        total_after = sum(c.after_tokens for c in comparisons)
        total_reduction = total_before - total_after
        avg_reduction_pct = sum(c.reduction_percentage for c in comparisons) / len(comparisons)

        print(f"{'TOTAL':<30} {total_before:<12} {total_after:<12} {total_reduction:<15} {avg_reduction_pct:.1f}%")
        print("\n" + "=" * 80)
        print(f"Average reduction: {avg_reduction_pct:.1f}%")
        print(f"Total tokens saved: {total_reduction} ({100-total_after/total_before*100:.1f}% of original)")


def benchmark_single_optimization(document_path: str, output_report: bool = False) -> None:
    """
    Run optimization on a single document and report results.

    Args:
        document_path: Path to markdown file
        output_report: Print detailed report
    """
    if not os.path.exists(document_path):
        print(f"File not found: {document_path}")
        return

    with open(document_path, 'r') as f:
        text = f.read()

    print(f"Optimizing: {document_path}")
    print("=" * 60)

    result = optimize_document(text)

    print(result.summary())

    if output_report:
        output_dir = Path(document_path).parent
        base_name = Path(document_path).stem
        optimized_path = output_dir / f"{base_name}_optimized.md"

        with open(optimized_path, 'w') as f:
            f.write(result.optimized_text)

        print(f"\nOptimized document saved to: {optimized_path}")


if __name__ == "__main__":
    benchmark_examples()
