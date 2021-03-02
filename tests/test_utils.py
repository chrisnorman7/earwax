"""Tests functions from earwax.utils."""

from datetime import timedelta
from typing import List

from earwax.utils import (english_list, format_timedelta, nearest_square,
                          pluralise)


def test_nearest_square() -> None:
    """Test the nearest_square function."""
    assert nearest_square(7) == 2
    assert nearest_square(7, allow_higher=True) == 3
    assert nearest_square(9) == 3
    assert nearest_square(9, allow_higher=True) == 3


def test_english_list() -> None:
    """Test the english_list function."""
    items: List[str] = []
    assert english_list(items) == "Nothing"
    items.append("tea")
    assert english_list(items) == "tea"
    items.append("coffee")
    assert english_list(items) == "tea, and coffee"
    assert english_list(items, and_="or ") == "tea, or coffee"
    assert english_list(items, sep=" ") == "tea and coffee"
    items.append("water")
    assert english_list(items) == "tea, coffee, and water"


def test_pluralise() -> None:
    """Test the pluralise function."""
    assert pluralise(1, "grape") == "grape"
    assert pluralise(2, "grape") == "grapes"
    assert pluralise(0, "grape") == "grapes"
    assert pluralise(1, "person", multiple="people") == "person"
    assert pluralise(15, "person", multiple="people") == "people"
    assert pluralise(0, "person", multiple="people") == "people"


def test_format_timedelta() -> None:
    """Test the format_timedelta function."""
    d = timedelta(days=400, hours=5, minutes=10, seconds=58)
    assert format_timedelta(d) == (
        "1 year, 1 month, 4 days, 5 hours, 10 minutes, and 58 seconds"
    )
    assert format_timedelta(d, sep=" ", and_="+ ") == (
        "1 year 1 month 4 days 5 hours 10 minutes + 58 seconds"
    )
