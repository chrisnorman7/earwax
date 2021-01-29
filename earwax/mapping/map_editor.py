"""Provides the MapEditor class."""

from enum import Enum
from keyword import iskeyword
from pathlib import Path
from typing import Dict, Generator, List, Optional

from attr import Factory, attrib, attrs
from shortuuid import uuid

from ..editor import Editor
from ..game import Game
from ..hat_directions import DOWN, LEFT, RIGHT, UP
from ..mixins import DumpLoadMixin
from ..point import Point
from ..pyglet import key
from .box import Box, BoxBounds, BoxTypes
from .box_level import BoxLevel

NoneGenerator = Generator[None, None, None]


class AnchorPoints(Enum):
    """The corners of a box points can be anchored to."""

    bottom_back_left = 0
    top_front_right = 1
    bottom_front_left = 2
    bottom_front_right = 3
    bottom_back_right = 4
    top_back_left = 5
    top_front_left = 6
    top_back_right = 7


@attrs(auto_attribs=True)
class BoxPoint(DumpLoadMixin):
    """Anchor a point to another box."""

    box_id: Optional[str] = None
    corner: Optional[AnchorPoints] = None
    x: int = 0
    y: int = 0
    z: int = 0


@attrs(auto_attribs=True)
class BoxTemplate(DumpLoadMixin):
    """A template for creating a box.

    Instances of this class will be dumped to the map file.
    """

    start: BoxPoint = Factory(BoxPoint)
    end: BoxPoint = Factory(BoxPoint)
    name: str = 'Untitled Box'
    surface_sound: Optional[str] = None
    wall_sound: Optional[str] = None

    type: BoxTypes = Factory(lambda: BoxTypes.empty)

    id: str = Factory(uuid)

    label: str = attrib()

    @label.default
    def get_default_label(instance: 'BoxTemplate') -> str:
        """Get a unique ID."""
        return f'box_{instance.id}'


@attrs(auto_attribs=True)
class LevelMap(DumpLoadMixin):
    """A representation of a :class:`earwax.BoxLevel` instance."""

    box_templates: List[BoxTemplate] = Factory(list)
    coordinates: BoxPoint = Factory(lambda: BoxPoint())
    bearing: int = 0
    name: str = 'Untitled Map'
    notes: str = Factory(str)


@attrs(auto_attribs=True)
class MapEditorContext:
    """A context to hold map information.

    This class acts as an interface between a
    :class:`~earwax.mapping.map_editor.LevelMap` instance, and a
    :class:`~earwax.MapEditor` instance.
    """

    level: 'MapEditor'

    level_map: LevelMap = Factory(LevelMap)
    template_ids: Dict[str, BoxTemplate] = Factory(dict)
    template_labels: Dict[str, BoxTemplate] = Factory(dict)
    box_ids: Dict[str, Box[str]] = Factory(dict)

    def to_point(self, data: BoxPoint) -> Point:
        """Return a point from the given data.

        :param data: The ``BoxPoint`` to load the point from.
        """
        p: Point = Point(data.x, data.y, data.z)
        if data.box_id is not None and data.corner is not None:
            box: Box = self.box_ids[data.box_id]
            bounds: BoxBounds = box.bounds
            adjustment: Point = getattr(bounds, data.corner.name)
            p += adjustment
        return p

    def to_box(self, game: Game, template: BoxTemplate) -> Box[str]:
        """Return a box from a template.

        :param template: The template to convert.
        """
        return Box(
            game,
            self.to_point(template.start), self.to_point(template.end),
            surface_sound=Path(template.surface_sound)
            if template.surface_sound is not None else None,
            wall_sound=Path(template.wall_sound)
            if template.wall_sound is not None else None,
            name=template.name, data=template.id
        )

    def add_template(self, template: BoxTemplate) -> None:
        """Add a template to this context.

        This method will add the given template to its
        :attr:`~earwax.mapping.map_editor.MapEditorContext.box_template_ids`
        dictionary.

        :param template: The template to add.
        """
        self.level_map.box_templates.append(template)
        self.template_ids[template.id] = template
        self.template_labels[template.label] = template
        box: Box[str] = self.to_box(self.level.game, template)
        self.level.add_box(box)
        self.box_ids[template.id] = box


