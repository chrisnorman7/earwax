from typing import Tuple

from pytest import raises

from earwax import Game, GameBoard, NoSuchTile, Point, PointDirections


class OnMoveWorks(Exception):
    pass


class OnMoveFailWorks(Exception):
    pass


def test_init(game: Game) -> None:

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
    b: GameBoard = GameBoard(game, Point(2, 2, 2), lambda p: 0)
    assert b.get_tile(Point(0, 0, 0)) == 0
    with raises(NoSuchTile):
        b.get_tile(Point(5, 5, 5))


def test_move(board: GameBoard[int]) -> None:
    assert board.coordinates == Point(0, 0, 0)  # Just checking.
    board.move(PointDirections.north)()
    assert board.coordinates == Point(0, 1, 0)
    board.move(PointDirections.southeast)()
    assert board.coordinates == Point(1, 0, 0)


def get_board(game: Game) -> GameBoard[Tuple[float, float, float]]:

    def tile_builder(p: Point) -> Tuple[float, float, float]:
        return p.coordinates

    b: GameBoard[Tuple[float, float, float]] = GameBoard(
        game, Point(4, 4, 4), tile_builder
    )

    @b.event
    def on_move(p: Point, t: Tuple[float, float, float]) -> None:
        raise OnMoveWorks(p, t)

    @b.event
    def on_move_fail(direction: PointDirections) -> None:
        raise OnMoveFailWorks(direction)

    return b


def test_on_move(game: Game) -> None:
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    with raises(OnMoveWorks) as exc:
        b.move(PointDirections.northeast)()
    assert exc.value.args == (
        PointDirections.northeast, b.coordinates.coordinates
    )


def test_on_move_fail(game: Game) -> None:
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    assert b.coordinates == Point(0, 0, 0)
    with raises(OnMoveFailWorks) as exc:
        b.move(PointDirections.south)()
    assert exc.value.args == (PointDirections.south,)


def test_move_wrap(game: Game) -> None:
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
    b: GameBoard[Tuple[float, float, float]] = get_board(game)
    assert b.current_tile == (0, 0, 0)
    b.coordinates = Point(1, 2, 3)
    assert b.current_tile == (1, 2, 3)
    b.coordinates = Point(10, 10, 10)
    assert b.current_tile is None
