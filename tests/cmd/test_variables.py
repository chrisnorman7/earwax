"""Test the Variable class."""

from pytest import raises

from earwax.cmd.variable import Variable, VariableDict, VariableTypes


def test_init() -> None:
    """Test initialisation."""
    v: Variable[int] = Variable('points', 500)
    assert v.name == 'points'
    assert v.value == 500


def test_get_type() -> None:
    """Test the get_type method."""
    v: Variable = Variable('Random', 1234)
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
    v: Variable[str] = Variable('character_name', 'Test Character')
    d: VariableDict = v.dump()
    assert d.get('name') == v.name
    assert d.get('value') == v.value
    assert d['type'] == v.get_type().name


def test_load() -> None:
    """Test the load constructor."""
    d: VariableDict = {
        'name': 'points',
        'value': 500,
        'type': 'type_int'
    }
    v: Variable[int] = Variable.load(d)
    assert v.name == 'points'
    assert v.value == 500
    assert isinstance(v.value, int)
    d['type'] = 'broken'
    with raises(TypeError):
        Variable.load(d)
