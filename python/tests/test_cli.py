"""Tests for CLI commands."""

import subprocess
import tempfile
from pathlib import Path


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


def test_fasta_info_command() -> None:
    """Test fasta-info command."""
    fasta_file = create_test_fasta()
    try:
        result = subprocess.run(
            ["fasta-info", str(fasta_file)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Number of sequences: 3" in result.stdout
        assert "seq1 short" in result.stdout
    finally:
        fasta_file.unlink()


def test_fasta_stats_command() -> None:
    """Test fasta-stats command."""
    fasta_file = create_test_fasta()
    try:
        result = subprocess.run(
            ["fasta-stats", str(fasta_file)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Total sequences: 3" in result.stdout
        assert "Min length: 4" in result.stdout
        assert "Max length: 24" in result.stdout
    finally:
        fasta_file.unlink()


def test_fasta_filter_command() -> None:
    """Test fasta-filter command."""
    fasta_file = create_test_fasta()
    try:
        result = subprocess.run(
            ["fasta-filter", str(fasta_file), "10"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        # Should keep seq2 and seq3, filter seq1
        assert ">seq2 medium" in result.stdout
        assert ">seq3 long" in result.stdout
        assert ">seq1 short" not in result.stdout
        assert "Kept 2 sequences, filtered 1" in result.stderr
    finally:
        fasta_file.unlink()