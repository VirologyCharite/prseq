#!/usr/bin/env python3
"""Generate synthetic FASTA and FASTQ files for benchmarking.

Creates test files with:
- 250,000 sequences
- Variable ID lengths (10-100 characters)
- Variable sequence lengths (100-200,000 characters)
- Reproducible via seed parameter
"""

import argparse
import random
from pathlib import Path


def generate_random_sequence(length: int, bases: str = "ACGT") -> str:
    """Generate a random DNA sequence of given length."""
    return "".join(random.choice(bases) for _ in range(length))


def generate_random_id(length: int) -> str:
    """Generate a random sequence ID of given length."""
    # Start with 'seq' prefix, then random alphanumeric
    prefix = "seq"
    remaining = length - len(prefix)
    if remaining <= 0:
        return prefix[:length]

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    random_part = "".join(random.choice(chars) for _ in range(remaining))
    return prefix + random_part


def generate_quality_string(length: int) -> str:
    """Generate a random quality string (Phred33 scores)."""
    # Quality chars range from '!' (Q=0) to '~' (Q=93)
    # Using range '!' to 'I' (Q=0 to Q=40) for realistic quality scores
    quality_chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHI"
    return "".join(random.choice(quality_chars) for _ in range(length))


def write_wrapped_lines(f: object, text: str, line_length: int) -> int:
    """Write text in wrapped lines of specified length.

    If line_length is -1, write on a single line.
    Returns the number of bytes written.
    """
    if line_length == -1:
        f.write(text + '\n')
        return len(text) + 1

    total_bytes = 0
    for i in range(0, len(text), line_length):
        line = text[i:i + line_length] + '\n'
        f.write(line)
        total_bytes += len(line)
    return total_bytes


def generate_fasta(output_path: Path, num_sequences: int,
                   id_min: int, id_max: int,
                   seq_min: int, seq_max: int,
                   line_length: int = 80) -> int:
    """Generate a FASTA file with specified parameters.

    Returns the total file size in bytes.
    """
    import time

    print(f"Generating FASTA file: {output_path}")
    print(f"  Sequences: {num_sequences:,}")
    print(f"  ID length range: {id_min}-{id_max}")
    print(f"  Sequence length range: {seq_min:,}-{seq_max:,}")
    print(f"  Line length: {line_length if line_length != -1 else 'unlimited'}")

    start_time = time.perf_counter()

    # Pre-generate master ID and sequence strings
    master_id = generate_random_id(id_max)
    master_seq = generate_random_sequence(seq_max)

    total_bytes = 0

    with open(output_path, 'w') as f:
        for i in range(num_sequences):
            if (i + 1) % 10000 == 0:
                print(f"  Generated {i + 1:,} sequences...")

            id_length = random.randint(id_min, id_max)
            seq_length = random.randint(seq_min, seq_max)

            # Use substring of master ID and sequence
            id_start = random.randint(0, id_max - id_length)
            seq_start = random.randint(0, seq_max - seq_length)

            seq_id = master_id[id_start:id_start + id_length]
            sequence = master_seq[seq_start:seq_start + seq_length]

            # Write FASTA record
            header = f">{seq_id}\n"
            f.write(header)
            total_bytes += len(header)

            total_bytes += write_wrapped_lines(f, sequence, line_length)

    elapsed = time.perf_counter() - start_time
    print(f"  Complete! File size: {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"  Generation time: {elapsed:.2f}s")
    return total_bytes


def generate_fastq(output_path: Path, num_sequences: int,
                   id_min: int, id_max: int,
                   seq_min: int, seq_max: int,
                   line_length: int = 80) -> int:
    """Generate a FASTQ file with specified parameters.

    Returns the total file size in bytes.
    """
    import time

    print(f"Generating FASTQ file: {output_path}")
    print(f"  Sequences: {num_sequences:,}")
    print(f"  ID length range: {id_min}-{id_max}")
    print(f"  Sequence length range: {seq_min:,}-{seq_max:,}")
    print(f"  Line length: {line_length if line_length != -1 else 'unlimited'}")

    start_time = time.perf_counter()

    # Pre-generate master ID, sequence, and quality strings
    master_id = generate_random_id(id_max)
    master_seq = generate_random_sequence(seq_max)
    master_qual = generate_quality_string(seq_max)

    total_bytes = 0

    with open(output_path, 'w') as f:
        for i in range(num_sequences):
            if (i + 1) % 10000 == 0:
                print(f"  Generated {i + 1:,} sequences...")

            id_length = random.randint(id_min, id_max)
            seq_length = random.randint(seq_min, seq_max)

            # Use substring of master ID, sequence, and quality
            id_start = random.randint(0, id_max - id_length)
            seq_start = random.randint(0, seq_max - seq_length)
            qual_start = random.randint(0, seq_max - seq_length)

            seq_id = master_id[id_start:id_start + id_length]
            sequence = master_seq[seq_start:seq_start + seq_length]
            quality = master_qual[qual_start:qual_start + seq_length]

            # Write FASTQ record
            header = f"@{seq_id}\n"
            f.write(header)
            total_bytes += len(header)

            total_bytes += write_wrapped_lines(f, sequence, line_length)

            plus_line = "+\n"
            f.write(plus_line)
            total_bytes += len(plus_line)

            total_bytes += write_wrapped_lines(f, quality, line_length)

    elapsed = time.perf_counter() - start_time
    print(f"  Complete! File size: {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"  Generation time: {elapsed:.2f}s")
    return total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic FASTA and FASTQ files for benchmarking"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--sequences",
        type=int,
        default=250000,
        help="Number of sequences to generate (default: 250,000)"
    )
    parser.add_argument(
        "--id-min",
        type=int,
        default=10,
        help="Minimum ID length (default: 10)"
    )
    parser.add_argument(
        "--id-max",
        type=int,
        default=100,
        help="Maximum ID length (default: 100)"
    )
    parser.add_argument(
        "--seq-min",
        type=int,
        default=100,
        help="Minimum sequence length (default: 100)"
    )
    parser.add_argument(
        "--seq-max",
        type=int,
        default=200000,
        help="Maximum sequence length (default: 200,000)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory (default: data)"
    )
    parser.add_argument(
        "--fasta",
        action="store_true",
        help="Generate only FASTA file"
    )
    parser.add_argument(
        "--fastq",
        action="store_true",
        help="Generate only FASTQ file"
    )
    parser.add_argument(
        "--line-length",
        type=int,
        default=80,
        help="Line length for sequences/quality (-1 for unlimited, default: 80)"
    )

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate files
    if not args.fastq:
        fasta_path = args.output_dir / "benchmark.fasta"
        generate_fasta(
            fasta_path,
            args.sequences,
            args.id_min,
            args.id_max,
            args.seq_min,
            args.seq_max,
            args.line_length
        )

    if not args.fasta:
        # Use same seed for FASTQ to get similar (but not identical) data
        if args.seed is not None:
            random.seed(args.seed + 1)

        fastq_path = args.output_dir / "benchmark.fastq"
        generate_fastq(
            fastq_path,
            args.sequences,
            args.id_min,
            args.id_max,
            args.seq_min,
            args.seq_max,
            args.line_length
        )

    print("\nGeneration complete!")


if __name__ == "__main__":
    main()
