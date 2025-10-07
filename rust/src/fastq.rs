use crate::common::create_reader_with_compression;
use std::fs::File;
use std::io::{BufRead, Read, Result};
use std::path::Path;

/// Represents a single FASTQ sequence record
#[derive(Debug, Clone, PartialEq)]
pub struct FastqRecord {
    pub id: String,
    pub sequence: String,
    pub quality: String,
}

/// Iterator over FASTQ records from any readable source
pub struct FastqReader {
    lines: std::io::Lines<std::io::BufReader<Box<dyn Read + Send>>>,
    sequence_size_hint: usize,
}

impl FastqReader {
    /// Create a new FastqReader from a file path
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        Self::from_file_with_capacity(path, 64 * 1024)
    }

    /// Create a new FastqReader from a file path with a sequence size hint
    ///
    /// The size_hint helps optimize memory allocation for sequence data.
    /// Use smaller values (e.g., 100-1000) for short sequences like primers,
    /// or larger values (e.g., 50000+) for genomes or long sequences.
    pub fn from_file_with_capacity<P: AsRef<Path>>(
        path: P,
        sequence_size_hint: usize,
    ) -> Result<Self> {
        let file = File::open(path)?;
        Self::from_reader_with_capacity(file, sequence_size_hint)
    }

    /// Create a new FastqReader from stdin
    pub fn from_stdin() -> Result<Self> {
        Self::from_stdin_with_capacity(64 * 1024)
    }

    /// Create a new FastqReader from stdin with a sequence size hint
    pub fn from_stdin_with_capacity(sequence_size_hint: usize) -> Result<Self> {
        let stdin = std::io::stdin();
        Self::from_reader_with_capacity(stdin, sequence_size_hint)
    }

    /// Create a new FastqReader from any readable source with compression detection
    pub fn from_reader_with_capacity<R: Read + Send + 'static>(
        reader: R,
        sequence_size_hint: usize,
    ) -> Result<Self> {
        let buf_reader = create_reader_with_compression(reader)?;
        let lines = buf_reader.lines();

        Ok(FastqReader {
            lines,
            sequence_size_hint: sequence_size_hint.max(64),
        })
    }

    fn read_next(&mut self) -> Result<Option<FastqRecord>> {
        // Read header line (@id)
        let id = loop {
            match self.lines.next() {
                Some(Ok(line)) => {
                    if line.is_empty() || line.chars().all(|c| c.is_whitespace()) {
                        continue;
                    }
                    let trimmed = line.trim();
                    if !trimmed.starts_with('@') {
                        return Err(std::io::Error::new(
                            std::io::ErrorKind::InvalidData,
                            "FASTQ record must start with '@'",
                        ));
                    }
                    break trimmed[1..].to_string();
                }
                Some(Err(e)) => return Err(e),
                None => return Ok(None),
            }
        };

        // Read sequence lines (until we hit a '+' line)
        let mut sequence = String::with_capacity(self.sequence_size_hint);
        let plus_line = loop {
            match self.lines.next() {
                Some(Ok(line)) => {
                    let trimmed = line.trim();
                    if trimmed.starts_with('+') {
                        break trimmed.to_string();
                    }
                    if !line.is_empty() && !line.chars().all(|c| c.is_whitespace()) {
                        sequence.push_str(trimmed);
                    }
                }
                Some(Err(e)) => return Err(e),
                None => {
                    return Err(std::io::Error::new(
                        std::io::ErrorKind::UnexpectedEof,
                        "Unexpected end of file while reading FASTQ sequence",
                    ));
                }
            }
        };

        // Validate the '+' line if it contains an ID
        if plus_line.len() > 1 {
            let plus_id = &plus_line[1..];
            if plus_id != id {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    format!(
                        "FASTQ '+' line ID '{}' does not match header ID '{}'",
                        plus_id, id
                    ),
                ));
            }
        }

        // Read quality lines (must match sequence length)
        let mut quality = String::with_capacity(sequence.len());
        let sequence_len = sequence.len();

        while quality.len() < sequence_len {
            match self.lines.next() {
                Some(Ok(line)) => {
                    let trimmed = line.trim();
                    if !line.is_empty() && !line.chars().all(|c| c.is_whitespace()) {
                        // Only add as many characters as we need
                        let needed = sequence_len - quality.len();
                        let to_add = if trimmed.len() <= needed {
                            trimmed
                        } else {
                            &trimmed[..needed]
                        };
                        quality.push_str(to_add);
                    }
                }
                Some(Err(e)) => return Err(e),
                None => {
                    return Err(std::io::Error::new(
                        std::io::ErrorKind::UnexpectedEof,
                        "Unexpected end of file while reading FASTQ quality scores",
                    ));
                }
            }
        }

        // Validate that sequence and quality have the same length
        if sequence.len() != quality.len() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!(
                    "FASTQ sequence length ({}) does not match quality length ({})",
                    sequence.len(),
                    quality.len()
                ),
            ));
        }

        Ok(Some(FastqRecord {
            id,
            sequence,
            quality,
        }))
    }
}

impl Iterator for FastqReader {
    type Item = Result<FastqRecord>;

    fn next(&mut self) -> Option<Self::Item> {
        match self.read_next() {
            Ok(Some(record)) => Some(Ok(record)),
            Ok(None) => None,
            Err(e) => Some(Err(e)),
        }
    }
}

pub fn read_fastq<P: AsRef<Path>>(path: P) -> Result<Vec<FastqRecord>> {
    read_fastq_with_capacity(path, 64 * 1024)
}

pub fn read_fastq_with_capacity<P: AsRef<Path>>(
    path: P,
    sequence_size_hint: usize,
) -> Result<Vec<FastqRecord>> {
    let reader = FastqReader::from_file_with_capacity(path, sequence_size_hint)?;
    reader.collect()
}
