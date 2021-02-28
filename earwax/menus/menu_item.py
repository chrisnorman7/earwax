"""Provides the MenuItem class."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from attr import attrs

from ..action import ActionFunctionType
from ..mixins import RegisterEventMixin

if TYPE_CHECKING:
    from ..types import TitleFunction


@attrs(auto_attribs=True)
class MenuItem(RegisterEventMixin):
    """An item in a :class:`~earwax.menu.Menu`.

    This class is rarely used directly, instead
    :meth:`earwax.menu.Menu.add_item` or :meth:`earwax.menu.Menu.item` can be
    used to return an instance.

    :ivar ~earwax.MenuItem.func: The function which will be called when this
        item is activated.

    :ivar ~earwax.MenuItem.title: The title of this menu item.

        If this value is a callable, it should return a string which will be
        used as the title.

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

    func: ActionFunctionType
    title: Optional[Union[str, "TitleFunction"]] = None
    select_sound_path: Optional[Path] = None
    loop_select_sound: bool = False
    activate_sound_path: Optional[Path] = None

    def __attrs_post_init__(self) -> None:
        """Register events."""
        self.register_event(self.on_selected)

    def get_title(self) -> Optional[str]:
        """Return the proper title of this object.

        If :attr:`self.title <earwax.mixins.TitleMixin.title>` is a callable,
        its return value will be returned.
        """
        if callable(self.title):
            return self.title()
        return self.title

    def on_selected(self) -> None:
        """Handle this menu item being selected."""
        pass
