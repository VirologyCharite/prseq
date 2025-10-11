"""FASTA file parsing functionality."""

from pathlib import Path
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
    """Iterator over FASTA records from a file, file object, or stdin.

    Examples:
        >>> reader = FastaReader("sequences.fasta")  # Read from file path (str)
        >>> reader = FastaReader(Path("sequences.fasta"))  # Read from Path object
        >>> reader = FastaReader()  # Read from stdin
        >>> with open("file.fasta", "rb") as f:
        ...     reader = FastaReader(f)  # Read from file object
        >>> for record in reader:
        ...     print(f"{record.id}: {len(record.sequence)} bp")
    """

    def __init__(
        self,
        source: str | Path | object | None = None,
        sequence_size_hint: int | None = None,
    ) -> None:
        """Create a new FASTA reader.

        Args:
            source: Input source, can be:
                - str or Path: Path to a FASTA file (uncompressed, .gz, or .bz2)
                - file object: An open file-like object in binary mode ('rb')
                - None or "-": Read from stdin
            sequence_size_hint: Optional hint for expected sequence length in characters.
                              Helps optimize memory allocation. Use smaller values (100-1000)
                              for short sequences like primers, or larger values (50000+)
                              for genomes or long sequences.

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file, or if a file object
                    is opened in text mode instead of binary mode

        Note:
            File objects must be opened in binary mode ('rb'). Text mode ('r') will
            raise an error. Example: `with open("file.fasta", "rb") as f: ...`
        """
        if isinstance(source, (str, Path)):
            # String or Path object - treat as file path
            self._reader = _prseq.FastaReader(path=str(source), file=None, sequence_size_hint=sequence_size_hint)
        elif source is None:
            # None - read from stdin
            self._reader = _prseq.FastaReader(path=None, file=None, sequence_size_hint=sequence_size_hint)
        elif hasattr(source, 'read'):
            # File-like object with read() method
            self._reader = _prseq.FastaReader(path=None, file=source, sequence_size_hint=sequence_size_hint)
        else:
            raise TypeError(f"source must be a str, Path, file object, or None, not {type(source).__name__}")

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