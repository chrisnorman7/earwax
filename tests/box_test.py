"""Test the Box class."""

from pathlib import Path
from typing import List, Optional

from pyglet.clock import schedule_interval
from pyglet.window import Window
from pytest import raises
from synthizer import (BufferGenerator, Context, Source3D, StreamingGenerator,
                       SynthizerError)

from earwax import (Box, BoxBounds, BoxLevel, BoxSound, BoxTypes, Door, Game,
                    NotADoor, OutOfBounds, Point, Portal, get_buffer)


def test_init(box: Box) -> None:
    """Test that boxes initialise properly."""
    assert isinstance(box, Box)
    assert box.start == Point(1, 2, 3)
    assert box.end == Point(4, 5, 6)
    assert box.surface_sound is None
    assert box.type is BoxTypes.empty
    b: Box = Box(box.start, box.end, parent=box)
    assert b.parent is box
    assert b in box.children


def test_add_child() -> None:
    """Test adding child boxes."""
    b: Box = Box(Point(0, 0, 0), Point(3, 3, 0))
    c: Box = Box(Point(1, 1, 0), Point(1, 1, 0), parent=b)
    assert c.parent is b
    assert b.children == [c]
    gc: Box = Box(Point(1, 1, 0), Point(1, 1, 0), parent=c)
    assert gc.parent is c
    assert c.children == [gc]
    broken: Box = Box(Point(-1, 0, 5), Point(-1, 0, -2))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
    broken = Box(Point(10, 10, 10), Point(10, 10, 10))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)


def test_contains_point() -> None:
    """Test Box.contains_point."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))
    assert b.contains_point(Point(0, 0, 0)) is True
    b.end = Point(5, 5, 0)
    assert b.contains_point(Point(3, 3, 0)) is True
    assert not b.contains_point(Point(55, 54, 52))
    assert not b.contains_point(Point(-3, -4, 0))
    assert not b.contains_point(Point(-1, 4, 5))
    assert not b.contains_point(Point(3, 7, 2))


def test_get_containing_child() -> None:
    """Test Box.get_containing_box."""
    parent: Box = Box(Point(0, 0, 0), Point(100, 100, 5))
    # Make a base for tracks to sit on.
    tracks: Box = Box(parent.start, parent.bounds.bottom_back_right + Point(0, 2, 0), parent=parent)
    assert parent.get_containing_box(Point(0, 0, 0)) is tracks
    assert parent.get_containing_box(Point(5, 5, 1)) is parent
    # Draw 2 parallel lines, like train tracks.
    b: BoxBounds = tracks.bounds
    southern_rail: Box = Box(b.bottom_back_left, b.bottom_back_right, parent=tracks)
    northern_rail = Box(b.bottom_front_left, b.bottom_front_right, parent=tracks)
    assert parent.get_containing_box(Point(5, 5, 0)) is parent
    assert parent.get_containing_box(Point(0, 0, 0)) is southern_rail
    assert parent.get_containing_box(Point(3, 2, 0)) is northern_rail
    assert parent.get_containing_box(Point(1, 1, 0)) is tracks
    assert parent.get_containing_box(Point(200, 201, 0)) is None


def test_fitted_box() -> None:
    """Test the FittedBox class."""
    southwest_box: Box = Box(Point(3, 5, 0), Point(8, 2, 0))
    northeast_box: Box = Box(Point(32, 33, 0), Point(80, 85, 5))
    middle_box: Box = Box(Point(14, 15, 2), Point(18, 22, 2))
    box: Box = Box.create_fitted([middle_box, northeast_box, southwest_box])
    assert box.start == southwest_box.start
    assert box.end == northeast_box.end


def test_create_row() -> None:
    """Test the create_row constructor."""
    start: Point = Point(1, 1, 0)
    boxes: List[Box] = Box.create_row(start, Point(5, 5, 4), 3, Point(1, 0, 0))
    assert len(boxes) == 3
    first: Box
    second: Box
    third: Box
    first, second, third = boxes
    assert first.start == start
    assert first.end == Point(5, 5, 3)
    assert first.name is None
    assert first.type is BoxTypes.empty
    assert second.start == Point(6, 1, 0)
    assert second.end == Point(10, 5, 3)
    assert third.start == Point(11, 1, 0)
    assert third.end == Point(15, 5, 3)
    first, second, third = Box.create_row(
        Point(0, 0, 0), Point(3, 4, 5), 3, Point(0, 3, 0)
    )
    assert first.start == Point(0, 0, 0)
    assert first.end == Point(2, 3, 4)
    assert second.start == Point(0, 6, 0)
    assert second.end == Point(2, 9, 4)
    assert third.start == Point(0, 12, 0)
    assert third.end == Point(2, 15, 4)
    first, second, third = Box.create_row(
        start, Point(5, 5, 4), 3, Point(0, 0, 1)
    )
    assert first.start == start
    assert first.end == Point(5, 5, 3)
    assert second.start == Point(1, 1, 4)
    assert second.end == Point(5, 5, 7)
    assert third.start == Point(1, 1, 8)
    assert third.end == Point(5, 5, 11)


def test_create_row_named() -> None:
    """Test creating a row of named rooms."""
    first, second = Box.create_row(
        Point(0, 0, 0), Point(3, 3, 3), 2, Point(1, 0, 0),
        get_name=lambda i: f'Room {i + 1}'
    )
    assert first.name == 'Room 1'
    assert second.name == 'Room 2'


def test_open() -> None:
    """Test door opening."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_close() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.open(None)
    d = Door(open=False)
    b.door = d
    b.open(None)
    assert d.open is True

    @b.event
    def on_open() -> None:
        d.open = False

    b.open(None)
    assert d.open is False


