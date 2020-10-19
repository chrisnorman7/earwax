Buffer Directories
==================

The idea behind the :class:`earwax.BufferDirectory` class, is that quite often we need a single directory of sounds we can pick from. This usually leads to code like the following::

    room_ambiance = Sound('sounds/ambiances/room.wav')
    station_ambiance = Sound('sounds/ambiances/station.wav')
    ship_ambiance = Sound('sounds/ambiances/ship.wav')

This is particularly error prone, although has the benefit of letting you autocomplete variable names in your editor of choice.

Inspired by a possible future feature of `Synthizer <https://synthizer.github.io/>`_, I decided to make a small utility class for the express purpose of loading a directory of sounds. Using this class, the above code can be rewritten as::

    from pathlib import Path

    from earwax import BufferDirectory

    ambiances: BufferDirectory = BufferDirectory(Path('sounds/ambiances'))

    room_ambiance = 'room.wav'
    station_ambiance = 'station.wav'
    ship_ambiance = 'ship.wav'

Now you can for example get the station ambiance with the below code::

    buffer: Buffer = ambiances.buffers[station_ambiance]

This is useful if for example you've moved the entire directory. Instead of performing a find and replace, you can simply change the BufferDirectory instance::

    ambiances: BufferDirectory = BufferDirectory(Path('sounds/amb'))

Another common idiom is to select a random sound file from a directory. Earwax has a few sound functions with this capability already. If you pass a ``Path`` instance which happens to be a directory to :meth:`earwax.play_path`, or :meth:`earwax.play_and_destroy`, then a random file will be selected from the resulting directory.

The BufferDirectory class takes things one step further::

    lasers: BufferDirectory = BufferDirectory(Path('sounds/weapons/lasers'))

    laser_buffer: Buffer = lasers.random_buffer()

This will get you a random buffer from ``lasers.buffers``.

Sometimes you may have other files in a sounds directory in addition to the sound files themselves, attribution information for example. If this is the case, simply pass a
`glob <https://en.wikipedia.org/wiki/Glob_(programming)>`_ argument when instantiating the class, like so::

    bd: BufferDirectory = BufferDirectory(Path('sounds/music'), glob='*.ogg')

In closing, the BufferDirectory class is useful if you have a directory of sound files, that you'll want at some point throughout the lifecycle of your game. Folders of music tracks, footstep sounds, and weapon sounds are just some of the examples that spring to mind.
