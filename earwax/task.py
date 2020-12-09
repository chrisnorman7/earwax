"""Provides the Task class."""

from typing import Callable

from attr import Factory, attrib, attrs

try:
    from pyglet.clock import schedule_once, unschedule
except ModuleNotFoundError:
    schedule_once, unschedule = (None, None)

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
        unschedule(self.func)
        self.running = False

    def start(self, immediately: bool = False) -> None:
        """Start this task."""
        schedule_once(self.func, self.interval())
        self.running = True
        if immediately:
            self.func(0.0)
