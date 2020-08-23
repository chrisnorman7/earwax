"""Provides the MenuItem class."""

from attr import attrs

from ..action import ActionFunctionType


@attrs(auto_attribs=True)
class MenuItem:
    """An item in a :class:`~earwax.menu.Menu`.

    This class is rarely used directly, instead
    :meth:`~earwax.menu.Menu.add_item` can be used to return an instance.

    :ivar ~earwax.MenuItem.title: The title of this menu item.

    :ivar ~earwax.MenuItem.func: The function which will be called when this
        item is activated.
    """

    title: str
    func: ActionFunctionType

    def on_selected(self) -> None:
        """The function which will be called when this menu item is
        selected.

        Could be overridden to play a sound for example."""
        pass
