# Makefile for benchmarking FASTA/FASTQ parsers

# Default benchmark parameters
SEQUENCES ?= 500000
SEQ_MIN ?= 100
SEQ_MAX ?= 20000
SIZE_HINT ?= 21000
SEED ?= 12345
DATA_DIR ?= data

.PHONY: all benchmark clean help

all: benchmark

benchmark:
	@echo "Running benchmarks with $(SEQUENCES) sequences ($(SEQ_MIN)-$(SEQ_MAX) bases)..."
	uv run python run_benchmarks.py \
		--sequences $(SEQUENCES) \
		--seq-min $(SEQ_MIN) \
		--seq-max $(SEQ_MAX) \
		--size-hint $(SIZE_HINT) \
		--seed $(SEED) \
		--data-dir $(DATA_DIR) | tee benchmark_results.txt

clean:
	@echo "Cleaning benchmark data and results..."
	rm -rf $(DATA_DIR)
	rm -f benchmark_results.txt
	@echo "Clean complete"

help:
	@echo "Benchmark Makefile targets:"
	@echo "  make benchmark    - Run benchmarks (default)"
	@echo "  make clean        - Remove generated data and results"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "Parameters (with defaults):"
	@echo "  SEQUENCES=$(SEQUENCES)  - Number of sequences"
	@echo "  SEQ_MIN=$(SEQ_MIN)      - Minimum sequence length"
	@echo "  SEQ_MAX=$(SEQ_MAX)      - Maximum sequence length"
	@echo "  SIZE_HINT=$(SIZE_HINT)  - Size hint for Rust/Python"
	@echo "  SEED=$(SEED)            - Random seed"
	@echo "  DATA_DIR=$(DATA_DIR)    - Data directory"
	@echo ""
	@echo "Example: make benchmark SEQUENCES=250000 SEQ_MAX=200000"
