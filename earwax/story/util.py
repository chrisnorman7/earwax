"""Provides various utility functions for stories."""

from typing import TYPE_CHECKING, Dict, Optional, Union
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    from .world import RoomObject, WorldRoom


def get_element(
    tag: str, text: Optional[str] = None, attrib: Dict[str, str] = {}
) -> Element:
    """Return a fully-formed element.

    For example::

        get_element('h1', text='This is a heading', attrib={'id': 'title'})

    The above code would return an object which - when rendered in XML, would
    give something like::

        <h1 id="title">This is a heading</h1>

    :param tag: The XML tag to use.

    :param text: The text contained by this element.

    :param attrib: The extra attributes for the element.
    """
    e: Element = Element(tag, attrib=attrib)
    if text is not None:
        e.text = text
    return e


def stringify(obj: Union['WorldRoom', 'RoomObject']) -> str:
    """Return this object as a string.

    :param obj: The object to work with.
    """
    return f'{obj.name} (#{obj.id})'
