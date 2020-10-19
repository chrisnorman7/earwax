Promises
========

Promises are a way of running different kinds of tasks with Earwax.

The term is shamelessly stolen from `JavaScript <https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/Promise>`_, and Earwax's interpretation is largely the same: A promise is instantiated, and set to run. At some point in the future, the promise will have a value, which can be listened for with the :meth:`~earwax.Promise.on_done` event.

This part of the tutorial contains some further thoughts on using the different types of promise Earwax has to offer.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   threaded_promise

   staggered_promise
