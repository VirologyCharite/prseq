"""Tests for FASTQ parsing functionality."""

import bz2
import gzip
import tempfile
from pathlib import Path

import pytest

from prseq.fastq import FastqReader, FastqRecord, read_fastq


def create_test_fastq() -> Path:
    """Create a temporary FASTQ file for testing."""
    content = """@seq1 test sequence
ATCGGATCCTAG
+
IIIIIIIIIIII
@seq2 another test
GGCCTTAAGGGG
+seq2 another test
JJJJJJJJJJJJ
@seq3 short
ATCG
+
AAAA
"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.fastq', delete=False)
    temp_file.write(content)
    temp_file.close()
    return Path(temp_file.name)


def create_compressed_test_fastq(compression: str = 'gzip') -> Path:
    """Create a temporary compressed FASTQ file for testing."""
    content = b"""@seq1 compressed
ATCGGATCC
+
IIIIIIIII
@seq2 compressed too
GGCCTTAA
+
JJJJJJJJ
"""

    if compression == 'gzip':
        compressed_content = gzip.compress(content)
        suffix = '.fastq.gz'
    elif compression == 'bzip2':
        compressed_content = bz2.compress(content)
        suffix = '.fastq.bz2'
    else:
        raise ValueError(f"Unsupported compression: {compression}")

    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temp_file.write(compressed_content)
    temp_file.close()
    return Path(temp_file.name)


def test_fastq_reader_iterator() -> None:
    """Test iterating over FASTQ records."""
    fastq_file = create_test_fastq()
    try:
        reader = FastqReader.from_file(str(fastq_file))
        records: list[FastqRecord] = list(reader)

        assert len(records) == 3

        # Test first record
        record1 = records[0]
        assert record1.id == "seq1 test sequence"
        assert record1.sequence == "ATCGGATCCTAG"
        assert record1.quality == "IIIIIIIIIIII"

        # Test second record with ID in '+' line
        record2 = records[1]
        assert record2.id == "seq2 another test"
        assert record2.sequence == "GGCCTTAAGGGG"
        assert record2.quality == "JJJJJJJJJJJJ"

        # Test third record
        record3 = records[2]
        assert record3.id == "seq3 short"
        assert record3.sequence == "ATCG"
        assert record3.quality == "AAAA"

    finally:
        fastq_file.unlink()


def test_read_fastq_convenience() -> None:
    """Test the read_fastq convenience function."""
    fastq_file = create_test_fastq()
    try:
        records = read_fastq(str(fastq_file))
        assert len(records) == 3
        assert records[0].id == "seq1 test sequence"
        assert records[0].sequence == "ATCGGATCCTAG"
        assert records[0].quality == "IIIIIIIIIIII"
    finally:
        fastq_file.unlink()


def test_fastq_record() -> None:
    """Test FastqRecord attributes and methods."""
    record = FastqRecord("test_id", "ATCG", "IIII")
    assert record.id == "test_id"
    assert record.sequence == "ATCG"
    assert record.quality == "IIII"

    # Test __repr__
    assert "FastqRecord" in repr(record)
    assert "test_id" in repr(record)
    assert "ATCG" in repr(record)
    assert "IIII" in repr(record)

    # Test equality
    record2 = FastqRecord("test_id", "ATCG", "IIII")
    record3 = FastqRecord("test_id", "ATCG", "JJJJ")  # Different quality
    assert record == record2
    assert record != record3


def test_gzip_compression() -> None:
    """Test reading gzip-compressed FASTQ files."""
    fastq_file = create_compressed_test_fastq('gzip')
    try:
        reader = FastqReader.from_file(str(fastq_file))
        records = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 compressed"
        assert records[0].sequence == "ATCGGATCC"
        assert records[0].quality == "IIIIIIIII"
        assert records[1].id == "seq2 compressed too"
        assert records[1].sequence == "GGCCTTAA"
        assert records[1].quality == "JJJJJJJJ"
    finally:
        fastq_file.unlink()


def test_bzip2_compression() -> None:
    """Test reading bzip2-compressed FASTQ files."""
    fastq_file = create_compressed_test_fastq('bzip2')
    try:
        reader = FastqReader.from_file(str(fastq_file))
        records = list(reader)

        assert len(records) == 2
        assert records[0].id == "seq1 compressed"
        assert records[0].sequence == "ATCGGATCC"
        assert records[0].quality == "IIIIIIIII"
    finally:
        fastq_file.unlink()


def test_from_stdin_class_method() -> None:
    """Test the from_stdin class method."""
    reader = FastqReader.from_stdin()
    assert reader is not None
    assert hasattr(reader, '_reader')


def test_file_not_found() -> None:
    """Test error handling for missing files."""
    with pytest.raises(IOError):
        list(FastqReader.from_file("nonexistent_file.fastq"))