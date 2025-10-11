"""FASTQ file parsing functionality."""

from pathlib import Path
from typing import Iterator

import prseq._prseq as _prseq


class FastqRecord:
    """Represents a single FASTQ sequence record."""

    def __init__(self, id: str, sequence: str, quality: str):
        self.id = id
        self.sequence = sequence
        self.quality = quality

    def __repr__(self) -> str:
        return f"FastqRecord(id='{self.id}', sequence='{self.sequence}', quality='{self.quality}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FastqRecord):
            return False
        return self.id == other.id and self.sequence == other.sequence and self.quality == other.quality


class FastqReader:
    """Iterator for reading FASTQ records from a file, file object, or stdin.

    Examples:
        >>> reader = FastqReader("sequences.fastq")  # Read from file path (str)
        >>> reader = FastqReader(Path("sequences.fastq"))  # Read from Path object
        >>> reader = FastqReader()  # Read from stdin
        >>> with open("file.fastq", "rb") as f:
        ...     reader = FastqReader(f)  # Read from file object
        >>> for record in reader:
        ...     print(f"{record.id}: {len(record.sequence)} bp")
    """

    def __init__(
        self,
        source: str | Path | object | None = None,
        sequence_size_hint: int | None = None,
    ):
        """Create a new FASTQ reader.

        Args:
            source: Input source, can be:
                - str or Path: Path to a FASTQ file (uncompressed, .gz, or .bz2)
                - file object: An open file-like object in binary mode ('rb')
                - None or "-": Read from stdin
            sequence_size_hint: Optional hint for expected sequence length in characters.
                              Helps optimize memory allocation.

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file, or if a file object
                    is opened in text mode instead of binary mode

        Note:
            File objects must be opened in binary mode ('rb'). Text mode ('r') will
            raise an error. Example: `with open("reads.fastq", "rb") as f: ...`
        """
        if isinstance(source, (str, Path)):
            # String or Path object - treat as file path
            self._reader = _prseq.FastqReader(path=str(source), file=None, sequence_size_hint=sequence_size_hint)
        elif source is None:
            # None - read from stdin
            self._reader = _prseq.FastqReader(path=None, file=None, sequence_size_hint=sequence_size_hint)
        elif hasattr(source, 'read'):
            # File-like object with read() method
            self._reader = _prseq.FastqReader(path=None, file=source, sequence_size_hint=sequence_size_hint)
        else:
            raise TypeError(f"source must be a str, Path, file object, or None, not {type(source).__name__}")

    def __iter__(self) -> Iterator[FastqRecord]:
        return self

    def __next__(self) -> FastqRecord:
        try:
            rust_record = next(self._reader)
            return FastqRecord(rust_record.id, rust_record.sequence, rust_record.quality)
        except StopIteration:
            raise


def read_fastq(path: str | None = None, sequence_size_hint: int | None = None) -> list[FastqRecord]:
    """Read all FASTQ records from a file into a list."""
    if path is None or path == "-":
        # Read from stdin - use iterator since we don't have stdin convenience functions
        reader = FastqReader.from_stdin(sequence_size_hint)
        return list(reader)
    else:
        # Read from file - use efficient Rust convenience functions
        rust_records = _prseq.read_fastq(path, sequence_size_hint)
        return [FastqRecord(r.id, r.sequence, r.quality) for r in rust_records]