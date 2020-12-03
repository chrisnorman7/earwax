"""Provides the Workspace class."""

from typing import Dict, Optional

from attr import asdict, attrs
from yaml import FullLoader, dump, load

from .constants import project_filename

WorkspaceDict = Dict[str, str]


@attrs(auto_attribs=True)
class Project:
    """An earwax project.

    This object holds the id of the initial level (if any), as well as global
    variables the user can create with the ``globals`` subcommand.
    """

    title: str
    initial_level_id: Optional[str] = None

    def dump(self) -> WorkspaceDict:
        """Return this object as a dictionary."""
        return asdict(self)

    def save(self) -> None:
        """Save this project.

        Saves this workspace to the file specified in
        ``constants.project_filename``.
        """
        with project_filename.absolute().open('w') as f:
            dump(self.dump(), stream=f)

    @classmethod
    def load(cls) -> 'Project':
        """Load an instance.

        Loads and returns an instance from the file specified in
        ``constants.project_filename``.
        """
        with project_filename.absolute().open('r') as f:
            data: WorkspaceDict = load(f, Loader=FullLoader)
        return cls(**data)
