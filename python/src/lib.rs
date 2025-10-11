use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use pyo3::types::PyBytes;
use std::io::{self, Read};

extern crate prseq as rust_prseq;

/// A wrapper that makes a Python file-like object compatible with Rust's Read trait
struct PyFileReader {
    file: Py<PyAny>,
}

impl PyFileReader {
    fn new(file: Py<PyAny>) -> Self {
        PyFileReader { file }
    }
}

impl Read for PyFileReader {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        Python::with_gil(|py| {
            let file = self.file.bind(py);

            // Call the Python read() method
            let result = file
                .call_method1("read", (buf.len(),))
                .map_err(|e| io::Error::new(io::ErrorKind::Other, e.to_string()))?;

            // Get the bytes returned
            let bytes: &Bound<PyBytes> = result
                .downcast()
                .map_err(|_| {
                    io::Error::new(
                        io::ErrorKind::InvalidInput,
                        "File must be opened in binary mode (use 'rb', not 'r'). \
                         The read() method returned a string instead of bytes."
                    )
                })?;

            let data = bytes.as_bytes();
            let len = data.len();
            buf[..len].copy_from_slice(data);
            Ok(len)
        })
    }
}

// Mark PyFileReader as Send since we control access through Python's GIL
unsafe impl Send for PyFileReader {}

#[pyclass]
struct FastaRecord {
    #[pyo3(get)]
    id: String,
    #[pyo3(get)]
    sequence: String,
}

#[pymethods]
impl FastaRecord {
    fn __repr__(&self) -> String {
        format!("FastaRecord(id='{}', sequence='{}')", self.id, self.sequence)
    }
}

impl From<rust_prseq::FastaRecord> for FastaRecord {
    fn from(record: rust_prseq::FastaRecord) -> Self {
        FastaRecord {
            id: record.id,
            sequence: record.sequence,
        }
    }
}

#[pyclass]
struct FastqRecord {
    #[pyo3(get)]
    id: String,
    #[pyo3(get)]
    sequence: String,
    #[pyo3(get)]
    quality: String,
}

#[pymethods]
impl FastqRecord {
    fn __repr__(&self) -> String {
        format!("FastqRecord(id='{}', sequence='{}', quality='{}')", self.id, self.sequence, self.quality)
    }
}

impl From<rust_prseq::FastqRecord> for FastqRecord {
    fn from(record: rust_prseq::FastqRecord) -> Self {
        FastqRecord {
            id: record.id,
            sequence: record.sequence,
            quality: record.quality,
        }
    }
}

#[pyclass(unsendable)]
struct FastaReader {
    reader: rust_prseq::FastaReader,
}

#[pyclass(unsendable)]
struct FastqReader {
    reader: rust_prseq::FastqReader,
}

