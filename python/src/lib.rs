use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use pyo3::types::{PyBytes, PyList};

extern crate prseq as rust_prseq;
use rust_prseq::StreamingZeroCopyFastaReader as RustStreamingZeroCopyFastaReader;

#[pyclass]
struct FastaRecord {
    #[pyo3(get)]
    header: String,
    #[pyo3(get)]
    sequence: String,
}

#[pymethods]
impl FastaRecord {
    fn __repr__(&self) -> String {
        format!("FastaRecord(header='{}', sequence='{}')", self.header, self.sequence)
    }
}

impl From<rust_prseq::FastaRecord> for FastaRecord {
    fn from(record: rust_prseq::FastaRecord) -> Self {
        FastaRecord {
            header: record.header,
            sequence: record.sequence,
        }
    }
}

#[pyclass]
struct FastaReader {
    reader: rust_prseq::FastaReader,
}

#[pymethods]
impl FastaReader {
    #[new]
    #[pyo3(signature = (path, sequence_size_hint = None))]
    fn new(path: String, sequence_size_hint: Option<usize>) -> PyResult<Self> {
        let reader = match sequence_size_hint {
            Some(hint) => rust_prseq::FastaReader::from_file_with_capacity(&path, hint),
            None => rust_prseq::FastaReader::from_file(&path),
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

#[pyclass]
struct ZeroCopyFastaReader {
    reader: rust_prseq::ZeroCopyFastaReader,
}

#[pymethods]
impl ZeroCopyFastaReader {
    #[new]
    #[pyo3(signature = (path, sequence_hint = 8192))]
    fn new(path: String, sequence_hint: usize) -> PyResult<Self> {
        let reader = rust_prseq::ZeroCopyFastaReader::from_file(&path, sequence_hint)
            .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(ZeroCopyFastaReader { reader })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<(PyObject, PyObject, usize)>> {
        let py = slf.py();
        match slf.reader.next_record() {
            Some(Ok((header, sequence_lines, total_length))) => {
                // Convert header to Python bytes
                let header_bytes = PyBytes::new_bound(py, &header).into();

                // Convert sequence lines to Python list of bytes
                let sequence_bytes_list: Vec<PyObject> = sequence_lines
                    .iter()
                    .map(|line| PyBytes::new_bound(py, line).into())
                    .collect();
                let sequence_list = PyList::new_bound(py, sequence_bytes_list).into();

                Ok(Some((header_bytes, sequence_list, total_length)))
            }
            Some(Err(e)) => Err(PyIOError::new_err(e.to_string())),
            None => Ok(None),
        }
    }
}

#[pyfunction]
#[pyo3(signature = (path, sequence_hint = 8192))]
fn read_fasta_zero_copy(path: String, sequence_hint: usize) -> PyResult<Vec<(PyObject, PyObject, usize)>> {
    Python::with_gil(|py| {
        let mut reader = rust_prseq::ZeroCopyFastaReader::from_file(&path, sequence_hint)
            .map_err(|e| PyIOError::new_err(e.to_string()))?;

        let mut results = Vec::new();

        while let Some(record) = reader.next_record() {
            match record {
                Ok((header, sequence_lines, total_length)) => {
                    let header_bytes = PyBytes::new_bound(py, &header).into();
                    let sequence_bytes_list: Vec<PyObject> = sequence_lines
                        .iter()
                        .map(|line| PyBytes::new_bound(py, line).into())
                        .collect();
                    let sequence_list = PyList::new_bound(py, sequence_bytes_list).into();
                    results.push((header_bytes, sequence_list, total_length));
                }
                Err(e) => return Err(PyIOError::new_err(e.to_string())),
            }
        }

        Ok(results)
    })
}

#[pyclass]
struct StreamingZeroCopyFastaReader {
    reader: RustStreamingZeroCopyFastaReader,
}

#[pymethods]
impl StreamingZeroCopyFastaReader {
    #[new]
    #[pyo3(signature = (path, buffer_size = 65536))]
    fn new(path: String, buffer_size: usize) -> PyResult<Self> {
        let reader = RustStreamingZeroCopyFastaReader::from_file(&path, buffer_size)
            .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(StreamingZeroCopyFastaReader { reader })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<(PyObject, PyObject, usize)>> {
        let py = slf.py();
        match slf.reader.next_record() {
            Some(Ok((header, sequence, total_length))) => {
                // Convert to Python bytes objects
                let header_bytes = PyBytes::new_bound(py, &header).into();
                let sequence_bytes = PyBytes::new_bound(py, &sequence).into();
                Ok(Some((header_bytes, sequence_bytes, total_length)))
            }
            Some(Err(e)) => Err(PyIOError::new_err(e.to_string())),
            None => Ok(None),
        }
    }
}


#[pymodule]
fn prseq(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FastaRecord>()?;
    m.add_class::<FastaReader>()?;
    m.add_class::<ZeroCopyFastaReader>()?;
    m.add_class::<StreamingZeroCopyFastaReader>()?;
    m.add_function(wrap_pyfunction!(read_fasta_zero_copy, m)?)?;
    Ok(())
}
