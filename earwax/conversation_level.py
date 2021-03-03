"""Provides the CallResponseLevel class, and various supporting classes."""

import os.path
from enum import Enum
from pathlib import Path
from typing import Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from attr import Factory, attrib, attrs
from pyglet.window import key
from shortuuid import uuid

from .config import Config, ConfigValue
from .editor import Editor
from .hat_directions import DOWN, UP
from .level import Level
from .menus.menu import Menu
from .mixins import DumpLoadMixin
from .types import ActionFunctionType, OptionalGenerator

T = TypeVar("T")
WaitType = Optional[Union[float, Tuple[float, float]]]


class CurrentPage(Enum):
    """The current page."""

    sections = 0
    finishers = 1


@attrs(auto_attribs=True)
class ConversationBase(DumpLoadMixin):
    """A base for conversations and finishers."""

    id: str
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
    response_ids: List[str] = Factory(list)
    finisher_ids: List[str] = Factory(list)


@attrs(auto_attribs=True)
class Finisher(ConversationBase):
    """Do something after a response has been selected."""


ItemType = Union[ConversationSection, Finisher]
CallDict = Dict[str, ConversationSection]
CallList = List[ConversationSection]
FinisherDict = Dict[str, Finisher]
FinisherList = List[Finisher]


@attrs(auto_attribs=True)
class ConversationTree(DumpLoadMixin):
    """A structure for holding conversation sections and finishers."""

    sections: CallDict = Factory(dict)
    finishers: FinisherDict = Factory(dict)
    initial_section_id: Optional[str] = None


class CallResponseSettings(Config):
    """Configuration for a conversation session."""

    __section_name__ = "Settings"
    output_audio: ConfigValue[bool] = ConfigValue(True, name="Play audio")
    output_braille: ConfigValue[bool] = ConfigValue(
        True, name="Output in braille"
    )
    output_speech: ConfigValue[bool] = ConfigValue(True, name="Speak text")


@attrs(auto_attribs=True)
class EditorPage(Generic[T]):
    """A page in the editor."""

    name: str
    items: Dict[str, T]
    bookmarks: Dict[int, str] = Factory(dict)
    position: int = Factory(int)


@attrs(auto_attribs=True)
class ConversationEditor(Level):
    """Used for editing a conversation tree."""

    tree: ConversationTree = Factory(ConversationTree)
    filename: Path = Factory(lambda: Path("tree.crt"))
    page: CurrentPage = Factory(lambda: CurrentPage.sections)
    pages: Dict[CurrentPage, EditorPage] = attrib()

    @pages.default
    def get_pages(
        instance: "ConversationEditor",
    ) -> Dict[CurrentPage, EditorPage]:
        """Return a list of suitable pages."""
        return {
            CurrentPage.sections: EditorPage(
                "Conversation Sections",
                instance.tree.sections,
            ),
            CurrentPage.finishers: EditorPage(
                "Finishers", instance.tree.finishers
            ),
        }

    def __attrs_post_init__(self) -> None:
        """Add actions."""
        self.action("Previous item", symbol=key.UP, hat_direction=UP)(
            self.previous_item
        )
        self.action("Next item", symbol=key.DOWN, hat_direction=DOWN)(
            self.next_item
        )
        self.action(
            "Conversation sections page", symbol=key._1, joystick_button=2
        )(self.sections_page)
        self.action("Finishers page", symbol=key._2, joystick_button=1)(
            self.finishers_page
        )
        self.action("Set item text", symbol=key.T)(self.set_text)
        self.action("Set item sound", symbol=key.S)(self.set_sound)
        self.action("New item", symbol=key.N)(self.new)
        self.action("Pick valid responses", symbol=key.R, joystick_button=3)(
            self.response_menu
        )
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
    def current_page(self) -> EditorPage:
        """Return the current page."""
        return self.pages[self.page]

    @property
    def current_position(self) -> int:
        """Return the current position in the current page."""
        return self.current_page.position

    @current_position.setter
    def current_position(self, pos: int) -> None:
        """Set the current position."""
        self.current_page.position = pos

    @property
    def items_dict(self) -> Union[CallDict, FinisherDict]:
        """Return the dictionary that the current page refers to."""
        return self.current_page.items

    @property
    def items(self) -> Union[CallList, FinisherList]:
        """Return a list of items on the current page."""
        return list(self.current_page.items.values())

    @property
    def current_item(self) -> ItemType:
        """Get the currently focused entry."""
        return self.items[self.current_position]

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
        if self.current_position >= len(self.items):
            self.current_position = 0
        elif self.current_position < 0:
            self.current_position += len(self.items)
        self.output_item()

    def previous_item(self) -> None:
        """Move up in the current list."""
        self.switch_item(-1)

    def next_item(self) -> None:
        """Move down in the items list."""
        self.switch_item(1)

    def set_page(self, page: CurrentPage) -> None:
        """Switch pages."""
        self.page = page
        self.game.output(self.current_page.name)

    def sections_page(self) -> None:
        """Go to the previous page."""
        self.set_page(CurrentPage.sections)

    def finishers_page(self) -> None:
        """Go to the next page."""
        self.set_page(CurrentPage.finishers)

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

    def new(self) -> None:
        """Create a new entry."""
        cls: Type
        if self.page is CurrentPage.sections:
            cls = ConversationSection
        else:
            cls = Finisher
        item: ItemType = cls(uuid(), text=f"Untitled {cls.__name__}")
        self.items_dict[item.id] = item  # type:ignore[assignment]
        self.current_position = 0
        self.previous_item()

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
