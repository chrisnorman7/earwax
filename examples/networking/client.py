"""An example earwax client."""

from pyglet.window import Window, key

from earwax import (AlreadyConnected, AlreadyConnecting, ConnectionStates,
                    Game, Level, NetworkConnection)

game: Game = Game(name="Networking Test")
window: Window = Window(caption="Networking Test")

con: NetworkConnection = NetworkConnection()


@con.event
def on_connect() -> None:
    """Handle connection."""
    game.output("Connected.")


@con.event
def on_disconnect() -> None:
    """Handle disconnection."""
    game.output("Disconnected.")


@con.event
def on_data(data: bytes) -> None:
    """Handle incoming data."""
    game.output(data.decode())


@con.event
def on_error(e: Exception) -> None:
    """Handle a connection error."""
    game.output(f"Connection failed: {e}")


level: Level = Level(game)


@level.action("Connect", symbol=key.C)
def do_connect() -> None:
    """Try and connect."""
    try:
        con.connect("raspberrypi", 1234)
        game.output("Connecting.")
    except AlreadyConnecting:
        game.output("Still trying to connect.")
    except AlreadyConnected:
        game.output("Already connected.")


@level.action("Disconnect", symbol=key.D)
def do_disconnect() -> None:
    """Disconnect from the server."""
    con.close()


@level.action('Send "Hello world".', symbol=key._1)
def send_hello_world() -> None:
    """Send a string."""
    if con.state is not ConnectionStates.connected:
        return game.output("Not connected yet.")
    con.send("Hello world.\r\n".encode())


@level.action("Exit", symbol=key.ESCAPE)
def do_exit() -> None:
    """Exit the game."""
    game.stop()


if __name__ == "__main__":
    game.run(window, initial_level=level)
