"""Provides the CallResponseLevel class, and various supporting classes."""

import os.path
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar, Union

from attr import Factory, attrs
from pyglet.window import key
from shortuuid import uuid

from .config import Config, ConfigValue
from .editor import Editor
from .hat_directions import DOWN, LEFT, RIGHT, UP
from .level import Level
from .menus.menu import Menu
from .mixins import DumpLoadMixin
from .types import ActionFunctionType, OptionalGenerator

T = TypeVar("T")
WaitType = Optional[Union[float, Tuple[float, float]]]


@attrs(auto_attribs=True)
class ConversationBase(DumpLoadMixin):
    """A base for conversations and finishers."""

    id: str = Factory(uuid)
    text: Optional[str] = None
    sound: Optional[str] = None

    def __attrs_post_init__(self) -> None:
        """Ensure we have either text or a sound."""
        if self.text is None and self.sound is None:
            raise RuntimeError(
                "Neither text or sound was provided. This object would be "
                "completely silent."
            )


@attrs(auto_attribs=True)
class ConversationSection(ConversationBase):
    """A part of a conversation."""

    before_wait: WaitType = None
    after_wait: WaitType = None
    response_ids: List[str] = Factory(list)
    finisher_ids: List[str] = Factory(list)


@attrs(auto_attribs=True)
class Finisher(ConversationBase):
    """Do something after a response has been selected."""


ItemType = Union[ConversationSection, Finisher]
ConversationSectionDict = Dict[str, ConversationSection]
FinisherDict = Dict[str, Finisher]


@attrs(auto_attribs=True)
class ConversationTree(DumpLoadMixin):
    """A structure for holding conversation sections and finishers."""

    sections: ConversationSectionDict = Factory(dict)
    finishers: FinisherDict = Factory(dict)
    initial_section_id: Optional[str] = None
    winning_section_ids: List[str] = Factory(list)


class CallResponseSettings(Config):
    """Configuration for a conversation session."""

    __section_name__ = "Settings"
    output_audio: ConfigValue[bool] = ConfigValue(True, name="Play audio")
    output_braille: ConfigValue[bool] = ConfigValue(
        True, name="Output in braille"
    )
    output_speech: ConfigValue[bool] = ConfigValue(True, name="Speak text")


@attrs(auto_attribs=True)
class ItemsStack:
    """Store items."""

    items: List[ItemType]
    position: int


