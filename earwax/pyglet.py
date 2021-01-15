"""A mock pyglet module.

This module exists to prevent ReadTheDocs from kicking off when docs are built.
"""

try:
    from pyglet import app
    from pyglet.clock import schedule, schedule_once, unschedule
    from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventDispatcher
    from pyglet.input import Joystick, get_joysticks
    from pyglet.resource import get_settings_path
    from pyglet.window import Window, key, mouse
except ModuleNotFoundError:
    app = None
    schedule, schedule_interval, schedule_once, unschedule = (
        print, print, print, print
    )
    EVENT_HANDLED = True
    EVENT_UNHANDLED = None
    EventDispatcher = object
    Joystick, get_joysticks = (object, list)
    get_settings_path = str
    Window = object
    key = None
    mouse = None