def test_close() -> None:
    """Test closing doors."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_open() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.close(None)
    d = Door(open=True)
    b.door = d
    b.close(None)
    assert d.open is False

    @b.event
    def on_close() -> None:
        d.open = True

    b.close(None)

    assert d.open is True


def test_nearest_door() -> None:
    """Test Box.nearest_door."""
    room: Box = Box(Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_door() is None
    d = Door()
    doorstep: Box = Box(room.end, room.end, door=d, parent=room)
    assert room.nearest_door() is None
    assert room.nearest_door(same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_door() is doorstep
    assert room.nearest_door(same_z=False) is doorstep


def test_nearest_portal(box_level: BoxLevel) -> None:
    """Test Box.nearest_portal."""
    room: Box = Box(Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_portal() is None
    p: Portal = Portal(box_level, Point(0, 0, 0))
    doorstep: Box = Box(room.end, room.end, portal=p, parent=room)
    assert room.nearest_portal() is None
    assert room.nearest_portal(same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_portal() is doorstep
    assert room.nearest_portal(same_z=False) is doorstep


def test_bounds() -> None:
    """Test the bounds of a box."""
    box: Box = Box(Point(1, 2, 3), Point(4, 5, 6))
    b: BoxBounds = box.bounds
    assert isinstance(b, BoxBounds)
    assert b.bottom_back_left == box.start
    assert b.bottom_front_left == Point(1, 5, 3)
    assert b.bottom_front_right == Point(4, 5, 3)
    assert b.bottom_back_right == Point(4, 2, 3)
    assert b.top_back_left == Point(1, 2, 6)
    assert b.top_front_left == Point(1, 5, 6)
    assert b.top_front_right == Point(4, 5, 6)
    assert b.top_back_right == Point(4, 2, 6)
    box = Box(Point(0, 0, 0), Point(5, 5, 5))
    b = box.bounds
    assert b.bottom_back_left == Point(0, 0, 0)
    assert b.bottom_front_left == Point(0, 5, 0)
    assert b.bottom_front_right == Point(5, 5, 0)
    assert b.bottom_back_right == Point(5, 0, 0)
    assert b.top_back_left == Point(0, 0, 5)
    assert b.top_front_left == Point(0, 5, 5)
    assert b.top_front_right == Point(5, 5, 5)
    assert b.top_back_right == Point(5, 0, 5)


def test_width() -> None:
    """Test box.width."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.width == 5


def test_depth() -> None:
    """Test box depth."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.depth == 3


def test_height() -> None:
    """Test box height."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.height == 1


def test_area() -> None:
    """Test box area."""
    b: BoxBounds = Box(Point(0, 0, 0), Point(5, 5, 5)).bounds
    assert b.area == 25
    b = Box(Point(5, 6, 0), Point(9, 12, 7)).bounds
    assert b.area == 24


def test_volume() -> None:
    """Test box volume."""
    b: BoxBounds = Box(Point(1, 2, 3), Point(10, 9, 8)).bounds
    assert b.volume == 315


def test_is_edge() -> None:
    """Test the is_edge method."""
    b: BoxBounds = Box(Point(0, 0, 0), Point(3, 3, 3)).bounds
    assert b.is_edge(Point(0, 0, 0))
    assert b.is_edge(Point(0, 1, 2))
    assert b.is_edge(Point(2, 0, 0))


