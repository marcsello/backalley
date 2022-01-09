import os.path
from typing import Optional
from threading import Thread
from queue import Queue, Empty
import hashlib
import logging

from entity_info import EntityInfo, EntityType


class InfoCollector(Thread):
    """
    This is a class that runs a separate thread and calculates hashes of each file
    It uses two queues, one where it receives files and one where it puts them after the hash has been calculated
    """

    def __init__(self, inqueue: Queue, outqueue: Queue):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self._inqueue = inqueue
        self._outqueue = outqueue

        self._stop_when_finished = False

    def _calculate_checksum(self, file: EntityInfo) -> bytes:
        self._logger.debug(f"Calculating checksum of {file.path}...")
        with file.open() as f:
            checksum = hashlib.sha256()
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break

                checksum.update(chunk)

        self._logger.debug(f"Calculated checksum of {file.path}: {checksum.hexdigest()}")
        return checksum.digest()

    def run(self) -> None:
        while True:

            try:
                entity: Optional[EntityInfo] = self._inqueue.get(timeout=5)
            except Empty:
                entity = None

            if not entity:
                if self._stop_when_finished:
                    break
                else:
                    continue

            if entity.type == EntityType.FILE:
                entity.checksum = self._calculate_checksum(entity)
                entity.size = os.path.getsize(entity.path)

    def stop_when_finished(self):
        self._stop_when_finished = True
