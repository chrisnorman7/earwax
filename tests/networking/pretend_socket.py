"""Provides the PretendSocket class."""

from socket import socket
from typing import Optional

from earwax import ConnectionStates, NetworkConnection


class PretendSocket(socket):
    """A pretend socket object."""

    data: Optional[bytes] = None
    connected: bool = True

    def sendall(  # type: ignore[override]
        self, data: bytes, flags: int = 0
    ) -> None:
        """Pretend to send data.

        Really set ``self.data`` to ``data``.
        """
        self.data = data

    def recv(  # type: ignore[override]
        self, bufsize: int, flags: int = 0
    ) -> bytes:
        """Pretend to receive data from a non-existant network connection.

        Really return ``self.data``.

        If ``self.data`` is ``None``, then raise ``BlockingIOError``.
        """
        if not self.connected:
            return b''
        if self.data is None:
            raise BlockingIOError('No data yet.')
        data: bytes = self.data
        self.data = None
        return data

    def close(self) -> None:
        """Pretend to close this pretend socket.

        Really set ``self.connected`` to ``False``.
        """
        self.connected = False

    def patch(self, con: NetworkConnection) -> None:
        """Assign this socket to a connection.

        This simulates the connection being connected to an actual host.
        """
        con.socket = self
        con.state = ConnectionStates.connected
