"""Provides hat motions to be used as shortcuts."""

from typing import Tuple

Motion = Tuple[int, int]

DEFAULT: Motion = (0, 0)
UP: Motion = (0, 1)
DOWN: Motion = (0, -1)
LEFT: Motion = (-1, 0)
RIGHT: Motion = (1, 0)
