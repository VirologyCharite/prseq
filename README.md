# prseq

Python tools (backed by Rust) for sequence analysis.

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
