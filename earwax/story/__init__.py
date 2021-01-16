"""The story module.

Stories are a way of building worlds with no code at all.

They can do a fair amount on their own: You can create rooms, exits, objects,
and you can add basic actions to those objects. In addition, you can create
complex actions if you code them in yourself.

What you get out of the box:

* An easy way of creating worlds with an on screen editor.

* A main menu, with items for playing, exiting, showing credits, and loading
    saved games.

* Basic keyboard and controller commands for interracting with your world.

* The ability to create rich 3d environments, with all the sounds, messages,
    and music you can think of.

* The ability to build your world into a single Python file you can compile
    with a tool such as `PyInstaller <https://www.pyinstaller.org/>`_, or send
    about as is.

If you do wish to extend your world, build it into a Python file, then edit it
to add extra actions, tasks, or whatever else you can think of.
"""

from typing import List

from .context import StoryContext
from .edit_level import EditLevel, ObjectPositionLevel
from .play_level import PlayLevel
from .world import (DumpablePoint, DumpableReverb, ObjectTypes, RoomExit,
                    RoomObject, StoryWorld, WorldAction, WorldAmbiance,
                    WorldMessages, WorldRoom, WorldState, WorldStateCategories)

__all__: List[str] = ['ObjectTypes']
__all__.extend(
    thing.__name__ for thing in [
        DumpablePoint, DumpableReverb, RoomExit, RoomObject, StoryWorld,
        WorldAction, WorldAmbiance, WorldMessages, WorldRoom, WorldState,
        WorldStateCategories, EditLevel, ObjectPositionLevel, PlayLevel,
        StoryContext
    ]
)
