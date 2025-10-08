#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "fastq_reader.h"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <fastq_file>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        perror("Error opening file");
        return 1;
    }

    fastq_reader_t *reader = fastq_reader_init();
    if (!reader) {
        fprintf(stderr, "Failed to initialize reader\n");
        fclose(fp);
        return 1;
    }

    clock_t start = clock();

    int count = 0;
    size_t total_bases = 0;
    size_t min_len = 0;
    size_t max_len = 0;
    int result;

    while ((result = fastq_read_next(fp, reader)) == 1) {
        count++;
        size_t seq_len = strlen(reader->sequence);
        total_bases += seq_len;

        if (count == 1 || seq_len < min_len) min_len = seq_len;
        if (count == 1 || seq_len > max_len) max_len = seq_len;

        if (count % 50000 == 0) {
            fprintf(stderr, "Processed %d sequences...\n", count);
        }
    }

    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;

    if (result == -1) {
        fprintf(stderr, "Error reading FASTQ file\n");
        fastq_reader_free(reader);
        fclose(fp);
        return 1;
    }

    printf("Total sequences: %d\n", count);
    printf("Total bases: %zu\n", total_bases);
    if (count > 0) {
        printf("Average length: %.1f bp\n", (double)total_bases / count);
        printf("Min length: %zu bp\n", min_len);
        printf("Max length: %zu bp\n", max_len);
    }
    printf("Time: %.3f seconds\n", elapsed);
    if (elapsed > 0) {
        printf("Throughput: %.2f MB/s\n", (total_bases / 1024.0 / 1024.0) / elapsed);
    }

    fastq_reader_free(reader);
    fclose(fp);
    return 0;
}
