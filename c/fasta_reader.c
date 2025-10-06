#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INITIAL_ID_SIZE 1024
#define INITIAL_SEQ_SIZE 50000
#define LINE_BUFFER_SIZE 8192

typedef struct {
    char *id;
    char *sequence;
    size_t id_capacity;
    size_t seq_capacity;
} fasta_reader_t;

fasta_reader_t* fasta_reader_init() {
    fasta_reader_t *reader = malloc(sizeof(fasta_reader_t));
    if (!reader) return NULL;

    reader->id = malloc(INITIAL_ID_SIZE);
    reader->sequence = malloc(INITIAL_SEQ_SIZE);
    reader->id_capacity = INITIAL_ID_SIZE;
    reader->seq_capacity = INITIAL_SEQ_SIZE;

    if (!reader->id || !reader->sequence) {
        free(reader->id);
        free(reader->sequence);
        free(reader);
        return NULL;
    }

    return reader;
}

void fasta_reader_free(fasta_reader_t *reader) {
    if (reader) {
        free(reader->id);
        free(reader->sequence);
        free(reader);
    }
}

// Ensure buffer has enough capacity, realloc if needed
static int ensure_capacity(char **buffer, size_t *capacity, size_t needed) {
    if (needed >= *capacity) {
        size_t new_capacity = *capacity;
        while (new_capacity <= needed) {
            new_capacity *= 2;
        }

        char *new_buffer = realloc(*buffer, new_capacity);
        if (!new_buffer) return 0;

        *buffer = new_buffer;
        *capacity = new_capacity;
    }
    return 1;
}

// Returns 1 if record read, 0 if EOF, -1 if error
int fasta_read_next(FILE *fp, fasta_reader_t *reader) {
    static char line_buffer[LINE_BUFFER_SIZE];
    char *line;

    // Clear previous data
    reader->id[0] = '\0';
    reader->sequence[0] = '\0';
    size_t seq_len = 0;

    // Read header line
    do {
        line = fgets(line_buffer, sizeof(line_buffer), fp);
        if (!line) return 0; // EOF

        // Skip empty lines
        if (line[0] == '\n' || line[0] == '\r') continue;

        // Must start with '>'
        if (line[0] != '>') {
            fprintf(stderr, "Error: FASTA record must start with '>'\n");
            return -1;
        }
        break;
    } while (1);

    // Extract header (remove '>' and newline)
    char *header_start = line + 1;
    char *newline = strchr(header_start, '\n');
    if (newline) *newline = '\0';
    char *cr = strchr(header_start, '\r');
    if (cr) *cr = '\0';

    // Ensure ID buffer capacity
    size_t header_len = strlen(header_start);
    if (!ensure_capacity(&reader->id, &reader->id_capacity, header_len + 1)) {
        return -1;
    }
    strcpy(reader->id, header_start);

    // Read sequence lines
    while ((line = fgets(line_buffer, sizeof(line_buffer), fp))) {
        // Stop if we hit next record
        if (line[0] == '>') {
            // Put the line back by seeking backwards
            fseek(fp, -(long)strlen(line), SEEK_CUR);
            break;
        }

        // Skip empty lines
        if (line[0] == '\n' || line[0] == '\r') continue;

        // Remove newline
        char *nl = strchr(line, '\n');
        if (nl) *nl = '\0';
        char *cr = strchr(line, '\r');
        if (cr) *cr = '\0';

        // Ensure sequence buffer capacity
        size_t line_len = strlen(line);
        if (!ensure_capacity(&reader->sequence, &reader->seq_capacity, seq_len + line_len + 1)) {
            return -1;
        }

        // Append to sequence
        strcpy(reader->sequence + seq_len, line);
        seq_len += line_len;
    }

    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <fasta_file>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        perror("Error opening file");
        return 1;
    }

    fasta_reader_t *reader = fasta_reader_init();
    if (!reader) {
        fprintf(stderr, "Failed to initialize FASTA reader\n");
        fclose(fp);
        return 1;
    }

    int record_count = 0;
    // size_t total_seq_length = 0;
    int result;

    while ((result = fasta_read_next(fp, reader)) > 0) {
        record_count++;
        // total_seq_length += strlen(reader->sequence);

        /* Print progress every 50k records
        if (record_count % 50000 == 0) {
            printf("Processed %d records...\n", record_count);
        }
        */
    }

    if (result < 0) {
        fprintf(stderr, "Error reading FASTA file\n");
        fasta_reader_free(reader);
        fclose(fp);
        return 1;
    }

    printf("Processed %d sequences\n", record_count);
    // printf("Total sequence length: %zu bp\n", total_seq_length);

    fasta_reader_free(reader);
    fclose(fp);
    return 0;
}
