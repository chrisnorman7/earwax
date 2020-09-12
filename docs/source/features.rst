Features
========

Implemented Features
--------------------

* Ability to separate disparate parts of a game into :class:`~earwax.Level` constructs.

* Ability to push, pop, and replace Level instances on the central :class:`~earwax.Game` object.

* A simple event handling system, allowing you to write clear and concise code.

* Uses `Synthizer <https://synthizer.github.io/>`_ as its sound backend.

* Both :class:`simple <earwax.SimpleInterfaceSoundPlayer>` and :class:`advanced <earwax.AdvancedInterfaceSoundPlayer>` sound players, designed for playing interface sounds.

* A flexible and unobtrusive configuration framework that uses yaml.

* The ability to use generic sound icons in menus, simply by setting a configuration value.

* Various sound functions for playing sounds, and cleaning them up when they're finished.

* Different types of levels already implemented:

    * Game board levels, so you can create board games with minimal boilerplate.

    * Box levels, which contain boxes, which can be connected together to make maps. Both free and restricted movement commands are already implemented.

Feature Requests
----------------

If you need a feature that is not already on this list, please `submit a feature request <https://github.com/chrisnorman7/earwax/issues/new>`_.
