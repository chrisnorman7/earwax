"""Provides the Workspace class."""

from typing import Dict, Optional

from attr import asdict, attrs
from yaml import FullLoader, dump, load

from .constants import workspace_file

WorkspaceDict = Dict[str, str]


@attrs(auto_attribs=True)
class Workspace:
    """An earwax "game".

    This object holds the id of the initial level (if any), as well as global
    variables the user can create with the ``globals`` subcommand."""

    title: str
    initial_level_id: Optional[str] = None

    def dump(self) -> WorkspaceDict:
        """Returns this object as a dictionary."""
        return asdict(self)

    def save(self) -> None:
        """Saves this workspace to
        :var:`~earwax.cmd.constants.workspace_file`."""
        with workspace_file.absolute().open('w') as f:
            dump(self.dump(), stream=f)

    @classmethod
    def load(cls) -> 'Workspace':
        """Load and return an instance from
        :var:`~earwax.cmd.constants.workspace_file`."""
        with workspace_file.absolute().open('r') as f:
            data: WorkspaceDict = load(f, Loader=FullLoader)
        return cls(**data)
