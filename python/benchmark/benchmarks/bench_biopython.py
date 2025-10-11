#!/usr/bin/env python3
"""Benchmark the BioPython implementation."""

import sys
import time
from pathlib import Path

from Bio import SeqIO


def benchmark_fasta(filepath: Path) -> dict:
    """Benchmark FASTA reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    for record in SeqIO.parse(str(filepath), "fasta"):
        count += 1
        sequence_bases += len(record.seq)

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


def benchmark_fastq(filepath: Path) -> dict:
    """Benchmark FASTQ reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    for record in SeqIO.parse(str(filepath), "fastq"):
        count += 1
        sequence_bases += len(record.seq)

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
    if len(sys.argv) != 2:
        print("Usage: bench_biopython.py <fasta|fastq_file>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Determine file type
    if filepath.suffix.lower() in ['.fasta', '.fa', '.fna']:
        results = benchmark_fasta(filepath)
    elif filepath.suffix.lower() in ['.fastq', '.fq']:
        results = benchmark_fastq(filepath)
    else:
        print(f"Error: Unknown file type: {filepath.suffix}", file=sys.stderr)
        sys.exit(1)

    # Print results
    print("BioPython")
    print(f"  Sequences: {results['count']:,}")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
