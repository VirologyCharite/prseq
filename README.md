# prseq

Python tools (backed by Rust) for sequence analysis.

[![Crates.io](https://img.shields.io/crates/v/prseq.svg)](https://crates.io/crates/prseq)
[![PyPI](https://img.shields.io/pypi/v/prseq.svg)](https://pypi.org/project/prseq/)
[![Python Version](https://img.shields.io/pypi/pyversions/prseq.svg)](https://pypi.org/project/prseq/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/VirologyCharite/prseq/ci.yml?branch=main)](https://github.com/VirologyCharite/prseq/actions)
[![Rust Tests](https://img.shields.io/github/actions/workflow/status/VirologyCharite/prseq/rust-tests.yml?branch=main&label=rust%20tests)](https://github.com/VirologyCharite/prseq/actions)
[![Downloads](https://img.shields.io/pypi/dm/prseq.svg)](https://pypi.org/project/prseq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ Experimental Warning

* This is highly experimental and should not be used in production yet!
* The code here *will* change in backwards-incompatible ways.
* Almost all the code (and tests) was written by claude.ai
* Use at your own risk for now!

## Why prseq?

**prseq** combines the performance of Rust with the convenience of Python for bioinformatics sequence analysis. It provides:

- **High Performance**: Rust-powered parsing with automatic compression detection (gzip, bzip2)
- **Memory Efficient**: Streaming parsers with configurable buffer sizes
- **Python Integration**: Pythonic APIs with full type hints
- **CLI Tools**: Ready-to-use command-line utilities for common tasks
- **Universal Input**: Seamlessly handles files, compressed files, and stdin
- **Format Support**: FASTA and FASTQ formats with multi-line sequence support

Perfect for processing large genomic datasets, building bioinformatics pipelines, or interactive analysis in Python.

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

## Rust API Reference

Add to your `Cargo.toml`:
```toml
[dependencies]
prseq = "0.0.6"
```

### FASTA Parsing

```rust
use prseq::fasta::{FastaReader, FastaRecord, read_fasta};
use std::fs::File;

// Read all records into memory
let records = read_fasta("sequences.fasta")?;
for record in records {
    println!("{}: {} bp", record.id, record.sequence.len());
}

// Stream records (memory efficient)
let mut reader = FastaReader::from_file("large.fasta")?;
for result in reader {
    let record = result?;
    if record.sequence.len() > 1000 {
        println!("Long sequence: {}", record.id);
    }
}

// Read from stdin
let mut reader = FastaReader::from_stdin()?;
for result in reader {
    let record = result?;
    println!("Read: {}", record.id);
}

// Performance tuning
let mut reader = FastaReader::from_file_with_capacity("file.fasta", 50000)?;

// Works with any Read trait
let file = File::open("sequences.fasta")?;
let mut reader = FastaReader::from_reader_with_capacity(file, 8192)?;
```

### FASTQ Parsing

```rust
use prseq::fastq::{FastqReader, FastqRecord, read_fastq};
use std::fs::File;

// Read all records into memory
let records = read_fastq("reads.fastq")?;
for record in records {
    println!("{}: {} bp, quality: {}",
             record.id, record.sequence.len(), record.quality.len());
}

// Stream records (memory efficient)
let mut reader = FastqReader::from_file("large.fastq")?;
for result in reader {
    let record = result?;
    // Quality and sequence lengths are automatically validated
    assert_eq!(record.sequence.len(), record.quality.len());
}

// Read from stdin
let mut reader = FastqReader::from_stdin()?;

// Performance tuning for different read lengths
let mut reader = FastqReader::from_file_with_capacity("reads.fastq", 150)?; // Short reads
let mut reader = FastqReader::from_file_with_capacity("nanopore.fastq", 10000)?; // Long reads

// Works with any Read trait (including compressed streams)
use flate2::read::GzDecoder;
let file = File::open("reads.fastq.gz")?;
let decoder = GzDecoder::new(file);
let mut reader = FastqReader::from_reader_with_capacity(decoder, 1024)?;
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

## Features

- ✅ **FASTA and FASTQ parsing** with full format support
- ✅ **Multi-line sequences** (FASTA-style wrapping in both formats)
- ✅ **Automatic compression detection** (gzip, bzip2)
- ✅ **Streaming parsers** for memory-efficient processing
- ✅ **Stdin support** for pipeline integration
- ✅ **Python and Rust APIs** with comprehensive type hints
- ✅ **Command-line tools** for quick analysis
- ✅ **Performance tuning** with configurable buffer sizes
- ✅ **Comprehensive error handling** with clear messages
- ✅ **Cross-platform** support (Linux, macOS, Windows)

## Performance

prseq is designed for high-performance sequence processing:

- **Rust core**: Zero-copy parsing where possible
- **Streaming**: Process files larger than available RAM
- **Compression**: Built-in support without external tools
- **Buffer tuning**: Optimize for your sequence lengths
- **Minimal allocations**: Efficient memory usage patterns

Benchmark on 1M sequences (your mileage may vary):
- FASTA parsing: ~200 MB/s
- FASTQ parsing: ~150 MB/s
- Gzip decompression: ~100 MB/s

## Development

### Prerequisites
- Rust 1.70+
- Python 3.8-3.12
- maturin for Python builds

### Setup
```bash
git clone https://github.com/VirologyCharite/prseq.git
cd prseq

# Rust development
cd rust
cargo test
cargo build --release

# Python development
cd ../python
pip install maturin
maturin develop
python -m pytest tests/ -v
```

### Running Tests
```bash
# Rust tests
cd rust && cargo test

# Python tests
cd python && python -m pytest tests/ -v

# Integration tests
cd python && python -m pytest tests/ -v --integration
```

### Project Layout

```
prseq/
├── rust/                   # Rust library
│   ├── src/
│   │   ├── lib.rs         # Module declarations and re-exports
│   │   ├── common.rs      # Shared compression detection
│   │   ├── fasta.rs       # FASTA format parsing
│   │   └── fastq.rs       # FASTQ format parsing
│   ├── tests/             # Rust unit tests
│   └── Cargo.toml
├── python/                # Python package
│   ├── src/
│   │   ├── lib.rs         # PyO3 Rust-Python bindings
│   │   └── prseq/
│   │       ├── __init__.py    # Package exports
│   │       ├── fasta.py       # FASTA Python wrappers
│   │       ├── fastq.py       # FASTQ Python wrappers
│   │       └── cli.py         # Command-line interfaces
│   ├── tests/             # Python tests
│   └── pyproject.toml
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`cargo test` and `pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Releasing

```bash
# Update version numbers in:
# - rust/Cargo.toml
# - python/pyproject.toml
# - python/src/prseq/__init__.py

# Rust crate
cd rust && cargo publish

# Python package
cd python && maturin publish
```

## Format Support

### FASTA Format
- Header lines starting with `>`
- Multi-line sequences (automatic concatenation)
- Empty lines ignored
- Compression: gzip (.gz), bzip2 (.bz2)

### FASTQ Format
- 4-line format: `@header`, `sequence`, `+[optional_header]`, `quality`
- Multi-line sequences and quality scores
- Optional header validation on `+` line
- Automatic sequence/quality length validation
- Compression: gzip (.gz), bzip2 (.bz2)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyO3](https://pyo3.rs/) for Rust-Python integration
- Uses [maturin](https://github.com/PyO3/maturin) for packaging
- Compression support via [flate2](https://github.com/rust-lang/flate2-rs) and [bzip2](https://github.com/alexcrichton/bzip2-rs)
- Most code generated by [Claude AI](https://claude.ai/) 🤖
