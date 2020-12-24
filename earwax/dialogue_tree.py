"""Provides the DialogueLine and DialogueTree classes."""

from pathlib import Path
from typing import Callable, Generic, List, Optional, TypeVar

from attr import Factory, attrib, attrs

DialogueLineDataType = TypeVar('DialogueLineDataType')
DialogueTreeDataType = TypeVar('DialogueTreeDataType')


@attrs(auto_attribs=True)
class DialogueLine(Generic[DialogueLineDataType]):
    """A line of dialogue.

    :param ~earwax.DialogueLine.parent: The dialogue tree that this line of
        dialogue belongs to.

    :param ~earwax.DialogueLine.text: The text that is shown as part of this
        dialogue line.

    :param ~earwax.DialogueLine.sound: A portion of recorded dialogue.

    :param ~earwax.DialogueLine.can_show: A callable which will determine
        whether or not this line is visible in the conversation.

        If it returns ``True``, this line will be shown in the list.

    :param ~earwax.DialogueLine.on_activate: A callable which will be called
        when this line is selected from the list of lines.

        If it returns ``True``, the conversation can continue.

    :param ~earwax.DialogueLine.responses: A list of responses to this line.
    """

    parent: 'DialogueTree'

    text: Optional[str] = None
    sound: Optional[Path] = None
    can_show: Optional[Callable[[DialogueLineDataType], bool]] = None
    on_activate: Optional[Callable[[DialogueLineDataType], bool]] = None

    responses: List['DialogueLine'] = attrib(
        default=Factory(list), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """Check that we have text or a sound."""
        if self.text is None and self.sound is None:
            raise RuntimeError(
                'A dialogue line must have either text or a sound.'
            )
        self.parent.children.append(self)


@attrs(auto_attribs=True)
class DialogueTree(Generic[DialogueTreeDataType]):
    """A dialogue tree object.

    :ivar ~earwax.DialogueTree.children: The top-level dialogue lines for this
        instance.
    """

    children: List[DialogueLine] = attrib(
        default=Factory(list), init=False, repr=False
    )

    def get_children(self, data: DialogueTreeDataType) -> List[DialogueLine]:
        """Get a list of all the children who can be shown currently.

        This method returns a list of those children for whom
        ``child.can_show(data)`` is True.

        :param data: The data to pass to :meth:`~earwax.DialogueLine.can_show`.
        """
        child: DialogueLine[DialogueTreeDataType]
        return [
            child for child in self.children if child.can_show is not None and
            child.can_show(data)
        ]
