"""A really terrible maze demo.

This demo is extremely difficult to make your way through. Eventually I'll add
some better navigation tools.

For now, it serves as a quick example on creating a maze level that can be
extended.
"""
from pathlib import Path

from earwax import Box, BoxLevel, Game
from mazelib import Maze
from mazelib.generate.Prims import Prims
from pyglet.window import Window

wall_sound: Path = Path("map_demo/sounds/collide.wav")
surface_sound: Path = Path("map_demo/sounds/footsteps/corridor")

if __name__ == "__main__":
    maze: Maze = Maze()
    maze.generator = Prims(100, 100)
    maze.generate()
    game: Game = Game()
    level: BoxLevel = BoxLevel(game)
    box: Box
    for box in Box.maze(game, maze.grid):
        box.name = "Corridor"
        level.add_box(box)
        box.surface_sound = surface_sound
        box.wall_sound = wall_sound
    level.set_coordinates(level.boxes[0].start.floor())
    level.add_default_actions()
    window: Window = Window(caption="Maze")
    game.run(window, initial_level=level)
