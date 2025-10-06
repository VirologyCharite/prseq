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
    sequence_size_hint: usize,
}

impl FastaReader {
    /// Create a new FastaReader from a file path
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        Self::from_file_with_capacity(path, 8192)
    }

    /// Create a new FastaReader from a file path with a sequence size hint
    ///
    /// The size_hint helps optimize memory allocation for sequence data.
    /// Use smaller values (e.g., 100-1000) for short sequences like primers,
    /// or larger values (e.g., 50000+) for genomes or long sequences.
    pub fn from_file_with_capacity<P: AsRef<Path>>(path: P, sequence_size_hint: usize) -> Result<Self> {
        let file = File::open(path)?;
        let reader = BufReader::with_capacity(64 * 1024, file); // Optimal buffer size
        let lines = reader.lines();
        Ok(FastaReader {
            lines,
            next_header: None,
            sequence_size_hint: sequence_size_hint.max(64), // Minimum reasonable size
        })
    }

    fn read_next(&mut self) -> Result<Option<FastaRecord>> {
        let header = if let Some(h) = self.next_header.take() {
            h
        } else {
            loop {
                match self.lines.next() {
                    Some(Ok(line)) => {
                        if line.is_empty() || line.chars().all(|c| c.is_whitespace()) {
                            continue;
                        }
                        let trimmed = line.trim();
                        if !trimmed.starts_with('>') {
                            return Err(std::io::Error::new(
                                std::io::ErrorKind::InvalidData,
                                "FASTA record must start with '>'",
                            ));
                        }
                        break trimmed[1..].to_string();
                    }
                    Some(Err(e)) => return Err(e),
                    None => return Ok(None),
                }
            }
        };

        let mut sequence = String::with_capacity(self.sequence_size_hint);
        loop {
            match self.lines.next() {
                Some(Ok(line)) => {
                    if line.is_empty() || line.chars().all(|c| c.is_whitespace()) {
                        continue;
                    }
                    let trimmed = line.trim();
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

/// Zero-copy FASTA reader that yields byte slices directly from memory buffer
/// This version loads the entire file into memory - use StreamingZeroCopyFastaReader for large files
pub struct ZeroCopyFastaReader {
    buffer: Vec<u8>,
    position: usize,
    sequence_hint: usize,
}

/// Streaming FASTA reader that reuses memory for very large files (TB+)
/// Uses efficient line reading with memory reuse to match regular iterator performance
pub struct StreamingFastaReader {
    lines: std::io::Lines<BufReader<std::fs::File>>,
    sequence_lines: Vec<String>,
    next_header: Option<String>,
}

impl ZeroCopyFastaReader {
    /// Create a new zero-copy FASTA reader
    pub fn from_file<P: AsRef<Path>>(path: P, sequence_hint: usize) -> Result<Self> {
        let mut file = std::fs::File::open(path)?;
        let mut buffer = Vec::new();
        std::io::Read::read_to_end(&mut file, &mut buffer)?;

        Ok(ZeroCopyFastaReader {
            buffer,
            position: 0,
            sequence_hint: sequence_hint.max(1024),
        })
    }

    /// Skip whitespace characters
    fn skip_whitespace(&mut self) {
        while self.position < self.buffer.len() {
            match self.buffer[self.position] {
                b' ' | b'\t' | b'\r' | b'\n' => self.position += 1,
                _ => break,
            }
        }
    }


    /// Read next FASTA record as owned byte vectors (zero-copy within each record)
    /// Returns (header, sequence_lines, total_sequence_length)
    pub fn next_record(&mut self) -> Option<std::io::Result<(Vec<u8>, Vec<Vec<u8>>, usize)>> {
        self.skip_whitespace();

        if self.position >= self.buffer.len() {
            return None;
        }

        // Find header line start
        let header_start = self.position;
        if self.buffer[header_start] != b'>' {
            return Some(Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "FASTA record must start with '>'",
            )));
        }

        // Find header line end
        let mut pos = header_start + 1; // Skip '>'
        while pos < self.buffer.len() && self.buffer[pos] != b'\n' {
            pos += 1;
        }

        let mut header_end = pos;
        if header_end > header_start + 1 && self.buffer[header_end - 1] == b'\r' {
            header_end -= 1;
        }

        let header = self.buffer[header_start + 1..header_end].to_vec();

        // Skip newline
        if pos < self.buffer.len() {
            pos += 1;
        }

        // Read sequence lines and track total length
        let mut sequence_lines = Vec::with_capacity(self.sequence_hint / 80);
        let mut total_sequence_length = 0usize;

        while pos < self.buffer.len() {
            // Check if we've hit the next record
            if self.buffer[pos] == b'>' {
                break;
            }

            // Find line end
            let line_start = pos;
            while pos < self.buffer.len() && self.buffer[pos] != b'\n' {
                pos += 1;
            }

            let mut line_end = pos;
            if line_end > line_start && self.buffer[line_end - 1] == b'\r' {
                line_end -= 1;
            }

            // Skip empty lines
            if line_end > line_start {
                let line = self.buffer[line_start..line_end].to_vec();
                total_sequence_length += line.len();
                sequence_lines.push(line);
            }

            // Skip newline
            if pos < self.buffer.len() {
                pos += 1;
            }
        }

        self.position = pos;
        Some(Ok((header, sequence_lines, total_sequence_length)))
    }
}

impl Iterator for ZeroCopyFastaReader {
    type Item = std::io::Result<(Vec<u8>, Vec<Vec<u8>>, usize)>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_record()
    }
}

impl StreamingFastaReader {
    /// Create a new streaming FASTA reader that reuses memory
    /// sequence_size_hint: Expected number of sequence lines per record for optimal memory allocation
    pub fn from_file<P: AsRef<Path>>(path: P, sequence_size_hint: usize) -> Result<Self> {
        let file = File::open(path)?;
        let reader = BufReader::with_capacity(64 * 1024, file); // Same buffer size as FastaReader
        let lines = reader.lines();
        Ok(StreamingFastaReader {
            lines,
            sequence_lines: Vec::with_capacity(sequence_size_hint.max(64)), // Pre-allocate capacity
            next_header: None,
        })
    }

    /// Read next FASTA record, reusing internal memory buffers
    /// Returns (header, sequence_lines, valid_count, total_sequence_length)
    /// Only the first `valid_count` entries in sequence_lines are valid for this record
    pub fn next_record(&mut self) -> Option<Result<(String, &Vec<String>, usize, usize)>> {
        let header = if let Some(h) = self.next_header.take() {
            h
        } else {
            loop {
                match self.lines.next() {
                    Some(Ok(line)) => {
                        if line.is_empty() || line.chars().all(|c| c.is_whitespace()) {
                            continue;
                        }
                        let trimmed = line.trim();
                        if !trimmed.starts_with('>') {
                            return Some(Err(std::io::Error::new(
                                std::io::ErrorKind::InvalidData,
                                "FASTA record must start with '>'",
                            )));
                        }
                        break trimmed[1..].to_string();
                    }
                    Some(Err(e)) => return Some(Err(e)),
                    None => return None,
                }
            }
        };

        // Clear the sequence lines but keep the capacity for reuse
        self.sequence_lines.clear();
        let mut total_sequence_length = 0usize;

        loop {
            match self.lines.next() {
                Some(Ok(line)) => {
                    if line.is_empty() || line.chars().all(|c| c.is_whitespace()) {
                        continue;
                    }
                    let trimmed = line.trim();
                    if trimmed.starts_with('>') {
                        self.next_header = Some(trimmed[1..].to_string());
                        break;
                    }
                    total_sequence_length += trimmed.len();
                    self.sequence_lines.push(trimmed.to_string());
                }
                Some(Err(e)) => return Some(Err(e)),
                None => break,
            }
        }

        let valid_count = self.sequence_lines.len();
        Some(Ok((header, &self.sequence_lines, valid_count, total_sequence_length)))
    }
}

impl Iterator for StreamingFastaReader {
    type Item = Result<(String, Vec<String>, usize, usize)>;

    fn next(&mut self) -> Option<Self::Item> {
        // For the iterator interface, we need to return owned data
        match self.next_record()? {
            Ok((header, sequence_lines, valid_count, total_length)) => {
                // Clone only the valid portion of the sequence lines
                let valid_lines = sequence_lines[..valid_count].to_vec();
                Some(Ok((header, valid_lines, valid_count, total_length)))
            }
            Err(e) => Some(Err(e))
        }
    }
}
