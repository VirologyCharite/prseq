"""FASTQ file parsing functionality."""

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

    Example:
        >>> reader = FastqReader.from_file("sequences.fastq")  # Read from file
        >>> reader = FastqReader.from_stdin()  # Read from stdin
        >>> with open("file.fastq", "rb") as f:
        ...     reader = FastqReader(file=f)  # Read from file object
        >>> for record in reader:
        ...     print(f"{record.id}: {len(record.sequence)} bp")
    """

    def __init__(
        self,
        path: str | None = None,
        file: object | None = None,
        sequence_size_hint: int | None = None,
    ):
        """Create a new FASTQ reader.

        Args:
            path: Path to the FASTQ file, or None/"-" for stdin. Files can be uncompressed,
                  gzip-compressed (.gz), or bzip2-compressed (.bz2). Compression is
                  automatically detected.
            file: A Python file-like object opened in binary mode. If provided, path must be None.
            sequence_size_hint: Optional hint for expected sequence length in characters.
                              Helps optimize memory allocation.

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
            ValueError: If both path and file are provided
        """
        self._reader = _prseq.FastqReader(path=path, file=file, sequence_size_hint=sequence_size_hint)

    @classmethod
    def from_file(cls, path: str, sequence_size_hint: int | None = None) -> 'FastqReader':
        """Create a FastqReader from a file path."""
        return cls(path=path, sequence_size_hint=sequence_size_hint)

    @classmethod
    def from_file_object(cls, file: object, sequence_size_hint: int | None = None) -> 'FastqReader':
        """Create a FastqReader from a Python file-like object."""
        return cls(file=file, sequence_size_hint=sequence_size_hint)

    @classmethod
    def from_stdin(cls, sequence_size_hint: int | None = None) -> 'FastqReader':
        """Create a FastqReader from stdin."""
        return cls(path=None, sequence_size_hint=sequence_size_hint)

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