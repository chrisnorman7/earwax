"""Provides the Task class."""

from typing import Callable

from attr import Factory, attrib, attrs
from pyglet.clock import schedule_once, unschedule

IntervalFunction = Callable[[], float]
TaskFunction = Callable[[float], None]


@attrs(auto_attribs=True)
class Task:
    """A repeating task.

    This class can be used to perform a task at irregular intervals.

    By using a function as the interval, you can make tasks more random.

    :param ~earwax.Task.interval: The function to determine the interval
        between task runs.

    :param ~earwax.Task.func: The function to run as the task.

    :param ~earwax.Task.running: Whether or not a task is running.
    """

    interval: IntervalFunction
    func: TaskFunction
    running: bool = attrib(default=Factory(bool), init=False)

    def stop(self) -> None:
        """Stop this task from running."""
        unschedule(self._run)
        self.running = False

    def start(self, immediately: bool = False) -> None:
        """Start this task.

        Schedules :attr:`~earwax.Task.func` to run after whatever interval is
        returned by :attr:`~earwax.Task.interval`.

        Every time it runs, it will be rescheduled, until
        :meth:`~earwax.Task.stop` is called.

        :param immediately: If ``True``, then :attr:`self.func
            <earwax.Task.func>` will run as soon as it has been scheduled.
        """
        schedule_once(self._run, self.interval())
        self.running = True
        if immediately:
            self.func(0.0)

    def _run(self, dt: float) -> None:
        """Run :attr:`~earwax.Task.func`, and reschedule this function.

        :param dt: The ``dt`` parameter passed by
            ``pyglet.clock.schedule_once``.
        """
        self.func(dt)
        schedule_once(self._run, self.interval())
