"""Test the ProjectCredit class."""

from pathlib import Path
from typing import Any, Dict

from earwax.cmd.project_credit import ProjectCredit


def test_init() -> None:
    """Test initialisation."""
    c: ProjectCredit = ProjectCredit('Test', 'test.com', None, True)
    assert c.name == 'Test'
    assert c.url == 'test.com'
    assert c.sound is None
    assert c.loop is True


def test_path(project_credit: ProjectCredit) -> None:
    """Test the path property."""
    assert isinstance(project_credit, ProjectCredit)
    assert project_credit.path == Path('sound.wav')
    project_credit.sound = None
    assert project_credit.path is None


def test_dump(project_credit: ProjectCredit) -> None:
    """Test the dump method."""
    assert project_credit.dump() == {
        'name': project_credit.name, 'url': project_credit.url, 'sound':
        project_credit.sound, 'loop': project_credit.loop
    }


def test_load(project_credit: ProjectCredit) -> None:
    """Test the load constructor."""
    d: Dict[str, Any] = project_credit.dump()
    c: ProjectCredit = ProjectCredit.load(d)
    assert isinstance(c, ProjectCredit)
    assert c == project_credit
