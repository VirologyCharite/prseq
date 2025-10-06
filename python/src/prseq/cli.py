import argparse
import sys
from pathlib import Path
from typing import Optional

from prseq import FastaReader, read_fasta


def info() -> None:
    """Display basic information about a FASTA file."""
    parser = argparse.ArgumentParser(
        prog='fasta-info',
        description='Display basic information about a FASTA file'
    )
    parser.add_argument('file', help='FASTA file to analyze')
    parser.add_argument(
        '--size-hint',
        type=int,
        help='Expected sequence length hint for optimization (uses internal default if not specified)'
    )

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        records = read_fasta(args.file, sequence_size_hint=args.size_hint)

        print(f"File: {args.file}")
        print(f"Number of sequences: {len(records)}")

        if records:
            print(f"First sequence:")
            print(f"  Header: {records[0].header}")
            print(f"  Length: {len(records[0].sequence)} bp")

    except Exception as e:
        print(f"Error reading FASTA file: {e}", file=sys.stderr)
        sys.exit(1)


def stats() -> None:
    """Calculate statistics for sequences in a FASTA file."""
    parser = argparse.ArgumentParser(
        prog='fasta-stats',
        description='Calculate statistics for sequences in a FASTA file'
    )
    parser.add_argument('file', help='FASTA file to analyze')
    parser.add_argument(
        '--size-hint',
        type=int,
        help='Expected sequence length hint for optimization (uses internal default if not specified)'
    )

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        reader = FastaReader(args.file, sequence_size_hint=args.size_hint)

        total_seqs = 0
        total_length = 0
        min_length: Optional[int] = None
        max_length: Optional[int] = None

        for record in reader:
            total_seqs += 1
            seq_len = len(record.sequence)
            total_length += seq_len

            if min_length is None or seq_len < min_length:
                min_length = seq_len
            if max_length is None or seq_len > max_length:
                max_length = seq_len

        if total_seqs == 0:
            print("No sequences found in file")
            return

        avg_length = total_length / total_seqs

        print(f"Statistics for: {args.file}")
        print(f"  Total sequences: {total_seqs}")
        print(f"  Total length: {total_length:,} bp")
        print(f"  Average length: {avg_length:.1f} bp")
        print(f"  Min length: {min_length:,} bp")
        print(f"  Max length: {max_length:,} bp")

    except Exception as e:
        print(f"Error processing FASTA file: {e}", file=sys.stderr)
        sys.exit(1)




def filter_cmd() -> None:
    """Filter FASTA sequences by minimum length."""
    parser = argparse.ArgumentParser(
        prog='fasta-filter',
        description='Filter FASTA sequences by minimum length'
    )
    parser.add_argument('file', help='FASTA file to filter')
    parser.add_argument('min_length', type=int, help='Minimum sequence length to keep')
    parser.add_argument(
        '--size-hint',
        type=int,
        help='Expected sequence length hint for optimization (uses internal default if not specified)'
    )

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        reader = FastaReader(args.file, sequence_size_hint=args.size_hint)

        kept = 0
        filtered = 0

        for record in reader:
            if len(record.sequence) >= args.min_length:
                print(f">{record.header}")
                print(record.sequence)
                kept += 1
            else:
                filtered += 1

        print(f"# Kept {kept} sequences, filtered {filtered} sequences", file=sys.stderr)

    except Exception as e:
        print(f"Error processing FASTA file: {e}", file=sys.stderr)
        sys.exit(1)
