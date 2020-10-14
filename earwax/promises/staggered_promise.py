"""Provides the StaggeredPromise class."""

from typing import Callable, Generator, Optional

from attr import attrs
from pyglet.clock import schedule_once

from .base import Promise, T

StaggeredPromiseGeneratorType = Generator[float, None, T]
StaggeredPromiseFunctionType = Callable[..., StaggeredPromiseGeneratorType]


@attrs(auto_attribs=True)
class StaggeredPromise(Promise):
    """A promise that can suspend itself at will."""

    func: StaggeredPromiseFunctionType
    generator: Optional[StaggeredPromiseGeneratorType]

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.register_event_type(self.on_next.__name__)

    def on_next(self, delay: float) -> None:
        """The event that is dispatched every time ``next`` is called on
        :meth:`self.func <earwax.StaggeredPromise.func>`.
        :param delay: The delay that was requested by the function.
        """
        pass

    def run(self, *args, **kwargs) -> None:
        """Start ``self.func`` running."""
        super().run()
        self.generator = self.func(*args, **kwargs)
        self.do_next(None)

    def do_next(self, dt: Optional[float]) -> None:
        """Call ``next(self.generator)``, and then suspend for however long the
        function demands.

        If ``StopIteration`` is raised, then the args from that exception are
        sent to the :meth:`self.on_done <earwax.Promise.on_done>` event.

        If any other exception is raised, then that exception is passed along
        to the :meth:`self.on_error <earwax.Promise.on_error>` event.

        :param dt: The time since the last run, as passed by
        ``pyglet.clock.schedule_once``.
        """
        if self.generator is None:
            raise RuntimeError('You must call ``self.run`` first.')
        try:
            delay: float = next(self.generator)
            self.dispatch_event('on_next', delay)
            schedule_once(self.do_next, delay)
        except StopIteration as e:
            self.done(*e.args)
            self.dispatch_event('on_finally')
        except Exception as e:
            self.error(e)
            self.dispatch_event('on_finally')

    def cancel(self) -> None:
        """Cancel :attr:`self.generator <earwax.StaggeredPromise.generator>`,
        and set the proper state."""
        super().cancel()
        if self.generator is not None:
            self.generator.close()
