#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include "fasta_reader.h"

// Simple test framework
static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) \
    printf("Running %s... ", #name); \
    tests_run++; \
    if (test_##name()) { \
        printf("PASSED\n"); \
        tests_passed++; \
    } else { \
        printf("FAILED\n"); \
    }

// Helper function to create a temporary test file
static FILE* create_test_file(const char* content) {
    FILE* fp = tmpfile();
    if (!fp) return NULL;

    fprintf(fp, "%s", content);
    rewind(fp);
    return fp;
}

// Test basic FASTA reading
static int test_basic_reading() {
    const char* test_content =
        ">seq1 first sequence\n"
        "ATCG\n"
        "GCTA\n"
        ">seq2 second sequence\n"
        "GGCC\n";

    FILE* fp = create_test_file(test_content);
    if (!fp) return 0;

    fasta_reader_t* reader = fasta_reader_init();
    if (!reader) {
        fclose(fp);
        return 0;
    }

    // Read first sequence
    int result = fasta_read_next(fp, reader);
    if (result != 1) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    if (strcmp(reader->id, "seq1 first sequence") != 0 ||
        strcmp(reader->sequence, "ATCGGCTA") != 0) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    // Read second sequence
    result = fasta_read_next(fp, reader);
    if (result != 1) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    if (strcmp(reader->id, "seq2 second sequence") != 0 ||
        strcmp(reader->sequence, "GGCC") != 0) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    // Should be EOF now
    result = fasta_read_next(fp, reader);
    if (result != 0) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    fasta_reader_free(reader);
    fclose(fp);
    return 1;
}

// Test empty file
static int test_empty_file() {
    FILE* fp = create_test_file("");
    if (!fp) return 0;

    fasta_reader_t* reader = fasta_reader_init();
    if (!reader) {
        fclose(fp);
        return 0;
    }

    int result = fasta_read_next(fp, reader);
    int success = (result == 0);  // Should return EOF

    fasta_reader_free(reader);
    fclose(fp);
    return success;
}

// Test single sequence
static int test_single_sequence() {
    const char* test_content = ">single\nACGT\n";

    FILE* fp = create_test_file(test_content);
    if (!fp) return 0;

    fasta_reader_t* reader = fasta_reader_init();
    if (!reader) {
        fclose(fp);
        return 0;
    }

    int result = fasta_read_next(fp, reader);
    if (result != 1) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    int success = (strcmp(reader->id, "single") == 0 &&
                   strcmp(reader->sequence, "ACGT") == 0);

    fasta_reader_free(reader);
    fclose(fp);
    return success;
}

// Test sequences with carriage returns
static int test_carriage_returns() {
    const char* test_content = ">test\r\nATCG\r\nGCTA\r\n";

    FILE* fp = create_test_file(test_content);
    if (!fp) return 0;

    fasta_reader_t* reader = fasta_reader_init();
    if (!reader) {
        fclose(fp);
        return 0;
    }

    int result = fasta_read_next(fp, reader);
    if (result != 1) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    int success = (strcmp(reader->id, "test") == 0 &&
                   strcmp(reader->sequence, "ATCGGCTA") == 0);

    fasta_reader_free(reader);
    fclose(fp);
    return success;
}

// Test long sequence (buffer reallocation)
static int test_long_sequence() {
    const char* header = ">long\n";
    FILE* fp = tmpfile();
    if (!fp) return 0;

    // Write header
    fprintf(fp, "%s", header);

    // Write a sequence longer than initial buffer size
    for (int i = 0; i < 60000; i++) {
        fputc('A', fp);
        if (i % 80 == 79) fputc('\n', fp);  // Line breaks every 80 chars
    }
    fprintf(fp, "\n");  // Final newline
    rewind(fp);

    fasta_reader_t* reader = fasta_reader_init();
    if (!reader) {
        fclose(fp);
        return 0;
    }

    int result = fasta_read_next(fp, reader);
    if (result != 1) {
        fasta_reader_free(reader);
        fclose(fp);
        return 0;
    }

    int success = (strcmp(reader->id, "long") == 0 &&
                   strlen(reader->sequence) == 60000);

    // Check that it's all A's
    if (success) {
        for (size_t i = 0; i < strlen(reader->sequence); i++) {
            if (reader->sequence[i] != 'A') {
                success = 0;
                break;
            }
        }
    }

    fasta_reader_free(reader);
    fclose(fp);
    return success;
}

int main() {
    printf("Running FASTA reader tests...\n\n");

    TEST(basic_reading);
    TEST(empty_file);
    TEST(single_sequence);
    TEST(carriage_returns);
    TEST(long_sequence);

    printf("\nTest Results: %d/%d passed\n", tests_passed, tests_run);

    return (tests_passed == tests_run) ? 0 : 1;
}