import subprocess
import sys
import time
import socket
import pytest
import redis


def wait_for_server(host="localhost", port=6399, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.05)
    raise RuntimeError(f"Server did not start on {host}:{port} within {timeout}s")


@pytest.fixture(scope="session")
def server_process():
    proc = subprocess.Popen(
        [sys.executable, "-m", "incache", "--port", "6399"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    wait_for_server()
    yield proc
    proc.terminate()
    proc.wait()


@pytest.fixture
def r(server_process):
    client = redis.Redis(host="localhost", port=6399, decode_responses=True)
    client.flushall()
    yield client
    client.close()


@pytest.fixture
def rb(server_process):
    """Binary client — returns bytes instead of str."""
    client = redis.Redis(host="localhost", port=6399, decode_responses=False)
    client.flushall()
    yield client
    client.close()
