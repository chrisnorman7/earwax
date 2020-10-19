Staggered Promises
==================

The :class:`earwax.StaggeredPromise` class, which should have probably been called the ``ContinuationPromise`` class, was created out of my desire to write MOO-style suspends in Python.

Using the class, you can simply yield a number, and your function will suspend for *approximately* that long::

    from earwax.types import StaggeredPromiseGeneratorType

    @StaggeredPromise.decorate
    def promise() -> StaggeredPromiseGeneratorType:
        game.output('Starting now.')
        yield 2.0
        game.output('Still working.')
        yield 5.0
        game.output('Done.')


    promise.run()

The only event which differs from those found on ::ref:`Threaded Promise`, is the :meth:`~earwax.StaggeredPromise.on_next` event.

This event is dispatched every time your promise function yields::

    @promise.event
    def on_next(delay: float) -> None:
    print('Delay: %.2f' % delay)
