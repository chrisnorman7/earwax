"""Test the MapEditor class."""

from typing import Optional

from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises

from earwax import BoxTypes, Editor, Game, MapEditor, Point
from earwax.mapping.map_editor import (AnchorPoints, BoxPoint, BoxTemplate,
                                       InvalidLabel, LevelMap, MapEditorBox,
                                       MapEditorContext, valid_label)


def test_valid_label() -> None:
    """Test the valid_label method."""
    with raises(InvalidLabel) as exc:
        valid_label("Hello world")
    assert exc.value.args == ("Invalid identifier: Hello world.",)
    with raises(InvalidLabel) as exc:
        valid_label(":")
    assert exc.value.args == ("Invalid identifier: :.",)
    with raises(InvalidLabel) as exc:
        valid_label("try")
    assert exc.value.args == ("Reserved keyword: try.",)
    with raises(InvalidLabel) as exc:
        valid_label("except")
    assert exc.value.args == ("Reserved keyword: except.",)
    with raises(InvalidLabel) as exc:
        valid_label("")
    assert exc.value.args == ("Cancelled.",)


def test_point_anchor_init() -> None:
    """Test initialisation."""
    a: BoxPoint = BoxPoint()
    assert a.box_id is None
    assert a.corner is None
    assert a.x == 0
    assert a.y == 0
    assert a.z == 0


def test_box_template_init() -> None:
    """Test initialisation."""
    t: BoxTemplate = BoxTemplate()
    assert isinstance(t.start, BoxPoint)
    assert t.start == BoxPoint()
    assert isinstance(t.end, BoxPoint)
    assert t.end == BoxPoint()
    assert t.name == "Untitled Box"
    assert t.surface_sound is None
    assert t.wall_sound is None
    assert t.type is BoxTypes.empty
    assert isinstance(t.label, str)
    assert t.label == f"box_{t.id}"


def test_level_map_init() -> None:
    """Test initialisation."""
    level_map: LevelMap = LevelMap()
    assert level_map.box_templates == []
    assert level_map.coordinates == BoxPoint()
    assert level_map.bearing == 0
    assert level_map.name == "Untitled Map"


def test_map_editor_init(game: Game, map_editor: MapEditor) -> None:
    """Test map editor initialisation."""
    assert isinstance(map_editor, MapEditor)
    assert map_editor.game is game
    assert len(map_editor.boxes) == 1
    b: MapEditorBox = map_editor.boxes[0]
    assert isinstance(b, MapEditorBox)
    box_id: str = b.id
    assert isinstance(box_id, str)
    assert box_id != ""
    context: MapEditorContext = map_editor.context
    assert isinstance(context, MapEditorContext)
    assert box_id in context.template_ids
    assert context.box_ids[box_id] is b
    level_map: LevelMap = context.level_map
    assert isinstance(level_map, LevelMap)
    assert len(level_map.box_templates) == 1
    t: BoxTemplate = level_map.box_templates[0]
    assert isinstance(t, BoxTemplate)
    assert t.name == b.name
    assert t.id == box_id
    assert context.template_ids[box_id] is t


def test_rename_box(
    game: Game,
    map_editor: MapEditor,
    map_editor_context: MapEditorContext,
    window: Window,
) -> None:
    """Make sure we can rename the current box."""
    new_name: str = "Testing"
    box: Optional[MapEditorBox] = map_editor.get_current_box()
    assert isinstance(box, MapEditorBox)
    assert box.id is not None
    assert map_editor_context.box_ids[box.id] is box
    template: BoxTemplate = map_editor_context.template_ids[box.id]

    @map_editor.event
    def on_push() -> None:
        assert isinstance(box, MapEditorBox)
        assert isinstance(template, BoxTemplate)
        map_editor.set_coordinates(Point(25, 25, 25))
        game.press_key(key.R, 0)
        assert game.level is map_editor
        map_editor.set_coordinates(Point(0, 0, 0))
        game.press_key(key.R, 0)
        assert isinstance(game.level, Editor)
        game.level.text = ""
        game.level.submit()
        assert box.name == "First Box"
        assert template.name == "First Box"
        game.press_key(key.R, 0)
        assert isinstance(game.level, Editor)
        game.level.dismiss()
        assert box.name == "First Box"
        assert template.name == "First Box"
        game.press_key(key.R, 0)
        assert isinstance(game.level, Editor)
        game.level.text = new_name
        game.level.submit()
        assert game.level is map_editor
        assert box.name == template.name
        assert template.name == new_name
        schedule_once(lambda dt: game.stop(), 0.1)

    game.run(window, initial_level=map_editor)


