#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "fasta_reader.h"
#include "fastq_reader.h"

// ===== FASTA Reader Python Object =====

typedef struct {
    PyObject_HEAD
    fasta_reader_t *reader;
    FILE *file;
    char *filename;
    int done;
} FastaReaderObject;

static void
FastaReader_dealloc(FastaReaderObject *self)
{
    if (self->reader) {
        fasta_reader_free(self->reader);
    }
    if (self->file) {
        fclose(self->file);
    }
    if (self->filename) {
        free(self->filename);
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
FastaReader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    FastaReaderObject *self;
    self = (FastaReaderObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->reader = NULL;
        self->file = NULL;
        self->filename = NULL;
        self->done = 0;
    }
    return (PyObject *) self;
}

static int
FastaReader_init(FastaReaderObject *self, PyObject *args, PyObject *kwds)
{
    char *filename;
    static char *kwlist[] = {"filename", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", kwlist, &filename)) {
        return -1;
    }

    // Open file
    self->file = fopen(filename, "r");
    if (!self->file) {
        PyErr_SetFromErrnoWithFilename(PyExc_IOError, filename);
        return -1;
    }

    // Initialize reader
    self->reader = fasta_reader_init();
    if (!self->reader) {
        fclose(self->file);
        self->file = NULL;
        PyErr_SetString(PyExc_MemoryError, "Failed to initialize FASTA reader");
        return -1;
    }

    // Store filename
    self->filename = strdup(filename);
    self->done = 0;

    return 0;
}

static PyObject *
FastaReader_iter(PyObject *self)
{
    Py_INCREF(self);
    return self;
}

static PyObject *
FastaReader_iternext(PyObject *self)
{
    FastaReaderObject *reader = (FastaReaderObject *) self;

    if (reader->done) {
        return NULL;
    }

    int result = fasta_read_next(reader->file, reader->reader);

    if (result == 0) {
        // EOF
        reader->done = 1;
        return NULL;
    } else if (result == -1) {
        // Error
        reader->done = 1;
        PyErr_SetString(PyExc_RuntimeError, "Error reading FASTA record");
        return NULL;
    }

    // Return tuple (id, sequence)
    return Py_BuildValue("(ss)", reader->reader->id, reader->reader->sequence);
}

static PyTypeObject FastaReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "prseq_c.FastaReader",
    .tp_doc = "FASTA file reader",
    .tp_basicsize = sizeof(FastaReaderObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = FastaReader_new,
    .tp_init = (initproc) FastaReader_init,
    .tp_dealloc = (destructor) FastaReader_dealloc,
    .tp_iter = FastaReader_iter,
    .tp_iternext = FastaReader_iternext,
};

// ===== FASTQ Reader Python Object =====

typedef struct {
    PyObject_HEAD
    fastq_reader_t *reader;
    FILE *file;
    char *filename;
    int done;
} FastqReaderObject;

static void
FastqReader_dealloc(FastqReaderObject *self)
{
    if (self->reader) {
        fastq_reader_free(self->reader);
    }
    if (self->file) {
        fclose(self->file);
    }
    if (self->filename) {
        free(self->filename);
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
FastqReader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    FastqReaderObject *self;
    self = (FastqReaderObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->reader = NULL;
        self->file = NULL;
        self->filename = NULL;
        self->done = 0;
    }
    return (PyObject *) self;
}

static int
FastqReader_init(FastqReaderObject *self, PyObject *args, PyObject *kwds)
{
    char *filename;
    static char *kwlist[] = {"filename", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", kwlist, &filename)) {
        return -1;
    }

    // Open file
    self->file = fopen(filename, "r");
    if (!self->file) {
        PyErr_SetFromErrnoWithFilename(PyExc_IOError, filename);
        return -1;
    }

    // Initialize reader
    self->reader = fastq_reader_init();
    if (!self->reader) {
        fclose(self->file);
        self->file = NULL;
        PyErr_SetString(PyExc_MemoryError, "Failed to initialize FASTQ reader");
        return -1;
    }

    // Store filename
    self->filename = strdup(filename);
    self->done = 0;

    return 0;
}

static PyObject *
FastqReader_iter(PyObject *self)
{
    Py_INCREF(self);
    return self;
}

static PyObject *
FastqReader_iternext(PyObject *self)
{
    FastqReaderObject *reader = (FastqReaderObject *) self;

    if (reader->done) {
        return NULL;
    }

    int result = fastq_read_next(reader->file, reader->reader);

    if (result == 0) {
        // EOF
        reader->done = 1;
        return NULL;
    } else if (result == -1) {
        // Error
        reader->done = 1;
        PyErr_SetString(PyExc_RuntimeError, "Error reading FASTQ record");
        return NULL;
    }

    // Return tuple (id, sequence, quality)
    return Py_BuildValue("(sss)",
                         reader->reader->id,
                         reader->reader->sequence,
                         reader->reader->quality);
}

static PyTypeObject FastqReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "prseq_c.FastqReader",
    .tp_doc = "FASTQ file reader",
    .tp_basicsize = sizeof(FastqReaderObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = FastqReader_new,
    .tp_init = (initproc) FastqReader_init,
    .tp_dealloc = (destructor) FastqReader_dealloc,
    .tp_iter = FastqReader_iter,
    .tp_iternext = FastqReader_iternext,
};

// ===== Module Definition =====

static PyModuleDef prseq_c_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "prseq_c",
    .m_doc = "C-based FASTA and FASTQ readers with Python bindings",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit_prseq_c(void)
{
    PyObject *m;

    if (PyType_Ready(&FastaReaderType) < 0)
        return NULL;

    if (PyType_Ready(&FastqReaderType) < 0)
        return NULL;

    m = PyModule_Create(&prseq_c_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&FastaReaderType);
    if (PyModule_AddObject(m, "FastaReader", (PyObject *) &FastaReaderType) < 0) {
        Py_DECREF(&FastaReaderType);
        Py_DECREF(m);
        return NULL;
    }

    Py_INCREF(&FastqReaderType);
    if (PyModule_AddObject(m, "FastqReader", (PyObject *) &FastqReaderType) < 0) {
        Py_DECREF(&FastqReaderType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
