"""Provides the base Promise class, and the PromisesStates enumeration."""

from enum import Enum
from typing import Generic, TypeVar

from attr import attrib, attrs
from pyglet.event import EventDispatcher

T = TypeVar('T')


class PromiseStates(Enum):
    """The possible states of :class:`earwax.ThreadedPromise` instances."""

    not_ready = 0
    ready = 1
    running = 2
    done = 3
    error = 4
    cancelled = 5


@attrs(auto_attribs=True)
class Promise(EventDispatcher, Generic[T]):
    """The base class for promises.

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
        """The event that is dispatched when the future completes with no
        error.

        :param result: The value returned by ``self.func``.
        """
        pass

    def on_error(self, e: Exception) -> None:
        """The event that is dispatched when ``self.func`` raises an error.

        :param e: The exception that was raised.
        """
        raise e

    def on_cancel(self) -> None:
        """The event that is dispatched when this instance has its
        :meth:`~earwax.Promise.cancel` method called."""
        pass

    def on_finally(self) -> None:
        """The event that is dispatched when ``self.func`` completes, whether
        or not it raises an error.
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
        """Dispatch the :meth:`earwax.Promise.on_done` event with ``value``,
        and set :attr:`self.state <earwax.Promise.stage>` to
        :attr:`earwax.PromiseStates.done`.

        :param value: The value that was returned from whatever function this
        promise had.
        """
        self.dispatch_event('on_done', value)
        self.state = PromiseStates.done

    def error(self, e: Exception) -> None:
        """Dispatch the :meth:`~earwax.Promise.on_error` event with the passed
        exception.

        :param e: The exception that was raised.
        """
        self.dispatch_event('on_error', e)
        self.state = PromiseStates.error
