"""Test the Task class."""

from pyglet.window import Window
from pytest import raises

from earwax import Game, Level, Task


class Works(Exception):
    """Something works."""


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


def test_start_immediately() -> None:
    """Test start a task straight away."""
    def func(dt: float) -> None:
        """Raise to exit."""
        raise Works

    task: Task = Task(lambda: 5.0, func)
    task.start()
    assert task.running is True
    task.stop()
    assert task.running is False
    with raises(Works):
        task.start(immediately=True)
    assert task.running is True
    task.stop()  # Make sure future tests don't raise an error.


def test_stop() -> None:
    """Test that a task can be stopped."""
    t: Task = Task(lambda: 0.0, lambda dt: print(dt))
    t.start()
    assert t.running is True
    t.stop()
    assert t.running is False


def test_register_task(game: Game) -> None:
    """Test the register_task decorator."""

    @game.register_task(lambda: 0.5)
    def task(dt: float) -> None:
        """Test task."""
        raise Works()

    assert isinstance(task, Task)
    assert task.interval() == 0.5
    with raises(Works):
        task.func(4.5)
    assert task.running is False
    assert task in game.tasks


def test_remove_task(game: Game) -> None:
    """Test the remove_task method."""

    @game.register_task(lambda: 0.0)
    def task(dt: float) -> None:
        """Test task."""
        pass

    task.start()
    assert task.running is True
    game.remove_task(task)
    assert task.running is False
    assert task not in game.tasks
