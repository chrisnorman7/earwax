"""Test the Credit class."""

from earwax import Credit


def test_init() -> None:
    """Test initialisation."""
    c: Credit = Credit("Test", "http://example.com")
    assert c.name == "Test"
    assert c.url == "http://example.com"
    assert c.sound is None
    assert c.loop is True
