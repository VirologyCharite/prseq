from typing import Iterator, NamedTuple, Generator, Tuple, List
from .prseq import FastaRecord as _FastaRecord, FastaReader as _FastaReader

__version__ = "0.0.5"
__all__ = ["FastaRecord", "FastaReader", "read_fasta"]


class FastaRecord(NamedTuple):
    """A single FASTA sequence record.
    
    Attributes:
        header: The sequence header (without the '>' prefix)
        sequence: The sequence data
    """
    header: str
    sequence: str


class FastaReader:
    """Iterator over FASTA records from a file or stdin.

    Example:
        >>> reader = FastaReader("sequences.fasta")  # Read from file
        >>> reader = FastaReader()  # Read from stdin
        >>> reader = FastaReader("-")  # Read from stdin explicitly
        >>> for record in reader:
        ...     print(f"{record.header}: {len(record.sequence)} bp")
    """

    def __init__(self, path: str | None = None, sequence_size_hint: int | None = None) -> None:
        """Create a new FASTA reader.

        Args:
            path: Path to the FASTA file, or None/"-" for stdin. Files can be uncompressed,
                  gzip-compressed (.gz), or bzip2-compressed (.bz2). Compression is
                  automatically detected.
            sequence_size_hint: Optional hint for expected sequence length in characters.
                              Helps optimize memory allocation. Use smaller values (100-1000)
                              for short sequences like primers, or larger values (50000+)
                              for genomes or long sequences.

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        self._reader = _FastaReader(path, sequence_size_hint)

    @classmethod
    def from_stdin(cls, sequence_size_hint: int | None = None) -> 'FastaReader':
        """Create a FastaReader that reads from stdin.

        Args:
            sequence_size_hint: Optional hint for expected sequence length in characters.

        Returns:
            A FastaReader instance reading from stdin
        """
        reader = cls.__new__(cls)
        reader._reader = _FastaReader.from_stdin(sequence_size_hint)
        return reader
    
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


def read_fasta(path: str | None = None, sequence_size_hint: int | None = None) -> list[FastaRecord]:
    """Read all FASTA records from a file or stdin.

    This is a convenience function that reads all records into memory.
    For large files, consider using FastaReader as an iterator instead.

    Args:
        path: Path to the FASTA file, or None/"-" for stdin. Files can be uncompressed,
              gzip-compressed (.gz), or bzip2-compressed (.bz2). Compression is
              automatically detected.
        sequence_size_hint: Optional hint for expected sequence length in characters.
                          Helps optimize memory allocation. Use smaller values (100-1000)
                          for short sequences like primers, or larger values (50000+)
                          for genomes or long sequences.

    Returns:
        List of all FASTA records from the input

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the input
    """
    return list(FastaReader(path, sequence_size_hint))


