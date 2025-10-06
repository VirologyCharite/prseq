from typing import Iterator, NamedTuple
from .prseq import FastaRecord as _FastaRecord, FastaReader as _FastaReader

__version__ = "0.0.4"
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
