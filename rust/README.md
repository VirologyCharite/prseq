# prseq (Rust)

High-performance Rust library for FASTA and FASTQ sequence parsing.

[![Crates.io](https://img.shields.io/crates/v/prseq.svg)](https://crates.io/crates/prseq)
[![Rust Tests](https://img.shields.io/github/actions/workflow/status/VirologyCharite/prseq/rust-tests.yml?branch=main&label=rust%20tests)](https://github.com/VirologyCharite/prseq/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`prseq` is a Rust library providing fast, memory-efficient parsers for FASTA and FASTQ sequence formats. It features:

- **High Performance**: Zero-copy parsing where possible with optimized buffered I/O
- **Streaming Iterators**: Process files larger than available RAM
- **Automatic Compression**: Built-in support for gzip and bzip2
- **Flexible Input**: Works with files, stdin, or any `Read` trait
- **Format Support**: Full FASTA and FASTQ with multi-line sequences

This library also powers the [Python prseq package](../python/README.md), which provides Python bindings and CLI tools.

## Installation

Add to your `Cargo.toml`:
```toml
[dependencies]
prseq = "0.0.6"
```

## Rust API Reference

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

## Development

### Building

```bash
cd rust
cargo build --release
```

### Testing

```bash
cd rust
cargo test
```

### Publishing

```bash
cd rust
cargo publish
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

## Python Bindings

For Python users, see the [Python prseq package](../python/README.md) which provides:
- Pythonic API with full type hints
- Command-line tools (`fasta-info`, `fastq-stats`, etc.)
- Easy installation via pip/uv

## Links

- [Main Project README](../README.md) - Project overview, features, and performance benchmarks
- [Python Package README](../python/README.md) - Python API and CLI documentation
- [Crates.io](https://crates.io/crates/prseq)
- [GitHub Repository](https://github.com/VirologyCharite/prseq)

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
