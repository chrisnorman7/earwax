# Earwax

An audio game engine for fast prototyping.

* [PyPi](https://pypi.org/project/earwax/)

* [Documentation](https://earwax.readthedocs.io/)

## Installation

You can install with pip:

```bash
pip install -U earwax
```

## Why Earwax

### Earwax is *simple*

You don't need to write out lots of boilerplate code to get simple things working. The ethos is that you probably don't care about how pedestrian things like input are processed, just that they are.

### Earwax is *powerful*

If you do decide you care about the lower level things, you can use Pyglet's event system to achieve your goals.

### Earwax has *lots* of helpers

Earwax already has classes for dice, game boards, mapping system, sound management, and menus.

Also, Earwax has a configuration framework which allows you to save and load configuration with minimal code.

The `Game` class also has a helpful method for getting a sensible folder for storing configuration. Using `Game.get_settings_path`, you will receive a `pathlib.Path` object containing your configuration directory.

### Earwax loves *output*

You can output speech or sound with very little code. Configuration files save with YAML, so they'll dump pretty much any object you can think of.

With the `Game.output` function, and the `SoundManager` class, emitting speech and sound is usually a one line affair.

### Size *doesn't* matter

Earwax doesn't care if your project is a one-file job, or a huge project containing hundreds of files. It's up to you how you organise your work, Earwax will be there when you need it.

### Earwax loves *input*

You can combine inputs in your actions. With one line of code you can add an action that works with a keyboard, a games controller, or the mouse.

### Earwax loves *tests*

Earwax has over 200 tests in its automated test framework, ensuring stability and reliability.

### Earwax has been made in *Great Britain*

As proved by a very clever fellow by the name of Pub Landlord, in his very scientific [video](https://www.youtube.com/watch?v=W5Gp2u4Q3BQ) on the topic, Great Britain sits at the very centre of the Earth. This means that Earwax is in fact: top hole, the bea's knees, the mutt's nuts, not to mention jolly blinking dapper.

## Example code

```python
from earwax import Game, Level
from pyglet.window import Window, key, mouse

game = Game()

level = Level(game)


@level.action('Say hello', symbol=key.H, mouse_button=mouse.LEFT, joystick_button=0)
def say_hello():
    """Say hello."""
    game.output('Hello there.')


level.action('Quit', symbol=key.Q)(game.stop)
level.action('Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT)(game.push_action_menu)

if __name__ == '__main__':
    window = Window(caption='Example Game')
    game.run(window, initial_level=level)
```

For more examples, see the examples directory in this repository.

## Building Documentation

You can build local documentation with the command:

```bash
python setup.py build_sphinx
```

The HTML docs will be available from `docs/build/html/index.html`.
