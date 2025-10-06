use prseq::{FastaReader, FastaRecord, read_fasta, ZeroCopyFastaReader, StreamingZeroCopyFastaReader};
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

#[test]
fn test_zero_copy_fasta_reader() {
    let file = create_test_fasta();
    let mut reader = ZeroCopyFastaReader::from_file(file.path(), 1024).unwrap();

    let mut records = Vec::new();
    while let Some(result) = reader.next_record() {
        records.push(result.unwrap());
    }

    assert_eq!(records.len(), 2);

    // Test first record
    let (header1, seq_lines1, total_len1) = &records[0];
    assert_eq!(header1, b"seq1 description one");
    assert_eq!(seq_lines1.len(), 2);
    assert_eq!(seq_lines1[0], b"ATCGATCG");
    assert_eq!(seq_lines1[1], b"GCTAGCTA");
    assert_eq!(*total_len1, 16); // 8 + 8

    // Test second record
    let (header2, seq_lines2, total_len2) = &records[1];
    assert_eq!(header2, b"seq2 description two");
    assert_eq!(seq_lines2.len(), 1);
    assert_eq!(seq_lines2[0], b"GGGGCCCC");
    assert_eq!(*total_len2, 8);
}

#[test]
fn test_zero_copy_iterator_interface() {
    let file = create_test_fasta();
    let reader = ZeroCopyFastaReader::from_file(file.path(), 1024).unwrap();

    let records: Vec<_> = reader.map(|r| r.unwrap()).collect();

    assert_eq!(records.len(), 2);
    assert_eq!(records[0].0, b"seq1 description one");
    assert_eq!(records[0].2, 16); // total length
    assert_eq!(records[1].0, b"seq2 description two");
    assert_eq!(records[1].2, 8); // total length
}

#[test]
fn test_zero_copy_large_sequence_hint() {
    let file = create_test_fasta();
    let mut reader = ZeroCopyFastaReader::from_file(file.path(), 50000).unwrap();

    // Should still work with large sequence hint
    let record = reader.next_record().unwrap().unwrap();
    assert_eq!(record.0, b"seq1 description one");
    assert_eq!(record.2, 16); // total length
}

#[test]
fn test_zero_copy_empty_lines() {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, ">test header").unwrap();
    writeln!(file, "").unwrap(); // Empty line
    writeln!(file, "ATCGATCG").unwrap();
    writeln!(file, "").unwrap(); // Another empty line
    writeln!(file, "GCTAGCTA").unwrap();

    let mut reader = ZeroCopyFastaReader::from_file(file.path(), 1024).unwrap();
    let (header, seq_lines, total_len) = reader.next_record().unwrap().unwrap();

    assert_eq!(header, b"test header");
    // Empty lines should be skipped
    assert_eq!(seq_lines.len(), 2);
    assert_eq!(seq_lines[0], b"ATCGATCG");
    assert_eq!(seq_lines[1], b"GCTAGCTA");
    assert_eq!(total_len, 16); // 8 + 8
}

#[test]
fn test_streaming_zero_copy_fasta_reader() {
    let file = create_test_fasta();
    let mut reader = StreamingZeroCopyFastaReader::from_file(file.path(), 1024).unwrap();

    let mut records = Vec::new();
    while let Some(result) = reader.next_record() {
        let (header, sequence, total_len) = result.unwrap();
        // Copy the data since it's only valid until next call
        records.push((header.to_vec(), sequence.to_vec(), total_len));
    }

    assert_eq!(records.len(), 2);

    // Test first record
    assert_eq!(records[0].0, b"seq1 description one");
    assert_eq!(records[0].1, b"ATCGATCGGCTAGCTA"); // Concatenated sequence
    assert_eq!(records[0].2, 16);

    // Test second record
    assert_eq!(records[1].0, b"seq2 description two");
    assert_eq!(records[1].1, b"GGGGCCCC");
    assert_eq!(records[1].2, 8);
}

#[test]
fn test_streaming_zero_copy_small_buffer() {
    let file = create_test_fasta();
    let mut reader = StreamingZeroCopyFastaReader::from_file(file.path(), 32).unwrap(); // Very small buffer

    let mut count = 0;
    while let Some(result) = reader.next_record() {
        let (header, sequence, total_len) = result.unwrap();
        count += 1;

        if count == 1 {
            assert_eq!(header, b"seq1 description one");
            assert_eq!(sequence, b"ATCGATCGGCTAGCTA");
            assert_eq!(total_len, 16);
        } else if count == 2 {
            assert_eq!(header, b"seq2 description two");
            assert_eq!(sequence, b"GGGGCCCC");
            assert_eq!(total_len, 8);
        }
    }

    assert_eq!(count, 2);
}

#[test]
fn test_streaming_zero_copy_iterator() {
    let file = create_test_fasta();
    let reader = StreamingZeroCopyFastaReader::from_file(file.path(), 1024).unwrap();

    let mut records = Vec::new();
    for result in reader {
        let (header, sequence, total_len) = result.unwrap();
        // Copy the data since it's only valid until next iteration
        records.push((header.to_vec(), sequence.to_vec(), total_len));
    }

    assert_eq!(records.len(), 2);
    assert_eq!(records[0].0, b"seq1 description one");
    assert_eq!(records[1].0, b"seq2 description two");
}
