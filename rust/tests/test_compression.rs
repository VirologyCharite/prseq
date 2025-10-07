// Unit tests for compression and internal functionality
use prseq::FastaReader;
use std::io::{Cursor, Write};

#[test]
fn test_basic_reading() {
    let content = b">seq1 test\nATCG\nGCTA\n>seq2 test\nGGCC\n";
    let cursor = Cursor::new(content);
    let mut reader = FastaReader::from_reader_with_capacity(cursor, 1024).unwrap();

    let record1 = reader.next().unwrap().unwrap();
    assert_eq!(record1.id, "seq1 test");
    assert_eq!(record1.sequence, "ATCGGCTA");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 test");
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
    assert_eq!(record1.id, "seq1 compressed");
    assert_eq!(record1.sequence, "ATCG");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 compressed");
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
    assert_eq!(record1.id, "seq1 bz2");
    assert_eq!(record1.sequence, "ATCG");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 bz2");
    assert_eq!(record2.sequence, "GGCC");

    assert!(reader.next().is_none());
}

#[test]
fn test_file_reading() {
    use tempfile::NamedTempFile;

    let content = ">seq1 file test\nATCG\nGCTA\n>seq2 file test\nGGCC\n";
    let mut temp_file = NamedTempFile::new().unwrap();
    temp_file.write_all(content.as_bytes()).unwrap();

    let mut reader = FastaReader::from_file(temp_file.path()).unwrap();

    let record1 = reader.next().unwrap().unwrap();
    assert_eq!(record1.id, "seq1 file test");
    assert_eq!(record1.sequence, "ATCGGCTA");

    let record2 = reader.next().unwrap().unwrap();
    assert_eq!(record2.id, "seq2 file test");
    assert_eq!(record2.sequence, "GGCC");

    assert!(reader.next().is_none());
}
