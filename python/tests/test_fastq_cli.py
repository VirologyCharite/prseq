"""Integration tests for FASTQ CLI commands via subprocess."""

import subprocess
import tempfile
from pathlib import Path


def create_test_fastq() -> Path:
    """Create a temporary FASTQ file for testing."""
    content = """@seq1 short
ATCG
+
IIII
@seq2 medium
ATCGATCGATCG
+
IIIIIIIIIIII
@seq3 long
ATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIII
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fastq') as f:
        f.write(content)
        return Path(f.name)


def test_fastq_info_command() -> None:
    """Test fastq-info command via subprocess."""
    fastq_file = create_test_fastq()
    try:
        result = subprocess.run(
            ["fastq-info", str(fastq_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Number of sequences: 3" in result.stdout
        assert "seq1 short" in result.stdout
    finally:
        fastq_file.unlink()


def test_fastq_stats_command() -> None:
    """Test fastq-stats command via subprocess."""
    fastq_file = create_test_fastq()
    try:
        result = subprocess.run(
            ["fastq-stats", str(fastq_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Total sequences: 3" in result.stdout
        assert "Min length: 4" in result.stdout
        assert "Max length: 24" in result.stdout
    finally:
        fastq_file.unlink()


def test_fastq_filter_command() -> None:
    """Test fastq-filter command via subprocess."""
    fastq_file = create_test_fastq()
    try:
        result = subprocess.run(
            ["fastq-filter", "10", str(fastq_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should keep seq2 and seq3, filter seq1
        assert "@seq2 medium" in result.stdout
        assert "@seq3 long" in result.stdout
        assert "@seq1 short" not in result.stdout
        assert "Kept 2 sequences, filtered 1" in result.stderr
    finally:
        fastq_file.unlink()
