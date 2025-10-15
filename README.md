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

We benchmark prseq against BioPython, pure Python, a C implementation, C with
Python bindings, and UNIX utilities (cat and wc) to demonstrate performance
characteristics. The benchmark generates synthetic FASTA and FASTQ files with
1,000,000 sequences ranging from 100-20,000 bases each, then measures throughput
(MB/s) for parsing.

**Test Configuration:**
- 1,000,000 sequences per file
- Sequence lengths: 100-20,000 bases
- FASTA file: ~9.8 GB
- FASTQ file: ~19.5 GB
- Test machine: Apple M2 Max with 96 GB RAM

**Results:**

**FASTA Benchmarks:**
| Implementation      | Elapsed (s) | Throughput (MB/s) | Relative to C |
|---------------------|------------:|------------------:|--------------:|
| cat > /dev/null     |       1.704 |          5,735.20 |         0.215 |
| wc -l               |       9.460 |          1,032.90 |         1.193 |
| C                   |       7.926 |          1,232.76 |         1.000 |
| Rust/Python (prseq) |       8.090 |          1,207.79 |         1.021 |
| C/Python            |       8.650 |          1,129.61 |         1.091 |
| BioPython           |      15.920 |            613.74 |         2.009 |
| Pure Python         |      16.744 |            583.54 |         2.113 |

**FASTQ Benchmarks:**
| Implementation      | Elapsed (s) | Throughput (MB/s) | Relative to C |
|---------------------|------------:|------------------:|--------------:|
| cat > /dev/null     |       3.566 |          5,458.16 |         0.231 |
| wc -l               |      19.076 |          1,020.43 |         1.238 |
| C                   |      15.406 |          1,263.50 |         1.000 |
| Rust/Python (prseq) |      15.822 |          1,230.31 |         1.027 |
| C/Python            |      16.880 |          1,153.18 |         1.096 |
| BioPython           |      62.411 |            311.89 |         4.051 |
| Pure Python         |      35.345 |            550.73 |         2.294 |

**Key findings:**
- **cat**: Raw I/O baseline at ~5.6 GB/s shows the theoretical maximum for file
  reading without any parsing
- **wc -l**: Simple line counting at ~1.03 GB/s provides a minimal parsing baseline
- **Rust/Python (prseq)**: Achieves 98.0% of C speed for FASTA and 97.4% for
  FASTQ, providing near-native performance with memory safety and Python
  integration
- **C/Python**: Achieves 91.6% of C speed for FASTA and 91.3% for FASTQ (1.09-1.10x
  slower), showing the overhead of Python C extension bindings
- **BioPython**: 49.8% of C speed for FASTA (2.009x slower), 24.7% for FASTQ
  (4.051x slower)
- **Pure Python**: 47.3% of C speed for FASTA (2.113x slower), 43.6% for FASTQ
  (2.294x slower)

**Checksum Verification:**

All benchmark implementations compute SHA256 checksums of sequence IDs and sequences during reading. At the end of each benchmark run, checksums are compared across all implementations to verify they read identical data in identical order. This cryptographic verification ensures that performance comparisons are valid and that all implementations correctly parse the same files.

To run benchmarks yourself:
```bash
cd python/benchmark
make
```

## Development

### Prerequisites
- Rust 1.70+
- Python 3.10-3.12
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