@attrs(auto_attribs=True)
class MapEditor(BoxLevel):
    """A level which can be used for editing maps.

    When this level talks about a map, it talks about a
    :class:`earwax.mapping.map_editor.LevelMap` instance.
    """

    filename: str = 'map.yaml'

    context: MapEditorContext = attrib(repr=False)

    @context.default
    def get_default_context(instance: 'MapEditor') -> MapEditorContext:
        """Return a suitable context."""
        return MapEditorContext(instance)

    def __attrs_post_init__(self) -> None:
        """Add the initial box if there is none, and add extra actions."""
        if not self.boxes:
            self.context.add_template(
                BoxTemplate(
                    BoxPoint(), BoxPoint(), name='First Box', id='first_box'
                )
            )
        self.action(
            'Move forwards', symbol=key.W, hat_direction=UP
        )(self.move())
        self.action(
            'Turn around', symbol=key.S, hat_direction=DOWN
        )(self.turn(180))
        self.action(
            'Turn left', symbol=key.A, hat_direction=LEFT
        )(self.turn(-45))
        self.action(
            'Turn right', symbol=key.D, hat_direction=RIGHT
        )(self.turn(45))
        self.action(
            'Show coordinates', symbol=key.C, joystick_button=0
        )(self.show_coordinates())
        self.action(
            'Show facing direction', symbol=key.F, joystick_button=3
        )(self.show_facing())
        self.action(
            'Describe current box', symbol=key.X, joystick_button=2
        )(self.describe_current_box)
        self.action(
            'Show nearest door', symbol=key.Z, joystick_button=1
        )
        self.action(
            'Rename current box', symbol=key.R
        )(self.rename_box)
        self.action(
            'Label current box', symbol=key.L
        )(self.label_box)
        return super().__attrs_post_init__()

    def on_move_fail(
        self, distance: float, vertical: Optional[float], bearing: int,
        coordinates: Point
    ) -> None:
        """Tell the user their move failed."""
        self.game.output('There is no box in that direction.')
        return super().on_move_fail(distance, vertical, bearing, coordinates)

    def rename_box(self) -> NoneGenerator:
        """Rename the current box."""
        b: Optional[Box[str]] = self.get_current_box()
        if b is None:
            return self.game.output('First move to a box.')
        assert b.data is not None
        t: BoxTemplate = self.context.template_ids[b.data]
        e: Editor = Editor(self.game, text=t.name)

        @e.event
        def on_submit(text: str) -> None:
            """Set the new name."""
            if text:
                assert b is not None
                b.name = text
                t.name = text
                self.game.output('Box renamed.')
                self.game.pop_level()
            else:
                self.game.cancel()

        self.game.output(f'Enter a new name for the current box: {t.name}')
        yield
        self.game.push_level(e)

    def label_box(self) -> NoneGenerator:
        """Rename the current box."""
        b: Optional[Box[str]] = self.get_current_box()
        if b is None:
            return self.game.output('First move to a box.')
        assert b.data is not None
        t: BoxTemplate = self.context.template_ids[b.data]
        e: Editor = Editor(self.game, text=t.label)

        @e.event
        def on_submit(text: str) -> None:
            """Set the new name."""
            if not text or not text.isidentifier() or iskeyword(text):
                msg: str
                if not text.isidentifier():
                    msg = f'Invalid identifier: {text}.'
                elif iskeyword(text):
                    msg = f'Reserved keyword: {text}.'
                else:
                    msg = 'Cancelled.'
                self.game.cancel(message=msg)
            else:
                t.label = text
                self.game.output('Label set.')
                self.game.pop_level()

        self.game.output(f'Enter a new label for the current box: {t.label}')
        yield
        self.game.push_level(e)
