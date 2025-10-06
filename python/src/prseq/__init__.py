from typing import Iterator, NamedTuple, Generator, Tuple, List
from .prseq import FastaRecord as _FastaRecord, FastaReader as _FastaReader, ZeroCopyFastaReader as _ZeroCopyFastaReader, read_fasta_zero_copy as _read_fasta_zero_copy

__version__ = "0.0.4"
__all__ = ["FastaRecord", "FastaReader", "read_fasta", "ZeroCopyFastaReader", "read_fasta_zero_copy"]


class FastaRecord(NamedTuple):
    """A single FASTA sequence record.
    
    Attributes:
        header: The sequence header (without the '>' prefix)
        sequence: The sequence data
    """
    header: str
    sequence: str


class FastaReader:
    """Iterator over FASTA records in a file.
    
    Example:
        >>> reader = FastaReader("sequences.fasta")
        >>> for record in reader:
        ...     print(f"{record.header}: {len(record.sequence)} bp")
    """
    
    def __init__(self, path: str, sequence_size_hint: int | None = None) -> None:
        """Create a new FASTA reader.

        Args:
            path: Path to the FASTA file
            sequence_size_hint: Optional hint for expected sequence length in characters.
                              Helps optimize memory allocation. Use smaller values (100-1000)
                              for short sequences like primers, or larger values (50000+)
                              for genomes or long sequences.

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        self._reader = _FastaReader(path, sequence_size_hint)
    
    def __iter__(self) -> Iterator[FastaRecord]:
        """Return the iterator object."""
        return self
    
    def __next__(self) -> FastaRecord:
        """Get the next FASTA record.
        
        Returns:
            The next FastaRecord
            
        Raises:
            StopIteration: When there are no more records
            IOError: If there's an error reading the file
        """
        rust_record = next(self._reader)
        return FastaRecord(header=rust_record.header, sequence=rust_record.sequence)


def read_fasta(path: str, sequence_size_hint: int | None = None) -> list[FastaRecord]:
    """Read all FASTA records from a file.

    This is a convenience function that reads all records into memory.
    For large files, consider using FastaReader as an iterator instead.

    Args:
        path: Path to the FASTA file
        sequence_size_hint: Optional hint for expected sequence length in characters.
                          Helps optimize memory allocation. Use smaller values (100-1000)
                          for short sequences like primers, or larger values (50000+)
                          for genomes or long sequences.

    Returns:
        List of all FASTA records in the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    return list(FastaReader(path, sequence_size_hint))


class ZeroCopyFastaReader:
    """Zero-copy FASTA reader that yields bytes objects directly from Rust memory.

    This reader loads the entire file into memory and returns byte slices pointing
    directly into the Rust-allocated buffer. No copying or string allocation occurs
    in Python, making this extremely fast for applications that can work with bytes.

    Example:
        >>> reader = ZeroCopyFastaReader("sequences.fasta", sequence_hint=30000)
        >>> for header_bytes, sequence_lines in reader:
        ...     header = header_bytes.decode('utf-8')
        ...     sequence = b''.join(sequence_lines).decode('utf-8')
        ...     print(f"{header}: {len(sequence)} bp")
    """

    def __init__(self, path: str, sequence_hint: int = 8192) -> None:
        """Create a new zero-copy FASTA reader.

        Args:
            path: Path to the FASTA file
            sequence_hint: Expected sequence length for memory optimization

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        self._reader = _ZeroCopyFastaReader(path, sequence_hint)

    def __iter__(self) -> Generator[Tuple[bytes, List[bytes]], None, None]:
        """Iterate over FASTA records as (header_bytes, sequence_lines_bytes).

        Yields:
            Tuple of (header_bytes, sequence_lines) where:
            - header_bytes: bytes object of the header (without '>')
            - sequence_lines: List[bytes] of sequence lines from the file
        """
        return self

    def __next__(self) -> Tuple[bytes, List[bytes]]:
        """Get the next FASTA record as bytes objects."""
        result = next(self._reader)
        return result


def read_fasta_zero_copy(path: str, sequence_hint: int = 8192) -> List[Tuple[bytes, List[bytes]]]:
    """Read all FASTA records with zero-copy byte slices.

    This function loads the entire file into memory and returns byte slices pointing
    directly into the Rust-allocated buffer. No copying or string allocation occurs.

    Args:
        path: Path to the FASTA file
        sequence_hint: Expected sequence length for memory optimization

    Returns:
        List of (header_bytes, sequence_lines) tuples where:
        - header_bytes: bytes object of the header (without '>')
        - sequence_lines: List[bytes] of sequence lines from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file

    Example:
        >>> records = read_fasta_zero_copy("file.fasta", sequence_hint=30000)
        >>> for header_bytes, sequence_lines in records:
        ...     header = header_bytes.decode('utf-8')
        ...     sequence = b''.join(sequence_lines).decode('utf-8')
        ...     process_sequence(header, sequence)
    """
    return _read_fasta_zero_copy(path, sequence_hint)
