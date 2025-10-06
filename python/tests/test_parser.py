"""Tests for the FASTA parser Python bindings."""

import tempfile
from pathlib import Path
from typing import List

import pytest
from prseq import FastaRecord, FastaReader, read_fasta, ZeroCopyFastaReader, read_fasta_zero_copy


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


def test_zero_copy_fasta_reader() -> None:
    """Test the zero-copy FASTA reader."""
    fasta_file = create_test_fasta()
    try:
        reader = ZeroCopyFastaReader(str(fasta_file), sequence_hint=1024)
        records = list(reader)

        assert len(records) == 2

        # Test first record
        header1, seq_lines1, total_len1 = records[0]
        assert isinstance(header1, bytes)
        assert isinstance(seq_lines1, list)
        assert isinstance(total_len1, int)
        assert header1 == b"seq1 description one"
        assert len(seq_lines1) == 2
        assert seq_lines1[0] == b"ATCGATCG"
        assert seq_lines1[1] == b"GCTAGCTA"
        assert total_len1 == 16

        # Test second record
        header2, seq_lines2, total_len2 = records[1]
        assert header2 == b"seq2 description two"
        assert len(seq_lines2) == 1
        assert seq_lines2[0] == b"GGGGCCCC"
        assert total_len2 == 8

    finally:
        fasta_file.unlink()


def test_read_fasta_zero_copy_function() -> None:
    """Test the zero-copy convenience function."""
    fasta_file = create_test_fasta()
    try:
        records = read_fasta_zero_copy(str(fasta_file), sequence_hint=1024)

        assert len(records) == 2
        assert isinstance(records[0][0], bytes)
        assert isinstance(records[0][1], list)
        assert isinstance(records[0][2], int)
        assert records[0][0] == b"seq1 description one"
        assert records[0][2] == 16
        assert records[1][0] == b"seq2 description two"
        assert records[1][2] == 8

    finally:
        fasta_file.unlink()


def test_zero_copy_sequence_reconstruction() -> None:
    """Test reconstructing sequences from zero-copy data."""
    fasta_file = create_test_fasta()
    try:
        reader = ZeroCopyFastaReader(str(fasta_file))

        for header_bytes, sequence_lines, total_length in reader:
            # Convert back to strings
            header = header_bytes.decode('utf-8')
            sequence = b''.join(sequence_lines).decode('utf-8')

            assert isinstance(header, str)
            assert isinstance(sequence, str)
            assert isinstance(total_length, int)
            assert len(sequence) == total_length

            if "seq1" in header:
                assert sequence == "ATCGATCGGCTAGCTA"
                assert total_length == 16
            elif "seq2" in header:
                assert sequence == "GGGGCCCC"
                assert total_length == 8

    finally:
        fasta_file.unlink()


def test_zero_copy_vs_regular_reader() -> None:
    """Compare zero-copy reader results with regular reader."""
    fasta_file = create_test_fasta()
    try:
        # Read with regular reader
        regular_records = read_fasta(str(fasta_file))

        # Read with zero-copy reader
        zero_copy_records = read_fasta_zero_copy(str(fasta_file))

        assert len(regular_records) == len(zero_copy_records)

        for regular, (header_bytes, seq_lines, total_length) in zip(regular_records, zero_copy_records):
            # Convert zero-copy to strings
            header = header_bytes.decode('utf-8')
            sequence = b''.join(seq_lines).decode('utf-8')

            assert regular.header == header
            assert regular.sequence == sequence
            assert len(regular.sequence) == total_length

    finally:
        fasta_file.unlink()


def test_zero_copy_large_sequence_hint() -> None:
    """Test zero-copy reader with large sequence hint."""
    fasta_file = create_test_fasta()
    try:
        reader = ZeroCopyFastaReader(str(fasta_file), sequence_hint=50000)
        records = list(reader)

        assert len(records) == 2
        assert records[0][0] == b"seq1 description one"
        assert records[0][2] == 16  # total length

    finally:
        fasta_file.unlink()


def test_zero_copy_memory_efficiency() -> None:
    """Test that zero-copy reader returns actual bytes objects."""
    fasta_file = create_test_fasta()
    try:
        records = read_fasta_zero_copy(str(fasta_file))

        for header_bytes, seq_lines, total_length in records:
            # Verify these are actual bytes objects, not strings
            assert type(header_bytes) is bytes
            assert type(seq_lines) is list
            assert type(total_length) is int
            for line in seq_lines:
                assert type(line) is bytes

    finally:
        fasta_file.unlink()