@attrs(auto_attribs=True)
class ConversationEditor(Level):
    """Used for editing a conversation tree."""

    tree: ConversationTree = Factory(ConversationTree)
    filename: Path = Factory(lambda: Path("tree.crt"))
    items: List[ItemType] = Factory(list)
    stack: List[ItemsStack] = Factory(list)
    at_home: bool = False
    current_position: int = 0

    def __attrs_post_init__(self) -> None:
        """Add actions."""
        self.home(silent=True)
        self.action("Previous item", symbol=key.UP, hat_direction=UP)(
            self.previous_item
        )
        self.action("Collapse item", symbol=key.LEFT, hat_direction=LEFT)(
            self.collapse_item
        )
        self.action("Next item", symbol=key.DOWN, hat_direction=DOWN)(
            self.next_item
        )
        self.action("Expand item", symbol=key.RIGHT, hat_direction=RIGHT)(
            self.expand_item
        )
        self.action("Set item text", symbol=key.T)(self.set_text)
        self.action("Set item sound", symbol=key.S)(self.set_sound)
        self.action("New conversation section", symbol=key.N)(self.new_section)
        self.action("New finisher", symbol=key.N, modifiers=key.MOD_SHIFT)(
            self.new_finisher
        )
        self.action("Pick valid responses", symbol=key.R, joystick_button=3)(
            self.response_menu
        )
        self.action("Pick possible finishers", symbol=key.F)(
            self.finisher_menu
        )
        self.action("Set initial section", symbol=key.I)(self.set_initial_id)
        self.action(
            "Save", symbol=key.S, modifiers=key.MOD_CTRL, joystick_button=0
        )(self.save)
        self.action(
            "Help",
            symbol=key.SLASH,
            modifiers=key.MOD_SHIFT,
            joystick_button=4,
        )(self.game.push_action_menu)
        return super().__attrs_post_init__()

    @property
    def current_item(self) -> ItemType:
        """Get the currently focused entry."""
        return self.items[self.current_position]

    def home(self, silent: bool = False) -> None:
        """Populate the items list with all items.

        :param silent: If ``True``, the selected item will not be output.
        """
        self.at_home = True
        self.items.clear()
        self.items.extend(self.tree.sections.values())
        self.items.extend(self.tree.finishers.values())
        self.sort_items()
        self.current_position = 0
        if not silent:
            self.output_item()

    def sort_items(self) -> None:
        """Sort items by ID."""

        def k(item: ItemType) -> str:
            if (
                isinstance(item, ConversationSection)
                and item.id == self.tree.initial_section_id
            ):
                return ""
            return item.id

        self.items.sort(key=k)

    def output_item(self) -> None:
        """Output the current item."""
        item: ItemType = self.current_item
        if item.text is not None:
            self.game.output(item.text)
        if item.sound is not None:
            p: Path = Path(item.sound)
            self.game.interface_sound_manager.play_path(p)

    def switch_item(self, direction: int) -> None:
        """Switch items."""
        if not self.items:
            return self.game.output("There are no items to show.")
        self.current_position += direction
        if self.current_position < 0:
            self.current_position = 0
        elif self.current_position >= len(self.items):
            self.current_position = len(self.items) - 1
        self.output_item()

    def previous_item(self) -> None:
        """Move up in the current list."""
        self.switch_item(-1)

    def next_item(self) -> None:
        """Move down in the items list."""
        self.switch_item(1)

    def collapse_item(self) -> None:
        """Move up to the previous level of items."""
        try:
            stack: ItemsStack = self.stack.pop()
            self.items = stack.items
            self.current_position = stack.position
        except IndexError:
            self.home(silent=True)
        self.output_item()

    def expand_item(self) -> None:
        """Move into the next level of items."""
        if not self.at_home:
            self.stack.append(ItemsStack(self.items, self.current_position))
        else:
            self.at_home = False
        item: ItemType = self.current_item
        s: ConversationSection
        f: Finisher
        if isinstance(item, ConversationSection):
            self.items = [
                s
                for s in self.tree.sections.values()
                if s.id in item.response_ids
            ]
            self.items.extend(
                f
                for f in self.tree.finishers.values()
                if f.id in item.finisher_ids
            )
        else:
            self.items = [
                s
                for s in self.tree.sections.values()
                if item.id in s.finisher_ids
            ]
        if self.items:
            self.sort_items()
            self.current_position = 0
            self.output_item()
        else:
            self.game.output("There are no items to show.")

    def set_text(self) -> OptionalGenerator:
        """Set the text for the currently focused item."""
        if not self.items:
            return self.game.output(
                "There is nothing for you to set the text on."
            )
        item: ItemType = self.current_item
        e: Editor = Editor(self.game, text=item.text or "")

        @e.event
        def on_submit(text: str) -> None:
            if text:
                item.text = text
                self.game.output("Text set.")
            else:
                item.text = None
                self.game.output("Text cleared.")
            self.game.pop_level()

        self.game.output(f"Enter text: {item.text}")
        yield
        self.game.push_level(e)

    def set_sound(self) -> OptionalGenerator:
        """Set the sound for the current item."""
        if not self.items:
            return self.game.output(
                "There is nothing for you to set the sound for."
            )
        item: ItemType = self.current_item
        e: Editor = Editor(self.game, text=item.sound or "")

        @e.event
        def on_submit(text: str) -> None:
            if text:
                if os.path.exists(text):
                    item.sound = text
                    self.game.output("Sound set.")
                else:
                    self.game.output(f"Path does not exist: {text}.")
            else:
                item.sound = None
                self.game.output("Sound cleared.")
            self.game.pop_level()

        self.game.output(f"Enter sound: {item.sound}")
        yield
        self.game.push_level(e)

    def save(self) -> None:
        """Save this tree."""
        self.tree.save(self.filename)
        self.game.output("Saved.")

    def new_section(self) -> None:
        """Create a new conversation section."""
        s: ConversationSection = ConversationSection(text="Untitled Section")
        self.tree.sections[s.id] = s
        self.home(silent=True)
        self.current_position = self.items.index(s)
        self.output_item()

    def new_finisher(self) -> None:
        """Create a new finisher."""
        f: Finisher = Finisher(text="Untitled Finisher")
        self.tree.finishers[f.id] = f
        self.home(silent=True)
        self.current_position = self.items.index(key.S)
        self.output_item()

    def response_menu(self) -> OptionalGenerator:
        """Show a response menu for the current item."""
        item: ItemType = self.current_item
        if isinstance(item, Finisher):
            return self.game.output(
                "Finishers cannot have calls or responses."
            )

        def add_response(response: ConversationSection) -> ActionFunctionType:
            def inner() -> None:
                assert isinstance(item, ConversationSection)
                item.response_ids.append(response.id)
                self.game.cancel("Done.")

            return inner

        def remove_response(
            response: ConversationSection,
        ) -> ActionFunctionType:
            def inner() -> None:
                assert isinstance(item, ConversationSection)
                if response.id in item.response_ids:
                    item.response_ids.remove(response.id)
                self.game.cancel("Done.")

            return inner

        m: Menu = Menu(self.game, "Responses")
        i: str
        response: ConversationSection
        for i in item.response_ids:
            response = self.tree.sections[i]
            m.add_item(
                remove_response(response),
                title=f"Remove {response.text}",
                select_sound_path=None
                if response.sound is None
                else Path(response.sound),
            )
        for response in self.tree.sections.values():
            if response.id in item.response_ids or response is item:
                continue
            m.add_item(
                add_response(response),
                title=f"Add {response.text}",
                select_sound_path=None
                if response.sound is None
                else Path(
                    response.sound,
                ),
            )
        yield
        self.game.push_level(m)

    def finisher_menu(self) -> OptionalGenerator:
        """Show a menu of finishers for the current item."""
        item: ItemType = self.current_item
        if isinstance(item, Finisher):
            return self.game.output(
                "Finishers cannot contain other finishers."
            )

        def add_finisher(finisher: Finisher) -> ActionFunctionType:
            def inner() -> None:
                assert isinstance(item, ConversationSection)
                item.finisher_ids.append(finisher.id)
                self.game.cancel("Done.")

            return inner

        def remove_finisher(
            finisher: Finisher,
        ) -> ActionFunctionType:
            def inner() -> None:
                assert isinstance(item, ConversationSection)
                if finisher.id in item.finisher_ids:
                    item.finisher_ids.remove(finisher.id)
                self.game.cancel("Done.")

            return inner

        m: Menu = Menu(self.game, "Finishers")
        i: str
        finisher: Finisher
        for i in item.finisher_ids:
            finisher = self.tree.finishers[i]
            m.add_item(
                remove_finisher(finisher),
                title=f"Remove {finisher.text}",
                select_sound_path=None
                if finisher.sound is None
                else Path(finisher.sound),
            )
        for finisher in self.tree.finishers.values():
            if finisher.id in item.finisher_ids:
                continue
            m.add_item(
                add_finisher(finisher),
                title=f"Add {finisher.text}",
                select_sound_path=None
                if finisher.sound is None
                else Path(
                    finisher.sound,
                ),
            )
        yield
        self.game.push_level(m)

    def set_initial_id(self) -> None:
        """Set the initial conversation section."""
        if not self.tree.sections:
            return self.game.output(
                "There are currently no conversation sections."
            )
        item: ItemType = self.current_item
        if isinstance(item, Finisher):
            return self.game.output("You must select a conversation section.")
        self.tree.initial_section_id = item.id
        self.game.output("Initial section set.")
