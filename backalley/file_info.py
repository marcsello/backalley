from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=False, eq=False)
class FileInfo:
    path: str  # Might be full_path or rel_path, depending on the configuration and CWD
    size: int = None
    checksum: sha256 = None

    def open(self):
        return open(self.path, 'rb')

    def __hash__(self):
        return hash(self.path)
