"""Provides the tts object.

You can use this object to output speech through the currently active screen
reader::

    from earwax import tts
    tts.output('Hello, Earwax.')
    tts.speak('Hello, speech.')
    tts.braille('Hello, braille.')

*NOTE*: Since version 2020-10-11, Earwax uses `Cytolk
<https://pypi.org/project/cytolk/>`_ for its TTS needs.

In addition to this change, there is now an extra :attr:`speech
<earwax.EarwaxConfig.speech` configuration section, which can be set to make
the :meth:`~earwax.Game.output` method behave how you'd like.
"""

try:
    from cytolk import tolk as tts
except ModuleNotFoundError:
    tts = None

__all__ = ["tts"]
