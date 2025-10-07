mod common;
pub mod fasta;
pub mod fastq;

// Re-export the main FASTA types for backward compatibility
pub use fasta::{FastaRecord, FastaReader, read_fasta, read_fasta_with_capacity};

// Re-export FASTQ types
pub use fastq::{FastqRecord, FastqReader, read_fastq, read_fastq_with_capacity};


