Stories
#######

Stories are a way to create simple games using Earwax with no code. Stories consist of rooms, which contain exits and objects. Objects and exits in turn have actions which can be performed on them.

This document attempts to layout the steps involved in creating and editing a story.

Prerequisites
*************

Before getting started, let's make sure everything is installed correctly. This assumes you are comfortable with whatever terminal is offered by your system.

Make sure earwax is installed::

    pip install -U earwax

Earwax is frequently changing, so it's important you have the latest version.

If you want to copy and paste with earwax, you'll need the `Pyperclip <https://pypi.org/project/pyperclip/>`_ package. Let's install that now::

    pip install -U pyperclip

This package is not necessary, but when you're copy and pasting long sound paths, it's certainly helpful.

Getting Started
***************

Before we can edit a story, we must first create one. To do this, we use the ``story new`` subcommand of earwax::

    earwax story new world.yaml

You should see something like the following::

    Created Untitled World.

The filename can be whatever you want, and you are free to rename or move this file as you wish. Be aware however, that unless the paths to the sound files you use are absolute, moving the file will not work as you expect.

Playing a Story
***************

Stories can be played with the ``story play`` command, like so::

    earwax story play world.yaml

You can replace ``world.yaml`` in the command above to be whatever filename you have chosen for your world.

Editing a Story
***************

Now we have created a story, let's edit it.

When editing stories, you see the same interface as if you were a normal player. There are extra hotkeys of course, and the main menu changes to present you with extra options for configuring the over all story, as well as Earwax itself.

To get started, type::

    earwax story edit world.yaml

The filename in that command should be the same one you gave to the ``story new`` command.

You will see a couple of log lines printed to your terminal's standard output, then you'll be in the main menu.

The Main Menu
*************

The main menu is largely the same whether you're playing or editing a story. The difference is the number of items which are displayed.

Start new game
==============

Takes you into the game world, where you can perform your edits.

This option is also present when playing a story.

Load game
=========

Start with a loaded saved game.

This option is also present when playing a story.

Show warnings
=============

This option will show you a list of any warnings which were generated while loading the story file.

When you first edit a game, there will be 1 warning. This is because the default room that is created has no exits leading from it.

Save story
==========

This option will save any edits you have made so far. The story can also be saved by pressing control + s from within the story itself.

Configure Earwax
================

You can use this option to configure various parts of the game engine itself, such as the default menu sounds, and whether or not speech and braille are enabled.

When you have finished in this menu, you must activate the "Return to main menu" option at the end. This is so that the configuration can be saved, and you can be warned of any problems.

Add or remove credits
=====================

This option lets you add or remove credits from your game. This is useful if you plan to (or even need to) attribute someone for assets used in your story.

Set initial room
================

This option lets you set the room which the player will end up in when they first start playing your game.

It won't always be the room they appear in when they start playing, because they can save their progress, and then load it using the ``Load game`` option.

Main menu music
===============

This menu is where you can add or remove music from the main menu.

It is possible to have multiple tracks playing simultaneously, but you cannot alter their individual volumes.

World options
=============

This menu allows you to rename your story, add an author, and set the default panning strategy.

Report Earwax bug
=================

This option opens a web page where you can `report a bug <https://github.com/chrisnorman7/earwax/issues/new>`_ to Earwax.

As a personal note: Please please please use this if you find a problem. Letting me know personally is a great way to get your bug report lost.

Exit
====

This option is fairly self-explanatory: It quits the game and closes the window.

What it *doesn't* do is save your work. You have to do that manually.

Credits
=======

When you have added credits to your game, an option for viewing them will appear in the main menu.

This option won't appear unless there are credits, since showing an empty credits menu to players would serve no purpose.

Start Game
**********

Choosing the first option "Start new game", you will be placed into the first room.

Rooms
=====

This room doesn't really have that much going for it: It's called "first_room", which incidentally is also its ID, and it has no meaningful description. Let's change that now.

Renaming Rooms
--------------

There are two ways to rename a room: With a new textual name, or by "shadowing" the name of another room.

Simple Renaming
^^^^^^^^^^^^^^^

You can rename anything with this first method. Press the ``r`` key on any object you want to rename, and you can type in a new name, before pressing enter.

Shadowing Names
^^^^^^^^^^^^^^^

Shadowing room names is only possible for rooms. It involves using the ID of another room, to "shadow" the name.

To do this, press ``shift + r``. A menu will appear, showing every other room in the story. If you have no other rooms, this menu will be empty.

It is worth noting that shadowing room names and descriptions can only work for one level of rooms. That is, you cannot have room 1 shadow the name of room 2 which shadows the name of room 3. This is because you could also then have room 3 shadowing the name of room 1, which would cause an infinite loop.

Describing a Room
-----------------

Rooms are the only things in stories which can be described. You can describe a room with the ``e`` key. The ``d`` key is not used, since this would conflict with dropping objects.

The key combination ``shift + e`` allows you to shadow the description of another room. Shadowing descriptions follows the same rules as shadowing names.

Adding New Rooms
----------------

A world wouldn't be much with only one room to visit. The way to create rooms - and incidentally exits and objects - is with the ``c`` key.

