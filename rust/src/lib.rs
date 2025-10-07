use std::fs::File;
use std::io::{BufRead, BufReader, Read, Result, Cursor};
use std::path::Path;
use flate2::read::GzDecoder;
use bzip2::read::BzDecoder;

/// Represents a single FASTA sequence with its header and sequence data
#[derive(Debug, Clone, PartialEq)]
pub struct FastaRecord {
    pub header: String,
    pub sequence: String,
}

/// Iterator over FASTA records from any readable source
pub struct FastaReader {
    lines: std::io::Lines<BufReader<Box<dyn Read + Send>>>,
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
        Self::from_reader_with_capacity(file, sequence_size_hint)
    }

    /// Create a new FastaReader from stdin
    pub fn from_stdin() -> Result<Self> {
        Self::from_stdin_with_capacity(8192)
    }

    /// Create a new FastaReader from stdin with a sequence size hint
    pub fn from_stdin_with_capacity(sequence_size_hint: usize) -> Result<Self> {
        let stdin = std::io::stdin();
        Self::from_reader_with_capacity(stdin, sequence_size_hint)
    }

    /// Create a new FastaReader from any readable source with compression detection
    pub fn from_reader_with_capacity<R: Read + Send + 'static>(mut reader: R, sequence_size_hint: usize) -> Result<Self> {
        // Peek at first few bytes to detect compression
        let mut magic_buf = [0u8; 3];
        let mut bytes_read = 0;

        // Try to read magic bytes
        while bytes_read < magic_buf.len() {
            match reader.read(&mut magic_buf[bytes_read..])? {
                0 => break, // EOF
                n => bytes_read += n,
            }
        }

        // Create appropriate decoder based on magic bytes
        let decoded_reader: Box<dyn Read + Send> = if bytes_read >= 2 && magic_buf[0] == 0x1f && magic_buf[1] == 0x8b {
            // Gzip format - make owned copy of magic bytes
            let magic_copy = magic_buf[..bytes_read].to_vec();
            let chained = Cursor::new(magic_copy).chain(reader);
            let gz_reader = GzDecoder::new(chained);
            Box::new(gz_reader)
        } else if bytes_read >= 3 && magic_buf[0] == 0x42 && magic_buf[1] == 0x5a && magic_buf[2] == 0x68 {
            // Bzip2 format - make owned copy of magic bytes
            let magic_copy = magic_buf[..bytes_read].to_vec();
            let chained = Cursor::new(magic_copy).chain(reader);
            let bz_reader = BzDecoder::new(chained);
            Box::new(bz_reader)
        } else {
            // Uncompressed - put magic bytes back
            let magic_copy = magic_buf[..bytes_read].to_vec();
            let cursor = Cursor::new(magic_copy);
            Box::new(cursor.chain(reader))
        };

        let buf_reader = BufReader::with_capacity(64 * 1024, decoded_reader);
        let lines = buf_reader.lines();

        Ok(FastaReader {
            lines,
            next_header: None,
            sequence_size_hint: sequence_size_hint.max(64),
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;
    use tempfile::NamedTempFile;
    use std::io::Write;

    #[test]
    fn test_basic_reading() {
        let content = b">seq1 test\nATCG\nGCTA\n>seq2 test\nGGCC\n";
        let cursor = Cursor::new(content);
        let mut reader = FastaReader::from_reader_with_capacity(cursor, 1024).unwrap();

        let record1 = reader.next().unwrap().unwrap();
        assert_eq!(record1.header, "seq1 test");
        assert_eq!(record1.sequence, "ATCGGCTA");

        let record2 = reader.next().unwrap().unwrap();
        assert_eq!(record2.header, "seq2 test");
        assert_eq!(record2.sequence, "GGCC");

        assert!(reader.next().is_none());
    }

    #[test]
    fn test_gzip_compression() {
        use flate2::write::GzEncoder;
        use flate2::Compression;

        let content = b">seq1 compressed\nATCG\n>seq2 compressed\nGGCC\n";
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(content).unwrap();
        let compressed = encoder.finish().unwrap();

        let cursor = Cursor::new(compressed);
        let mut reader = FastaReader::from_reader_with_capacity(cursor, 1024).unwrap();

        let record1 = reader.next().unwrap().unwrap();
        assert_eq!(record1.header, "seq1 compressed");
        assert_eq!(record1.sequence, "ATCG");

        let record2 = reader.next().unwrap().unwrap();
        assert_eq!(record2.header, "seq2 compressed");
        assert_eq!(record2.sequence, "GGCC");

        assert!(reader.next().is_none());
    }

    #[test]
    fn test_bzip2_compression() {
        use bzip2::write::BzEncoder;
        use bzip2::Compression;

        let content = b">seq1 bz2\nATCG\n>seq2 bz2\nGGCC\n";
        let mut encoder = BzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(content).unwrap();
        let compressed = encoder.finish().unwrap();

        let cursor = Cursor::new(compressed);
        let mut reader = FastaReader::from_reader_with_capacity(cursor, 1024).unwrap();

        let record1 = reader.next().unwrap().unwrap();
        assert_eq!(record1.header, "seq1 bz2");
        assert_eq!(record1.sequence, "ATCG");

        let record2 = reader.next().unwrap().unwrap();
        assert_eq!(record2.header, "seq2 bz2");
        assert_eq!(record2.sequence, "GGCC");

        assert!(reader.next().is_none());
    }

    #[test]
    fn test_file_reading() {
        let content = ">seq1 file test\nATCG\nGCTA\n>seq2 file test\nGGCC\n";
        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(content.as_bytes()).unwrap();

        let mut reader = FastaReader::from_file(temp_file.path()).unwrap();

        let record1 = reader.next().unwrap().unwrap();
        assert_eq!(record1.header, "seq1 file test");
        assert_eq!(record1.sequence, "ATCGGCTA");

        let record2 = reader.next().unwrap().unwrap();
        assert_eq!(record2.header, "seq2 file test");
        assert_eq!(record2.sequence, "GGCC");

        assert!(reader.next().is_none());
    }
}

