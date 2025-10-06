"""Tests for the FASTA parser Python bindings."""

import tempfile
from pathlib import Path
from typing import List

import pytest
from prseq import FastaRecord, FastaReader, read_fasta


def create_test_fasta() -> Path:
    """Create a temporary FASTA file for testing."""
    content = """>seq1 description one
ATCGATCG
GCTAGCTA
>seq2 description two
GGGGCCCC
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
        f.write(content)
        return Path(f.name)


def test_fasta_reader_iterator() -> None:
    """Test iterating over FASTA records."""
    fasta_file = create_test_fasta()
    try:
        reader = FastaReader(str(fasta_file))
        records: List[FastaRecord] = list(reader)
        
        assert len(records) == 2
        assert records[0].header == "seq1 description one"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].header == "seq2 description two"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_read_fasta_convenience() -> None:
    """Test the convenience function to read all records."""
    fasta_file = create_test_fasta()
    try:
        records = read_fasta(str(fasta_file))
        
        assert len(records) == 2
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert isinstance(records[0], FastaRecord)
    finally:
        fasta_file.unlink()


def test_file_not_found() -> None:
    """Test error handling for missing files."""
    with pytest.raises(IOError):
        FastaReader("nonexistent.fasta")


def test_fasta_record_tuple() -> None:
    """Test that FastaRecord behaves as a NamedTuple."""
    fasta_file = create_test_fasta()
    try:
        records = read_fasta(str(fasta_file))
        record = records[0]
        
        # Test tuple unpacking
        header, sequence = record
        assert header == "seq1 description one"
        assert sequence == "ATCGATCGGCTAGCTA"
        
        # Test attribute access
        assert record.header == header
        assert record.sequence == sequence
    finally:
        fasta_file.unlink()


def test_multiple_iterations() -> None:
    """Test that we can iterate multiple times."""
    fasta_file = create_test_fasta()
    try:
        records1 = read_fasta(str(fasta_file))
        records2 = read_fasta(str(fasta_file))
        
        assert records1 == records2
    finally:
        fasta_file.unlink()


