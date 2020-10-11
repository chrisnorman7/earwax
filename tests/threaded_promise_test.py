from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Any, Tuple

from pyglet.clock import schedule_once
from pyglet.event import EVENT_HANDLED
from pyglet.window import Window
from pytest import raises

from earwax import Game, Level, ThreadedPromise, ThreadedPromiseStates


class CorrectException(Exception):
    pass


def test_init(thread_pool: ThreadPoolExecutor) -> None:
    p: ThreadedPromise = ThreadedPromise(thread_pool)
    assert p.thread_pool is thread_pool
    assert p.state is ThreadedPromiseStates.not_ready
    assert p.future is None
    assert p.func is None
    with raises(RuntimeError):
        p.run()
        assert p.state is ThreadedPromiseStates.not_ready


def test_run(game: Game, window: Window, level: Level) -> None:
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def increment() -> None:
        game.push_level(level)

    assert p.state is ThreadedPromiseStates.ready

    @game.event
    def before_run() -> None:
        schedule_once(lambda dt: window.close(), .25)
        p.run()

    game.run(window)
    assert game.level is level
    assert game.levels == [level]
    assert p.state is ThreadedPromiseStates.done


def test_on_done_no_args(game: Game, window: Window, level: Level) -> None:
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def return_5() -> int:
        sleep(1)
        return 5

    @p.event
    def on_done(value: int) -> None:
        assert value == 5
        game.push_level(level)

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: window.close(), 1.5)

    game.run(window)
    assert game.levels == [level]


def test_on_done_with_args(game: Game, window: Window, level: Level) -> None:
    p: ThreadedPromise = ThreadedPromise(game.thread_pool)

    @p.register_func
    def with_args(name: str, number: int = 0) -> Tuple[str, int]:
        return (name, number)

    @p.event
    def on_done(t: Tuple[str, int]) -> None:
        assert t == ('test', 10)
        game.push_level(level)

    @game.event
    def before_run() -> None:
        p.run('test', number=10)
        schedule_once(lambda dt: window.close(), .5)

    game.run(window)
    assert game.levels == [level]


def test_on_error(game: Game, window: Window) -> None:
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
        return EVENT_HANDLED

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: window.close(), .5)

    game.run(window)
    assert game.level is worked
    assert p.state is ThreadedPromiseStates.error


def test_cancel(game: Game, window: Window) -> None:
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

    @p.event
    def on_error(e: Exception) -> None:
        game.push_level(error)

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: p.cancel(), 0.5)
        schedule_once(lambda DT: window.close(), 1.5)

    game.run(window)
    assert game.levels == [worked]
    assert p.state is ThreadedPromiseStates.cancelled


def test_finally_no_error(game: Game, window: Window) -> None:
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

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: window.close(), .5)

    game.run(window)
    assert game.levels == [return_level, finally_level]


def test_finally_with_error(game: Game, window: Window) -> None:
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

    @game.event
    def before_run() -> None:
        p.run()
        schedule_once(lambda dt: window.close(), .5)

    game.run(window)
    assert game.levels == [error_level, finally_level]