#[pymethods]
impl FastaReader {
    #[new]
    #[pyo3(signature = (path = None, file = None, sequence_size_hint = None))]
    fn new(
        path: Option<String>,
        file: Option<Py<PyAny>>,
        sequence_size_hint: Option<usize>,
    ) -> PyResult<Self> {
        let reader = match (path, file) {
            (Some(_), Some(_)) => {
                return Err(PyIOError::new_err(
                    "Cannot specify both path and file arguments",
                ));
            }
            (None, Some(file_obj)) => {
                // Use the provided Python file object
                let py_reader = PyFileReader::new(file_obj);
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastaReader::from_reader_with_capacity(py_reader, hint),
                    None => rust_prseq::FastaReader::from_reader_with_capacity(py_reader, 64 * 1024),
                }
            }
            (Some(file_path), None) if file_path == "-" => {
                // Treat "-" as stdin
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastaReader::from_stdin_with_capacity(hint),
                    None => rust_prseq::FastaReader::from_stdin(),
                }
            }
            (Some(file_path), None) => {
                // Regular file
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastaReader::from_file_with_capacity(&file_path, hint),
                    None => rust_prseq::FastaReader::from_file(&file_path),
                }
            }
            (None, None) => {
                // No path or file provided, read from stdin
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastaReader::from_stdin_with_capacity(hint),
                    None => rust_prseq::FastaReader::from_stdin(),
                }
            }
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastaReader { reader })
    }

    /// Create a FastaReader from a file path
    #[staticmethod]
    #[pyo3(signature = (path, sequence_size_hint = None))]
    fn from_file(path: String, sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastaReader::from_file_with_capacity(&path, hint),
            None => rust_prseq::FastaReader::from_file(&path),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastaReader { reader })
    }

    /// Create a FastaReader from a Python file-like object
    #[staticmethod]
    #[pyo3(signature = (file, sequence_size_hint = None))]
    fn from_file_object(file: Py<PyAny>, sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let py_reader = PyFileReader::new(file);
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastaReader::from_reader_with_capacity(py_reader, hint),
            None => rust_prseq::FastaReader::from_reader_with_capacity(py_reader, 64 * 1024),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastaReader { reader })
    }

    /// Create a FastaReader from stdin
    #[staticmethod]
    #[pyo3(signature = (sequence_size_hint = None))]
    fn from_stdin(sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastaReader::from_stdin_with_capacity(hint),
            None => rust_prseq::FastaReader::from_stdin(),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastaReader { reader })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<FastaRecord>> {
        // For single record reads, don't release GIL to avoid complexity
        // The performance gain is minimal for individual records
        match slf.reader.next() {
            Some(Ok(record)) => Ok(Some(record.into())),
            Some(Err(e)) => Err(PyIOError::new_err(e.to_string())),
            None => Ok(None),
        }
    }

    /// Read multiple records at once with GIL released for better performance
    fn read_batch(&mut self, py: Python<'_>, count: usize) -> PyResult<Vec<FastaRecord>> {
        // Release GIL for batch operations where the performance benefit is significant
        py.allow_threads(move || {
            let mut records = Vec::with_capacity(count);
            for _ in 0..count {
                match self.reader.next() {
                    Some(Ok(record)) => records.push(record.into()),
                    Some(Err(e)) => return Err(PyIOError::new_err(e.to_string())),
                    None => break,
                }
            }
            Ok(records)
        })
    }
}

#[pymethods]
impl FastqReader {
    #[new]
    #[pyo3(signature = (path = None, file = None, sequence_size_hint = None))]
    fn new(
        path: Option<String>,
        file: Option<Py<PyAny>>,
        sequence_size_hint: Option<usize>,
    ) -> PyResult<Self> {
        let reader = match (path, file) {
            (Some(_), Some(_)) => {
                return Err(PyIOError::new_err(
                    "Cannot specify both path and file arguments",
                ));
            }
            (None, Some(file_obj)) => {
                // Use the provided Python file object
                let py_reader = PyFileReader::new(file_obj);
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastqReader::from_reader_with_capacity(py_reader, hint),
                    None => rust_prseq::FastqReader::from_reader_with_capacity(py_reader, 64 * 1024),
                }
            }
            (Some(file_path), None) if file_path == "-" => {
                // Treat "-" as stdin
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastqReader::from_stdin_with_capacity(hint),
                    None => rust_prseq::FastqReader::from_stdin(),
                }
            }
            (Some(file_path), None) => {
                // Regular file
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastqReader::from_file_with_capacity(&file_path, hint),
                    None => rust_prseq::FastqReader::from_file(&file_path),
                }
            }
            (None, None) => {
                // No path or file provided, read from stdin
                match sequence_size_hint {
                    Some(hint) => rust_prseq::FastqReader::from_stdin_with_capacity(hint),
                    None => rust_prseq::FastqReader::from_stdin(),
                }
            }
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastqReader { reader })
    }

    /// Create a FastqReader from a file path
    #[staticmethod]
    #[pyo3(signature = (path, sequence_size_hint = None))]
    fn from_file(path: String, sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastqReader::from_file_with_capacity(&path, hint),
            None => rust_prseq::FastqReader::from_file(&path),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastqReader { reader })
    }

    /// Create a FastqReader from a Python file-like object
    #[staticmethod]
    #[pyo3(signature = (file, sequence_size_hint = None))]
    fn from_file_object(file: Py<PyAny>, sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let py_reader = PyFileReader::new(file);
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastqReader::from_reader_with_capacity(py_reader, hint),
            None => rust_prseq::FastqReader::from_reader_with_capacity(py_reader, 64 * 1024),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastqReader { reader })
    }

    /// Create a FastqReader from stdin
    #[staticmethod]
    #[pyo3(signature = (sequence_size_hint = None))]
    fn from_stdin(sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastqReader::from_stdin_with_capacity(hint),
            None => rust_prseq::FastqReader::from_stdin(),
        }
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastqReader { reader })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<FastqRecord>> {
        match slf.reader.next() {
            Some(Ok(record)) => Ok(Some(record.into())),
            Some(Err(e)) => Err(PyIOError::new_err(e.to_string())),
            None => Ok(None),
        }
    }

    /// Read multiple records at once with GIL released for better performance
    fn read_batch(&mut self, py: Python<'_>, count: usize) -> PyResult<Vec<FastqRecord>> {
        py.allow_threads(move || {
            let mut records = Vec::with_capacity(count);
            for _ in 0..count {
                match self.reader.next() {
                    Some(Ok(record)) => records.push(record.into()),
                    Some(Err(e)) => return Err(PyIOError::new_err(e.to_string())),
                    None => break,
                }
            }
            Ok(records)
        })
    }
}

