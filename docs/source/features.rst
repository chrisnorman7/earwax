Features
========

Implemented Features
--------------------

* Ability to separate disparate parts of a game into :class:`~earwax.Level` constructs.

* Ability to push, pop, and replace Level instances on the central :class:`~earwax.Game` object.

* Uses Pyglet's event system, mostly eliminating the need for subclassing.

* Uses `Synthizer <https://synthizer.github.io/>`_ as its sound backend.

* Both :class:`simple <earwax.SimpleInterfaceSoundPlayer>` and :class:`advanced <earwax.AdvancedInterfaceSoundPlayer>` sound players, designed for playing interface sounds.

* A flexible and unobtrusive configuration framework that uses yaml.

* The ability to configure various apsects of the framework (including generic sound icons in menus), simply by setting configuration values on a :class:`configuration object <earwax.EarwaxConfig>` which resides on your :class:`game object <earwax.Game>`.

* Various sound functions for playing sounds, and cleaning them up when they're finished.

* Different types of levels already implemented:

    * Game board levels, so you can create board games with minimal boilerplate.

    * Box levels, which contain boxes, which can be connected together to make maps. Both free and restricted movement commands are already implemented.

* The ability to add actions to :class:`earwax.Level` instances with keyboard keys, mouse buttons, joystick buttons, and joystick hat positions.

* A text-to-speech system.

* An ``earwax`` command which can currently create default games.

Feature Requests
----------------

If you need a feature that is not already on this list, please `submit a feature request <https://github.com/chrisnorman7/earwax/issues/new>`_.
