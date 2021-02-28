"""Test Earwax networking."""

from pyglet.clock import schedule, schedule_once, unschedule
from pyglet.event import EVENT_HANDLED
from pyglet.window import Window

from earwax import ConnectionStates, Game, Level, NetworkConnection

from .pretend_socket import PretendSocket


class TooSlow(Exception):
    """Connection was too slow."""


def test_init(con: NetworkConnection) -> None:
    """Test that all the defaults are sensible."""
    assert isinstance(con, NetworkConnection)
    assert con.socket is None
    assert con.state is ConnectionStates.not_connected


def test_on_connect(
    con: NetworkConnection, window: Window, game: Game
) -> None:
    """Test the ``on_connect`` event."""
    works_level: Level = Level(game)
    fails_level: Level = Level(game)

    def too_slow(dt: float) -> None:
        """Raise ``TooSlow``."""
        game.stop()
        raise TooSlow

    @con.event
    def on_connect() -> None:
        game.push_level(works_level)
        window.close()

    @con.event
    def on_error(e: Exception) -> None:
        game.push_level(fails_level)
        window.close()
        raise e

    @game.event
    def before_run() -> None:
        con.connect("google.com", 80)

    schedule_once(too_slow, 2.0)
    game.run(window)
    assert game.level is works_level
    unschedule(too_slow)


def test_on_error(
    con: NetworkConnection, game: Game, window: Window, level: Level
) -> None:
    """Make sure we get the ``on_error`` event when connecting fails."""
    works_level: Level = Level(game)
    fails_level: Level = Level(game)

    @con.event
    def on_connect() -> None:
        game.push_level(fails_level)
        window.close()

    @con.event
    def on_error(e: Exception) -> bool:
        assert isinstance(e, OSError)
        game.push_level(works_level)
        window.close()
        return EVENT_HANDLED

    def do_connect(dt: float) -> None:
        con.connect("test.nothing", 1234)

    @game.event
    def before_run() -> None:
        schedule_once(do_connect, 0.5)

    game.run(window)
    assert game.level is works_level
    unschedule(do_connect)


def test_on_send(con: NetworkConnection, socket: PretendSocket) -> None:
    """Ensure that data is sent properly."""
    socket.patch(con)
    con.send(b"test")
    assert socket.data == b"test"
    con.send(b"hello world")
    assert socket.data == b"hello world"


def test_on_disconnect(
    socket: PretendSocket, con: NetworkConnection, game: Game, window: Window
) -> None:
    """Make sure the ``on_disconnect`` event dispatches properly."""
    works_level: Level = Level(game)
    socket.patch(con)

    @con.event
    def on_disconnect() -> None:
        game.push_level(works_level)
        window.close()

    @game.event
    def before_run() -> None:
        schedule_once(lambda dt: con.close(), 0.5)

    game.run(window)
    assert game.level is works_level


def test_on_data(
    socket: PretendSocket, con: NetworkConnection, game: Game, window: Window
) -> None:
    """Make sure the ``on_data`` event dispatches properly."""
    second_level: Level = Level(game)
    works_level: Level = Level(game)
    socket.patch(con)

    @con.event
    def on_data(data: bytes) -> None:
        if game.level is None:
            assert data == b"Hello world"
            con.send(b"test")
            game.push_level(second_level)
        elif game.level is second_level:
            assert data == b"test"
            game.push_level(works_level)
            con.shutdown()
            window.close()
        else:
            raise RuntimeError("Something went wrong.")

    def setup(dt: float) -> None:
        con.send(b"Hello world")
        schedule(con.poll)

    schedule_once(setup, 0.5)
    game.run(window)
    assert game.level is works_level
