.. _Threaded Promise:

Threaded Promises
=================

The inspiration for the :class:`earwax.ThreadedPromise` class came from a game i was writing. I wanted to load assets, as well as data from the internet, and it was taking ages. While things were loading, the game appeared to crash, which obviously wasn't good.

With the :class:`~earwax.ThreadedPromise` class, you can leave something to work in another thread, while the main thread remains free to process input ETC. You can use the :meth:`~earwax.Promise.on_done` event to be notified of (and provided with) the return value from your function.

For example::

    promise: ThreadedPromise = ThreadedPromise(game.thread_pool)


    @promise.register_func
    def long_running_task() -> str:
        # Something which takes forever...
        return 'Finished.'


    @promise.event
    def on_done(value: str) -> None:
        game.output('Task complete.')


    promise.run()

As you can see from the above code, you use the :meth:`~earwax.ThreadedPromise.register_func` method to register the function to use. That function will be automatically called in another thread, and the result send to the :meth:`~earwax.Promise.on_done` event.

If your code is likely to raise an error, there is a :meth:`~earwax.Promise.on_error` event too::

    from pyglet.event import event_handled


    @promise.event
    def on_error(e: Exception) -> bool:
        game.output('Error: %r.' % e)
        return event_handled

By default, the ``on_error`` event raises the passed error, so it is necessary to return the ``event_handled`` value to prevent any other handlers from firing.

For the sake of completeness, there is a :meth:`~earwax.Promise.on_finally` event too::

    @promise.event
    def on_finally() -> None:
        game.output('Done.')

This event will be dispatched when the promise has been completed, whether or not an exception was raised.

If you want to cancel, there is a :meth:`~earwax.Promise.cancel` method to do it with, and of course a :meth:`~earwax.Promise.on_cancel` event which will be dispatched.

It is unlikely that the actual function will be cancelled, but you can rest assured that no futher events will be dispatched.

When you have created all of your events, you should use the :meth:`~earwax.ThreadedPromise.run` method to start your promise running.

It is worth noting that although this particular part of the tutorial concerns the :class:`~earwax.ThreadedPromise` class, all of the events that have been mentioned are actually present on the :class:`earwax.Promise` class, and it is simply up to subclasses to implement them.
