"""Provides the MenuItem class."""

from pathlib import Path
from typing import Optional

from attr import attrs

from ..action import ActionFunctionType
from ..mixins import RegisterEventMixin


@attrs(auto_attribs=True)
class MenuItem(RegisterEventMixin):
    """An item in a :class:`~earwax.menu.Menu`.

    This class is rarely used directly, instead
    :meth:`earwax.menu.Menu.add_item` can be used to return an instance.

    :ivar ~earwax.MenuItem.title: The title of this menu item.

    :ivar ~earwax.MenuItem.func: The function which will be called when this
        item is activated.

    :ivar ~earwax.MenuItem.select_sound_path: The path to a sound which should
        play when this menu item is selected.

        If this value is ``None`` (the default), then no sound will be heard
        unless the containing menu has its
        :attr:`~earwax.Menu.item_select_sound_path` attribute set to something
        that is not ``None``, or
        :attr:`earwax.EarwaxConfig.menus.default_item_select_sound` is not
        ``None``.

    :ivar ~earwax.MenuItem.activate_sound_path: The path to a sound which
        should play when this menu item is activated.

        If this value is ``None`` (the default), then no sound will be heard
        unless the containing menu has its
        :attr:`~earwax.Menu.item_activate_sound_path` attribute set to
        something that is not ``None``, or
        :attr:`earwax.EarwaxConfig.menus.default_item_select_sound` is not
        ``None``.
    """

    title: str
    func: ActionFunctionType
    select_sound_path: Optional[Path] = None
    activate_sound_path: Optional[Path] = None

    def __attrs_post_init__(self) -> None:
        """Register events."""
        self.register_event(self.on_selected)

    def on_selected(self) -> None:
        """Handle this menu item being selected."""
        pass
