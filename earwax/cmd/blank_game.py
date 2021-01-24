"""A minimal game which can be expanded upon.

A description for your new game should probably go here.
"""

from pyglet.window import Window, key

from earwax import Credit, Game, Level, Menu, Track, TrackTypes

game: Game = Game(
    name='New Game',
    credits=[
        Credit.earwax_credit()
    ]
)

# Create a main menu to be shown when the game loads.
main_menu: Menu = Menu(game, 'Main Menu', dismissible=False)

# Create music for the menu.
main_menu_music: Track = Track('file', 'menu_music.mp3', TrackTypes.music)
# main_menu.tracks.append(main_menu_music)

# Create the first level.
#
# This level will be shown when the "Play" entry from the main menu is
# selected.
level: Level = Level(game)

# Create music for the level.
level_music: Track = Track('file', 'level_music.mp3', TrackTypes.music)
# level.tracks.append(level_music)


@level.action('Return to main menu', symbol=key.Q)
def return_to_main_menu() -> None:
    """Return to the main menu."""
    game.replace_level(main_menu)


@main_menu.item(title='Play game')
def play_game() -> None:
    """Replace this menu with ``level``."""
    game.replace_level(level)


main_menu.add_item(game.push_credits_menu, title='Show credits')
main_menu.add_item(game.stop, title='Exit')
level.action(
    'Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT
)(game.push_action_menu)

if __name__ == '__main__':
    window: Window = Window(caption=game.name)
    game.run(window, initial_level=main_menu)
