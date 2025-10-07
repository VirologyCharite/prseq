# prseq

Python tools (backed by Rust) for sequence analysis.

## Notes

* This is highly experimental and should not be used yet!
* The code here *will* change in backwards-incompatible ways.
* Almost all the code (and tests) was written by claude.ai

## Building

### Rust Library
```bash
cd rust
cargo test
cargo build --release
```

### Python Package
```bash
cd python
pip install maturin
maturin develop  # For development
maturin build --release  # For production wheels
```

## Publishing

### To crates.io
```bash
cd rust
cargo publish
```

### To PyPI
```bash
cd python
maturin publish
```
