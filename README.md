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
500,000 sequences ranging from 100-20,000 bases each, then measures throughput
(MB/s) for parsing.

**Test Configuration:**
- 500,000 sequences per file
- Sequence lengths: 100-20,000 bases
- FASTA file: ~4.9 GB
- FASTQ file: ~9.7 GB

**Results:**

**FASTA Benchmarks:**
| Implementation | Elapsed | Throughput | % of C | Slowdown |
|----------------|---------|------------|--------|----------|
| cat > /dev/null | 0.384s | 12,669.87 MB/s | 995.6% | 0.10x |
| wc -l | 4.702s | 1,035.84 MB/s | 81.4% | 1.23x |
| C | 3.759s | 1,272.53 MB/s | 100.0% | 1.00x |
| Rust/Python (prseq) | 3.961s | 1,207.55 MB/s | 94.9% | 1.05x |
| C/Python | 4.162s | 1,149.16 MB/s | 90.3% | 1.11x |
| BioPython | 7.790s | 614.01 MB/s | 48.3% | 2.07x |
| Pure Python | 8.200s | 583.31 MB/s | 45.8% | 2.18x |

**FASTQ Benchmarks:**
| Implementation | Elapsed | Throughput | % of C | Slowdown |
|----------------|---------|------------|--------|----------|
| cat > /dev/null | 0.782s | 12,445.39 MB/s | 1913.9% | 0.05x |
| wc -l | 9.328s | 1,043.47 MB/s | 160.5% | 0.62x |
| C | 7.370s | 650.28 MB/s | 100.0% | 1.00x |
| Rust/Python (prseq) | 7.774s | 616.52 MB/s | 94.8% | 1.05x |
| C/Python | 8.235s | 581.96 MB/s | 89.5% | 1.12x |
| BioPython | 30.836s | 155.43 MB/s | 23.9% | 4.18x |
| Pure Python | 18.021s | 265.95 MB/s | 40.9% | 2.45x |

**Key findings:**
- **cat**: Raw I/O baseline at ~12.5 GB/s shows the theoretical maximum for file
  reading without any parsing
- **wc -l**: Simple line counting provides a minimal parsing baseline,
  outperforming dedicated parsers for FASTQ (160.5% of C) where line-based
  format is simpler
- **Rust/Python (prseq)**: Achieves 94.9% of C speed for FASTA and 94.8% for
  FASTQ, providing near-native performance with memory safety and Python
  integration
- **C/Python**: Achieves 90.3% of C speed for FASTA and 89.5% for FASTQ (1.11x
  slower), showing the overhead of Python C extension bindings
- **BioPython**: 48.3% of C speed for FASTA (2.07x slower), 23.9% for FASTQ
  (4.18x slower)
- **Pure Python**: 45.8% of C speed for FASTA (2.18x slower), 40.9% for FASTQ
  (2.45x slower)

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
