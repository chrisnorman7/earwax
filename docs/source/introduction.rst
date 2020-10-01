Introduction
============

Workflow
--------

The basic flow of an Earwax program is:

* Create a `Game instance`.

* Create 1 or more `Level` instances.

* Add actions to the level instance(s) you created in the previous step.

* Create a pyglet `Window` instance.

* Run the game object you created in step ` with the window object you created in the previous step.

Full Example
------------

The below code is a full -albeit minimal -  code example::

    from earwax import Game, Level, tts
    from pyglet.window import key, mouse, Window
    w = Window(caption='Test Game')
    g = Game()
    l = Level()
    @l.action('Key speak', symbol=key.S)
    def key_speak():
        """"Say something when the s key is pressed."""
        tts.speak('You pressed the s key.')

    @l.action('Mouse speak', mouse_button=mouse.LEFT)
    def mouse_speak():
        """Speak when the left mouse button is pressed."""
        tts.speak('You pressed the left mouse button.')

    @l.action('Quit', symbol=key.ESCAPE, mouse_button=mouse.RIGHT)
    def do_quit():
        """Quit the game."""
        w.close()

    g.run(w, initial_level=l)
