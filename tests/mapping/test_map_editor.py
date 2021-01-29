"""Test the MapEditor class."""

from typing import Optional

from pyglet.clock import schedule_once
from pyglet.window import Window, key

from earwax import Box, BoxTypes, Editor, Game, MapEditor, Point
from earwax.mapping.map_editor import (BoxPoint, BoxTemplate, LevelMap,
                                       MapEditorContext)


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
    assert t.name == 'Untitled Box'
    assert t.surface_sound is None
    assert t.wall_sound is None
    assert t.type is BoxTypes.empty
    assert isinstance(t.label, str)
    assert t.label == f'box_{t.id}'


def test_level_map_init() -> None:
    """Test initialisation."""
    level_map: LevelMap = LevelMap()
    assert level_map.box_templates == []
    assert level_map.coordinates == BoxPoint()
    assert level_map.bearing == 0
    assert level_map.name == 'Untitled Map'


def test_map_editor_init(game: Game, map_editor: MapEditor) -> None:
    """Test map editor initialisation."""
    assert isinstance(map_editor, MapEditor)
    assert map_editor.game is game
    assert len(map_editor.boxes) == 1
    b: Box[str] = map_editor.boxes[0]
    assert isinstance(b, Box)
    assert isinstance(b.data, str)
    assert b.data != ''
    box_id: str = b.data
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
    game: Game, map_editor: MapEditor, map_editor_context: MapEditorContext,
    window: Window
) -> None:
    """Make sure we can rename the current box."""
    new_name: str = 'Testing'
    box: Optional[Box[str]] = map_editor.get_current_box()
    assert isinstance(box, Box)
    assert box.data is not None
    assert map_editor_context.box_ids[box.data] is box
    template: BoxTemplate = map_editor_context.template_ids[box.data]

    @map_editor.event
    def on_push() -> None:
        assert isinstance(box, Box)
        assert isinstance(template, BoxTemplate)
        map_editor.set_coordinates(Point(5, 5, 5))
        game.press_key(key.R, 0)
        assert game.level is map_editor
        map_editor.set_coordinates(Point(0, 0, 0))
        game.press_key(key.R, 0)
        assert isinstance(game.level, Editor)
        game.level.text = ''
        game.level.submit()
        assert box.name == 'First Box'
        assert template.name == 'First Box'
        game.press_key(key.R, 0)
        assert isinstance(game.level, Editor)
        game.level.dismiss()
        assert box.name == 'First Box'
        assert template.name == 'First Box'
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
    game: Game, map_editor: MapEditor, map_editor_context: MapEditorContext,
    window: Window
) -> None:
    """Make sure we can rename the current box."""
    box: Optional[Box[str]] = map_editor.get_current_box()
    assert isinstance(box, Box)
    assert box.data is not None
    assert map_editor_context.box_ids[box.data] is box
    template: BoxTemplate = map_editor_context.template_ids[box.data]
    old_label: str = template.label

    @map_editor.event
    def on_push() -> None:
        assert isinstance(template, BoxTemplate)
        map_editor.set_coordinates(Point(5, 5, 5))
        game.press_key(key.L, 0)
        assert game.level is map_editor
        map_editor.set_coordinates(Point(0, 0, 0))
        game.press_key(key.L, 0)
        assert isinstance(game.level, Editor)
        game.level.text = ''
        game.level.submit()
        assert template.label == old_label
        game.press_key(key.L, 0)
        assert isinstance(game.level, Editor)
        game.level.dismiss()
        assert template.label == old_label
        game.press_key(key.L, 0)
        assert isinstance(game.level, Editor)
        game.level.text = 'try'
        game.level.submit()
        assert game.level is map_editor
        assert template.label == old_label
        game.press_key(key.L, 0)
        assert isinstance(game.level, Editor)
        game.level.text = 'invalid label'
        game.level.submit()
        assert game.level is map_editor
        assert template.label == old_label
        game.press_key(key.L, 0)
        assert isinstance(game.level, Editor)
        game.level.text = 'valid_label'
        game.level.submit()
        assert game.level is map_editor
        assert template.label == 'valid_label'
        schedule_once(lambda dt: game.stop(), 0.1)

    game.run(window, initial_level=map_editor)
