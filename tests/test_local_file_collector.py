import sys
import tempfile
import pytest
import shutil
import os.path
import socket
import threading

from local_file_collector import LocalFileCollector

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

    yield LocalFileCollector([testdir1, testdir2])
    shutil.rmtree(testdir1)
    shutil.rmtree(testdir2)


# constructor

def test_abs_path_only():
    print(os.getcwd(),flush=True)
    with pytest.raises(ValueError):
        LocalFileCollector(['alma/barack.txt'])


def test_no_falsy():
    with pytest.raises(ValueError):
        LocalFileCollector([])

    with pytest.raises(ValueError):
        LocalFileCollector(None)


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
    run = True

    def mover_thread():
        while run:
            item = file_collector_instance.queue.get(timeout=5)
            complete_list.append(item)

    t = threading.Thread(target=lambda: mover_thread())
    t.run()

    file_collector_instance.collect()
    run = False

    t.join()

    assert len(complete_list) == 5


# misc

def test_commonpath(file_collector_instance):
    assert file_collector_instance.commonpath == "/tmp"
