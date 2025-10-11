#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fasta_reader.h"

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
    size_t total_seq_length = 0;
    int result;

    while ((result = fasta_read_next(fp, reader)) > 0) {
        record_count++;
        total_seq_length += strlen(reader->sequence);

        // Print progress every 50k records
        if (record_count % 50000 == 0) {
            printf("Processed %d records...\n", record_count);
        }
    }

    if (result < 0) {
        fprintf(stderr, "Error reading FASTA file\n");
        fasta_reader_free(reader);
        fclose(fp);
        return 1;
    }

    printf("Processed %d sequences\n", record_count);
    printf("Total sequence length: %zu bp\n", total_seq_length);

    fasta_reader_free(reader);
    fclose(fp);
    return 0;
}