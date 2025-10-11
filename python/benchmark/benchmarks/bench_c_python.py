#!/usr/bin/env python3
"""Benchmark the C/Python implementation using Python C extension."""

import sys
import time
from pathlib import Path

# Add the c directory to the path to import the prseq_c module
c_dir = Path(__file__).parent.parent.parent.parent / "c"
sys.path.insert(0, str(c_dir))

try:
    import prseq_c
except ImportError as e:
    print(f"Error: Failed to import prseq_c module: {e}", file=sys.stderr)
    print(f"Please build the C extension with: cd {c_dir} && python setup.py build_ext --inplace", file=sys.stderr)
    sys.exit(1)


def benchmark_fasta(filepath: Path) -> dict:
    """Benchmark FASTA reading."""
    start = time.perf_counter()

    count = 0
    total_bases = 0

    reader = prseq_c.FastaReader(str(filepath))
    for record_id, sequence in reader:
        count += 1
        total_bases += len(sequence)

    elapsed = time.perf_counter() - start

    return {
        'count': count,
        'total_bases': total_bases,
        'elapsed': elapsed,
        'throughput_mb_s': (total_bases / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def benchmark_fastq(filepath: Path) -> dict:
    """Benchmark FASTQ reading."""
    start = time.perf_counter()

    count = 0
    total_bases = 0

    reader = prseq_c.FastqReader(str(filepath))
    for record_id, sequence, quality in reader:
        count += 1
        total_bases += len(sequence)

    elapsed = time.perf_counter() - start

    return {
        'count': count,
        'total_bases': total_bases,
        'elapsed': elapsed,
        'throughput_mb_s': (total_bases / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: bench_c_python.py <fasta|fastq_file>", file=sys.stderr)
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
    print(f"C/Python")
    print(f"  Sequences: {results['count']:,}")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
