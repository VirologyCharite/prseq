#!/usr/bin/env python3
"""Benchmark the Rust/Python prseq implementation."""

import sys
import time
from pathlib import Path

from prseq.fasta import FastaReader
from prseq.fastq import FastqReader


def benchmark_fasta(filepath: Path, sequence_size_hint: int = None) -> dict:
    """Benchmark FASTA reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    reader = FastaReader(str(filepath), sequence_size_hint=sequence_size_hint)
    for record in reader:
        count += 1
        sequence_bases += len(record.sequence)

    elapsed = time.perf_counter() - start

    # Use file size for throughput calculation
    file_size = filepath.stat().st_size

    return {
        'count': count,
        'total_bases': file_size,
        'sequence_bases': sequence_bases,
        'elapsed': elapsed,
        'throughput_mb_s': (file_size / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def benchmark_fastq(filepath: Path, sequence_size_hint: int = None) -> dict:
    """Benchmark FASTQ reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    reader = FastqReader.from_file(str(filepath), sequence_size_hint=sequence_size_hint)
    for record in reader:
        count += 1
        sequence_bases += len(record.sequence)

    elapsed = time.perf_counter() - start

    # Use file size for throughput calculation
    file_size = filepath.stat().st_size

    return {
        'count': count,
        'total_bases': file_size,
        'sequence_bases': sequence_bases,
        'elapsed': elapsed,
        'throughput_mb_s': (file_size / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: bench_rust_python.py <fasta|fastq_file> [sequence_size_hint]", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    sequence_size_hint = None
    if len(sys.argv) == 3:
        sequence_size_hint = int(sys.argv[2])

    # Determine file type
    if filepath.suffix.lower() in ['.fasta', '.fa', '.fna']:
        results = benchmark_fasta(filepath, sequence_size_hint)
    elif filepath.suffix.lower() in ['.fastq', '.fq']:
        results = benchmark_fastq(filepath, sequence_size_hint)
    else:
        print(f"Error: Unknown file type: {filepath.suffix}", file=sys.stderr)
        sys.exit(1)

    # Print results
    print("Rust/Python (prseq)")
    print(f"  Sequences: {results['count']:,}")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
