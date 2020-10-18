"""Provides the base Promise class, and the PromisesStates enumeration."""

from enum import Enum
from typing import Generic, TypeVar

from attr import attrib, attrs

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object

T = TypeVar('T')


class PromiseStates(Enum):
    """The possible states of :class:`earwax.Promise` instances.

    :ivar ~earwax.PromiseStates.not_ready: The promise has been created, but a
        function must still be added.

        How this is done depends on how the promise subclass in question has
        been implemented, and may not always be used.

    :ivar ~earwax.PromiseStates.ready: The promise has been created, and a
        function registered. The :meth:`~earwax.ThreadedPromise.run` method has
        not yet been called.

    :ivar ~earwax.PromiseStates.running: The promise's
        :meth:`~earwax.ThreadedPromise.run` method has been called, but the
        function has not yet returned a value, or raised an error.

    :ivar ~earwax.PromiseStates.done: The promise has finished, and there was
        no error. The :meth:`~earwax.Promise.on_done` and
        :meth:`~earwax.Promise.on_finally` events have already been dispatched.

    :ivar ~earwax.PromiseStates.error: The promise completed, but there was an
        error, which was handled by the :meth:`~earwax.Promise.on_error` event.

        The :meth:`~earwax.Promise.on_finally` event has been dispatched.

    :ivar ~earwax.PromiseStates.cancelled: The promise has had its
        :meth:`~earwax.Promise.cancel` method called, and its
        :meth:`~earwax.Promise.on_cancel` event has been dispatched.
    """

    not_ready = 0
    ready = 1
    running = 2
    done = 3
    error = 4
    cancelled = 5


@attrs(auto_attribs=True)
class Promise(Generic[T], EventDispatcher):
    """The base class for promises.

    Instances of this class have a few possible states which are contained in
    the :class:`~earwax.PromiseStates` enumeration.

    :ivar ~earwax.Promise.state: The state this promise is in (see
        above).
    """

    state: PromiseStates = attrib(default=PromiseStates.ready, init=False)

    def __attrs_post_init__(self) -> None:
        for func in (
            self.on_done, self.on_error, self.on_cancel, self.on_finally
        ):
            self.register_event_type(func.__name__)

    def on_done(self, result: T) -> None:
        """The event that is dispatched when this promise completes with no
        error.

        :param result: The value returned by the function.
        """
        pass

    def on_error(self, e: Exception) -> None:
        """The event that is dispatched when this promise raises an error.

        :param e: The exception that was raised.
        """
        raise e

    def on_cancel(self) -> None:
        """The event that is dispatched when this instance has its
        :meth:`~earwax.Promise.cancel` method called.
        """
        pass

    def on_finally(self) -> None:
        """The event that is dispatched when this promise completes, whether or
        not it raises an error.
        """
        pass

    def run(self, *args, **kwargs) -> None:
        """Start this promise running."""
        self.state = PromiseStates.running

    def cancel(self) -> None:
        """Override to provide cancel functionality."""
        self.state = PromiseStates.cancelled
        self.dispatch_event('on_cancel')

    def done(self, value: T) -> None:
        """Dispatch the :meth:`~earwax.Promise.on_done` event with the given
        ``value``, and set :attr:`self.state <earwax.Promise.state>` to
        :attr:`earwax.PromiseStates.done`.

        :param value: The value that was returned from whatever function this
            promise had.
        """
        self.dispatch_event('on_done', value)
        self.dispatch_event('on_finally')
        self.state = PromiseStates.done

    def error(self, e: Exception) -> None:
        """Dispatch the :meth:`~earwax.Promise.on_error` event with the passed
        exception.

        :param e: The exception that was raised.
        """
        self.dispatch_event('on_error', e)
        self.dispatch_event('on_finally')
        self.state = PromiseStates.error
