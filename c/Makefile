CC = gcc
CFLAGS = -O3 -Wall -Wextra -std=c99

FASTA_INFO = fasta_info.c
FASTA_LIB = fasta_reader.c
FASTA_TARGET = fasta_reader

FASTQ_INFO = fastq_info.c
FASTQ_LIB = fastq_reader.c
FASTQ_TARGET = fastq_reader

TEST_SOURCE = tests.c
TEST_TARGET = test_runner

.PHONY: all clean test python

all: $(FASTA_TARGET) $(FASTQ_TARGET)

python:
	@if [ -f ../python/.venv/bin/python ]; then \
		../python/.venv/bin/python setup.py build_ext --inplace; \
	else \
		python3 setup.py build_ext --inplace; \
	fi

$(FASTA_TARGET): $(FASTA_LIB) $(FASTA_INFO) fasta_reader.h
	$(CC) $(CFLAGS) -o $(FASTA_TARGET) $(FASTA_LIB) $(FASTA_INFO)

$(FASTQ_TARGET): $(FASTQ_LIB) $(FASTQ_INFO) fastq_reader.h
	$(CC) $(CFLAGS) -o $(FASTQ_TARGET) $(FASTQ_LIB) $(FASTQ_INFO)

$(TEST_TARGET): $(FASTA_LIB) $(TEST_SOURCE) fasta_reader.h
	$(CC) $(CFLAGS) -o $(TEST_TARGET) $(FASTA_LIB) $(TEST_SOURCE)

test: $(TEST_TARGET)
	@echo "Running unit tests..."
	./$(TEST_TARGET)

clean:
	rm -f $(FASTA_TARGET) $(FASTQ_TARGET) $(TEST_TARGET)
	rm -rf build *.so *.o
	rm -rf prseq_c.*.so
