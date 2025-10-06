CC = gcc
CFLAGS = -O3 -Wall -Wextra -std=c99
TARGET = fasta_reader
SOURCE = fasta_reader.c

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE)

clean:
	rm -f $(TARGET)

test: $(TARGET)
	@echo "Testing C FASTA reader..."
	time ./$(TARGET) ../python/gisaid-100M.fasta

.PHONY: test