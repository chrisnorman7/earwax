"""This module is useless.

It is here so that NVDA doesn't crash when testing Earwax in the REPL.

To use it::

    import t
    # ...

It just unsets Pyglet's shadow_window flag.
"""

import pyglet
pyglet.options['shadow_window'] = False
