"""Tests for FASTA parsing Python API."""

import bz2
import gzip
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from prseq import cli
from prseq.fasta import FastaReader, FastaRecord, read_fasta


def create_test_fasta() -> Path:
    """Create a temporary FASTA file for testing."""
    content = """>seq1 short
ATCG
>seq2 medium
ATCGATCGATCG
>seq3 long
ATCGATCGATCGATCGATCGATCG
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
        f.write(content)
        return Path(f.name)


def create_test_fasta_multiline() -> Path:
    """Create a temporary FASTA file with multiline sequences."""
    content = """>seq1 description one
ATCGATCG
GCTAGCTA
>seq2 description two
GGGGCCCC
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
        f.write(content)
        return Path(f.name)


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


# ============================================================================
# FastaReader API tests
# ============================================================================

def test_fasta_reader_iterator() -> None:
    """Test iterating over FASTA records."""
    fasta_file = create_test_fasta_multiline()
    try:
        reader = FastaReader(str(fasta_file))
        records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 description one"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].id == "seq2 description two"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_read_fasta_convenience() -> None:
    """Test the convenience function to read all records."""
    fasta_file = create_test_fasta_multiline()
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
    fasta_file = create_test_fasta_multiline()
    try:
        records = read_fasta(str(fasta_file))
        record = records[0]

        # Test tuple unpacking
        record_id, sequence = record
        assert record_id == "seq1 description one"
        assert sequence == "ATCGATCGGCTAGCTA"

        # Test attribute access
        assert record.id == record_id
        assert record.sequence == sequence
    finally:
        fasta_file.unlink()


def test_multiple_iterations() -> None:
    """Test that we can iterate multiple times."""
    fasta_file = create_test_fasta_multiline()
    try:
        records1 = read_fasta(str(fasta_file))
        records2 = read_fasta(str(fasta_file))

        assert records1 == records2
    finally:
        fasta_file.unlink()


def test_gzip_compression() -> None:
    """Test reading gzip-compressed FASTA files."""
    fasta_file = create_compressed_test_fasta("gzip")
    try:
        reader = FastaReader(str(fasta_file))
        records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 compressed test"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].id == "seq2 another compressed"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_bz2_compression() -> None:
    """Test reading bzip2-compressed FASTA files."""
    fasta_file = create_compressed_test_fasta("bz2")
    try:
        reader = FastaReader(str(fasta_file))
        records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 compressed test"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].id == "seq2 another compressed"
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
from prseq.fasta import FastaReader
records = list(FastaReader('-'))
print(f"{len(records)}")
print(f"{records[0].id}")
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
from prseq.fasta import FastaReader
records = list(FastaReader())
print(f"{len(records)}")
print(f"{records[0].id}")
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
from prseq.fasta import FastaReader
records = list(FastaReader())
print(f"{len(records)}")
print(f"{records[0].id}")
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
from prseq.fasta import FastaReader
records = list(FastaReader.from_stdin())
print(f"{len(records)}")
print(f"{records[0].id}")
"""],
        input=fasta_content,
        text=True,
        capture_output=True
    )

    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert lines[0] == "1"  # 1 record
    assert lines[1] == "seq1 class method test"


def test_file_object_with_open() -> None:
    """Test reading from an already-opened file object."""
    fasta_file = create_test_fasta_multiline()
    try:
        with open(fasta_file, 'rb') as f:
            reader = FastaReader(file=f)
            records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 description one"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].id == "seq2 description two"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_file_object_with_from_file_object() -> None:
    """Test reading from a file object using the from_file_object class method."""
    fasta_file = create_test_fasta_multiline()
    try:
        with open(fasta_file, 'rb') as f:
            reader = FastaReader.from_file_object(f)
            records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 description one"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
    finally:
        fasta_file.unlink()


def test_file_object_gzip_compressed() -> None:
    """Test reading from a gzip-compressed file object."""
    fasta_file = create_compressed_test_fasta("gzip")
    try:
        with open(fasta_file, 'rb') as f:
            reader = FastaReader(file=f)
            records: list[FastaRecord] = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 compressed test"
        assert records[0].sequence == "ATCGATCGGCTAGCTA"
        assert records[1].id == "seq2 another compressed"
        assert records[1].sequence == "GGGGCCCC"
    finally:
        fasta_file.unlink()


def test_file_object_io_bytesio() -> None:
    """Test reading from an io.BytesIO object."""
    from io import BytesIO

    fasta_content = b""">seq1 bytesio test
ATCGATCG
>seq2 another bytesio
GGGGCCCC
"""
    file_obj = BytesIO(fasta_content)
    reader = FastaReader(file=file_obj)
    records: list[FastaRecord] = list(reader)

    assert len(records) == 2
    assert records[0].id == "seq1 bytesio test"
    assert records[0].sequence == "ATCGATCG"
    assert records[1].id == "seq2 another bytesio"
    assert records[1].sequence == "GGGGCCCC"


def test_file_object_and_path_error() -> None:
    """Test that providing both file and path raises an error."""
    fasta_file = create_test_fasta_multiline()
    try:
        with open(fasta_file, 'rb') as f:
            with pytest.raises(IOError, match="Cannot specify both path and file"):
                FastaReader(path=str(fasta_file), file=f)
    finally:
        fasta_file.unlink()


# ============================================================================
# CLI function tests (direct Python API)
# ============================================================================

def test_fasta_info_function() -> None:
    """Test fasta-info CLI function directly."""
    fasta_file = create_test_fasta()
    try:
        with patch('sys.argv', ['fasta-info', str(fasta_file)]):
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                cli.info()
                output = mock_stdout.getvalue()

                assert "Number of sequences: 3" in output
                assert "seq1 short" in output
    finally:
        fasta_file.unlink()


def test_fasta_stats_function() -> None:
    """Test fasta-stats CLI function directly."""
    fasta_file = create_test_fasta()
    try:
        with patch('sys.argv', ['fasta-stats', str(fasta_file)]):
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                cli.stats()
                output = mock_stdout.getvalue()

                assert "Total sequences: 3" in output
                assert "Min length: 4" in output
                assert "Max length: 24" in output
    finally:
        fasta_file.unlink()


def test_fasta_filter_function() -> None:
    """Test fasta-filter CLI function directly."""
    fasta_file = create_test_fasta()
    try:
        with patch('sys.argv', ['fasta-filter', '10', str(fasta_file)]):
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                with patch('sys.stderr', new=StringIO()) as mock_stderr:
                    cli.filter_cmd()
                    output = mock_stdout.getvalue()
                    stderr = mock_stderr.getvalue()

                    # Should keep seq2 and seq3, filter seq1
                    assert ">seq2 medium" in output
                    assert ">seq3 long" in output
                    assert ">seq1 short" not in output
                    assert "Kept 2" in stderr
                    assert "filtered 1" in stderr
    finally:
        fasta_file.unlink()
