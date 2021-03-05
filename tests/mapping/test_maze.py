"""Test mazes."""

from earwax import Box, BoxTypes, Game
from mazelib import Maze
from mazelib.generate.Prims import Prims
from numpy import ndarray


def test_boxes(game: Game) -> None:
    """Test the maze constructor."""
    maze: Maze = Maze()
    maze.generator = Prims(10, 10)
    maze.generate()
    g: ndarray = maze.grid
    box: Box
    for box in Box.maze(game, g):
        expected: int
        if box.type is BoxTypes.empty:
            expected = 0
        else:
            expected = 1
        assert g[box.start.x][box.start.y] == expected
