#ifndef FASTA_READER_H
#define FASTA_READER_H

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    char *id;
    char *sequence;
    size_t id_capacity;
    size_t seq_capacity;
} fasta_reader_t;

fasta_reader_t* fasta_reader_init();
void fasta_reader_free(fasta_reader_t *reader);
int fasta_read_next(FILE *fp, fasta_reader_t *reader);

#endif