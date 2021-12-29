from dataclasses import dataclass

@dataclass(frozen=False, eq=False)
class FileInfo:
    path: str  # Might be full_path or rel_path, depending on the configuration and CWD
    size: int = None
    checksum: bytes = None

    def open(self):
        return open(self.path, 'rb')

    def __hash__(self):
        return hash(self.path)