/// Read all FASTA records from a file
#[pyfunction]
#[pyo3(signature = (path, sequence_size_hint = None))]
fn read_fasta(path: String, sequence_size_hint: Option<usize>) -> PyResult<Vec<FastaRecord>> {
    let records = match sequence_size_hint {
        Some(hint) => rust_prseq::read_fasta_with_capacity(&path, hint),
        None => rust_prseq::read_fasta(&path),
    }
    .map_err(|e| PyIOError::new_err(e.to_string()))?;
    Ok(records.into_iter().map(|r| r.into()).collect())
}

/// Read all FASTA records from a file with capacity hint
#[pyfunction]
fn read_fasta_with_capacity(path: String, sequence_size_hint: usize) -> PyResult<Vec<FastaRecord>> {
    let records = rust_prseq::read_fasta_with_capacity(&path, sequence_size_hint)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    Ok(records.into_iter().map(|r| r.into()).collect())
}

/// Read all FASTQ records from a file
#[pyfunction]
#[pyo3(signature = (path, sequence_size_hint = None))]
fn read_fastq(path: String, sequence_size_hint: Option<usize>) -> PyResult<Vec<FastqRecord>> {
    let records = match sequence_size_hint {
        Some(hint) => rust_prseq::read_fastq_with_capacity(&path, hint),
        None => rust_prseq::read_fastq(&path),
    }
    .map_err(|e| PyIOError::new_err(e.to_string()))?;
    Ok(records.into_iter().map(|r| r.into()).collect())
}

/// Read all FASTQ records from a file with capacity hint
#[pyfunction]
fn read_fastq_with_capacity(path: String, sequence_size_hint: usize) -> PyResult<Vec<FastqRecord>> {
    let records = rust_prseq::read_fastq_with_capacity(&path, sequence_size_hint)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    Ok(records.into_iter().map(|r| r.into()).collect())
}

#[pymodule]
fn _prseq(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FastaRecord>()?;
    m.add_class::<FastaReader>()?;
    m.add_class::<FastqRecord>()?;
    m.add_class::<FastqReader>()?;
    m.add_function(wrap_pyfunction!(read_fasta, m)?)?;
    m.add_function(wrap_pyfunction!(read_fasta_with_capacity, m)?)?;
    m.add_function(wrap_pyfunction!(read_fastq, m)?)?;
    m.add_function(wrap_pyfunction!(read_fastq_with_capacity, m)?)?;
    Ok(())
}
