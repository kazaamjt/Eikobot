"""
Contains various odds and ends.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Index:
    """Index of where a token came from."""

    line: int
    col: int
    file: Path

    def __repr__(self) -> str:
        return f"{self.file}({self.line + 1},{self.col + 1})"
