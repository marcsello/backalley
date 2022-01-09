import enum
from dataclasses import dataclass


class EntityType(enum.Enum):
    FILE = 1
    EMPTY_DIRECTORY = 2


@dataclass(frozen=False, eq=False)
class EntityInfo:
    path: str  # we enforce it to be fullpath
    type: EntityType
    size: int = None
    checksum: bytes = None

    def open(self):
        return open(self.path, 'rb')

    def __hash__(self):
        return hash(self.path)
