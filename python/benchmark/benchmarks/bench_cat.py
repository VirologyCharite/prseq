#!/usr/bin/env python3
"""Benchmark the 'cat' utility by piping to /dev/null."""

import subprocess
import sys
import time
from pathlib import Path


def benchmark_file(filepath: Path) -> dict:
    """Benchmark cat file > /dev/null."""
    start = time.perf_counter()

    # Run cat and pipe to /dev/null
    with open('/dev/null', 'w') as devnull:
        result = subprocess.run(
            ['cat', str(filepath)],
            stdout=devnull,
            stderr=subprocess.PIPE,
            text=True
        )

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"Error running cat: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Get file size for throughput calculation
    file_size = filepath.stat().st_size

    return {
        'count': 0,  # cat doesn't count sequences
        'total_bases': file_size,  # Use file size as proxy
        'elapsed': elapsed,
        'throughput_mb_s': (file_size / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: bench_cat.py <fasta|fastq_file>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    results = benchmark_file(filepath)

    # Print results
    print(f"cat > /dev/null")
    print(f"  Sequences: 0")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
