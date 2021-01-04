"""Test the Variable class."""

from typing import Any, Dict

from pytest import raises

from earwax.cmd.variable import Variable, VariableTypes

VariableDict = Dict[str, Any]


def test_init() -> None:
    """Test initialisation."""
    v: Variable[int] = Variable('points', VariableTypes.type_int, 500)
    assert isinstance(v.id, str)
    assert v.name == 'points'
    assert v.type is VariableTypes.type_int
    assert v.value == 500


def test_get_type() -> None:
    """Test the get_type method."""
    v: Variable = Variable('Random', VariableTypes.type_int, 1234)
    assert v.get_type() is VariableTypes.type_int
    v.value = 'Hello world'
    assert v.get_type() is VariableTypes.type_string
    v.value = True
    assert v.get_type() is VariableTypes.type_bool
    v.value = 4.56
    assert v.get_type() is VariableTypes.type_float
    v.value = {}
    with raises(TypeError):
        v.get_type()
    v.value = 'Sorted.'
    assert v.get_type() is VariableTypes.type_string


def test_dump() -> None:
    """Test the dump method."""
    v: Variable[str] = Variable(
        'character_name', VariableTypes.type_string, 'Test Character'
    )
    d: VariableDict = v.dump()
    assert d[Variable.__type_key__] == Variable.__name__
    d = d[Variable.__value_key__]
    assert isinstance(d, dict)
    assert d.get('name') == v.name
    assert d.get('value') == v.value
    assert d['type'] == v.get_type()


def test_load() -> None:
    """Test the load constructor."""
    d: VariableDict = {
        Variable.__type_key__: Variable.__name__,
        Variable.__value_key__: {
            'name': 'points',
            'id': 'test id',
            'type': VariableTypes.type_int,
            'value': 500
        }
    }
    v: Variable[int] = Variable.load(d)
    assert v.id == 'test id'
    assert v.name == 'points'
    assert v.value == 500
    assert isinstance(v.value, int)
    d[Variable.__value_key__]['type'] = VariableTypes.type_string
    with raises(TypeError):
        Variable.load(d)
