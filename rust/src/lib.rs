use std::fs::File;
use std::io::{BufRead, BufReader, Result};
use std::path::Path;

/// Represents a single FASTA sequence with its header and sequence data
#[derive(Debug, Clone, PartialEq)]
pub struct FastaRecord {
    pub header: String,
    pub sequence: String,
}

/// Iterator over FASTA records in a file
pub struct FastaReader {
    lines: std::io::Lines<BufReader<File>>,
    next_header: Option<String>,
}

impl FastaReader {
    /// Create a new FastaReader from a file path
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let file = File::open(path)?;
        let reader = BufReader::with_capacity(64 * 1024, file);
        let lines = reader.lines();
        Ok(FastaReader {
            lines,
            next_header: None,
        })
    }

    fn read_next(&mut self) -> Result<Option<FastaRecord>> {
        let header = if let Some(h) = self.next_header.take() {
            h
        } else {
            loop {
                match self.lines.next() {
                    Some(Ok(line)) => {
                        let line = line.trim();
                        if line.is_empty() {
                            continue;
                        }
                        if !line.starts_with('>') {
                            return Err(std::io::Error::new(
                                std::io::ErrorKind::InvalidData,
                                "FASTA record must start with '>'",
                            ));
                        }
                        break line[1..].to_string();
                    }
                    Some(Err(e)) => return Err(e),
                    None => return Ok(None),
                }
            }
        };

        let mut sequence = String::with_capacity(1024);
        loop {
            match self.lines.next() {
                Some(Ok(line)) => {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    if trimmed.starts_with('>') {
                        self.next_header = Some(trimmed[1..].to_string());
                        break;
                    }
                    sequence.push_str(trimmed);
                }
                Some(Err(e)) => return Err(e),
                None => break,
            }
        }

        Ok(Some(FastaRecord { header, sequence }))
    }
}

impl Iterator for FastaReader {
    type Item = Result<FastaRecord>;

    fn next(&mut self) -> Option<Self::Item> {
        match self.read_next() {
            Ok(Some(record)) => Some(Ok(record)),
            Ok(None) => None,
            Err(e) => Some(Err(e)),
        }
    }
}

pub fn read_fasta<P: AsRef<Path>>(path: P) -> Result<Vec<FastaRecord>> {
    let reader = FastaReader::from_file(path)?;
    reader.collect()
}
