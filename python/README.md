# prseq (Python)

Python tools for sequence analysis, powered by Rust.

[![PyPI](https://img.shields.io/pypi/v/prseq.svg)](https://pypi.org/project/prseq/)
[![Python Version](https://img.shields.io/pypi/pyversions/prseq.svg)](https://pypi.org/project/prseq/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/virologieCharite/prseq/workflow.yaml?branch=main)](https://github.com/virologieCharite/prseq/actions)
[![Downloads](https://img.shields.io/pypi/dm/prseq.svg)](https://pypi.org/project/prseq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`prseq` provides Python bindings to a high-performance Rust library for FASTA and FASTQ parsing. It includes:

- **Pythonic API**: Full type hints and Python-native data structures
- **CLI Tools**: Ready-to-use command-line utilities
- **Rust Performance**: Fast parsing with automatic compression detection
- **Memory Efficient**: Streaming parsers for large files
- **Universal Input**: Files, compressed files, and stdin support

The core parsing is implemented in the [Rust prseq library](../rust/README.md).

## Installation

### Using uv (recommended)
```bash
uv add prseq
```

### Using pip
```bash
pip install prseq
```

### From source (developers)
```bash
git clone https://github.com/VirologyCharite/prseq.git
cd prseq/python
pip install maturin
maturin develop
```

## Quick Start

### Command Line Tools

```bash
# Analyze a FASTA file
fasta-info sequences.fasta
fasta-stats sequences.fasta.gz  # Works with compressed files
fasta-filter 100 sequences.fasta  # Keep sequences ≥100bp

# Analyze a FASTQ file
fastq-info reads.fastq
fastq-stats reads.fastq.bz2
fastq-filter 50 reads.fastq  # Keep sequences ≥50bp

# All tools support stdin
cat sequences.fasta | fasta-stats
gunzip -c reads.fastq.gz | fastq-filter 75
```

### Python API

```python
import prseq

# FASTA files
records = prseq.read_fasta("sequences.fasta")
for record in records:
    print(f"{record.id}: {len(record.sequence)} bp")

# FASTQ files
records = prseq.read_fastq("reads.fastq")
for record in records:
    print(f"{record.id}: {len(record.sequence)} bp, quality: {len(record.quality)}")

# Streaming for large files
for record in prseq.FastaReader.from_file("large.fasta"):
    if len(record.sequence) > 1000:
        print(f"Long sequence: {record.id}")

# Works with stdin too
for record in prseq.FastqReader.from_stdin():
    print(f"Read: {record.id}")
```

## Python API Reference

### FASTA Support

```python
from prseq import FastaRecord, FastaReader, read_fasta

# FastaRecord - represents a single sequence
record = FastaRecord(id="seq1", sequence="ATCG")
print(record.id)        # "seq1"
print(record.sequence)  # "ATCG"

# Read all records into memory
records = read_fasta("file.fasta")
records = read_fasta("file.fasta.gz")  # Auto-detects compression
records = read_fasta(None)  # Read from stdin

# Stream records (memory efficient)
reader = FastaReader.from_file("large.fasta")
reader = FastaReader.from_stdin()

for record in reader:
    # Process one record at a time
    print(f"{record.id}: {len(record.sequence)}")

# Performance tuning
reader = FastaReader.from_file("file.fasta", sequence_size_hint=50000)
```

### FASTQ Support

```python
from prseq import FastqRecord, FastqReader, read_fastq

# FastqRecord - represents a single read
record = FastqRecord(id="read1", sequence="ATCG", quality="IIII")
print(record.id)        # "read1"
print(record.sequence)  # "ATCG"
print(record.quality)   # "IIII"

# Read all records into memory
records = read_fastq("reads.fastq")
records = read_fastq("reads.fastq.bz2")  # Auto-detects compression
records = read_fastq(None)  # Read from stdin

# Stream records (memory efficient)
reader = FastqReader.from_file("large.fastq")
reader = FastqReader.from_stdin()

for record in reader:
    # Validate quality length matches sequence
    assert len(record.sequence) == len(record.quality)
    print(f"{record.id}: {len(record.sequence)} bp")

# Performance tuning for short/long reads
reader = FastqReader.from_file("reads.fastq", sequence_size_hint=150)  # Short reads
reader = FastqReader.from_file("nanopore.fastq", sequence_size_hint=10000)  # Long reads
```

### Advanced Usage

```python
import prseq

# Filter sequences by length
def filter_by_length(filename, min_length):
    for record in prseq.FastaReader.from_file(filename):
        if len(record.sequence) >= min_length:
            yield record

# Calculate GC content
def gc_content(sequence):
    gc_count = sequence.upper().count('G') + sequence.upper().count('C')
    return gc_count / len(sequence) if sequence else 0

# Process compressed files
records = prseq.read_fasta("sequences.fasta.gz")
avg_gc = sum(gc_content(r.sequence) for r in records) / len(records)

# Convert FASTQ to FASTA
def fastq_to_fasta(fastq_file, fasta_file):
    with open(fasta_file, 'w') as f:
        for record in prseq.FastqReader.from_file(fastq_file):
            f.write(f">{record.id}\n{record.sequence}\n")
```

## CLI Tools

### FASTA Tools

| Command | Description | Example |
|---------|-------------|---------|
| `fasta-info` | Show basic file information | `fasta-info sequences.fasta` |
| `fasta-stats` | Calculate sequence statistics | `fasta-stats sequences.fasta.gz` |
| `fasta-filter` | Filter by minimum length | `fasta-filter 100 sequences.fasta` |

### FASTQ Tools

| Command | Description | Example |
|---------|-------------|---------|
| `fastq-info` | Show basic file information | `fastq-info reads.fastq` |
| `fastq-stats` | Calculate sequence statistics | `fastq-stats reads.fastq.bz2` |
| `fastq-filter` | Filter by minimum length | `fastq-filter 50 reads.fastq` |

### CLI Examples

```bash
# Basic usage
fasta-info genome.fasta
fastq-stats reads.fastq

# With compressed files (auto-detected)
fasta-stats sequences.fasta.gz
fastq-info reads.fastq.bz2

# Using stdin (great for pipelines)
cat sequences.fasta | fasta-stats
gunzip -c reads.fastq.gz | fastq-filter 100

# Performance tuning for large sequences
fasta-stats --size-hint 50000 genome.fasta
fastq-filter --size-hint 10000 150 nanopore.fastq
```

## Development

### Prerequisites
- Python 3.8-3.12
- Rust 1.70+
- maturin for building Python extensions

### Setup

```bash
cd python
pip install maturin
maturin develop
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/ -v --integration

# Type checking with MyPy
mypy src/prseq
```

### Building

```bash
# Development build
maturin develop

# Production wheel
maturin build --release
```

### Publishing

```bash
cd python
maturin publish
```

## Type Checking

The package includes full type hints and is configured for MyPy with Python 3.8+ compatibility. Type stubs are automatically generated for the Rust extension modules.

## Rust Core

The Python package is built on top of the [Rust prseq library](../rust/README.md), which provides the high-performance parsing implementation. If you need Rust-native parsing without Python, check out the Rust crate directly.

## Links

- [Main Project README](../README.md) - Project overview, features, and performance benchmarks
- [Rust Library README](../rust/README.md) - Rust API documentation
- [PyPI](https://pypi.org/project/prseq/)
- [GitHub Repository](https://github.com/VirologyCharite/prseq)

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
