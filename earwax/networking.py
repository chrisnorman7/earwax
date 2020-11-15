"""Provides classes for networking."""

from enum import Enum
from socket import AF_INET, SOCK_STREAM, error
from socket import socket as _socket
from typing import List, Optional

from attr import Factory, attrib, attrs
from pyglet.clock import schedule, unschedule

from .mixins import RegisterEventMixin


class ConnectionError(Exception):
    """Base class for connection errors."""


class AlreadyConnecting(ConnectionError):
    """An attempt was made to connect a connection which is already attempting
    to connect.
    """


class AlreadyConnected(ConnectionError):
    """Attempted to call ``connect()`` on an already connected connection
    object."""


class NotConnectedYet(ConnectionError):
    """Tried to send data on an connection which is not yet connected."""


class ConnectionStates(Enum):
    """Various states that :class:`earwax.NetworkConnection` classes can be in.

    :ivar not_connected: The connection's
    :meth:`~earwax.NetworkConnection.connect` method has not yet been called.

    :ivar connecting: The connection is still being established.

    :ivar connected: A connection has been established.

    :ivar disconnected: This connection was connected at some point, but now is
    not.

    :ivar error: There was an error establishing a connection.
    """

    not_connected = 0
    connecting = 1
    connected = 2
    disconnected = 3
    error = 4


@attrs(auto_attribs=True)
class NetworkConnection(RegisterEventMixin):
    """Represents a single outbound connection."""

    socket: Optional[_socket] = attrib(
        default=Factory(lambda: None), init=False
    )

    state: ConnectionStates = attrib(
        default=Factory(lambda: ConnectionStates.not_connected), init=False
    )

    def __attrs_post_init__(self) -> None:
        for func in (
            self.on_connect, self.on_disconnect, self.on_data, self.on_error
        ):
            self.register_event(func)  # type: ignore[arg-type]

    def on_connect(self) -> None:
        """An event which is dispatched when a connection is established."""
        pass

    def on_disconnect(self) -> None:
        """An event which is dispatched when :attr:`self.socket
        <earwax.NetworkConnection.socket>` has disconnected.
        """
        pass

    def on_data(self, data: bytes) -> None:
        """An event which is dispatched whenever data is received from
        :attr:`self.socket <earwax.NetworkConnection.socket>`.
        """
        pass

    def on_error(self, e: Exception) -> None:
        """An event which is dispatched when there is an error establishing a
        connection.

        :param e: The exception that was raised.
        """
        raise e

    def connect(self, hostname: str, port: int) -> None:
        """Connect :attr:`self.socket <earwax.NetworkConnection.socket>` to the
        provided hostname and port.

        :param hostname: The hostname to connect to.

        :param port: The port to connect on.
        """
        if self.state is ConnectionStates.connecting:
            raise AlreadyConnecting(self)
        if self.state is ConnectionStates.connected:
            raise AlreadyConnected(self)
        self.socket = _socket(AF_INET, SOCK_STREAM)
        self.state = ConnectionStates.connecting
        self.socket.setblocking(False)
        try:
            self.socket.connect((hostname, port))
        except BlockingIOError:
            schedule(self.poll)
        except error as e:
            self.state = ConnectionStates.error
            self.dispatch_event('on_error', e)
            self.socket = None

    def close(self) -> None:
        """Disconnect :attr:`self.socket <earwax.NetworkConnection.socket>`,
        and unschedule :meth:`self.poll <earwax.NetworkConnection.poll>`.
        """
        if self.socket is None:
            raise NotConnectedYet(self)
        self.socket.close()
        self.dispatch_event('on_disconnect')
        self.shutdown()

    def poll(self, dt: float) -> None:
        """Poll :attr:`self.socket <earwax.NetworkConnection.socket>` for
        data.

        If this connection is not connected yet (I.E.: you called this function
        yourself), then :class:`earwax.NotConnectedYet` will be raised.
        """
        if self.socket is None:
            raise NotConnectedYet(self)
        chunks: List[bytes] = []
        while True:
            try:
                data: bytes = self.socket.recv(1024)
                if not data:
                    self.dispatch_event('on_disconnect')
                    return self.shutdown()
                chunks.append(data)
            except BlockingIOError:
                if self.state is ConnectionStates.connecting:
                    self.state = ConnectionStates.connected
                    self.dispatch_event('on_connect')
                break  # There is no data to read.
            except error:
                return  # Still connecting.
        if chunks:
            self.dispatch_event('on_data', b''.join(chunks))

    def shutdown(self) -> None:
        """Unschedule :meth:`self.poll <earwax.NetworkConnection.poll>`."""
        unschedule(self.poll)
        self.socket = None
        self.state = ConnectionStates.not_connected

    def send(self, data: bytes) -> None:
        """Send some data to :attr:`self.socket
        <earwax.NetworkConnection.socket>`.

        If this object is not connected yet, then
        :class:`~earwax.NotConectedYet` will be raised.

        :param data: The data to send to the socket.

            Must end with ``'\\r\\n'``.
        """
        if self.socket is None:
            raise NotConnectedYet(self)
        self.socket.sendall(data)
