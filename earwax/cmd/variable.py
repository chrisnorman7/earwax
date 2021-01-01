"""Provides the Variable class."""

from enum import Enum
from typing import Dict, Generic, TypeVar, Union, cast

from attr import attrs

T = TypeVar('T')
VariableDict = Dict[str, Union[str, T]]


class VariableTypes(Enum):
    """Provides the possible types of variable.

    :ivar type_int: An integer.

    :ivar type_float: A floating point number.

    :ivar type_string: a string.

    :ivar type_bool: A boolean value.
    """

    type_int = 0
    type_float = 1
    type_string = 2
    type_bool = 3


@attrs(auto_attribs=True)
class Variable(Generic[T]):
    """A variable in a game made with the earwax script.

    :ivar name: The name of the variable.

    :ivar value: The value this variable holds.
    """

    name: str
    value: T

    def get_type(self) -> VariableTypes:
        """Return the type of this variable.

        This method returns a member of :class:`VariableTypes`.
        """
        cls = type(self.value)
        if cls is int:
            return VariableTypes.type_int
        elif cls is float:
            return VariableTypes.type_float
        elif cls is str:
            return VariableTypes.type_string
        elif cls is bool:
            return VariableTypes.type_bool
        else:
            raise TypeError('Unknown type for %r.' % self)

    def dump(self) -> VariableDict:
        """Return this object as a dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.get_type().name
        }

    @classmethod
    def load(cls, data: VariableDict) -> 'Variable':
        """Load and return an instance from the provided dictionary.

        :param data: The data to load.
        """
        name: str = data['name']
        value: T = cast(T, data['value'])
        self: Variable[T] = cls(name, value)
        if self.get_type().name != data['type']:
            raise TypeError(
                'Type mismatch: Got %r but stored was %s.' % (
                    self.get_type(), data['type']
                )
            )
        return self
