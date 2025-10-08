CC = gcc
CFLAGS = -O3 -Wall -Wextra -std=c99
FASTA_TARGET = fasta_reader
FASTQ_TARGET = fastq_reader
FASTA_LIB = fasta_reader.c
FASTQ_LIB = fastq_reader.c
MAIN_SOURCE = main.c
FASTQ_INFO = fastq_info.c
TEST_SOURCE = tests.c
TEST_TARGET = test_runner

.PHONY: all clean test

all: $(FASTA_TARGET) $(FASTQ_TARGET)

$(FASTA_TARGET): $(FASTA_LIB) $(MAIN_SOURCE) fasta_reader.h
	$(CC) $(CFLAGS) -o $(FASTA_TARGET) $(FASTA_LIB) $(MAIN_SOURCE)

$(FASTQ_TARGET): $(FASTQ_LIB) $(FASTQ_INFO) fastq_reader.h
	$(CC) $(CFLAGS) -o $(FASTQ_TARGET) $(FASTQ_LIB) $(FASTQ_INFO)

$(TEST_TARGET): $(FASTA_LIB) $(TEST_SOURCE) fasta_reader.h
	$(CC) $(CFLAGS) -o $(TEST_TARGET) $(FASTA_LIB) $(TEST_SOURCE)

test: $(TEST_TARGET)
	@echo "Running unit tests..."
	./$(TEST_TARGET)

benchmark: $(FASTA_TARGET)
	@echo "Running benchmark test..."
	time ./$(FASTA_TARGET) ../python/gisaid-100M.fasta

clean:
	rm -f $(FASTA_TARGET) $(FASTQ_TARGET) $(TEST_TARGET)

.PHONY: benchmark
