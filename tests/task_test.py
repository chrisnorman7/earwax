"""Test the Task class."""

from pyglet.window import Window

from earwax import Game, Level, Task


def test_init() -> None:
    """Test initialisation."""
    def interval() -> float:
        """Return an interval."""
        return 5.0

    def func(dt: float) -> None:
        """Do something."""
        print('Worked.')

    t: Task = Task(interval, func)
    assert isinstance(t, Task)
    assert t.interval is interval
    assert t.func is func
    assert t.running is False


def test_start(level: Level, game: Game, window: Window) -> None:
    """Test that a task can be run."""

    def func(dt: float) -> None:
        """Close the window."""
        game.push_level(level)
        window.close()

    t: Task = Task(lambda: 0.5, func)

    @game.event
    def before_run() -> None:
        """Start the task running."""
        t.start()
        assert t.running is True

    game.run(window)
    assert game.level is level


def test_stop() -> None:
    """Test that a task can be stopped."""
    t: Task = Task(lambda: 0.0, lambda dt: print(dt))
    t.start()
    assert t.running is True
    t.stop()
    assert t.running is False
