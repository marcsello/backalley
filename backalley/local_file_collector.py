from typing import List
from queue import Queue
import logging

import os
import os.path

from entity_info import EntityInfo, EntityType


class LocalFileCollector:
    """
    This class is used to collect all paths that are need to be backed up.
    """

    def __init__(self, source_list: List[str], queue_size: int = 15):
        """

        :param source_list: List of paths on the local machine. A path can be a single file or a directory.
        :param queue_size: Size of the output queue. See. queue.Queue
        """
        super().__init__()
        if (not source_list) or not isinstance(source_list, List):  # It needs to be a list for copy
            raise ValueError("No or invalid sources provided")

        self._source_list = source_list.copy()

        # Check sources beforehand and fail early
        for i, source in enumerate(source_list):

            if not os.path.isabs(source):
                raise ValueError(
                    f"{i}. element of source list is not absolute path: {source}; Only absolute paths supported!")

            if not (os.path.isfile(source) or os.path.isdir(source)):
                raise ValueError(f"{i}. element of source list is not a supported type: {source}")

        self._entity_queue = Queue(queue_size)

        self._logger = logging.getLogger(self.__class__.__name__)
        self._commonpath = os.path.commonpath(source_list)

    def collect(self):
        """
        Run the actual collection.
        Goes trough the source list, and put every file with their full path into the output queue.

        This is a blocking function.
        """
        for source in self._source_list:

            if os.path.isfile(source) or os.path.islink(source):
                # Walk over dirs only
                self._entity_queue.put(source)
                continue

            if not os.path.isdir(source):
                # This should only happen if the filesystem contents changed during the backup
                self._logger.warning(f"{source} is not supported type. Skipping!")
                continue

            potentially_empty_dirs = [source]  # The root dir is potentially empty until it's visited
            for root, dirs, files in os.walk(source):
                potentially_empty_dirs.extend([os.path.join(root, d) for d in dirs])

                if dirs or files:
                    potentially_empty_dirs.remove(root)

                for file in files:
                    full_path = os.path.abspath(os.path.join(root, file))

                    self._entity_queue.put(
                        EntityInfo(
                            path=full_path,
                            type=EntityType.FILE
                        )
                    )

            for empty_dir in potentially_empty_dirs:
                self._entity_queue.put(
                    EntityInfo(
                        path=empty_dir,
                        type=EntityType.EMPTY_DIRECTORY
                    )
                )

    @property
    def commonpath(self):
        return self._commonpath

    @property
    def queue(self) -> Queue:
        return self._entity_queue
