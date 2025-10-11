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

## Language-Specific Documentation

For detailed API documentation and development guides:

- **[Rust Library](rust/README.md)** - Core Rust library with FASTA/FASTQ parsers
- **[Python Package](python/README.md)** - Python bindings, CLI tools, and API reference

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

For complete API documentation, see:
- **[Python API Reference](python/README.md#python-api-reference)** - Detailed Python API with examples
- **[Rust API Reference](rust/README.md#rust-api-reference)** - Complete Rust documentation
- **[CLI Tools](python/README.md#cli-tools)** - Command-line tool documentation

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

## Benchmarks

We benchmark prseq against BioPython, pure Python, a C implementation, and C
with Python bindings to demonstrate performance characteristics. The benchmark
generates synthetic FASTA and FASTQ files with 500,000 sequences ranging from
100-20,000 bases each, then measures throughput (MB/s) for parsing.

**Test Configuration:**
- 500,000 sequences per file
- Sequence lengths: 100-20,000 bases
- FASTA file: ~4.8 GB
- FASTQ file: ~9.6 GB

**Results:**

**FASTA Benchmarks:**
| Implementation | Throughput | % of C | Slowdown |
|----------------|------------|--------|----------|
| C | 1,321.14 MB/s | 100.0% | 1.00x |
| Rust/Python (prseq) | 1,256.25 MB/s | 95.1% | 1.05x |
| C/Python | 1,184.31 MB/s | 89.6% | 1.12x |
| BioPython | 627.00 MB/s | 47.5% | 2.11x |
| Pure Python | 591.11 MB/s | 44.7% | 2.24x |

**FASTQ Benchmarks:**
| Implementation | Throughput | % of C | Slowdown |
|----------------|------------|--------|----------|
| C | 677.47 MB/s | 100.0% | 1.00x |
| Rust/Python (prseq) | 633.33 MB/s | 93.5% | 1.07x |
| C/Python | 602.38 MB/s | 88.9% | 1.12x |
| BioPython | 160.06 MB/s | 23.6% | 4.23x |
| Pure Python | 268.67 MB/s | 39.7% | 2.52x |

**Key findings:**
- **Rust/Python (prseq)**: Achieves 95.1% of C speed for FASTA and 93.5% for
  FASTQ, providing near-native performance with memory safety and Python
  integration
- **C/Python**: Achieves 89.6% of C speed for FASTA and 88.9% for FASTQ (1.12x
  slower), showing the overhead of Python C extension bindings
- **BioPython**: 47.5% of C speed for FASTA (2.11x slower), 23.6% for FASTQ
  (4.23x slower)
- **Pure Python**: 44.7% of C speed for FASTA (2.24x slower), 39.7% for FASTQ
  (2.52x slower)

To run benchmarks yourself:
```bash
cd python/benchmark
make
```

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
- Code almost entirely generated by [Claude AI](https://claude.ai/) 🤖
