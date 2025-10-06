from typing import Iterator, NamedTuple, Generator, Tuple, List
from .prseq import FastaRecord as _FastaRecord, FastaReader as _FastaReader, ZeroCopyFastaReader as _ZeroCopyFastaReader, StreamingFastaReader as _StreamingFastaReader, read_fasta_zero_copy as _read_fasta_zero_copy

__version__ = "0.0.4"
__all__ = ["FastaRecord", "FastaReader", "read_fasta", "ZeroCopyFastaReader", "read_fasta_zero_copy", "StreamingFastaReader"]


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

    def __iter__(self) -> Generator[Tuple[bytes, List[bytes], int], None, None]:
        """Iterate over FASTA records as (header_bytes, sequence_lines_bytes, total_length).

        Yields:
            Tuple of (header_bytes, sequence_lines, total_length) where:
            - header_bytes: bytes object of the header (without '>')
            - sequence_lines: List[bytes] of sequence lines from the file
            - total_length: int total sequence length (sum of all sequence lines)
        """
        return self

    def __next__(self) -> Tuple[bytes, List[bytes], int]:
        """Get the next FASTA record as bytes objects with total length."""
        result = next(self._reader)
        return result


def read_fasta_zero_copy(path: str, sequence_hint: int = 8192) -> List[Tuple[bytes, List[bytes], int]]:
    """Read all FASTA records with zero-copy byte slices.

    This function loads the entire file into memory and returns byte slices pointing
    directly into the Rust-allocated buffer. No copying or string allocation occurs.

    Args:
        path: Path to the FASTA file
        sequence_hint: Expected sequence length for memory optimization

    Returns:
        List of (header_bytes, sequence_lines, total_length) tuples where:
        - header_bytes: bytes object of the header (without '>')
        - sequence_lines: List[bytes] of sequence lines from the file
        - total_length: int total sequence length (sum of all sequence lines)

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file

    Example:
        >>> records = read_fasta_zero_copy("file.fasta", sequence_hint=30000)
        >>> for header_bytes, sequence_lines, total_length in records:
        ...     header = header_bytes.decode('utf-8')
        ...     sequence = b''.join(sequence_lines).decode('utf-8')
        ...     process_sequence(header, sequence, total_length)
    """
    return _read_fasta_zero_copy(path, sequence_hint)


class StreamingFastaReader:
    """Memory-efficient streaming FASTA reader for very large files (TB+).

    This reader reuses memory buffers between records and does NOT load the entire file
    into memory, making it suitable for files larger than available RAM. It should
    perform nearly identically to the regular FastaReader while using constant memory.

    Example:
        >>> reader = StreamingFastaReader("huge_file.fasta", sequence_size_hint=500)
        >>> for header, sequence_lines, valid_count, total_length in reader:
        ...     # Only first 'valid_count' items in sequence_lines are valid
        ...     valid_lines = sequence_lines[:valid_count]
        ...     concatenated = ''.join(valid_lines)
        ...     print(f"{header}: {total_length} bp")
    """

    def __init__(self, path: str, sequence_size_hint: int = 100) -> None:
        """Create a new streaming FASTA reader.

        Args:
            path: Path to the FASTA file
            sequence_size_hint: Expected number of sequence lines per record.
                              Used for optimal memory pre-allocation (default 100 lines).

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        self._reader = _StreamingFastaReader(path, sequence_size_hint)

    def __iter__(self) -> Generator[Tuple[str, List[str], int, int], None, None]:
        """Iterate over FASTA records as (header, sequence_lines, valid_count, total_length).

        Yields:
            Tuple of (header, sequence_lines, valid_count, total_length) where:
            - header: str of the header (without '>')
            - sequence_lines: List[str] of sequence lines (reused buffer)
            - valid_count: int number of valid entries in sequence_lines for this record
            - total_length: int total sequence length (sum of all valid lines)
        """
        return self

    def __next__(self) -> Tuple[str, List[str], int, int]:
        """Get the next FASTA record with memory reuse."""
        result = next(self._reader)
        return result
