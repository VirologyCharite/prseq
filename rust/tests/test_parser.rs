use prseq::{FastaReader, FastaRecord, read_fasta};
use std::io::Write;
use tempfile::NamedTempFile;

fn create_test_fasta() -> NamedTempFile {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, ">seq1 description one").unwrap();
    writeln!(file, "ATCGATCG").unwrap();
    writeln!(file, "GCTAGCTA").unwrap();
    writeln!(file, ">seq2 description two").unwrap();
    writeln!(file, "GGGGCCCC").unwrap();
    file
}

#[test]
fn test_fasta_reader_iterator() {
    let file = create_test_fasta();
    let reader = FastaReader::from_file(file.path()).unwrap();
    
    let records: Vec<FastaRecord> = reader.map(|r| r.unwrap()).collect();
    
    assert_eq!(records.len(), 2);
    assert_eq!(records[0].header, "seq1 description one");
    assert_eq!(records[0].sequence, "ATCGATCGGCTAGCTA");
    assert_eq!(records[1].header, "seq2 description two");
    assert_eq!(records[1].sequence, "GGGGCCCC");
}

#[test]
fn test_read_fasta_convenience() {
    let file = create_test_fasta();
    let records = read_fasta(file.path()).unwrap();
    
    assert_eq!(records.len(), 2);
    assert_eq!(records[0].sequence, "ATCGATCGGCTAGCTA");
}

#[test]
fn test_invalid_fasta() {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, "INVALID LINE").unwrap();
    
    let reader = FastaReader::from_file(file.path()).unwrap();
    let result: Result<Vec<_>, _> = reader.collect();
    
    assert!(result.is_err());
}