If you press the ``c`` key, a menu will appear, allowing you to select what you would like to create.

Selecting ``Room`` from the bottom of this menu, will create - and move you to - another empty room.

Moving Between Rooms
--------------------

While exits are the primary way for *players* to move between rooms, it is helpful to have a quicker way as a builder.

Pressing the ``g`` key brings up a menu of rooms you can use to move quickly between rooms. This obviously bypasses exits, allowing you to get to as yet unlinked rooms.

Exits
=====

Exits are the only way for *players* to move between rooms. They must be built to link rooms, otherwise there will be no way to access them.

Incidentally, unlinked (or inaccessible) rooms will result in warnings when editing worlds.

Building Exits
--------------

To create an exit, again use the ``c`` (create) key, and select ``Exit``.

This will bring up a list of rooms (excluding the current one), which - when selected - will construct the exit.

Renaming Exits
--------------

You can rename an exit by first selecting it from the exits list, and pressing the ``r`` key.

Objects
=======

The second entry in the create menu is for creating objects. You *must* be in the room where you plan to place the object before you create. Taking the object and dropping it elsewhere will not actually "move" the object, and currently there is no way to relocate objects.

This can be looked at if someone is upset by this lack enough to `submit an issue <https://github.com/chrisnorman7/earwax/issues/new?title=Relocating%20Objects%20in%20Stories>`_.

Renaming Objects
----------------

You can rename an object by selecting it from the objects list, and pressing the ``r`` key.

Object Types
------------

objects can have one of a couple of different types. You can change the object type with the ``t`` key.

The object types are listed below:

Cannot Be Taken
^^^^^^^^^^^^^^^

This type is best for stationary objects like scenery. It will not be possible to take such objects.

Can Be Taken
^^^^^^^^^^^^

Objects of this type can be picked up. Their ``take action`` dictates what message and sound is presented to the player when they are taken.

If an object's ``take action`` is not set, the world's ``take action`` will be used instead.

Objects of this type cannot be dropped. If you think that's stupid, read on (there is another type).

Can Be Dropped
^^^^^^^^^^^^^^

Objects of this type can both be picked up and dropped.

The object's ``drop action`` will be used to provide a message and a sound for when the object is dropped.

If there is no ``drop action`` on the object in question, the world's default ``drop action`` will be used instead.

Can Be Used
^^^^^^^^^^^

This final type is ``not`` listed in the types menu. It is only applicable when a ``use action`` is specified for an object. Otherwise, the object is considered unusable.

It is perfectly possible for an object to be usable but not droppable. It is even possible for an object to be usable, but impossible for that object to be picked up in the first place. Note that this would be pointless, since the ``use action`` can only be accessed by the player when the object is in their inventory.

Object Classes
--------------

Objects can belong to 0 or more ``classes``. These classes are useful for grouping objects, and will be used to make exits allow or disallow player access in the future.

To keep apprised of the work on exits, please track `this issue <https://github.com/chrisnorman7/earwax/issues/5>`_.

To add and remove classes from an object, use the ``o`` key.

Object classes can be added and removed with the key combination ``shift + o``.

Messages
========

Objects, exits, and the world itself all have messages. To set messages, use the ``m`` key.

This key will set different messages depending on which category is shown:

* When in the ``location`` category, edit the world messages.

* When an entry from the ``objects`` category is selected, you can set the message that is shown when any object action is used.

* When an entry from the ``exits`` category is selected, you can set the message which is shown when using that exit.

Sounds
======

You can set sounds for objects and exits, as well as the world itself.

To set sounds, use the ``s`` key. This key performs different actions, depending on which category is shown:

* When in the ``location`` category, edit the world sounds.

* When an entry from the ``objects`` category is selected, you can set the sound which is heard when any object action is used.

* When an entry from the ``exits`` category is selected, you can set the sound which is heard when using that exit.

Ambiances
=========

Using the ``a`` key, you can edit ambiances for the current room, and for objects.

Exits do *not* have ambiances, so the ``a`` key does nothing when in the ``exits`` category.

Actions
=======

Actions are used throughout stories. They can be edited with the ``shift + a`` shortcut.

* When in the ``location`` category, you can edit (or clear) the default actions for the world.

* When an entry from the ``objects`` category is selected, you can edit (or delete) actions for when an object is taken, dropped, or used, or you can edit the custom actions for the given object.

* When an entry from the ``exits`` category is selected, you can edit (or clear) the action which is used when the exit is traversed.

Saving Stories
**************

As mentioned in the `Save Story`_ section, you can save your story at any time with the keyboard shortcut ``control + s``.

Building Stories
################

You can build your story into a Python file with the ``story build`` command.

Assuming you have a world file named ``world.yaml``, you can convert it to python with the command::

    earwax story build world.yaml world.py

This will output ``world.py``. You can then play your story with::

    python world.py

If you wish to consolidate all your sounds, you can use the ``-s`` switch::

    earwax story build world.yaml world.py -s assets

This will copy all your sound files into a folder named ``assets``. Their names will be changed, and the folder structure will be defined by earwax.

A note for screen reader users: It is not recommended that you read the generated python file line-by-line. This is because the line which holds the YAML data for your world can be extremely long, and this negatively impacts screen reader use.
