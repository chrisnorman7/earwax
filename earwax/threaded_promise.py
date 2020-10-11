"""Provides the ThreadedPromise class."""

from concurrent.futures import Executor, Future
from enum import Enum
from typing import Any, Callable, Optional

from attr import attrib, attrs
from pyglet.clock import schedule, unschedule
from pyglet.event import EventDispatcher

ThreadedPromiseFunctionType = Callable[..., Any]


class ThreadedPromiseStates(Enum):
    """The possible states of :class:`earwax.ThreadedPromise` instances."""

    not_ready = 0
    ready = 1
    running = 2
    done = 3
    error = 4
    cancelled = 5


@attrs(auto_attribs=True)
class ThreadedPromise(EventDispatcher):
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

    Instances of this class have a few possible states which are all contained
    in the :class:`~earwax.ThreadedPromiseStates` enumeration:

    :attr:`~earwax.ThreadedPromiseStates.not_ready`
        The promise has been created, but a function must still be registered
        with the :meth:`~earwax.ThreadedPromise.register_func` method.

    :attr:`~earwax.ThreadedPromiseStates.ready`
        The promise has been created, and a function registered. The
        :meth:`~earwax.ThreadedPromise.run` method has not yet been called.

    :attr:`~earwax.ThreadedPromiseStates.running`
        The promise's :meth:`~earwax.ThreadedPromise.run` method has been
        called, but the :attr:`~earwax.ThreadedPromise.future` has not
        completed yet.

    :attr:`~earwax.ThreadedPromiseStates.done`
        The promise has finished, and there was no error. The
        :meth:`~earwax.ThreadedPromise.on_done` event has already been
        dispatched.

    :attr:`~earwax.ThreadedPromiseStates.error`
        The promise completed, but there was an error, which was handled by the
        :attr:`~earwax.ThreadedPromise.on_error` event.

    :attr:`~earwax.ThreadedPromiseStates.cancelled`
        The promise has had its :meth:`~earwax.ThreadedPromise.cancel` method
        called, and its :meth:`~earwax.ThreadedPromise.on_cancel` event has
        been dispatched.

    :ivar ~earwax.ThreadedPromise.thread_pool: The thread pool to use.

    :ivar ~earwax.ThreadedPromise.func: The function to submit to the thread
    pool.

    :ivar ~earwax.ThreadedPromise.future: The future that is running, or None
    if the :meth:`~earwax.ThreadedPromise.run` method has not yet been called.

    :ivar ~earwax.ThreadedPromise.state: The state this promise is in (see
    above).
    """

    thread_pool: Executor

    func: Optional[ThreadedPromiseFunctionType] = None

    future: Optional[Future] = None

    state: ThreadedPromiseStates = attrib()

    @state.default
    def get_state(instance: 'ThreadedPromise') -> ThreadedPromiseStates:
        if instance.func is None:
            return ThreadedPromiseStates.not_ready
        return ThreadedPromiseStates.ready

    def __attrs_post_init__(self) -> None:
        for func in (
            self.on_done, self.on_error, self.on_cancel, self.on_finally
        ):
            self.register_event_type(func.__name__)

    def register_func(
        self, func: ThreadedPromiseFunctionType
    ) -> ThreadedPromiseFunctionType:
        """Register the function to be called by the
        :meth:`~earwax.ThreadedPromise.run` method.

        :param func: The function to use. Will be stored in :attr:`self.func
        <earwax.ThreadedPromise.func>`.
        """
        self.func = func
        return func

    def on_done(self, result: Any) -> None:
        """The event that is dispatched when the future completes with no
        error."""
        pass

    def on_error(self, e: Exception) -> None:
        """The event that is dispatched when the future raises an error."""
        raise e

    def on_cancel(self) -> None:
        """The event that is dispatched when this instance has its
        :meth:`~earwax.ThreadedPromise.cancel` method called."""
        pass

    def on_finally(self) -> None:
        """The event that is dispatched when the future completes, whether or
        not it raises an error."""
        pass

    def check(self, dt: float) -> None:
        """Check to see if the future has finished or not.

        If it has, dispatch the :meth:`~earwax.ThreadedPromise.on_done` event
        with the resulting value.

        If an error has been raised, dispatch the
        :meth:`~earwax.ThreadedPromise.on_error` event.
        """
        if self.future is not None and self.future.done():
            try:
                self.dispatch_event('on_done', self.future.result())
                self.state = ThreadedPromiseStates.done
            except Exception as e:
                self.dispatch_event('on_error', e)
                self.state = ThreadedPromiseStates.error
            finally:
                unschedule(self.check)
                self.dispatch_event('on_finally')

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
            raise RuntimeError('%r has no function registered.' % self)
        self.future = self.thread_pool.submit(self.func, *args, **kwargs)
        self.state = ThreadedPromiseStates.running
        schedule(self.check)

    def cancel(self) -> None:
        """Try to cancel :attr:`~earwax.ThreadedPromise.future`.

        If There is no future, ``RuntimeError`` will be raised.
        """
        if self.future is None:
            raise RuntimeError('%s has no future yet.' % self)
        self.future.cancel()
        self.state = ThreadedPromiseStates.cancelled
        self.dispatch_event('on_cancel')
