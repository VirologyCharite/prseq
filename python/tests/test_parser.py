"""Tests for the FASTA parser Python bindings."""

import gzip
import bz2
import tempfile
import subprocess
import sys
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


def create_compressed_test_fasta(compression: str) -> Path:
    """Create a compressed FASTA file for testing."""
    content = b""">seq1 compressed test
ATCGATCG
GCTAGCTA
>seq2 another compressed
GGGGCCCC
"""
    if compression == "gzip":
        suffix = ".fasta.gz"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            with gzip.open(f.name, 'wb') as gz_file:
                gz_file.write(content)
            return Path(f.name)
    elif compression == "bz2":
        suffix = ".fasta.bz2"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            with bz2.open(f.name, 'wb') as bz_file:
                bz_file.write(content)
            return Path(f.name)
    else:
        raise ValueError(f"Unsupported compression: {compression}")


def test_gzip_compression() -> None:
    """Test reading gzip-compressed FASTA files."""
    fasta_file = create_compressed_test_fasta("gzip")
    try:
        reader = FastaReader(str(fasta_file))
        records: List[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].header == "seq1 compressed test"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].header == "seq2 another compressed"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_bz2_compression() -> None:
    """Test reading bzip2-compressed FASTA files."""
    fasta_file = create_compressed_test_fasta("bz2")
    try:
        reader = FastaReader(str(fasta_file))
        records: List[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].header == "seq1 compressed test"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].header == "seq2 another compressed"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_stdin_with_dash() -> None:
    """Test reading from stdin using '-' as filename."""
    fasta_content = """>seq1 stdin test
ATCGATCG
>seq2 stdin test two
GGGGCCCC
"""
    # Use subprocess to simulate stdin input
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
from prseq import FastaReader
records = list(FastaReader('-'))
print(f"{len(records)}")
print(f"{records[0].header}")
print(f"{records[0].sequence}")
"""],
        input=fasta_content,
        text=True,
        capture_output=True
    )

    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert lines[0] == "2"  # 2 records
    assert lines[1] == "seq1 stdin test"
    assert lines[2] == "ATCGATCG"


def test_stdin_with_none() -> None:
    """Test reading from stdin using None as filename."""
    fasta_content = """>seq1 stdin test
ATCGATCG
>seq2 stdin test two
GGGGCCCC
"""
    # Use subprocess to simulate stdin input
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
from prseq import FastaReader
records = list(FastaReader())
print(f"{len(records)}")
print(f"{records[0].header}")
print(f"{records[0].sequence}")
"""],
        input=fasta_content,
        text=True,
        capture_output=True
    )

    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert lines[0] == "2"  # 2 records
    assert lines[1] == "seq1 stdin test"
    assert lines[2] == "ATCGATCG"


def test_stdin_compressed_gzip() -> None:
    """Test reading gzip-compressed data from stdin."""
    fasta_content = b""">seq1 compressed stdin
ATCGATCG
>seq2 compressed stdin two
GGGGCCCC
"""
    compressed_content = gzip.compress(fasta_content)

    # Use subprocess to simulate stdin input
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
from prseq import FastaReader
records = list(FastaReader())
print(f"{len(records)}")
print(f"{records[0].header}")
print(f"{records[0].sequence}")
"""],
        input=compressed_content,
        capture_output=True
    )

    assert result.returncode == 0
    lines = result.stdout.decode().strip().split('\n')
    assert lines[0] == "2"  # 2 records
    assert lines[1] == "seq1 compressed stdin"
    assert lines[2] == "ATCGATCG"


def test_from_stdin_class_method() -> None:
    """Test using the from_stdin class method."""
    fasta_content = """>seq1 class method test
ATCGATCG
"""
    # Use subprocess to simulate stdin input
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
from prseq import FastaReader
records = list(FastaReader.from_stdin())
print(f"{len(records)}")
print(f"{records[0].header}")
"""],
        input=fasta_content,
        text=True,
        capture_output=True
    )

    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert lines[0] == "1"  # 1 record
    assert lines[1] == "seq1 class method test"


