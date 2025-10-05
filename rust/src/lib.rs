use std::fs::File;
use std::io::{BufRead, BufReader, Result, Seek};
use std::path::Path;

/// Represents a single FASTA sequence with its header and sequence data
#[derive(Debug, Clone, PartialEq)]
pub struct FastaRecord {
    pub header: String,
    pub sequence: String,
}

/// Iterator over FASTA records in a file
pub struct FastaReader {
    reader: BufReader<File>,
    buffer: String,
}

impl FastaReader {
    /// Create a new FastaReader from a file path
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let file = File::open(path)?;
        let reader = BufReader::new(file);
        Ok(FastaReader {
            reader,
            buffer: String::new(),
        })
    }

    /// Read the next FASTA record
    fn read_next(&mut self) -> Result<Option<FastaRecord>> {
        self.buffer.clear();
        
        // Read the header line
        let bytes_read = self.reader.read_line(&mut self.buffer)?;
        if bytes_read == 0 {
            return Ok(None); // EOF
        }

        let header = self.buffer.trim().to_string();
        if !header.starts_with('>') {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "FASTA record must start with '>'",
            ));
        }

        // Remove the '>' prefix
        let header = header[1..].to_string();

        // Read sequence lines until next header or EOF
        let mut sequence = String::new();
        loop {
            self.buffer.clear();
            let pos = self.reader.stream_position()?;
            let bytes_read = self.reader.read_line(&mut self.buffer)?;
            
            if bytes_read == 0 || self.buffer.starts_with('>') {
                // EOF or next record, rewind to start of line
                if self.buffer.starts_with('>') {
                    self.reader.seek(std::io::SeekFrom::Start(pos))?;
                }
                break;
            }
            
            sequence.push_str(self.buffer.trim());
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

/// Convenience function to read all FASTA records from a file
pub fn read_fasta<P: AsRef<Path>>(path: P) -> Result<Vec<FastaRecord>> {
    let reader = FastaReader::from_file(path)?;
    reader.collect()
}
