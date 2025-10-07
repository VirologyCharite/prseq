mod common;
pub mod fasta;
pub mod fastq;

// Re-export the main FASTA types for backward compatibility
pub use fasta::{read_fasta, read_fasta_with_capacity, FastaReader, FastaRecord};

// Re-export FASTQ types
pub use fastq::{read_fastq, read_fastq_with_capacity, FastqReader, FastqRecord};
