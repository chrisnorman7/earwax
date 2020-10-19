Editors
=======

In earwax, an Editor represents a simple text editor.

Editors can be used for editing single lines of text. While it is entirely possible to add a line break to the text when you create an ``Editor`` instance, pressing the enter key while an ``Editor`` instance is pushed onto your game will result in the :meth:`~earwax.Editor.on_submit` event being dispatched.

Creating An Editor
==================

Creating an editor can be done the same way you can create most :class:`earwax.Level` instances::

    e: Editor = Editor(game)

As you can see, a :class:`earwax.Game` instance is necessary.

You can also supply a ``text`` argument::

    e: editor = Editor(game, text='Hello world')

The cursor will be placed at the end of the text, and it can be edited with standard operating system commands, unless you alter what motions are supported of course.

Motions
#######

You can easily add extra motions, or override the default ones::

    from pyglet.window import key

    @e.motion(key.MOTION_BACKSPACE)
    def backspace():
        game.output('Backspace was pressed.')

Now, when the backspace key is pressed, your new event will fire too.

Submitting Text
===============

When the enter key is pressed, or a game hat is used to select "submit" (more on that later), the :meth:`earwax.Editor.submit` method is called.

You can retrieve the text that was entered with the :meth:`~earwax.Editor.on_submit` event::

    @e.event
    def on_submit(text: str) -> None:
        print('Text entered: %r.' % text)

Dismissing Editors
==================

Like Earwax :class:`menus <earwax.Menu>`, editors are dismissible by default. This can of course be changed::

    e: Editor = Editor(game, dismissible=False)

Now, when the escape key is pressed, nothing happens.

Editing With The Hat
====================

You can use a game controller to edit text. Simply use the left and right directions to move through text, and the up and down directions to select letters.

If you keep pressing the up hat, you will come to a delete option. One more up performs the deletion.

If your focus is at the end of the line, the delete option will be replaced with a "Submit" option instead. This is the same as pressing the enter key.
