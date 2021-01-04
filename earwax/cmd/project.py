"""Provides the Workspace class."""

from getpass import getuser
from typing import Any, Dict, List

from attr import Factory, attrs

try:
    from yaml import CDumper, CLoader, dump, load
except ImportError:
    CDumper, CLoader, dump, load = (None, None, None, None)  # type: ignore

from earwax.mixins import DumpLoadMixin

from .constants import project_filename
from .game_level import GameLevel
from .project_credit import ProjectCredit
from .variable import Variable


@attrs(auto_attribs=True)
class Project(DumpLoadMixin):
    """An earwax project.

    This object holds the id of the initial map (if any), as well as global
    variables the user can create with the ``global`` subcommand.

    :ivar ~earwax.cmd.project.Project.name: The name of this project.

    :ivar ~earwax.cmd.project.Project.author: The author of this project.

    :ivar ~earwax.cmd.project.Project.description: A description for this
        project.

    :ivar ~earwax.cmd.project.Project.version: The version string of this
        project.

    :ivar ~earwax.cmd.project.Project.initial_map_id: The id of the first map
        to load with the game.

    :ivar ~earwax.cmd.project.Project.credits: A list of credits for this
        project.

    :ivar ~earwax.cmd.project.Project.variables: The variables created for this
        project.
    """

    name: str
    author: str = Factory(lambda: f'{getuser()} <{getuser()}@localhost')
    description: str = Factory(str)
    version: str = Factory(lambda: '0.0.0')
    requirements: str = Factory(
        lambda: 'earwax\npyglet\nsynthizer\n'
    )

    credits: List[ProjectCredit] = Factory(list)
    variables: List[Variable] = Factory(list)
    levels: List[GameLevel] = Factory(list)

    def save(self) -> None:
        """Save this project.

        Saves this workspace to the file specified in
        ``constants.project_filename``.
        """
        with project_filename.open('w') as f:
            dump(self.dump(), stream=f, Dumper=CDumper)

    @classmethod
    def from_file(cls) -> 'Project':
        """Load an instance.

        Loads and returns an instance from the file specified in
        ``constants.project_filename``.
        """
        with project_filename.open('r') as f:
            data: Dict[str, Any] = load(f, Loader=CLoader)
            return cls.load(data)
