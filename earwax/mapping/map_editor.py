"""Provides the MapEditor class."""

from enum import Enum
from keyword import iskeyword
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional

from attr import Factory, attrib, attrs
from pyglet.window import key
from shortuuid import uuid

from ..editor import Editor
from ..menus import Menu
from ..mixins import DumpLoadMixin
from ..point import Point
from .box import Box, BoxBounds, BoxTypes
from .box_level import BoxLevel

NoneGenerator = Generator[None, None, None]


class InvalidLabel(Exception):
    """An invalid ID or label was given."""


def valid_label(text: str) -> None:
    """Ensure the given label or ID is valid.

    If it could not be used as a Python identifier for any reason,
    :class:`earwax.mapping.map_editor.InvalidLabel` will be raised.

    :param text: The text to check.
    """
    if not text or not text.isidentifier() or iskeyword(text):
        msg: str
        if not text:
            msg = "Cancelled."
        elif not text.isidentifier():
            msg = f"Invalid identifier: {text}."
        elif iskeyword(text):
            msg = f"Reserved keyword: {text}."
        else:
            msg = "Unknown error."
        raise InvalidLabel(msg)


@attrs(auto_attribs=True)
class MapEditorBox(Box):
    """A box with an ID."""

    id: str = attrib()

    @id.default
    def get_default_id(instance: "MapEditorBox") -> str:
        """Raise an error if the id is not provided."""
        raise RuntimeError("You must provide an ID.")

    def __str__(self) -> str:
        """Return a string representation of this object."""
        return f"{self.name} (#{self.id})"


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
    name: str = "Untitled Box"
    surface_sound: Optional[str] = None
    wall_sound: Optional[str] = None

    type: BoxTypes = Factory(lambda: BoxTypes.empty)

    id: str = Factory(uuid)

    label: str = attrib()

    @label.default
    def get_default_label(instance: "BoxTemplate") -> str:
        """Get a unique ID."""
        return f"box_{instance.id}"


@attrs(auto_attribs=True)
class LevelMap(DumpLoadMixin):
    """A representation of a :class:`earwax.BoxLevel` instance."""

    box_templates: List[BoxTemplate] = Factory(list)
    coordinates: BoxPoint = Factory(lambda: BoxPoint())
    bearing: int = 0
    name: str = "Untitled Map"
    notes: str = Factory(str)


@attrs(auto_attribs=True)
class MapEditorContext:
    """A context to hold map information.

    This class acts as an interface between a
    :class:`~earwax.mapping.map_editor.LevelMap` instance, and a
    :class:`~earwax.MapEditor` instance.
    """

    level: "MapEditor"
    level_map: LevelMap

    template_ids: Dict[str, BoxTemplate] = Factory(dict)
    box_ids: Dict[str, Box[str]] = Factory(dict)

    def __attrs_post_init__(self) -> None:
        """Add templates to ``self.template_ids``."""
        t: BoxTemplate
        for t in self.level_map.box_templates:
            self.template_ids[t.id] = t

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

    def to_box(self, template: BoxTemplate) -> MapEditorBox:
        """Return a box from a template.

        :param template: The template to convert.
        """
        return MapEditorBox(
            self.level.game,
            self.to_point(template.start),
            self.to_point(template.end),
            surface_sound=Path(template.surface_sound)
            if template.surface_sound is not None
            else None,
            wall_sound=Path(template.wall_sound)
            if template.wall_sound is not None
            else None,
            name=template.name,
            id=template.id,
        )

    def add_template(
        self, template: BoxTemplate, box: Optional[MapEditorBox] = None
    ) -> None:
        """Add a template to this context.

        This method will add the given template to its
        :attr:`~earwax.mapping.map_editor.MapEditorContext.box_template_ids`
        dictionary.

        :param template: The template to add.
        """
        self.level_map.box_templates.append(template)
        self.template_ids[template.id] = template
        if box is None:
            box = self.to_box(template)
        self.level.add_box(box)
        self.box_ids[template.id] = box

    def reload_template(self, template: BoxTemplate) -> None:
        """Reload the given template.

        This method recreates the box associated with the given template.

        :param template: The template to reload.
        """
        self.level_map.box_templates.remove(template)
        box: MapEditorBox = self.box_ids.pop(template.id)
        self.level.remove_box(box)
        self.add_template(template)
        if self.level.get_current_box() is None:
            # Better move the player.
            box = self.box_ids[template.id]
            self.level.set_coordinates(box.start)


