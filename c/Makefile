CC = gcc
CFLAGS = -O3 -Wall -Wextra -std=c99
TARGET = fasta_reader
LIB_SOURCE = fasta_reader.c
MAIN_SOURCE = main.c
TEST_SOURCE = tests.c
TEST_TARGET = test_runner

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(LIB_SOURCE) $(MAIN_SOURCE) fasta_reader.h
	$(CC) $(CFLAGS) -o $(TARGET) $(LIB_SOURCE) $(MAIN_SOURCE)

$(TEST_TARGET): $(LIB_SOURCE) $(TEST_SOURCE) fasta_reader.h
	$(CC) $(CFLAGS) -o $(TEST_TARGET) $(LIB_SOURCE) $(TEST_SOURCE)

test: $(TEST_TARGET)
	@echo "Running unit tests..."
	./$(TEST_TARGET)

benchmark: $(TARGET)
	@echo "Running benchmark test..."
	time ./$(TARGET) ../python/gisaid-100M.fasta

clean:
	rm -f $(TARGET) $(TEST_TARGET)

.PHONY: benchmark
