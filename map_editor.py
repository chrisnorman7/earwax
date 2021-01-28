"""Basic map editor."""

from pyglet.window import Window

from earwax import Game, MapEditor

game: Game = Game(name='Map Editor')
level: MapEditor = MapEditor(game)

if __name__ == '__main__':
    window: Window = Window(caption=game.name)
    game.run(window, initial_level=level)
