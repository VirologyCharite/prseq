#!/usr/bin/env python3
"""Benchmark pure Python FASTA/FASTQ implementations."""

import sys
import time
from pathlib import Path
from typing import Iterator, NamedTuple


class FastaRecord(NamedTuple):
    """FASTA sequence record."""
    id: str
    sequence: str


class FastqRecord(NamedTuple):
    """FASTQ sequence record."""
    id: str
    sequence: str
    quality: str


def read_fasta(filepath: Path) -> Iterator[FastaRecord]:
    """Pure Python FASTA reader."""
    with open(filepath, 'r') as f:
        current_id = None
        current_seq = []

        for line in f:
            line = line.rstrip('\n\r')

            if line.startswith('>'):
                # Yield previous record if exists
                if current_id is not None:
                    yield FastaRecord(id=current_id, sequence=''.join(current_seq))

                # Start new record
                current_id = line[1:]  # Remove '>'
                current_seq = []
            else:
                current_seq.append(line)

        # Yield final record
        if current_id is not None:
            yield FastaRecord(id=current_id, sequence=''.join(current_seq))


def read_fastq(filepath: Path) -> Iterator[FastqRecord]:
    """Pure Python FASTQ reader."""
    with open(filepath, 'r') as f:
        while True:
            # Read ID line
            id_line = f.readline()
            if not id_line:
                break  # EOF

            id_str = id_line.rstrip('\n\r')[1:]  # Remove '@'

            # Read sequence lines until we hit '+'
            seq_parts = []
            while True:
                line = f.readline()
                if not line or line.startswith('+'):
                    break
                seq_parts.append(line.rstrip('\n\r'))

            seq_str = ''.join(seq_parts)

            # Read quality lines (same number of chars as sequence)
            qual_parts = []
            qual_length = 0
            while qual_length < len(seq_str):
                line = f.readline()
                line_stripped = line.rstrip('\n\r')
                qual_parts.append(line_stripped)
                qual_length += len(line_stripped)

            qual_str = ''.join(qual_parts)

            yield FastqRecord(id=id_str, sequence=seq_str, quality=qual_str)


def benchmark_fasta(filepath: Path) -> dict:
    """Benchmark FASTA reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    for record in read_fasta(filepath):
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


def benchmark_fastq(filepath: Path) -> dict:
    """Benchmark FASTQ reading."""
    start = time.perf_counter()

    count = 0
    sequence_bases = 0

    for record in read_fastq(filepath):
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
    if len(sys.argv) != 2:
        print("Usage: bench_pure_python.py <fasta|fastq_file>", file=sys.stderr)
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
    print("Pure Python")
    print(f"  Sequences: {results['count']:,}")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