def test_is_wall() -> None:
    """Test the is_wall method."""
    b: Box = Box(Point(1, 2, 3), Point(4, 5, 6))
    assert not b.is_wall(Point(1, 2, 3))
    assert not b.is_wall(Point(2, 3, 4))
    b.type = BoxTypes.solid
    assert b.is_wall(Point(1, 2, 3))
    assert b.is_wall(Point(2, 3, 4))
    b.type = BoxTypes.room
    assert b.is_wall(Point(1, 2, 3))
    assert not b.is_wall(Point(2, 3, 4))


def test_get_oldest_parent() -> None:
    """Tes the get_oldest_parent method."""
    start: Point = Point(0, 0, 0)
    end: Point = Point(3, 3, 3)
    a: Box = Box(start, end)
    b: Box = Box(start, end, parent=a)
    c: Box = Box(start, end, parent=b)
    assert a.get_oldest_parent() is a
    assert b.get_oldest_parent() is a
    assert c.get_oldest_parent() is a
    d: Box = Box(start, end)
    assert d.get_oldest_parent() is d


def test_box_sound(
    context: Context, source: Source3D, generator: StreamingGenerator, box: Box
) -> None:
    """Test the BoxSound constructor."""
    s: BoxSound = BoxSound(box, generator, source)
    assert s.box is box
    assert s.generator is generator
    assert s.source
    assert s.on_destroy is None


def test_play_sound(
    context: Context, box: Box, window: Window, game: Game
) -> None:
    """Test the play_sound method."""
    s: Optional[BoxSound] = box.play_sound(context, Path('sound.wav'))
    assert isinstance(s, BoxSound)
    assert s.box is box
    assert isinstance(s.generator, BufferGenerator)
    assert s.generator.looping is False
    assert s.generator.buffer is get_buffer('file', 'sound.wav')
    assert isinstance(s.source, Source3D)
    assert s.source.position == box.start.coordinates
    assert s in box.sounds
    assert s.on_destroy is None
    s.on_destroy = lambda: window.close()
    game.run(window)
    assert s not in box.sounds
    with raises(SynthizerError):
        s.generator.destroy()
    with raises(SynthizerError):
        s.source.destroy()


def test_play_sound_looping(
    context: Context, box: Box, window: Window, game: Game
) -> None:
    """Test the play_sound method."""
    s: Optional[BoxSound] = box.play_sound(
        context, Path('sound.wav'), looping=True
    )
    assert isinstance(s, BoxSound)
    assert s.box is box
    assert isinstance(s.generator, BufferGenerator)
    assert s.generator.looping is True
    assert s.generator.buffer is get_buffer('file', 'sound.wav')
    assert isinstance(s.source, Source3D)
    assert s.source.position == box.start.coordinates
    assert s in box.sounds

    def on_destroy() -> None:
        """Raise an error.

        This method should never be called, because the sound should never
        automatically be destroyed while looping.
        """
        window.close()
        raise RuntimeError(
            'A looping sound was automatically destroyed. This IS an error.'
        )

    s.on_destroy = on_destroy
    schedule_interval(
        lambda dt: window.close(),
        s.generator.buffer.get_length_in_seconds() * 3
    )
    game.run(window)
    assert s in box.sounds
    s.on_destroy = None
    s.stop()


def test_stream_sound(
    context: Context, box: Box, window: Window, game: Game
) -> None:
    """Test the stream_sound method."""
    s: BoxSound = box.stream_sound(context, 'file', 'sound.wav')
    assert s.box is box
    assert isinstance(s.generator, StreamingGenerator)
    assert s.generator.looping is False
    assert isinstance(s.source, Source3D)
    assert s.source.position == box.start.coordinates
    assert s in box.sounds
    schedule_interval(
        lambda dt: window.close(),
        get_buffer('file', 'sound.wav').get_length_in_seconds() * 3
    )
    game.run(window)
    assert s in box.sounds
    s.stop()


def test_stream_sound_looping(
    context: Context, box: Box, window: Window, game: Game
) -> None:
    """Test the stream_sound method."""
    s: BoxSound = box.stream_sound(context, 'file', 'sound.wav', looping=True)
    assert s.box is box
    assert isinstance(s.generator, StreamingGenerator)
    assert s.generator.looping is True
    assert isinstance(s.source, Source3D)
    assert s.source.position == box.start.coordinates
    assert s in box.sounds
    schedule_interval(
        lambda dt: window.close(),
        get_buffer('file', 'sound.wav').get_length_in_seconds() * 3
    )
    game.run(window)
    assert s in box.sounds
    s.stop()
