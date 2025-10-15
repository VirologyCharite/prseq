#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
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

    // Initialize SHA256 contexts for checksums
    SHA256_CTX id_ctx, seq_ctx;
    SHA256_Init(&id_ctx);
    SHA256_Init(&seq_ctx);

    while ((result = fasta_read_next(fp, reader)) > 0) {
        record_count++;
        size_t seq_len = strlen(reader->sequence);
        total_seq_length += seq_len;

        // Update checksums
        SHA256_Update(&id_ctx, reader->id, strlen(reader->id));
        SHA256_Update(&seq_ctx, reader->sequence, seq_len);

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

    // Finalize checksums
    unsigned char id_hash[SHA256_DIGEST_LENGTH];
    unsigned char seq_hash[SHA256_DIGEST_LENGTH];
    SHA256_Final(id_hash, &id_ctx);
    SHA256_Final(seq_hash, &seq_ctx);

    printf("Processed %d sequences\n", record_count);
    printf("Total sequence length: %zu bp\n", total_seq_length);

    // Print ID checksum
    printf("ID checksum (SHA256): ");
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        printf("%02x", id_hash[i]);
    }
    printf("\n");

    // Print sequence checksum
    printf("Sequence checksum (SHA256): ");
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        printf("%02x", seq_hash[i]);
    }
    printf("\n");

    fasta_reader_free(reader);
    fclose(fp);
    return 0;
}