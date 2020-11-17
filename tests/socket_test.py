"""Test the PretendSocket class."""

from socket import AF_INET, SOCK_STREAM
from .conftest import PretendSocket
from pytest import raises


def test_init(socket: PretendSocket) -> None:
    """Test initialisation."""
    assert isinstance(socket, PretendSocket)
    assert socket.connected is True
    assert socket.data is None
    assert socket.family is AF_INET
    assert socket.type is SOCK_STREAM
    with raises(BlockingIOError):
        socket.recv(1024)
    socket.sendall(b'Hello world.')
    assert socket.recv(1024) == b'Hello world.'
