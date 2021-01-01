"""Provides the Workspace class."""

from typing import Dict, List, Optional

from attr import Factory, asdict, attrs
from yaml import FullLoader, dump, load

from .constants import project_filename
from .variable import Variable, VariableDict


@attrs(auto_attribs=True)
class Project:
    """An earwax project.

    This object holds the id of the initial map (if any), as well as global
    variables the user can create with the ``global`` subcommand.

    :ivar title: The title of this project.

    :ivar initial_map_id: The id of the first map to load with the game.

    :ivar variables: The variables created for this project.
    """

    title: str
    initial_map_id: Optional[str] = None

    variables: List[Variable] = Factory(list)

    def dump(self) -> Dict:
        """Return this object as a dictionary."""
        return asdict(self)

    def save(self) -> None:
        """Save this project.

        Saves this workspace to the file specified in
        ``constants.project_filename``.
        """
        with project_filename.open('w') as f:
            dump(self.dump(), stream=f)

    @classmethod
    def load(cls) -> 'Project':
        """Load an instance.

        Loads and returns an instance from the file specified in
        ``constants.project_filename``.
        """
        with project_filename.open('r') as f:
            data: Dict = load(f, Loader=FullLoader)
        variables_data: List[VariableDict] = data.pop('variables')
        self: Project = cls(**data)
        variable_data: VariableDict
        for variable_data in variables_data:
            self.variables.append(Variable.load(variable_data))
        return self
