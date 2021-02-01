"""Test the earwax.GameBoard class."""
from typing import Tuple

from pytest import raises

from earwax import Game, GameBoard, NoSuchTile, Point, PointDirections


class OnMoveWorks(Exception):
    """Movement works."""


class OnMoveFailWorks(Exception):
    """Movement fail works."""


def test_init(game: Game) -> None:
    """Test initialisation."""

    def tile_builder(p: Point) -> Point:
        return p

    b: GameBoard[Point] = GameBoard(game, Point(1, 1, 1), tile_builder)
    assert b.coordinates == Point(0, 0, 0)
    assert b.get_tile(Point(0, 0, 0)) == Point(0, 0, 0)
    assert b.get_tile(Point(1, 0, 0)) == Point(1, 0, 0)
    assert b.get_tile(Point(0, 1, 0)) == Point(0, 1, 0)
    assert b.get_tile(Point(1, 1, 0)) == Point(1, 1, 0)
    assert b.get_tile(Point(0, 0, 1)) == Point(0, 0, 1)
    assert b.get_tile(Point(1, 0, 1)) == Point(1, 0, 1)
    assert b.get_tile(Point(0, 1, 1)) == Point(0, 1, 1)
    assert b.get_tile(Point(1, 1, 1)) == Point(1, 1, 1)


def test_get_tile(game: Game) -> None:
    """Test GameBoard.get_tile."""
    b: GameBoard = GameBoard(game, Point(2, 2, 2), lambda p: 0)
    assert b.get_tile(Point(0, 0, 0)) == 0
    with raises(NoSuchTile):
        b.get_tile(Point(5, 5, 5))


def test_move(board: GameBoard[int]) -> None:
    """Test GameBoard.move."""
    assert board.coordinates == Point(0, 0, 0)  # Just checking.
    board.move(PointDirections.north)()
    assert board.coordinates == Point(0, 1, 0)
    board.move(PointDirections.southeast)()
    assert board.coordinates == Point(1, 0, 0)


def get_board(game: Game) -> GameBoard[Tuple[float, float, float]]:
    """Get a board for future tests."""

    def tile_builder(p: Point) -> Tuple[float, float, float]:
        return p.coordinates

    b: GameBoard[Tuple[float, float, float]] = GameBoard(
        game, Point(4, 4, 4), tile_builder
    )

    @b.event
    def on_move_success(p: Point) -> None:
        raise OnMoveWorks(p)

    @b.event
    def on_move_fail(direction: PointDirections) -> None:
        raise OnMoveFailWorks(direction)

    return b


def test_on_move(game: Game) -> None:
    """Test the on_move event."""
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    with raises(OnMoveWorks) as exc:
        b.move(PointDirections.northeast)()
    assert exc.value.args == (PointDirections.northeast,)


def test_on_move_fail(game: Game) -> None:
    """Test the on_move_fail event."""
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    assert b.coordinates == Point(0, 0, 0)
    with raises(OnMoveFailWorks) as exc:
        b.move(PointDirections.south)()
    assert exc.value.args == (PointDirections.south,)


def test_move_wrap(game: Game) -> None:
    """Test movement with wrap around."""
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    b.coordinates = Point(0, 0, 0)
    with raises(OnMoveWorks):
        b.move(PointDirections.south, wrap=True)()
    assert b.coordinates == Point(0, 3, 0)
    b.coordinates = Point(4, 0, 0)
    with raises(OnMoveWorks):
        b.move(PointDirections.east, wrap=True)()
    assert b.coordinates == Point(0, 0, 0)


def test_current_tile(game: Game) -> None:
    """Test getting the current tile."""
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    assert b.current_tile == (0, 0, 0)
    b.coordinates = Point(1, 2, 3)
    assert b.current_tile == (1, 2, 3)
    b.coordinates = Point(10, 10, 10)
    assert b.current_tile is None


def test_populated_points(game: Game) -> None:
    """Test the populated_points list."""
    b: GameBoard[None] = GameBoard(game, Point(2, 2, 0), lambda P: None)
    assert len(b.populated_points) == 9
    assert Point(0, 0, 0) in b.populated_points
    assert Point(2, 0, 0) in b.populated_points
    assert Point(2, 2, 0) in b.populated_points
    assert Point(0, 2, 0) in b.populated_points
