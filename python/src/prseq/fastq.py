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
    """Iterator for reading FASTQ records from a file or stdin."""

    def __init__(self, reader):
        self._reader = reader

    @classmethod
    def from_file(cls, path: str, sequence_size_hint: int | None = None) -> 'FastqReader':
        """Create a FastqReader from a file path."""
        reader = _prseq.FastqReader.from_file(path, sequence_size_hint)
        return cls(reader)

    @classmethod
    def from_stdin(cls, sequence_size_hint: int | None = None) -> 'FastqReader':
        """Create a FastqReader from stdin."""
        reader = _prseq.FastqReader.from_stdin(sequence_size_hint)
        return cls(reader)

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