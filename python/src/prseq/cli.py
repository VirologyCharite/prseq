"""Command-line interface for FASTA parser."""

import sys
from pathlib import Path
from typing import Optional

from prseq import FastaReader, read_fasta


def info() -> None:
    """Display basic information about a FASTA file.
    
    Usage: fasta-info <file.fasta>
    """
    if len(sys.argv) != 2:
        print("Usage: fasta-info <file.fasta>", file=sys.stderr)
        sys.exit(1)
    
    fasta_path = sys.argv[1]
    
    if not Path(fasta_path).exists():
        print(f"Error: File not found: {fasta_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        records = read_fasta(fasta_path)
        
        print(f"File: {fasta_path}")
        print(f"Number of sequences: {len(records)}")
        
        if records:
            print(f"First sequence:")
            print(f"  Header: {records[0].header}")
            print(f"  Length: {len(records[0].sequence)} bp")
            
    except Exception as e:
        print(f"Error reading FASTA file: {e}", file=sys.stderr)
        sys.exit(1)


def stats() -> None:
    """Calculate statistics for sequences in a FASTA file.
    
    Usage: fasta-stats <file.fasta>
    """
    if len(sys.argv) != 2:
        print("Usage: fasta-stats <file.fasta>", file=sys.stderr)
        sys.exit(1)
    
    fasta_path = sys.argv[1]
    
    if not Path(fasta_path).exists():
        print(f"Error: File not found: {fasta_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        reader = FastaReader(fasta_path)
        
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
        
        print(f"Statistics for: {fasta_path}")
        print(f"  Total sequences: {total_seqs}")
        print(f"  Total length: {total_length:,} bp")
        print(f"  Average length: {avg_length:.1f} bp")
        print(f"  Min length: {min_length:,} bp")
        print(f"  Max length: {max_length:,} bp")
        
    except Exception as e:
        print(f"Error processing FASTA file: {e}", file=sys.stderr)
        sys.exit(1)


def filter_cmd() -> None:
    """Filter FASTA sequences by minimum length.
    
    Usage: fasta-filter <file.fasta> <min_length>
    """
    if len(sys.argv) != 3:
        print("Usage: fasta-filter <file.fasta> <min_length>", file=sys.stderr)
        sys.exit(1)
    
    fasta_path = sys.argv[1]
    
    try:
        min_length = int(sys.argv[2])
    except ValueError:
        print(f"Error: min_length must be an integer", file=sys.stderr)
        sys.exit(1)
    
    if not Path(fasta_path).exists():
        print(f"Error: File not found: {fasta_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        reader = FastaReader(fasta_path)
        
        kept = 0
        filtered = 0
        
        for record in reader:
            if len(record.sequence) >= min_length:
                print(f">{record.header}")
                print(record.sequence)
                kept += 1
            else:
                filtered += 1
        
        print(f"# Kept {kept} sequences, filtered {filtered} sequences", file=sys.stderr)
        
    except Exception as e:
        print(f"Error processing FASTA file: {e}", file=sys.stderr)
        sys.exit(1)
