#!/usr/bin/env python3
"""Benchmark the C implementation via subprocess."""

import subprocess
import sys
import time
from pathlib import Path


def benchmark_file(filepath: Path, executable: Path) -> dict:
    """Benchmark reading via C executable."""
    start = time.perf_counter()

    result = subprocess.run(
        [str(executable), str(filepath)],
        capture_output=True,
        text=True
    )

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"Error running {executable}: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Parse output to extract stats
    count = 0
    total_bases = 0

    for line in result.stdout.split('\n'):
        if 'sequences:' in line.lower():
            # Format: "Total sequences: 100"
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    count = int(parts[1].strip().split()[0].replace(',', ''))
                except ValueError:
                    pass
        elif 'processed' in line.lower() and 'sequences' in line.lower():
            # Format: "Processed 100000 sequences"
            try:
                words = line.split()
                for i, word in enumerate(words):
                    if word.lower() == 'sequences' and i > 0:
                        count = int(words[i-1].replace(',', ''))
                        break
            except (ValueError, IndexError):
                pass
        elif 'total bases:' in line.lower() or 'total sequence length:' in line.lower():
            # Extract total bases
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    total_bases = int(parts[1].strip().split()[0].replace(',', ''))
                except ValueError:
                    pass

    # Use file size for throughput calculation
    file_size = filepath.stat().st_size

    return {
        'count': count,
        'total_bases': file_size,
        'sequence_bases': total_bases,
        'elapsed': elapsed,
        'throughput_mb_s': (file_size / 1024 / 1024) / elapsed if elapsed > 0 else 0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: bench_c.py <fasta|fastq_file>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Determine executable based on file type
    c_dir = Path(__file__).parent.parent.parent.parent / "c"

    if filepath.suffix.lower() in ['.fasta', '.fa', '.fna']:
        executable = c_dir / "fasta_reader"
    elif filepath.suffix.lower() in ['.fastq', '.fq']:
        executable = c_dir / "fastq_reader"
    else:
        print(f"Error: Unknown file type: {filepath.suffix}", file=sys.stderr)
        sys.exit(1)

    if not executable.exists():
        print(f"Error: C executable not found: {executable}", file=sys.stderr)
        print(f"Please build it with: cd {c_dir} && make", file=sys.stderr)
        sys.exit(1)

    results = benchmark_file(filepath, executable)

    # Print extra info for debugging
    if 'sequence_bases' in results:
        print(f"  Sequence bases: {results['sequence_bases']:,}", file=sys.stderr)

    # Print results
    print(f"C")
    print(f"  Sequences: {results['count']:,}")
    print(f"  Total bases: {results['total_bases']:,}")
    print(f"  Time: {results['elapsed']:.3f}s")
    print(f"  Throughput: {results['throughput_mb_s']:.2f} MB/s")


if __name__ == "__main__":
    main()
