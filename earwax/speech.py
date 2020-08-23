"""Provides the tts object.

>>> from earwax import tts
>>> tts.speak('Hello, Earwax.')
"""

from accessible_output2.outputs.auto import Auto

tts: Auto = Auto()
