#ifndef FASTQ_READER_H
#define FASTQ_READER_H

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    char *id;
    char *sequence;
    char *quality;
    size_t id_capacity;
    size_t seq_capacity;
    size_t qual_capacity;
} fastq_reader_t;

fastq_reader_t* fastq_reader_init();
void fastq_reader_free(fastq_reader_t *reader);
int fastq_read_next(FILE *fp, fastq_reader_t *reader);

#endif
