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

Editing a Story
***************

Now we have created a story, let's edit it.

When editing stories, you see the same interface as if you were a normal player. There are extra hotkeys obviously, and the main menu changes to present you with extra options for configuring the over all story, as well as Earwax itself.

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

This room doesn't really have that much going for it: It's called "first_room", which incidentally is also its ID, and it has no meaningful description. Let's change that now.

Renaming a Room
===============

There are two ways to rename a room: With a new textual name, or by "shadowing" the name of another room.

Simple Renaming
---------------

You can rename anything with this first method. Press the ``r`` key on any object you want to rename, and you can type in a new name, before pressing enter.

Shadowing Names
---------------

Shadowing room names is only possible for rooms. It involves using the ID of another room, to "shadow" the name.

To do this, press ``shift + r``. A menu will appear, showing every other room in the story. If you have no other rooms, this menu will be empty.

It is worth noting that shadowing room names and descriptions can only work for one level of rooms. That is, you cannot have room 1 shadow the name of room 2 which shadows the name of room 3. This is because you could also then have room 3 shadowing the name of room 1, which would cause an infinite loop.

Describing a Room
=================

Rooms are the only things in stories which can be described. You can describe a room with the ``e`` key. The ``d`` key is not used, since this would conflict with dropping objects.

The key combination ``shift + e`` allows you to shadow the description of another room. Shadowing descriptions follows the same rules as shadowing names.
