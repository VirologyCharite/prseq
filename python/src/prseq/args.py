import os
import io
from pathlib import Path
from typing import BinaryIO
import builtins
from unittest.mock import Mock

_original_open = builtins.open


def _testing() -> bool:
    return (
        "PYTEST_CURRENT_TEST" in os.environ or
        builtins.open is not _original_open or
        isinstance(builtins.open, Mock)
    )


def parse_args(source: str | Path | BinaryIO | None) -> tuple[str | None, BinaryIO | None]:

    if isinstance(source, (str, Path)):
        str_source = str(source)
        if str_source == "-":
            # stdin.
            return None, None

        if Path(source).exists():
            return str_source, None

        if _testing():
            # open is mocked. We need to play along and use the mocked version. We can't
            # pass the source filename to the Rust reader because the file doesn't exist
            # and an exception would be raised. Note that we do not (cannot) close the
            # mock "file" - we are not in charge!
            return None, open(source, "rb")

        raise ValueError("File {source!r} does not exist.")

    if source is None:
        # stdin.
        return None, None

    if hasattr(source, "read"):
        if isinstance(source, io.TextIOBase):
            raise IOError("file object was not opened in binary mode. Use mode='rb'.")

        return None, source

    raise TypeError(
        "source must be a str, Path, file object, or None, not "
        f"{type(source).__name__}"
    )
