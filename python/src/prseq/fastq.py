import os
from pathlib import Path
from typing import Iterator, BinaryIO

from .args import parse_args

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
        return (
            self.id == other.id
            and self.sequence == other.sequence
            and self.quality == other.quality
        )


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
        source: str | Path | BinaryIO | None = None,
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
            raise an error.
        """
        path, fp = parse_args(source)

        self._reader = _prseq.FastqReader(
            path=path, file=fp, sequence_size_hint=sequence_size_hint
        )

    def __iter__(self) -> Iterator[FastqRecord]:
        return self

    def __next__(self) -> FastqRecord:
        try:
            rust_record = next(self._reader)
            return FastqRecord(
                rust_record.id, rust_record.sequence, rust_record.quality
            )
        except StopIteration:
            raise


def read_fastq(
    path: str | Path | None = None, sequence_size_hint: int | None = None
) -> list[FastqRecord]:
    """Read all FASTQ records from a file into a list."""
    if path is None or str(path) == "-":
        # Read from stdin.
        return list(FastqReader(sequence_size_hint=sequence_size_hint))
    else:
        # Read from file - use efficient Rust convenience functions.
        rust_records = _prseq.read_fastq(path, sequence_size_hint)
        return [FastqRecord(r.id, r.sequence, r.quality) for r in rust_records]
