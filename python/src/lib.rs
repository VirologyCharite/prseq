use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;

// Import the Rust crate with an explicit alias to avoid naming conflict
extern crate prseq as rust_fasta;

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

impl From<rust_fasta::FastaRecord> for FastaRecord {
    fn from(record: rust_fasta::FastaRecord) -> Self {
        FastaRecord {
            header: record.header,
            sequence: record.sequence,
        }
    }
}

#[pyclass]
struct FastaReader {
    reader: rust_fasta::FastaReader,
}

#[pymethods]
impl FastaReader {
    #[new]
    fn new(path: String) -> PyResult<Self> {
        let reader = rust_fasta::FastaReader::from_file(&path)
            .map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(FastaReader { reader })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<FastaRecord>> {
        match slf.reader.next() {
            Some(Ok(record)) => Ok(Some(record.into())),
            Some(Err(e)) => Err(PyIOError::new_err(e.to_string())),
            None => Ok(None),
        }
    }
}

#[pymodule]
fn prseq(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FastaRecord>()?;
    m.add_class::<FastaReader>()?;
    Ok(())
}
