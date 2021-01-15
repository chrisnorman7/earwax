"""Provides classes for networking."""

from enum import Enum
from socket import AF_INET, SOCK_STREAM, error
from socket import socket as _socket
from typing import List, Optional

from attr import Factory, attrib, attrs

from .mixins import RegisterEventMixin
from .pyglet import schedule, unschedule


class NetworkingConnectionError(Exception):
    """Base class for connection errors."""


class AlreadyConnecting(NetworkingConnectionError):
    """Already connecting.

    An attempt was made to call :meth:`~earwax.NetworkConnection.connect` on an
    :class:`~earwax.NetworkConnection` instance which is already attempting to
    connect.
    """


class AlreadyConnected(NetworkingConnectionError):
    """Already connected.

    Attempted to call :meth:`~earwax.NetworkConnection.connect` on an already
    connected :class:`~earwax.NetworkConnection` instance.
    """


class NotConnectedYet(NetworkingConnectionError):
    """Tried to send data on a connection which is not yet connected."""


class ConnectionStates(Enum):
    """Various states that :class:`~earwax.NetworkConnection` classes can be in.

    :ivar ~earwax.ConnectionStates.not_connected: The connection's
        :meth:`~earwax.NetworkConnection.connect` method has not yet been
        called.

    :ivar ~earwax.ConnectionStates.connecting: The connection is still being
        established.

    :ivar ~earwax.ConnectionStates.connected: A connection has been
        established.

    :ivar ~earwax.ConnectionStates.disconnected: This connection is no longer
        connected (but was at some point).

    :ivar ~earwax.ConnectionStates.error: There was an error establishing a
        connection.
    """

    not_connected = 0
    connecting = 1
    connected = 2
    disconnected = 3
    error = 4


@attrs(auto_attribs=True)
class NetworkConnection(RegisterEventMixin):
    """Represents a single outbound connection.

    You can read data by providing an event handler for
    :meth:`~earwax.NetworkConnection.on_data`, and write data with the
    :meth:`~earwax.NetworkConnection.send` method.

    :ivar ~earwax.NetworkConnection.socket: The raw socket this instance uses
        for communication.

    :ivar ~earwax.NetworkConnection.state: The state this connection is in.
    """

    socket: Optional[_socket] = attrib(
        default=Factory(lambda: None), init=False
    )

    state: ConnectionStates = attrib(
        default=Factory(lambda: ConnectionStates.not_connected), init=False
    )

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        for func in (
            self.on_connect, self.on_disconnect, self.on_data, self.on_error
        ):
            self.register_event(func)  # type: ignore[arg-type]

    def on_connect(self) -> None:
        """Deal with the connection being opened.

        This event is dispatched when text is first received from
        :attr:`self.socket <earwax.NetworkConnection.socket>`, since I've not
        found a better way to know when the socket is properly open.
        """
        pass

    def on_disconnect(self) -> None:
        """Handle the connection closing.

        Dispatched when :attr:`self.socket <earwax.NetworkConnection.socket>`
        has disconnected.

        A socket disconnect is defined by the socket in question receiving an
        empty string.
        """
        pass

    def on_data(self, data: bytes) -> None:
        """Handle incoming data.

        An event which is dispatched whenever data is received from
        :attr:`self.socket <earwax.NetworkConnection.socket>`.
        """
        pass

    def on_error(self, e: Exception) -> None:
        """Handle a connection error.

        This event is dispatched when there is an error establishing a
        connection.

        :param e: The exception that was raised.
        """
        raise e

    def connect(self, hostname: str, port: int) -> None:
        """Open a new connection.

        Connect :attr:`self.socket <earwax.NetworkConnection.socket>` to the
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
        """Close this connection.

        Disconnect :attr:`self.socket <earwax.NetworkConnection.socket>`, and
        call :meth:`~earwax.NetworkConnection.shutdown` to clean up..
        """
        if self.socket is None:
            raise NotConnectedYet(self)
        self.socket.close()
        self.dispatch_event('on_disconnect')
        self.shutdown()

    def poll(self, dt: float) -> None:
        """Check if any data has been received.

        Poll :attr:`self.socket <earwax.NetworkConnection.socket>` for anything
        that has been received since the last time this function ran.

        This function will be scheduled by
        :meth:`~earwax.NetworkConnection.connect`, and unscheduled by
        :meth:`~earwax.NetworkConnection.shutdown`, when no more data is
        received from the socket.

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
        """Shutdown this server.

        Unschedule :meth:`self.poll <earwax.NetworkConnection.poll>`, set
        :attr:`self.socket <earwax.NetworkConnection.socket>` to ``None``, and
        reset :attr:`self.state <earwax.NetworkConnection.state>` to
        :attr:`earwax.ConnectionStates.not_connected`.
        """
        unschedule(self.poll)
        self.socket = None
        self.state = ConnectionStates.not_connected

    def send(self, data: bytes) -> None:
        r"""Send some data over this connection.

        Sends some data to :attr:`self.socket
        <earwax.NetworkConnection.socket>`.

        If this object is not connected yet, then
        :class:`~earwax.NotConnectedYet` will be raised.

        :param data: The data to send to the socket.

            Must end with ``'\r\n'``.
        """
        if self.socket is None:
            raise NotConnectedYet(self)
        self.socket.sendall(data)
