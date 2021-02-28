"""Provides various utility functions used by Earwax."""

from datetime import timedelta
from pathlib import Path
from random import choice
from typing import List, Optional


def nearest_square(n: int, allow_higher: bool = False) -> int:
    """Given a number ``n``, find the nearest square number.

    If ``allow_higher`` evaluates to ``True``, return the first square higher
    than ``n``. Otherwise, return the last square below ``n``.

    For example::

        nearest_square(5) == 2  # 2 * 2 == 4
        nearest_square(24, allow_higher=True) == 5  # 5 * 5 == 25
        nearest_square(16) == 4
        nearest_square(16, allow_higher=True) == 4

    :param n: The number whose nearest square should be returned.
    """
    i: int = 1
    while True:
        res: int = i * i
        if res == n:
            return i
        elif res > n:
            if allow_higher:
                return i
            else:
                return i - 1
        else:
            i += 1


def english_list(
    items: List[str],
    empty: str = "Nothing",
    sep: str = ", ",
    and_: str = "and ",
) -> str:
    """Given a list of strings, returns a string representing them as a list.

    For example::

        english_list([]) == 'Nothing'
        english_list(['bananas']) == 'bananas'
        english_list(['apples', 'bananas']) == 'apples, and bananas'
        english_list(
            ['apples', 'bananas', 'oranges']
        ) == 'apples, bananas, and oranges'
        english_list(['tea', 'coffee'], and_='or ') == 'tea, or coffee'

    :param items: The items to turn into a string.

    :param empty: The string to return if ``items`` is empty.

    :param sep: The string to separate list items with.

    :param and_: The string to show before the last item in the list.
    """
    items = items.copy()
    if len(items) == 1:
        return items[0]
    if len(items) == 0:
        return empty
    else:
        items[-1] = f"{and_}{items[-1]}"
        return sep.join(items)


def pluralise(n: int, single: str, multiple: Optional[str] = None) -> str:
    """If ``n == 1``, return ``single``. Otherwise return ``multiple``.

    If ``multiple`` is ``None``, it will become ``single + 's'``.

    For example::

        pluralise(1, 'axe') == 'axe'
        pluralise(2, 'axe') == 'axes'
        pluralise(1, 'person', multiple='people') == 'person'
        pluralise(2, 'person', multiple='people') == 'people'
        pluralise(0, 'person', multiple='people') == 'people'

    :param n: The number of items we are dealing with.

    :param single: The name of the thing when there is only 1.

    :param multiple: The name of things when there are numbers other than 1.
    """
    if n == 1:
        return single
    elif multiple is None:
        return single + "s"
    else:
        return multiple


def format_timedelta(td: timedelta, *args, **kwargs) -> str:
    """Given a timedelta ``td``, return it as a human readable time.

    For example::

        td = timedelta(days=400, hours=2, seconds=3)
        format_timedelta(
            td
        ) == '1 year, 1 month, 4 days, 2 hours, and 3 seconds'

    *Note*: It is assumed that a month always contains 31 days.

    :param td: The time delta to work with.

    :param args: The extra positional arguments to pass to
        :meth:`~earwax.utils.english_list`.

    :param kwargs: The extra keyword arguments to pass onto
        :meth:`~earwax.utils.english_list`.
    """
    items: List[str] = []
    years: int
    days: int
    years, days = divmod(td.days, 365)
    items.append(f'{years} {pluralise(years, "year")}')
    months: int
    months, days = divmod(days, 31)
    items.append(f'{months} {pluralise(months, "month")}')
    items.append(f'{days} {pluralise(days, "day")}')
    hours: int
    seconds: int
    hours, seconds = divmod(td.seconds, 3600)
    items.append(f'{hours} {pluralise(hours, "hour")}')
    minutes: int
    minutes, seconds = divmod(seconds, 60)
    items.append(f'{minutes} {pluralise(minutes, "minute")}')
    items.append(f'{seconds} {pluralise(seconds, "second")}')
    return english_list(items, *args, **kwargs)


def random_file(path: Path) -> Path:
    """Call recursively until a file is reached.

    :param path: The path to start with.
    """
    if path.is_dir():
        path = choice(list(path.iterdir()))
        return random_file(path)
    return path
