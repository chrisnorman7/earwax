"""Test the PretendSocket class."""

from socket import AF_INET, SOCK_STREAM

from pytest import raises

from .conftest import PretendSocket


def test_init(socket: PretendSocket) -> None:
    """Test initialisation."""
    assert isinstance(socket, PretendSocket)
    assert socket.connected is True
    assert socket.data is None
    assert socket.family is AF_INET
    assert socket.type is SOCK_STREAM


def test_sendall(socket: PretendSocket) -> None:
    """Test that data can be sent properly.

    Data should be stored on ``socket.data``.
    """
    socket.sendall(b'Test')
    assert socket.data == b'Test'
    socket.sendall(b'hello world')
    assert socket.data == b'hello world'


def test_recv(socket: PretendSocket) -> None:
    """Test that pretend data is pretendedly received."""
    with raises(BlockingIOError):
        socket.recv(1024)
    socket.sendall(b'Hello world.')
    assert socket.recv(1024) == b'Hello world.'
    with raises(BlockingIOError):
        socket.recv(1024)


def test_close(socket: PretendSocket) -> None:
    """Test that we can close the socket properly.

    All closing does is to set ``socket.connected = False``.
    """
    socket.close()
    assert socket.recv(1024) == b''
    assert socket.recv(1024) == b''