@attrs(auto_attribs=True)
class MapEditor(BoxLevel):
    """A level which can be used for editing maps.

    When this level talks about a map, it talks about a
    :class:`earwax.mapping.map_editor.LevelMap` instance.
    """

    filename: Optional[Path] = None

    context: MapEditorContext = attrib(repr=False)

    @context.default
    def get_default_context(instance: "MapEditor") -> MapEditorContext:
        """Return a suitable context."""
        level_map: LevelMap
        if instance.filename is not None:
            level_map = LevelMap.from_filename(instance.filename)
        else:
            level_map = LevelMap()
        return MapEditorContext(instance, level_map)

    def __attrs_post_init__(self) -> None:
        """Add the initial box if there is none, and add extra actions."""
        t: BoxTemplate
        for t in self.context.level_map.box_templates:
            b: MapEditorBox = self.context.to_box(t)
            self.context.box_ids[t.id] = b
            self.add_box(b)
        if not self.boxes:
            self.context.add_template(
                BoxTemplate(
                    BoxPoint(),
                    BoxPoint(x=10, y=10, z=10),
                    name="First Box",
                    id="first_box",
                )
            )
        self.add_default_actions()
        self.action("New box", symbol=key.N)(self.create_box)
        self.action("Rename current box", symbol=key.R)(self.rename_box)
        self.action("Box menu", symbol=key.B)(self.boxes_menu)
        self.action("Move box", symbol=key.P)(self.points_menu)
        self.action("Save map", symbol=key.S, modifiers=key.MOD_CTRL)(
            self.save
        )
        self.action("Help menu", symbol=key.SLASH, modifiers=key.MOD_SHIFT)(
            self.game.push_action_menu
        )
        return super().__attrs_post_init__()

    def complain_box(self) -> None:
        """Complain about there being no box."""
        return self.game.output("First move to a box.")

    def on_move_fail(
        self,
        distance: float,
        vertical: Optional[float],
        bearing: int,
        coordinates: Point,
    ) -> None:
        """Tell the user their move failed."""
        self.game.output("There is no box in that direction.")
        return super().on_move_fail(distance, vertical, bearing, coordinates)

    def save(self) -> None:
        """Save the map level."""
        if self.filename is None:
            return self.game.output("There is no filename to save to.")
        try:
            self.context.level_map.save(self.filename)
        except Exception as e:
            self.game.output(f"Failed to save the map: {e}.")
            raise
        else:
            self.game.output("Map saved.")

    def boxes_menu(self) -> None:
        """Push a menu to select a box to configure.

        If there is only 1 box, it will not be shown.
        """

        def inner(box: MapEditorBox) -> None:
            if isinstance(self.game.level, Menu):
                self.game.pop_level()
            return self.box_menu(box)

        boxes: List[MapEditorBox] = []
        b: MapEditorBox
        for b in self.boxes:
            if b.contains_point(self.coordinates):
                boxes.append(b)
        if not boxes:
            return self.complain_box()
        elif len(boxes) == 1:
            return inner(boxes[0])
        else:
            m: Menu = Menu(self.game, "Select Box")
            for b in boxes:
                m.add_item(lambda: inner(b), title=str(b))
            self.game.push_level(m)

    def box_menu(self, box: MapEditorBox) -> None:
        """Push a menu to configure the provided box."""
        t: BoxTemplate = self.context.template_ids[box.id]
        m: Menu = Menu(self.game, lambda: f"Configure {box}")
        m.add_item(self.rename_box, title=lambda: f"Rename ({box.name})")
        m.add_item(self.points_menu, title="Move")
        m.add_item(self.box_sounds, title="Sounds")
        m.add_item(self.label_box, title=lambda: f"Label ({t.label})")
        m.add_item(self.id_box, title=lambda: f"ID ({t.id})")
        self.game.push_level(m)

    def rename_box(self) -> NoneGenerator:
        """Rename the current box."""
        b: Optional[MapEditorBox] = self.get_current_box()
        if b is None:
            return self.complain_box()
        t: BoxTemplate = self.context.template_ids[b.id]
        e: Editor = Editor(self.game, text=t.name)

        @e.event
        def on_submit(text: str) -> None:
            """Set the new name."""
            if text:
                assert b is not None
                b.name = text
                t.name = text
                self.game.output("Box renamed.")
                self.game.pop_level()
            else:
                self.game.cancel()

        self.game.output(f"Enter a new name for the current box: {t.name}")
        yield
        self.game.push_level(e)

    def label_box(self) -> NoneGenerator:
        """Rename the current box."""
        b: Optional[MapEditorBox] = self.get_current_box()
        if b is None:
            return self.complain_box()
        t: BoxTemplate = self.context.template_ids[b.id]
        e: Editor = Editor(self.game, text=t.label)

        @e.event
        def on_submit(text: str) -> None:
            """Set the new name."""
            try:
                valid_label(text)
            except InvalidLabel as e:
                self.game.cancel(message=str(e))
            else:
                t.label = text
                self.game.output("Label set.")
                self.game.pop_level()

        self.game.output(f"Enter a new label for the current box: {t.label}")
        yield
        self.game.push_level(e)

    def id_box(self) -> NoneGenerator:
        """Change the ID for the current box."""
        b: Optional[MapEditorBox] = self.get_current_box()
        if b is None:
            return self.complain_box()
        t: BoxTemplate = self.context.template_ids[b.id]
        e: Editor = Editor(self.game, text=t.id)

        @e.event
        def on_submit(text: str) -> None:
            """Set the new name."""
            try:
                valid_label(text)
            except InvalidLabel as e:
                self.game.cancel(message=str(e))
            else:
                assert b is not None
                t.id = text
                template: BoxTemplate
                for template in self.context.level_map.box_templates:
                    if template.start.box_id == b.id:
                        template.start.box_id = text
                    if template.end.box_id == b.id:
                        template.end.box_id = text
                b.id = text
                self.game.output("Label set.")
                self.game.pop_level()

        self.game.output(f"Enter a new ID for the current box: {t.id}")
        yield
        self.game.push_level(e)

    def point_menu(
        self, template: BoxTemplate, point: BoxPoint
    ) -> Callable[[], None]:
        """Push a menu for configuring individual points."""

        def set_coordinates() -> NoneGenerator:
            e: Editor = Editor(
                self.game, text=f"{point.x}, {point.y}, {point.z}"
            )

            @e.event
            def on_submit(text: str) -> None:
                """Parse coordinates from the given text."""
                if not text:
                    return self.game.cancel()
                x: int
                y: int
                z: int
                try:
                    x, y, z = (int(i) for i in text.split(","))
                except ValueError:
                    return self.game.cancel(
                        message=f"Invalid coordinates: {text}."
                    )
                else:
                    point.x, point.y, point.z = x, y, z
                    self.context.reload_template(template)
                    self.game.cancel(message="Coordinates changed.")

            self.game.output("Enter new coordinates:")
            yield
            self.game.push_level(e)

        def set_anchor() -> None:
            m: Menu = Menu(self.game, "Anchor")
            current_box: Optional[MapEditorBox] = self.get_current_box()

            def _set_anchor(id: Optional[str] = None) -> Callable[[], None]:
                def inner() -> None:
                    point.box_id = id
                    self.context.reload_template(template)
                    self.game.cancel(
                        message=f'Anchor {"cleared" if id is None else "set"}.'
                    )

                return inner

            if point.box_id is not None:
                m.add_item(_set_anchor(None), title="Clear Anchor")
            box: MapEditorBox
            for box in reversed(self.boxes):
                if box is current_box or box.id == point.box_id:
                    continue
                m.add_item(_set_anchor(box.id), title=str(box))
            if m.items:
                self.game.push_level(m)
            else:
                self.game.output("There is nothing to anchor to.")

        def inner() -> None:
            m: Menu = Menu(self.game, "Configure Point")
            m.add_item(
                set_coordinates,
                title=lambda: (
                    f"Set coordinates ({point.x}, {point.y}, {point.z})"
                ),
            )

            def anchor_title() -> str:
                anchor: str = "Not Anchored"
                if point.box_id is not None and point.corner is not None:
                    anchor_box: MapEditorBox = self.context.box_ids[
                        point.box_id
                    ]
                    anchor = f"{anchor_box} "
                    anchor += f'[{point.corner.name.replace("_", " ")}]'
                return f"Anchor ({anchor})"

            m.add_item(set_anchor, title=anchor_title)
            self.game.push_level(m)

        return inner

    def points_menu(self) -> None:
        """Push a menu for moving the current box."""
        box: Optional[MapEditorBox] = self.get_current_box()
        if box is None:
            return self.complain_box()
        t: BoxTemplate = self.context.template_ids[box.id]
        m: Menu = Menu(self.game, f"Move {box}")
        m.add_item(
            self.point_menu(t, t.start),
            title=f"Start coordinates {box.start.coordinates}",
        )
        m.add_item(
            self.point_menu(t, t.end),
            title=f"End coordinates {box.end.coordinates}",
        )
        self.game.push_level(m)

    def box_sound(
        self, template: BoxTemplate, name: str
    ) -> Callable[[], NoneGenerator]:
        """Push an editor for setting the given sound.

        :param template: The template to modify.

        :param name: The name of the sound to modify.
        """

        def inner() -> NoneGenerator:
            e: Editor = Editor(self.game, text=getattr(template, name))

            @e.event
            def on_submit(text: str) -> None:
                box: MapEditorBox = self.context.box_ids[template.id]
                if not text:
                    setattr(box, name, None)
                    setattr(template, name, None)
                    return self.game.cancel(message="Sound cleared.")
                p: Path = Path(text)
                if not p.exists():
                    return self.game.cancel(
                        message=f"Path does not exist: {p}."
                    )
                setattr(template, name, text)
                setattr(box, name, p)
                self.game.cancel(message="Sound set.")

            self.game.output(f"Enter the path to a new sound: {e.text}")
            yield
            self.game.push_level(e)

        return inner

    def box_sounds(self) -> None:
        """Push a menu for configuring sounds."""
        box: Optional[MapEditorBox] = self.get_current_box()
        if box is None:
            return self.complain_box()
        t: BoxTemplate = self.context.template_ids[box.id]
        m: Menu = Menu(self.game, "Box Sounds")
        m.add_item(
            self.box_sound(t, "surface_sound"),
            title=lambda: f"Footstep sound ({t.surface_sound})",
        )
        m.add_item(
            self.box_sound(t, "wall_sound"),
            title=lambda: f"Wall sound ({t.wall_sound})",
        )
        self.game.push_level(m)

    def create_box(self) -> None:
        """Create a box, then call :meth:`~earwax.MapEditor.box_menu`."""
        x: int
        y: int
        z: int
        x, y, z = self.coordinates.floor().coordinates
        t: BoxTemplate = BoxTemplate(
            BoxPoint(x=x, y=y, z=z), BoxPoint(x=x, y=y, z=z)
        )
        self.context.add_template(t)
        self.box_menu(self.context.box_ids[t.id])
