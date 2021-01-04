"""Provides the Variable class."""

from enum import Enum
from typing import Any, Dict, Generic, TypeVar

from attr import attrs

from earwax.mixins import DumpLoadMixin

T = TypeVar('T')


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


type_strings: Dict[VariableTypes, str] = {
    VariableTypes.type_bool: 'Boolean',
    VariableTypes.type_string: 'String',
    VariableTypes.type_int: 'Integer',
    VariableTypes.type_float: 'Float'
}


@attrs(auto_attribs=True)
class Variable(Generic[T], DumpLoadMixin):
    """A variable in a game made with the earwax script.

    :ivar name: The name of the variable.

    :ivar value: The value this variable holds.
    """

    name: str
    type: VariableTypes
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

    @classmethod
    def load(cls, data: Dict[str, Any]) -> 'Variable':
        """Load a variable, and check its type.

        :param value: The value to load.
        """
        v: Variable = super().load(data)
        if v.type is not v.get_type():
            raise TypeError(
                'Loaded type %r but expected %r from data %r.' % (
                    v.get_type(), v.type, data
                )
            )
        return v
