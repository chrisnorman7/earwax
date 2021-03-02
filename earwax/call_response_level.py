"""Provides the CallResponseLevel class, and various supporting classes."""

from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from attr import Factory, attrib, attrs
from pyglet.window import key
from shortuuid import uuid

from .config import Config, ConfigValue
from .editor import Editor
from .hat_directions import DOWN, LEFT, RIGHT, UP
from .level import Level
from .mixins import DumpLoadMixin
from .types import NoneGenerator

BookmarkDict = Dict[int, Optional[str]]


@attrs(auto_attribs=True)
class CallResponseBase(DumpLoadMixin):
    """A base for calls and responses."""

    id: str
    text: Optional[str] = None
    sound: Optional[str] = None
    sound_gain: float = 0.75
    sound_pan: float = 0.0

    def __attrs_post_init__(self) -> None:
        """Ensure we have either text or a sound."""
        if self.text is None and self.sound is None:
            raise RuntimeError(
                "Neither text or sound was provided. This object would be "
                "completely silent."
            )


@attrs(auto_attribs=True)
class Call(CallResponseBase):
    """A call from an NPC."""

    before_wait: Optional[float] = None
    after_wait: Optional[float] = None
    responses: List[str] = Factory(list)


@attrs(auto_attribs=True)
class Finisher(CallResponseBase):
    """Do something after a :class:`~earwax.Response` has been triggered."""


@attrs(auto_attribs=True)
class Response(CallResponseBase):
    """A response to a call."""

    call_id: Optional[str] = None
    finishers: List[str] = Factory(list)


EntryType = Union[Call, Response, Finisher]
CallDict = Dict[str, Call]
ResponseDict = Dict[str, Response]
FinisherDict = Dict[str, Finisher]


@attrs(auto_attribs=True)
class CallResponseTree(DumpLoadMixin):
    """A structure for holding calls and responses."""

    calls: Dict[str, Call] = Factory(dict)
    responses: Dict[str, Response] = Factory(dict)
    finishers: Dict[str, Finisher] = Factory(dict)
    initial_call_id: Optional[str] = None


class CallResponseSettings(Config):
    """Configuration for a call and response session."""

    __section_name__ = "Settings"
    output_audio: ConfigValue[bool] = ConfigValue(True, name="Play audio")
    output_braille: ConfigValue[bool] = ConfigValue(
        True, name="Output in braille"
    )
    output_speech: ConfigValue[bool] = ConfigValue(True, name="Speak text")


@attrs(auto_attribs=True)
class CallResponseEditor(Level):
    """Used for editing a call response tree."""

    tree: CallResponseTree = Factory(CallResponseTree)
    filename: Path = Factory(lambda: Path("tree.crt"))
    CALLS: int = 0
    RESPONSES: int = 1
    FINISHERS: int = 2
    page: int = CALLS
    page_names: Dict[int, str] = {
        CALLS: "Calls",
        RESPONSES: "Responses",
        FINISHERS: "Finishers",
    }
    page_classes: Dict[int, Type] = {
        CALLS: Call,
        RESPONSES: Response,
        FINISHERS: Finisher,
    }
    position: Dict[int, int] = attrib()

    @position.default
    def default_position(instance: "CallResponseEditor") -> Dict[int, int]:
        """Get the default position dictionary."""
        return {
            instance.CALLS: 0,
            instance.RESPONSES: 0,
            instance.FINISHERS: 0,
        }

    bookmarks: Dict[int, BookmarkDict] = attrib()

    @bookmarks.default
    def default_bookmarks(
        instance: "CallResponseEditor",
    ) -> Dict[int, BookmarkDict]:
        """Get the default bookmarks dictionary."""
        return {
            instance.CALLS: {},
            instance.RESPONSES: {},
            instance.FINISHERS: {},
        }

    def __attrs_post_init__(self) -> None:
        """Add actions."""
        self.action("Previous item", symbol=key.UP, hat_direction=UP)(
            self.previous_item
        )
        self.action("Next item", symbol=key.DOWN, hat_direction=DOWN)(
            self.next_item
        )
        self.action("Previous page", symbol=key.LEFT, hat_direction=LEFT)(
            self.previous_page
        )
        self.action("Next page", symbol=key.RIGHT, hat_direction=RIGHT)(
            self.next_page
        )
        self.action("Set item text", symbol=key.T)(self.set_text)
        self.action(
            "Save", symbol=key.S, modifiers=key.MOD_CTRL, joystick_button=0
        )(self.save)
        self.action("New item", symbol=key.N, joystick_button=1)(self.new)
        self.action("Help", symbol=key.SLASH, modifiers=key.MOD_SHIFT)(
            self.game.push_action_menu
        )
        return super().__attrs_post_init__()

    @property
    def current_position(self) -> int:
        """Return the current position in the current page."""
        return self.position[self.page]

    @current_position.setter
    def current_position(self, pos: int) -> None:
        """Set the current position."""
        self.position[self.page] = pos

    @property
    def items_dict(self) -> Union[CallDict, ResponseDict, FinisherDict]:
        """Return the dictionary that the current page refers to."""
        if self.page == self.CALLS:
            return self.tree.calls
        elif self.page == self.RESPONSES:
            return self.tree.responses
        else:
            return self.tree.finishers

    @property
    def items(self) -> List[EntryType]:
        """Return a list of items on the current page."""
        return list(self.items_dict.values())

    @property
    def current_item(self) -> EntryType:
        """Get the currently focused entry."""
        return self.items[self.current_position]

    def switch_item(self, direction: int) -> None:
        """Switch items."""
        if not self.items:
            return self.game.output("There are no items to show.")
        self.current_position += direction
        if self.current_position >= len(self.items):
            self.current_position = 0
        elif self.current_position < 0:
            self.current_position += len(self.items)
        item: EntryType = self.current_item
        if item.text is not None:
            self.game.output(item.text)
        if item.sound is not None:
            p: Path = Path(item.sound)
            self.game.interface_sound_manager.play_path(
                p, gain=item.sound_gain, position=item.sound_pan
            )

    def previous_item(self) -> None:
        """Move up in the current list."""
        self.switch_item(-1)

    def next_item(self) -> None:
        """Move down in the items list."""
        self.switch_item(1)

    def switch_page(self, direction: int) -> None:
        """Switch pages."""
        self.page += direction
        if self.page < self.CALLS:
            self.page = self.FINISHERS
        if self.page > self.FINISHERS:
            self.page = self.CALLS
        self.game.output(self.page_names[self.page])

    def previous_page(self) -> None:
        """Go to the previous page."""
        self.switch_page(-1)

    def next_page(self) -> None:
        """Go to the next page."""
        self.switch_page(1)

    def set_text(self) -> NoneGenerator:
        """Set the text for the currently focused item."""
        if not self.items:
            return self.game.output(
                "There is nothing for you to set the text on."
            )
        item: EntryType = self.current_item
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

    def save(self) -> None:
        """Save this tree."""
        self.tree.save(self.filename)
        self.game.output("Saved.")

    def new(self) -> None:
        """Create a new entry."""
        cls = self.page_classes[self.page]
        item: EntryType = cls(uuid(), text=f"Untitled {cls.__name__}")
        self.items_dict[item.id] = item  # type:ignore[assignment]
        self.current_position = 0
        self.previous_item()
