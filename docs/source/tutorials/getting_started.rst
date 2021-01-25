Getting Started
###############

When getting started with any new library, it is often hard to know where to start. Earwax contains many `tutorials <index.html>`_, but that doesn't help you write your first line of code.

For writing your first game, there is the ``game`` command::

    $ earwax game main.py
    Creating a blank game at main.py.
    Done.

This will create you a very minimal :class:`game <earwax.game.Game>`, which can already be run::

    $ python main.py

This should load up a game called "New Game".

This game already has a few things to get you started:

* A main :class:`menu <earwax.menus.menu.Menu>`, with an entry to :meth:`play the game <earwax.level.Level.push_level>`, :meth:`show credits <earwax.game.Game.push_credits_menu>`, and :meth:`exit <earwax.game.Game.stop>`.

* An initial level with a :class:`help menu <earwax.menus.action_menu.ActionMenu>`. You can press ``Q`` from this level to return to the main menu.

* An extremely self-aggrandising default :class:`credit <earwax.credit.Credit>`, mentioning Earwax, and its illustrious creator.

* Commented out lines which provide main menu, and initial level :class:`music <earwax.track.Track>`.

This game serves as a starting point for your own work, and should be :mod:`expanded upon <earwax>`.
