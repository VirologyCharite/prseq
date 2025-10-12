import argparse
import sys
from pathlib import Path

from .fasta import FastaReader, read_fasta
from .fastq import FastqReader, read_fastq


def fasta_info() -> None:
    """Display basic information about a FASTA file or stdin."""
    parser = argparse.ArgumentParser(
        prog="fasta-info",
        description="Display basic information about a FASTA file or stdin",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTA file to analyze (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Expected sequence length hint for optimization (uses internal default if not specified)",
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        records = read_fasta(args.file, sequence_size_hint=args.size_hint)

        source = args.file if args.file else "stdin"
        print(f"Source: {source}")
        print(f"Number of sequences: {len(records)}")

        if records:
            print("First sequence:")
            print(f"  ID: {records[0].id}")
            print(f"  Length: {len(records[0].sequence)} bp")

    except Exception as e:
        print(f"Error reading FASTA input: {e}", file=sys.stderr)
        sys.exit(1)


def fasta_stats() -> None:
    """Calculate statistics for sequences in a FASTA file or stdin."""
    parser = argparse.ArgumentParser(
        prog="fasta-stats",
        description="Calculate statistics for sequences in a FASTA file or stdin",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTA file to analyze (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help=(
            "Expected sequence length hint for optimization (uses internal default "
            "if not specified)"
        ),
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    reader = FastaReader(args.file, sequence_size_hint=args.size_hint)

    total_seqs = 0
    total_length = 0
    min_length: int | None = None
    max_length: int | None = None

    for record in reader:
        total_seqs += 1
        seq_len = len(record.sequence)
        total_length += seq_len

        if min_length is None or seq_len < min_length:
            min_length = seq_len
        if max_length is None or seq_len > max_length:
            max_length = seq_len

    if total_seqs == 0:
        print("No sequences found in input")
        return

    avg_length = total_length / total_seqs

    source = args.file if args.file else "stdin"
    print(f"Statistics for: {source}")
    print(f"  Total sequences: {total_seqs}")
    print(f"  Total length: {total_length:,} bp")
    print(f"  Average length: {avg_length:.1f} bp")
    print(f"  Min length: {min_length:,} bp")
    print(f"  Max length: {max_length:,} bp")


def fasta_filter() -> None:
    """Filter FASTA sequences by minimum length."""
    parser = argparse.ArgumentParser(
        prog="fasta-filter", description="Filter FASTA sequences by minimum length"
    )
    parser.add_argument("min_length", type=int, help="Minimum sequence length to keep")
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTA file to filter (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Expected sequence length hint for optimization (uses internal default if not specified)",
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        reader = FastaReader(args.file, sequence_size_hint=args.size_hint)

        kept = 0
        filtered = 0

        for record in reader:
            if len(record.sequence) >= args.min_length:
                print(f">{record.id}")
                print(record.sequence)
                kept += 1
            else:
                filtered += 1

        print(
            f"# Kept {kept} sequences, filtered {filtered} sequences", file=sys.stderr
        )

    except Exception as e:
        print(f"Error processing FASTA input: {e}", file=sys.stderr)
        sys.exit(1)


def fastq_info() -> None:
    """Display basic information about a FASTQ file or stdin."""
    parser = argparse.ArgumentParser(
        prog="fastq-info",
        description="Display basic information about a FASTQ file or stdin",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTQ file to analyze (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Expected sequence length hint for optimization (uses internal default if not specified)",
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        records = read_fastq(args.file, sequence_size_hint=args.size_hint)

        source = args.file if args.file else "stdin"
        print(f"Source: {source}")
        print(f"Number of sequences: {len(records)}")

        if records:
            print("First sequence:")
            print(f"  ID: {records[0].id}")
            print(f"  Length: {len(records[0].sequence)} bp")
            print(f"  Quality length: {len(records[0].quality)}")

    except Exception as e:
        print(f"Error reading FASTQ input: {e}", file=sys.stderr)
        sys.exit(1)


def fastq_stats() -> None:
    """Calculate statistics for sequences in a FASTQ file or stdin."""
    parser = argparse.ArgumentParser(
        prog="fastq-stats",
        description="Calculate statistics for sequences in a FASTQ file or stdin",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTQ file to analyze (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Expected sequence length hint for optimization (uses internal default if not specified)",
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        reader = FastqReader(args.file, sequence_size_hint=args.size_hint)

        total_seqs = 0
        total_length = 0
        min_length: int | None = None
        max_length: int | None = None

        for record in reader:
            total_seqs += 1
            seq_len = len(record.sequence)
            total_length += seq_len

            if min_length is None or seq_len < min_length:
                min_length = seq_len
            if max_length is None or seq_len > max_length:
                max_length = seq_len

        if total_seqs == 0:
            print("No sequences found in input")
            return

        avg_length = total_length / total_seqs

        source = args.file if args.file else "stdin"
        print(f"Statistics for: {source}")
        print(f"  Total sequences: {total_seqs}")
        print(f"  Total length: {total_length:,} bp")
        print(f"  Average length: {avg_length:.1f} bp")
        print(f"  Min length: {min_length:,} bp")
        print(f"  Max length: {max_length:,} bp")

    except Exception as e:
        print(f"Error processing FASTQ input: {e}", file=sys.stderr)
        sys.exit(1)


def fastq_filter() -> None:
    """Filter FASTQ sequences by minimum length."""
    parser = argparse.ArgumentParser(
        prog="fastq-filter", description="Filter FASTQ sequences by minimum length"
    )
    parser.add_argument("min_length", type=int, help="Minimum sequence length to keep")
    parser.add_argument(
        "file",
        nargs="?",
        help="FASTQ file to filter (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Expected sequence length hint for optimization (uses internal default if not specified)",
    )

    args = parser.parse_args()

    # Check file exists only if not reading from stdin
    if args.file and args.file != "-" and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        reader = FastqReader(args.file, sequence_size_hint=args.size_hint)

        kept = 0
        filtered = 0

        for record in reader:
            if len(record.sequence) >= args.min_length:
                print(f"@{record.id}")
                print(record.sequence)
                print("+")
                print(record.quality)
                kept += 1
            else:
                filtered += 1

        print(
            f"# Kept {kept} sequences, filtered {filtered} sequences", file=sys.stderr
        )

    except Exception as e:
        print(f"Error processing FASTQ input: {e}", file=sys.stderr)
        sys.exit(1)
