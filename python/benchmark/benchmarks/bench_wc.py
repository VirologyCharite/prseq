#!/usr/bin/env python3
"""Benchmark the 'wc -l' utility."""

import subprocess
import sys
import time
from pathlib import Path


def benchmark_file(filepath: Path) -> dict:
    """Benchmark wc -l file."""
    start = time.perf_counter()

    # Run wc -l
    result = subprocess.run(
        ['wc', '-l', str(filepath)],
        capture_output=True,
        text=True
    )

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"Error running wc: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Parse line count from output
    line_count = 0
    try:
        # wc -l output format: "  123456 filename"
        line_count = int(result.stdout.strip().split()[0])
    except (ValueError, IndexError):
        print(f"Error parsing wc output: {result.stdout}", file=sys.stderr)

    # Get file size for throughput calculation
    file_size = filepath.stat().st_size

    return {
        'count': line_count,
        'total_bases': file_size,  # Use file size as proxy
        'elapsed': elapsed,
        'throughput_mb_s': (file_size / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: bench_wc.py <fasta|fastq_file>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    results = benchmark_file(filepath)

    # Print results
    print(f"wc -l")
    print(f"  Sequences: 0")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
