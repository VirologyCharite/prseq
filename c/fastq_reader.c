#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INITIAL_ID_SIZE 1024
#define INITIAL_SEQ_SIZE 50000
#define LINE_BUFFER_SIZE 8192

typedef struct {
    char *id;
    char *sequence;
    char *quality;
    size_t id_capacity;
    size_t seq_capacity;
    size_t qual_capacity;
} fastq_reader_t;

fastq_reader_t* fastq_reader_init() {
    fastq_reader_t *reader = malloc(sizeof(fastq_reader_t));
    if (!reader) return NULL;

    reader->id = malloc(INITIAL_ID_SIZE);
    reader->sequence = malloc(INITIAL_SEQ_SIZE);
    reader->quality = malloc(INITIAL_SEQ_SIZE);
    reader->id_capacity = INITIAL_ID_SIZE;
    reader->seq_capacity = INITIAL_SEQ_SIZE;
    reader->qual_capacity = INITIAL_SEQ_SIZE;

    if (!reader->id || !reader->sequence || !reader->quality) {
        free(reader->id);
        free(reader->sequence);
        free(reader->quality);
        free(reader);
        return NULL;
    }

    return reader;
}

void fastq_reader_free(fastq_reader_t *reader) {
    if (reader) {
        free(reader->id);
        free(reader->sequence);
        free(reader->quality);
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
int fastq_read_next(FILE *fp, fastq_reader_t *reader) {
    static char line_buffer[LINE_BUFFER_SIZE];
    char *line;

    // Clear previous data
    reader->id[0] = '\0';
    reader->sequence[0] = '\0';
    reader->quality[0] = '\0';

    // Read header line (starts with '@')
    do {
        line = fgets(line_buffer, sizeof(line_buffer), fp);
        if (!line) return 0; // EOF

        // Skip empty lines
        if (line[0] == '\n' || line[0] == '\r') continue;

        // Must start with '@'
        if (line[0] != '@') {
            fprintf(stderr, "Error: FASTQ record must start with '@'\n");
            return -1;
        }
        break;
    } while (1);

    // Extract header (remove '@' and newline)
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

    // Read sequence lines (until we hit '+')
    size_t seq_len = 0;
    while ((line = fgets(line_buffer, sizeof(line_buffer), fp))) {
        // Check if this is the separator line
        if (line[0] == '+') {
            break;
        }

        // Skip empty lines
        if (line[0] == '\n' || line[0] == '\r') continue;

        // Remove newline
        newline = strchr(line, '\n');
        if (newline) *newline = '\0';
        cr = strchr(line, '\r');
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

    if (!line) {
        fprintf(stderr, "Error: Unexpected EOF before '+' separator\n");
        return -1;
    }

    // Read quality lines (must match sequence length)
    size_t qual_len = 0;
    while (qual_len < seq_len && (line = fgets(line_buffer, sizeof(line_buffer), fp))) {
        // Skip empty lines
        if (line[0] == '\n' || line[0] == '\r') continue;

        // Remove newline
        newline = strchr(line, '\n');
        if (newline) *newline = '\0';
        cr = strchr(line, '\r');
        if (cr) *cr = '\0';

        // Ensure quality buffer capacity
        size_t line_len = strlen(line);
        if (!ensure_capacity(&reader->quality, &reader->qual_capacity, qual_len + line_len + 1)) {
            return -1;
        }

        // Append to quality
        strcpy(reader->quality + qual_len, line);
        qual_len += line_len;
    }

    // Validate sequence and quality lengths match
    if (seq_len != qual_len) {
        fprintf(stderr, "Error: Sequence length (%zu) != quality length (%zu)\n",
                seq_len, qual_len);
        return -1;
    }

    return 1;
}
