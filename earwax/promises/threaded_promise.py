"""Provides the ThreadedPromise class."""

from concurrent.futures import Executor, Future
from typing import Callable, Optional

from attr import attrs

try:
    from pyglet.clock import schedule, unschedule
except ModuleNotFoundError:
    pass

from .base import Promise, PromiseStates, T

ThreadedPromiseFunctionType = Callable[..., T]


@attrs(auto_attribs=True)
class ThreadedPromise(Promise):
    """A promise that a value will be available in the future.

    Uses an ``Executor`` subclass (like ``ThreadPoolExecutor``, or
    ``ProcessPoolExecutor`` for threading).

    You can create this class directly, or by using decorators.

    Here is an example of the decorator syntax::

        from concurrent.futures import ThreadPoolExecutor

        promise: ThreadedPromise = ThreadedPromise(ThreadPoolExecutor())

        @promise.register_func
        def func() -> None:
            # Long-running task...
            return 5

        @promise.event
        def on_done(value: int) -> None:
            # Do something with the return value.

        @promise.event
        def on_error(e: Exception) -> None:
            # Do something with an error.

        @promise.event
        def on_finally():
            print('Done.')

        promise.run()

    Or you could create the promise manually::

        promise = ThreadedPromise(
            ThreadPoolExecutor(), func=predefined_function
        )
        promise.event('on_done')(print)
        promise.run()

    Note the use of Pyglet's own event system.

    :ivar ~earwax.ThreadedPromise.thread_pool: The thread pool to use.

    :ivar ~earwax.ThreadedPromise.func: The function to submit to the thread
        pool.

    :ivar ~earwax.ThreadedPromise.future: The future that is running, or None
        if the :meth:`~earwax.ThreadedPromise.run` method has not yet been
        called.
    """

    thread_pool: Executor

    func: Optional[ThreadedPromiseFunctionType] = None

    future: Optional[Future] = None

    def __attrs_post_init__(self) -> None:
        """Set the proper default state."""
        super().__attrs_post_init__()
        if self.func is None:
            self.state = PromiseStates.not_ready

    def register_func(
        self, func: ThreadedPromiseFunctionType
    ) -> ThreadedPromiseFunctionType:
        """Register promise function.

        Registers the function to be called by the
        :meth:`~earwax.ThreadedPromise.run` method.

        :param func: The function to use. Will be stored in :attr:`self.func
            <earwax.ThreadedPromise.func>`.
        """
        self.func = func
        self.state = PromiseStates.ready
        return func

    def check(self, dt: float) -> None:
        """Check state and react accordingly.

        Checks to see if :attr:`self.future <earwax.ThreadedPromise.future>`
        has finished or not.

        If it has, dispatch the :meth:`~earwax.Promise.on_done` event
        with the resulting value.

        If an error has been raised, dispatch the
        :meth:`~earwax.Promise.on_error` event with the resulting
        error.

        If either of these things have happened, dispatch the
        :meth:`~earwax.Promise.on_finally` event.

        :param dt: The time since the last run.

            This argument is required by ``pyglet.clock.schedule``.
        """
        if self.future is not None and self.future.done():
            try:
                self.done(self.future.result())
            except Exception as e:
                self.error(e)
            finally:
                unschedule(self.check)

    def run(self, *args, **kwargs) -> None:
        """Start this promise running.

        The result of calling ``submit`` on :attr:`self.thread_pool
        <earwax.ThreadedPromise.thread_pool>` will be stored on
        :attr:`self.future <earwax.ThreadedPromise.future>`.

        If this instance does not have a function registered yet,
        ``RuntimeError`` will be raised.

        :param args: The extra positional arguments to pass along to
            ``submit``.

        :param kwargs: The extra keyword arguments to pass along to ``submit``.
        """
        if self.func is None:
            raise RuntimeError("%r has no function registered." % self)
        self.future = self.thread_pool.submit(self.func, *args, **kwargs)
        super().run(*args, **kwargs)
        schedule(self.check)

    def cancel(self) -> None:
        """Try to cancel :attr:`self.future <earwax.ThreadedPromise.future>`.

        If There is no future, ``RuntimeError`` will be raised.
        """
        if self.future is None:
            raise RuntimeError("%s has no future yet." % self)
        self.future.cancel()
        unschedule(self.check)
        super().cancel()
