"""Test the ThreadedPromise class."""

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Any, Tuple

from pyglet.clock import schedule_once
from pyglet.event import EVENT_HANDLED
from pyglet.window import Window
from pytest import raises

from earwax import Game, Level, PromiseStates, ThreadedPromise


class CorrectException(Exception):
    """Something was correct."""


def test_init(thread_pool: ThreadPoolExecutor) -> None:
    """Test initialisation."""
    p: ThreadedPromise = ThreadedPromise(thread_pool)
    assert p.thread_pool is thread_pool
    assert p.state is PromiseStates.not_ready
    assert p.future is None
    assert p.func is None
    with raises(RuntimeError):
        p.run()
        assert p.state is PromiseStates.not_ready


def test_run(game: Game, window: Window, level: Level) -> None:
    """Test the ``run`` function."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def increment() -> None:
        game.push_level(level)
        schedule_once(lambda dt: window.close(), 0)

    assert p.state is PromiseStates.ready

    @game.event
    def before_run() -> None:
        p.run()

    game.run(window)
    assert game.level is level
    assert game.levels == [level]
    assert p.state is PromiseStates.done


def test_on_done_no_args(game: Game, window: Window, level: Level) -> None:
    """Test ``on_done`` with no arguments."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def return_5() -> int:
        sleep(0.1)
        return 5

    @p.event
    def on_done(value: int) -> None:
        assert value == 5
        game.push_level(level)
        window.close()

    @game.event
    def before_run() -> None:
        p.run()

    game.run(window)
    assert game.levels == [level]


def test_on_done_with_args(game: Game, window: Window, level: Level) -> None:
    """Test ``on_done`` with arguments."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def with_args(name: str, number: int = 0) -> Tuple[str, int]:
        return (name, number)

    @p.event
    def on_done(t: Tuple[str, int]) -> None:
        assert t == ("test", 10)
        game.push_level(level)
        window.close()

    @game.event
    def before_run() -> None:
        p.run("test", number=10)

    game.run(window)
    assert game.levels == [level]


def test_on_error(game: Game, window: Window) -> None:
    """Test the ``on_error`` event."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)
    worked: Level = Level(game)
    failed: Level = Level(game)

    @p.register_func
    def raise_an_error() -> None:
        raise CorrectException()

    @p.event
    def on_done() -> None:
        game.push_level(failed)

    @p.event
    def on_error(e: Exception) -> None:
        assert isinstance(e, CorrectException)
        game.push_level(worked)
        window.close()
        return EVENT_HANDLED

    @game.event
    def before_run() -> None:
        p.run()

    game.run(window)
    assert game.level is worked
    assert p.state is PromiseStates.error


def test_cancel(game: Game, window: Window) -> None:
    """Test the ``cancel`` function."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)
    worked: Level = Level(game)
    failed: Level = Level(game)
    error: Level = Level(game)

    @p.register_func
    def do_something() -> None:
        sleep(1)

    @p.event
    def on_done(value: None) -> None:
        game.push_level(failed)

    @p.event
    def on_cancel() -> None:
        game.push_level(worked)
        window.close()

    @p.event
    def on_error(e: Exception) -> None:
        game.push_level(error)

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: p.cancel(), 0.5)

    game.run(window)
    assert game.levels == [worked]
    assert p.state is PromiseStates.cancelled


def test_finally_no_error(game: Game, window: Window) -> None:
    """Test ``on_finally`` with no error."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)
    return_level: Level = Level(game)
    finally_level: Level = Level(game)
    error_level: Level = Level(game)

    @p.register_func
    def do_something() -> int:
        return 6

    @p.event
    def on_done(value: int) -> None:
        assert value == 6
        game.push_level(return_level)

    @p.event
    def on_error(e: Exception) -> None:
        game.push_level(error_level)

    @p.event
    def on_finally() -> None:
        game.push_level(finally_level)
        window.close()

    @game.event
    def before_run() -> None:
        p.run()

    game.run(window)
    assert game.levels == [return_level, finally_level]


def test_finally_with_error(game: Game, window: Window) -> None:
    """Test ``on_finally`` with an error."""
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)
    return_level: Level = Level(game)
    finally_level: Level = Level(game)
    error_level: Level = Level(game)

    @p.register_func
    def do_something() -> int:
        raise CorrectException()

    @p.event
    def on_done(value: Any) -> None:
        game.push_level(return_level)

    @p.event
    def on_error(e: Exception) -> None:
        game.push_level(error_level)
        return EVENT_HANDLED

    @p.event
    def on_finally() -> None:
        game.push_level(finally_level)
        window.close()

    @game.event
    def before_run() -> None:
        p.run()

    game.run(window)
    assert game.levels == [error_level, finally_level]