def test_label_box(
    game: Game,
    map_editor: MapEditor,
    map_editor_context: MapEditorContext,
    window: Window,
) -> None:
    """Make sure we can relabel the current box."""
    box: Optional[MapEditorBox] = map_editor.get_current_box()
    assert isinstance(box, MapEditorBox)
    assert map_editor_context.box_ids[box.id] is box
    template: BoxTemplate = map_editor_context.template_ids[box.id]
    old_label: str = template.label

    @map_editor.event
    def on_push() -> None:
        assert isinstance(template, BoxTemplate)
        map_editor.set_coordinates(Point(5, 5, 5))
        map_editor.label_box()
        assert game.level is map_editor
        map_editor.set_coordinates(Point(0, 0, 0))
        list(map_editor.label_box())
        assert isinstance(game.level, Editor)
        game.level.text = ""
        game.level.submit()
        assert template.label == old_label
        list(map_editor.label_box())
        assert isinstance(game.level, Editor)
        game.level.dismiss()
        assert template.label == old_label
        list(map_editor.label_box())
        assert isinstance(game.level, Editor)
        game.level.text = "try"
        game.level.submit()
        assert game.level is map_editor
        assert template.label == old_label
        list(map_editor.label_box())
        assert isinstance(game.level, Editor)
        game.level.text = "invalid label"
        game.level.submit()
        assert game.level is map_editor
        assert template.label == old_label
        list(map_editor.label_box())
        assert isinstance(game.level, Editor)
        game.level.text = "valid_label"
        game.level.submit()
        assert game.level is map_editor
        assert template.label == "valid_label"
        schedule_once(lambda dt: game.stop(), 0.1)

    game.run(window, initial_level=map_editor)


def test_to_box(game: Game, map_editor_context: MapEditorContext) -> None:
    """Test the to_box method."""
    t1: BoxTemplate = BoxTemplate(
        start=BoxPoint(x=1, y=2, z=3), end=BoxPoint(x=4, y=5, z=6)
    )
    b1: MapEditorBox = map_editor_context.to_box(t1)
    assert isinstance(b1, MapEditorBox)
    assert b1.id == t1.id
    assert b1.name == t1.name
    assert b1.start == Point(1, 2, 3)
    assert b1.end == Point(4, 5, 6)
    map_editor_context.add_template(t1, box=b1)
    t2: BoxTemplate = BoxTemplate(
        start=BoxPoint(
            box_id=t1.id, corner=AnchorPoints.bottom_back_left, x=3, y=2, z=1
        ),
        end=BoxPoint(
            box_id=t1.id, corner=AnchorPoints.top_front_right, x=4, y=3, z=2
        ),
    )
    b2: MapEditorBox = map_editor_context.to_box(t2)
    assert isinstance(b2, MapEditorBox)
    assert b2.start == Point(4, 4, 4)
    assert b2.end == Point(8, 8, 8)
    map_editor_context.add_template(t2, box=b2)
    t3: BoxTemplate = BoxTemplate(
        start=BoxPoint(
            box_id=t2.id, corner=AnchorPoints.bottom_back_right, x=1
        ),
        end=BoxPoint(box_id=t2.id, corner=AnchorPoints.top_front_right, x=10),
    )
    b3: MapEditorBox = map_editor_context.to_box(t3)
    assert isinstance(b3, MapEditorBox)
    assert b3.start == Point(9, 4, 4)
    assert b3.end == Point(18, 8, 8)


def test_id_box(
    game: Game,
    map_editor: MapEditor,
    map_editor_context: MapEditorContext,
    window: Window,
) -> None:
    """Make sure we can change the ID of the current box.

    Any points that rely on a box should have their ``box_id`` attributes
    changed also.
    """
    box: Optional[MapEditorBox] = map_editor.get_current_box()
    assert isinstance(box, MapEditorBox)
    assert map_editor_context.box_ids[box.id] is box
    template: BoxTemplate = map_editor_context.template_ids[box.id]
    old_id: str = template.id
    t1: BoxTemplate = BoxTemplate(
        start=BoxPoint(
            box_id=template.id, corner=AnchorPoints.bottom_back_left, x=3, y=3
        ),
        end=BoxPoint(
            box_id=template.id,
            corner=AnchorPoints.top_front_right,
            x=5,
            y=5,
            z=5,
        ),
    )
    map_editor_context.add_template(t1)
    t2: BoxTemplate = BoxTemplate(
        start=BoxPoint(
            box_id=template.id, corner=AnchorPoints.bottom_back_right
        ),
        end=BoxPoint(box_id=t1.id, corner=AnchorPoints.top_front_right, x=5),
    )
    map_editor_context.add_template(t2)
    assert len(map_editor.boxes) == 3

    @map_editor.event
    def on_push() -> None:
        assert isinstance(template, BoxTemplate)
        map_editor.set_coordinates(Point(-5, -5, -5))
        list(map_editor.id_box())
        assert game.level is map_editor
        map_editor.set_coordinates(Point(0, 0, 0))
        list(map_editor.id_box())
        assert isinstance(game.level, Editor)
        game.level.text = ""
        game.level.submit()
        assert template.id == old_id
        list(map_editor.id_box())
        assert isinstance(game.level, Editor)
        game.level.dismiss()
        assert template.id == old_id
        list(map_editor.id_box())
        assert isinstance(game.level, Editor)
        game.level.text = "try"
        game.level.submit()
        assert game.level is map_editor
        assert template.id == old_id
        list(map_editor.id_box())
        assert isinstance(game.level, Editor)
        game.level.text = "invalid ID"
        game.level.submit()
        assert game.level is map_editor
        assert template.id == old_id
        list(map_editor.id_box())
        assert isinstance(game.level, Editor)
        game.level.text = "valid_id"
        game.level.submit()
        assert game.level is map_editor
        assert template.id == "valid_id"
        assert t1.start.box_id == template.id
        assert t2.start.box_id == template.id
        schedule_once(lambda dt: game.stop(), 0.1)

    game.run(window, initial_level=map_editor)
