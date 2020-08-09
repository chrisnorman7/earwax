"""Provides the MenuItem class."""

from attr import attrs

from ..action import ActionFunctionType


@attrs(auto_attribs=True)
class MenuItem:
    """An item in a menu."""

    # The title of this menu item.
    title: str

    # The function which will be called when this item is activated.
    func: ActionFunctionType

    def on_selected(self) -> None:
        """The function which will be called when this menu item is
        selected."""
        pass
