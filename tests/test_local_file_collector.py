import queue
import sys
import tempfile
import pytest
import shutil
import os.path
import socket
import threading

from local_file_collector import LocalFileCollector
from entity_info import EntityType


@pytest.fixture
def file_collector_instance():
    def writeto(content, path):
        with open(path, "w") as f:
            f.write(content)

    testdir1 = tempfile.mkdtemp()
    testdir2 = tempfile.mkdtemp()

    writeto("Test data", os.path.join(testdir2, "test1.txt"))
    writeto("Test data 2", os.path.join(testdir2, "test2.txt"))

    for dir_ in ['alpha', 'beta', 'gamma']:
        newdir = os.path.join(testdir2, dir_)
        os.makedirs(newdir)
        writeto("Hello world!", os.path.join(newdir, f"{dir_}.txt"))
    os.makedirs(os.path.join(testdir2, 'delta'))

    yield LocalFileCollector([testdir1, testdir2])
    shutil.rmtree(testdir1)
    shutil.rmtree(testdir2)


# constructor

def test_abs_path_only():
    print(os.getcwd(), flush=True)
    with pytest.raises(ValueError):
        LocalFileCollector(['alma/barack.txt'])


def test_wrong_parameters():
    with pytest.raises(ValueError):
        LocalFileCollector([])

    with pytest.raises(ValueError):
        LocalFileCollector(None)

    with pytest.raises(ValueError):
        LocalFileCollector(range(5))


def test_same_dirs():
    testdir = tempfile.mkdtemp()

    with pytest.raises(ValueError):
        LocalFileCollector([testdir, testdir])

    nested = os.path.join(testdir, 'apple')
    os.makedirs(nested)

    with pytest.raises(ValueError):
        LocalFileCollector([testdir, nested])

    shutil.rmtree(testdir)


def test_no_other_type():
    testdir = tempfile.mkdtemp()
    sockpath = os.path.join(testdir, "test.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(sockpath)

    with pytest.raises(ValueError):
        LocalFileCollector([sockpath])

    server.close()
    os.unlink(sockpath)


# test collection
def test_all_files_visited(file_collector_instance):
    complete_list = []

    def mover_thread():
        while mover_thread.run:
            try:
                item = file_collector_instance.queue.get(timeout=2)
            except queue.Empty:
                return
            complete_list.append(item)

    mover_thread.run = True

    t = threading.Thread(target=lambda: mover_thread())
    t.start()

    file_collector_instance.collect()
    mover_thread.run = False

    t.join()

    assert len(complete_list) == 7
    for entity in [
        (file_collector_instance._source_list[0], EntityType.EMPTY_DIRECTORY),
        (os.path.join(file_collector_instance._source_list[1], "test1.txt"), EntityType.FILE),
        (os.path.join(file_collector_instance._source_list[1], "test2.txt"), EntityType.FILE),
        (os.path.join(file_collector_instance._source_list[1], "alpha/alpha.txt"), EntityType.FILE),
        (os.path.join(file_collector_instance._source_list[1], "beta/beta.txt"), EntityType.FILE),
        (os.path.join(file_collector_instance._source_list[1], "gamma/gamma.txt"), EntityType.FILE),
        (os.path.join(file_collector_instance._source_list[1], "delta"), EntityType.EMPTY_DIRECTORY)
    ]:
        cnt = 0
        for fpath in complete_list:
            if fpath.path == entity[0] and fpath.type == entity[1]:
                cnt += 1

        assert cnt == 1


# misc

def test_commonpath(file_collector_instance):
    assert file_collector_instance.commonpath == "/tmp"
