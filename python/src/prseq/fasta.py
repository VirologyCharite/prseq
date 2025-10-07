"""FASTA file parsing functionality."""

from typing import Iterator, NamedTuple

import prseq._prseq as _prseq


class FastaRecord(NamedTuple):
    """A single FASTA sequence record.

    Attributes:
        id: The sequence identifier (without the '>' prefix)
        sequence: The sequence data
    """
    id: str
    sequence: str


class FastaReader:
    """Iterator over FASTA records from a file or stdin.

    Example:
        >>> reader = FastaReader("sequences.fasta")  # Read from file
        >>> reader = FastaReader()  # Read from stdin
        >>> reader = FastaReader("-")  # Read from stdin explicitly
        >>> for record in reader:
        ...     print(f"{record.id}: {len(record.sequence)} bp")
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
        if path is None or path == "-":
            # Read from stdin
            self._reader = _prseq.FastaReader.from_stdin(sequence_size_hint)
        else:
            # Read from file
            self._reader = _prseq.FastaReader.from_file(path, sequence_size_hint)

    @classmethod
    def from_file(cls, path: str, sequence_size_hint: int | None = None) -> 'FastaReader':
        """Create a FastaReader from a file path."""
        return cls(path, sequence_size_hint)

    @classmethod
    def from_stdin(cls, sequence_size_hint: int | None = None) -> 'FastaReader':
        """Create a FastaReader from stdin."""
        return cls(None, sequence_size_hint)

    def __iter__(self) -> Iterator[FastaRecord]:
        return self

    def __next__(self) -> FastaRecord:
        try:
            rust_record = next(self._reader)
            return FastaRecord(rust_record.id, rust_record.sequence)
        except StopIteration:
            raise


def read_fasta(path: str, sequence_size_hint: int | None = None) -> list[FastaRecord]:
    """Read all FASTA records from a file into a list."""
    rust_records = _prseq.read_fasta(path, sequence_size_hint)
    return [FastaRecord(r.id, r.sequence) for r in rust_records]