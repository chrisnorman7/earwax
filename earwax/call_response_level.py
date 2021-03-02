"""Provides the CallResponseLevel class, and various supporting classes."""

from typing import Dict, List, Optional

from attr import Factory, attrib, attrs

from .config import Config, ConfigValue
from .level import Level
from .mixins import DumpLoadMixin


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
    CALLS: int = 0
    RESPONSES: int = 1
    FINISHERS: int = 2
    page: int = CALLS
    position: Dict[int, int] = attrib()

    @position.default
    def default_position(instance: "CallResponseEditor") -> Dict[int, int]:
        """Get the default position dictionary."""
        return {
            instance.CALLS: 0,
            instance.RESPONSES: 0,
            instance.FINISHERS: 0,
        }

    def __attrs_post_init__(self) -> None:
        """Add actions."""
        return super().__attrs_post_init__()
