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

/// Streaming zero-copy FASTA reader that uses a fixed buffer and reuses memory
/// WARNING: The returned byte slices are only valid until the next call to next_record()
/// This is designed for very large files (TB+) that cannot fit in memory
pub struct StreamingZeroCopyFastaReader {
    file: std::fs::File,
    buffer: Vec<u8>,
    buffer_pos: usize,
    buffer_len: usize,
    overflow_buffer: Vec<u8>, // For records that span buffer boundaries
    eof: bool,
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

impl StreamingZeroCopyFastaReader {
    /// Create a new streaming zero-copy FASTA reader
    /// buffer_size: Size of the internal buffer in bytes (e.g., 64KB = 65536)
    pub fn from_file<P: AsRef<Path>>(path: P, buffer_size: usize) -> Result<Self> {
        let file = std::fs::File::open(path)?;
        let buffer_size = buffer_size.max(8192); // Minimum 8KB buffer
        Ok(StreamingZeroCopyFastaReader {
            file,
            buffer: vec![0; buffer_size],
            buffer_pos: 0,
            buffer_len: 0,
            overflow_buffer: Vec::new(),
            eof: false,
        })
    }

    /// Fill the buffer with more data from the file
    fn fill_buffer(&mut self) -> Result<()> {
        use std::io::Read;

        if self.eof {
            return Ok(());
        }

        // Move remaining data to the beginning of buffer
        if self.buffer_pos > 0 && self.buffer_pos < self.buffer_len {
            let remaining = self.buffer_len - self.buffer_pos;
            self.buffer.copy_within(self.buffer_pos..self.buffer_len, 0);
            self.buffer_pos = 0;
            self.buffer_len = remaining;
        } else {
            self.buffer_pos = 0;
            self.buffer_len = 0;
        }

        // Read more data
        let bytes_read = self.file.read(&mut self.buffer[self.buffer_len..])?;
        self.buffer_len += bytes_read;

        if bytes_read == 0 {
            self.eof = true;
        }

        Ok(())
    }

    /// Find the next complete FASTA record
    /// Returns (header_bytes, sequence_bytes, total_sequence_length)
    /// The returned Vec<u8> reuses internal buffers for memory efficiency
    pub fn next_record(&mut self) -> Option<Result<(Vec<u8>, Vec<u8>, usize)>> {
        loop {
            // Ensure we have data
            if self.buffer_pos >= self.buffer_len {
                if let Err(e) = self.fill_buffer() {
                    return Some(Err(e));
                }
                if self.buffer_len == 0 {
                    return None; // EOF
                }
            }

            // Find header start
            while self.buffer_pos < self.buffer_len && self.buffer[self.buffer_pos] != b'>' {
                self.buffer_pos += 1;
            }

            if self.buffer_pos >= self.buffer_len {
                if self.eof {
                    return None;
                }
                continue; // Need more data
            }

            // Found '>', now find end of header line
            let header_start = self.buffer_pos + 1; // Skip '>'
            let mut header_end = header_start;

            while header_end < self.buffer_len && self.buffer[header_end] != b'\n' {
                header_end += 1;
            }

            if header_end >= self.buffer_len && !self.eof {
                // Header spans buffer boundary - need to handle this case
                if let Err(e) = self.fill_buffer() {
                    return Some(Err(e));
                }
                continue;
            }

            // Handle CRLF
            let mut actual_header_end = header_end;
            if actual_header_end > header_start && self.buffer[actual_header_end - 1] == b'\r' {
                actual_header_end -= 1;
            }

            let header = self.buffer[header_start..actual_header_end].to_vec();

            // Move past the newline
            self.buffer_pos = if header_end < self.buffer_len { header_end + 1 } else { header_end };

            // Now collect sequence data until next '>' or EOF
            self.overflow_buffer.clear();
            let mut total_sequence_length = 0usize;

            loop {
                // Find end of sequence (next '>' or EOF)
                let mut seq_end = self.buffer_pos;
                while seq_end < self.buffer_len && self.buffer[seq_end] != b'>' {
                    seq_end += 1;
                }

                // Add current chunk to overflow buffer, skipping newlines
                for &byte in &self.buffer[self.buffer_pos..seq_end] {
                    if byte != b'\n' && byte != b'\r' {
                        self.overflow_buffer.push(byte);
                        total_sequence_length += 1;
                    }
                }

                self.buffer_pos = seq_end;

                if seq_end < self.buffer_len {
                    // Found next record start
                    break;
                } else if self.eof {
                    // End of file
                    break;
                } else {
                    // Need more data
                    if let Err(e) = self.fill_buffer() {
                        return Some(Err(e));
                    }
                    if self.buffer_len == 0 {
                        break; // EOF
                    }
                }
            }

            // Clone the sequence data - the overflow_buffer will be reused next iteration
            let sequence = self.overflow_buffer.clone();
            return Some(Ok((header, sequence, total_sequence_length)));
        }
    }
}

impl Iterator for StreamingZeroCopyFastaReader {
    type Item = Result<(Vec<u8>, Vec<u8>, usize)>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_record()
    }
}

