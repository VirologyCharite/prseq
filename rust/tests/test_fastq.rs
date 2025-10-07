// Tests for FASTQ parsing functionality
use prseq::fastq::{read_fastq, FastqReader};
use std::io::{Cursor, Write};
use tempfile::NamedTempFile;

#[test]
fn test_basic_fastq_reading() {
    let content = b"@seq1 test\nATCG\n+\nIIII\n@seq2 test\nGGCC\n+\nJJJJ\n";
    let cursor = Cursor::new(content);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let record1 = reader.next().unwrap().unwrap();
    assert_eq!(record1.id, "seq1 test");
    assert_eq!(record1.sequence, "ATCG");
    assert_eq!(record1.quality, "IIII");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 test");
    assert_eq!(record2.sequence, "GGCC");
    assert_eq!(record2.quality, "JJJJ");

    assert!(reader.next().is_none());
}

#[test]
fn test_multiline_fastq() {
    let content =
        b"@seq1 multiline\nATCG\nGCTA\n+seq1 multiline\nIIII\nJJJJ\n@seq2\nGG\nCC\n+\nKK\nLL\n";
    let cursor = Cursor::new(content);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let record1 = reader.next().unwrap().unwrap();
    assert_eq!(record1.id, "seq1 multiline");
    assert_eq!(record1.sequence, "ATCGGCTA");
    assert_eq!(record1.quality, "IIIIJJJJ");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2");
    assert_eq!(record2.sequence, "GGCC");
    assert_eq!(record2.quality, "KKLL");

    assert!(reader.next().is_none());
}

#[test]
fn test_fastq_plus_line_validation() {
    // Test that '+' line with wrong ID fails
    let content = b"@seq1\nATCG\n+wrong_id\nIIII\n";
    let cursor = Cursor::new(content);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let result = reader.next().unwrap();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .to_string()
        .contains("does not match header ID"));
}

#[test]
fn test_fastq_length_mismatch() {
    // Test sequence/quality length mismatch
    let content = b"@seq1\nATCG\n+\nII\n"; // quality too short
    let cursor = Cursor::new(content);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let result = reader.next().unwrap();
    assert!(result.is_err());
    let error_msg = result.unwrap_err().to_string();
    println!("Error message: {}", error_msg);
    assert!(
        error_msg.contains("Unexpected end of file")
            || error_msg.contains("does not match quality length")
    );
}

#[test]
fn test_fastq_file_reading() {
    let content = "@seq1 file test\nATCG\nGCTA\n+seq1 file test\nIIII\nJJJJ\n";
    let mut temp_file = NamedTempFile::new().unwrap();
    temp_file.write_all(content.as_bytes()).unwrap();

    let mut reader = FastqReader::from_file(temp_file.path()).unwrap();

    let record = reader.next().unwrap().unwrap();
    assert_eq!(record.id, "seq1 file test");
    assert_eq!(record.sequence, "ATCGGCTA");
    assert_eq!(record.quality, "IIIIJJJJ");

    assert!(reader.next().is_none());
}

#[test]
fn test_fastq_convenience_function() {
    let content = "@seq1\nATCG\n+\nIIII\n@seq2\nGGCC\n+\nJJJJ\n";
    let mut temp_file = NamedTempFile::new().unwrap();
    temp_file.write_all(content.as_bytes()).unwrap();

    let records = read_fastq(temp_file.path()).unwrap();

    assert_eq!(records.len(), 2);
    assert_eq!(records[0].id, "seq1");
    assert_eq!(records[0].sequence, "ATCG");
    assert_eq!(records[0].quality, "IIII");
    assert_eq!(records[1].sequence, "GGCC");
}

#[test]
fn test_invalid_fastq_start() {
    let content = b"INVALID LINE\nATCG\n+\nIIII\n";
    let cursor = Cursor::new(content);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let result = reader.next().unwrap();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .to_string()
        .contains("must start with '@'"));
}

#[test]
fn test_fastq_gzip_compression() {
    use flate2::write::GzEncoder;
    use flate2::Compression;

    let content = b"@seq1 compressed\nATCG\n+\nIIII\n@seq2 compressed\nGGCC\n+\nJJJJ\n";
    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(content).unwrap();
    let compressed = encoder.finish().unwrap();

    let cursor = Cursor::new(compressed);
    let mut reader = FastqReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let record1 = reader.next().unwrap().unwrap();
    assert_eq!(record1.id, "seq1 compressed");
    assert_eq!(record1.sequence, "ATCG");
    assert_eq!(record1.quality, "IIII");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 compressed");
    assert_eq!(record2.sequence, "GGCC");
    assert_eq!(record2.quality, "JJJJ");

    assert!(reader.next().is_none());
}
