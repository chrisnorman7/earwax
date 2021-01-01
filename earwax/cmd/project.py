"""Provides the Workspace class."""

from typing import Dict, List, Optional, Union, cast

from attr import Factory, attrs
from yaml import FullLoader, dump, load

from .constants import project_filename
from .variable import Variable, VariableDict

ProjectDict = Dict[str, Union[Optional[str], List[VariableDict]]]


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

    def dump(self) -> ProjectDict:
        """Return this object as a dictionary."""
        d: ProjectDict = {'title': self.title}
        variables_data: List[VariableDict] = []
        variable: Variable
        for variable in self.variables:
            variables_data.append(variable.dump())
        d['variables'] = variables_data
        return d

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
            data: ProjectDict = load(f, Loader=FullLoader)
            return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: ProjectDict) -> 'Project':
        """Load and return an instance from the provided data.

        :param data: The data to load.
        """
        name: str = cast(str, data['title'])
        variables_data: List[VariableDict] = cast(
            List[VariableDict], data.pop('variables')
        )
        self: Project = cls(name)
        variable_data: VariableDict
        for variable_data in variables_data:
            self.variables.append(Variable.load(variable_data))
        return self
