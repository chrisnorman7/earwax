"""Provides the Workspace class."""

from getpass import getuser
from typing import Any, Dict, List, Optional

from attr import Factory, attrs
from yaml import CDumper, CLoader, dump, load

from earwax.mixins import DumpLoadMixin

from .constants import project_filename
from .project_credit import ProjectCredit
from .variable import Variable


@attrs(auto_attribs=True)
class Project(DumpLoadMixin):
    """An earwax project.

    This object holds the id of the initial map (if any), as well as global
    variables the user can create with the ``global`` subcommand.

    :ivar title: The title of this project.

    :ivar author: The author of this project.

    :ivar description: A description for this project.

    :ivar version: The version string of this project.

    :ivar initial_map_id: The id of the first map to load with the game.

    :ivar credits: A list of credits for this project.

    :ivar variables: The variables created for this project.
    """

    title: str
    author: str = Factory(lambda: f'{getuser()} <{getuser()}@localhost')
    description: str = Factory(str)
    version: str = Factory(lambda: '0.0.0')
    initial_map_id: Optional[str] = None

    credits: List[ProjectCredit] = Factory(list)
    variables: List[Variable] = Factory(list)

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
