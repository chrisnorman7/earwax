"""Provides the tts object.

You can use this object to output speech through either the currently active
screen reader, or SAPI::

    from earwax import tts
    tts.speak('Hello, Earwax.')

Although Earwax currently uses `accessible_output2
<https://pypi.org/project/accessible-output2/>`_ for the TTS backend, you
should not rely upon its specifics in your own code, as this is subject to
possible future change.
"""

from accessible_output2.outputs.auto import Auto

tts: Auto = Auto()
