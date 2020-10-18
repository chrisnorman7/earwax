"""Provides the StaggeredPromise class."""

from typing import Callable, Generator, Optional

from attr import attrib, attrs

try:
    from pyglet.clock import schedule_once, unschedule
except ModuleNotFoundError:
    pass

from .base import Promise, T

StaggeredPromiseGeneratorType = Generator[float, None, T]
StaggeredPromiseFunctionType = Callable[..., StaggeredPromiseGeneratorType]


@attrs(auto_attribs=True)
class StaggeredPromise(Promise):
    """A promise that can suspend itself at will.

    I found myself missing the MOO-style suspend() function, so thought I'd
    make the same capability available in earwax::

        @StaggeredPromise.decorate
        def promise() -> StaggeredPromiseGeneratorType:
            game.output('Hello.')
            yield 2.0
            game.output('World.')

        promise.run()
        game.run(window)

    This class supports all the promise events found on
    :class:`earwax.Promise`, and also has a
    :meth:`~earwax.StaggeredPromise.on_next` event, which will fire whenever a
    promise suspends::

        @promise.event
        def on_next(delay: float) -> None:
            print(f'I waited {delay}.')

    :ivar ~earwax.StaggeredPromise.func: The function to run.

    :ivar ~earwax.StaggeredPromise.generator: The generator returned by
        :attr:`self.func <earwax.StaggeredPromise.func>`.
    """

    func: StaggeredPromiseFunctionType
    generator: Optional[StaggeredPromiseGeneratorType] = attrib(
        default=None, init=False
    )

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
        """Start :meth:`self.func <earwax.StaggeredPromise.func>` running, and
        set the proper state.

        :param args: The positional arguments passed to :meth:`self.func
            <earwax.StaggeredPromise.func>`.

        :param kwargs: The keyword arguments passed to :meth:`self.func
            <earwax.StaggeredPromise.func>`.
        """
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

            If this is the first time this method is called, ``dt`` will be
            ``None``.
        """
        if self.generator is None:
            raise RuntimeError('You must call ``self.run`` first.')
        try:
            delay: float = next(self.generator)
            self.dispatch_event('on_next', delay)
            schedule_once(self.do_next, delay)
        except StopIteration as e:
            if not e.args:
                e.args = (None, )
            self.done(*e.args)
        except Exception as e:
            self.error(e)

    def cancel(self) -> None:
        """Cancel :attr:`self.generator <earwax.StaggeredPromise.generator>`,
        and set the proper state.
        """
        super().cancel()
        if self.generator is None:
            raise RuntimeError('This promise has no generator.')
        unschedule(self.do_next)
        self.generator.close()

    @classmethod
    def decorate(
        cls, func: StaggeredPromiseFunctionType
    ) -> 'StaggeredPromise':
        """A decorator method for returning :class:`earwax.StaggeredPromise` instances.

        Using this function seems to help mypy figure out what type your
        function is.

        :param func: The function to decorate.
        """
        return cls(func)
