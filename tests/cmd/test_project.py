"""Test the Project class."""

from typing import Any, Dict

from earwax.cmd.project import Project, ProjectDict
from earwax.cmd.variable import Variable


def test_init() -> None:
    """Test initialisation."""
    p: Project = Project('Test')
    assert p.title == 'Test'
    assert p.initial_map_id is None
    assert p.variables == []


def test_dump() -> None:
    """Test the dump method."""
    p: Project = Project(
        'Test', author='Bob Test', description='A test dame', version='5.4.3'
    )
    character_name: Variable[str] = Variable(
        'character_name', 'Test character'
    )
    p.variables.append(character_name)
    character_points: Variable[int] = Variable('character_points', 500)
    p.variables.append(character_points)
    d: Dict[str, Any] = p.dump()
    assert d['title'] == p.title
    assert d['author'] == p.author
    assert d['version'] == p.version
    assert d['description'] == p.description
    assert d['variables'] == [character_name.dump(), character_points.dump()]


def test_from_dict() -> None:
    """Test the load constructor."""
    p: Project = Project(
        'Test', author='Bob Test', description='A test dame', version='5.4.3'
    )
    character_name: Variable[str] = Variable(
        'character_name', 'Test character'
    )
    p.variables.append(character_name)
    character_points: Variable[int] = Variable('character_points', 500)
    p.variables.append(character_points)
    d: ProjectDict = p.dump()
    p2: Project = Project.from_dict(d)
    assert p2 == p
