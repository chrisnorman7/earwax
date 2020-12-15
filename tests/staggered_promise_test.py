"""Tests for the StaggeredPromise class."""

from time import time
from typing import Any, List

from pyglet.event import EVENT_HANDLED
from pyglet.window import Window

from earwax import Game, Level, PromiseStates, StaggeredPromise
from earwax.types import StaggeredPromiseGeneratorType


class Works(Exception):
    """Something worked."""


def test_staggered_promise() -> None:
    """Test the decorate function."""
    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 1.0
        yield 2.0

    assert isinstance(promise, StaggeredPromise)
    assert promise.generator is None
    assert promise.state is PromiseStates.ready


def test_init() -> None:
    """Test initialization."""
    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 3.0

    assert isinstance(promise, StaggeredPromise)
    assert promise.generator is None
    assert promise.state is PromiseStates.ready


def test_run_no_args(game: Game, window: Window) -> None:
    """Test running with no arguments."""
    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        started: float = time()
        yield 0.5
        assert (time() - started) >= 0.4  # Pyglet's timing is slightly short.
        yield 0.2
        assert (time() - started) >= 0.6  # Pyglet's timing is slight short.
        window.close()

    @game.event
    def before_run() -> None:
        promise.run()
        assert promise.state is PromiseStates.running

    game.run(window)


def test_run_args(game: Game, window: Window) -> None:
    """Test running with arguments."""
    @StaggeredPromise.decorate
    def promise(a, b, c=1) -> StaggeredPromiseGeneratorType:
        started = time()
        yield 0.5
        assert a == 1
        assert b == 2
        assert c == 3
        yield 0.5
        assert (time() - started) >= 0.6
        window.close()

    @game.event
    def before_run() -> None:
        promise.run(1, 2, 3)
        assert promise.state is PromiseStates.running

    game.run(window)


def test_on_done(game: Game, window: Window) -> None:
    """Test the on_done event."""
    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 0.1
        return 3

    @promise.event
    def on_done(value: int) -> None:
        assert value == 3
        window.close()

    @game.event
    def before_run() -> None:
        promise.run()

    game.run(window)
    assert promise.state is PromiseStates.done


def test_on_error(game: Game, window: Window) -> None:
    """Test the on_error event."""
    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 0.1
        raise Works()

    @promise.event
    def on_error(e: Exception) -> None:
        assert isinstance(e, Works)
        window.close()
        return EVENT_HANDLED

    @promise.event
    def on_done(value: Any) -> None:
        raise RuntimeError('This event should not have fired.')

    @game.event
    def before_run() -> None:
        promise.run()

    game.run(window)
    assert promise.state is PromiseStates.error


def test_on_finally(game: Game, window: Window) -> None:
    """Test the on_finally event."""
    should_raise = True
    return_level: Level = Level(game)
    error_level: Level = Level(game)

    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 0.0
        if should_raise:
            raise RuntimeError('Raising...')
        return 5

    @promise.event
    def on_error(e: Exception) -> None:
        assert isinstance(e, RuntimeError)
        game.push_level(error_level)
        return EVENT_HANDLED

    @promise.event
    def on_done(value: int) -> None:
        assert value == 5
        game.push_level(return_level)

    @promise.event
    def on_finally() -> None:
        if game.window is not None:
            game.window.close()

    @game.event
    def before_run() -> None:
        promise.run()

    game.run(window)
    assert game.levels == [error_level]
    assert promise.state is PromiseStates.error
    should_raise = False
    game.levels.clear()
    game.run(Window(caption='Test'))
    assert game.levels == [return_level]
    assert promise.state is PromiseStates.done


def test_on_cancel(game: Game, window: Window) -> None:
    """Test the on_cancel event."""
    return_level: Level = Level(game)
    error_level: Level = Level(game)

    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        yield 5.0
        raise RuntimeError('Should never have gotten to this point.')

    @promise.event
    def on_done(value: Any) -> None:
        game.push_level(return_level)

    @promise.event
    def on_error(e: Exception) -> None:
        game.push_level(error_level)

    @promise.event
    def on_cancel() -> None:
        if game.window is not None:
            game.window.close()

    @StaggeredPromise.decorate
    def cancel_promise() -> StaggeredPromiseGeneratorType:
        yield 0.1
        promise.cancel()

    @game.event
    def before_run() -> None:
        promise.run()
        cancel_promise.run()

    game.run(window)
    assert game.levels == []
    assert promise.state is PromiseStates.cancelled


def test_on_next(game: Game, level: Level, window: Window) -> None:
    """Test the on_next event."""
    numbers: List[float] = [0.1, 0.2, 0.3, 0.4]

    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        x: float
        for x in numbers.copy():
            yield x

    @promise.event
    def on_next(duration: float) -> None:
        assert duration == numbers.pop(0)
        game.push_level(level)

    @promise.event
    def on_finally() -> None:
        window.close()

    @game.event
    def before_run() -> None:
        promise.run()

    game.run(window)
    assert len(game.levels) == 4
