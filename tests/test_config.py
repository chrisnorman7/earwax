"""Test the classes in earwax.config."""

from pathlib import Path
from typing import Any, Dict, Optional

from yaml import FullLoader, dump, load

from earwax import Config, ConfigValue


class ServerConfig(Config):
    """Pretend server information."""

    hostname = ConfigValue('example.com')
    port = ConfigValue(1234)


class AccountConfig(Config):
    """Test account configuration."""

    username = ConfigValue('test')
    password = ConfigValue('test123!')
    server: ServerConfig = ServerConfig()


class RecursiveConfig(Config):
    """Another configuration page, this one with a subsection."""

    data_dir = ConfigValue('.')
    account: AccountConfig = AccountConfig()


class GameConfig(Config):
    """Pretend game configuration."""

    character_name = ConfigValue(None, type_=Optional[str])
    server: ServerConfig = ServerConfig()


def test_init() -> None:
    """Test initialisation."""
    c: Config = Config()
    assert c.dump() == {}
    assert c.__config_subsections__ == {}
    assert c.__config_values__ == {}


def test_dump() -> None:
    """Test that configuration sections can be dumped."""
    c: GameConfig = GameConfig()
    d: Dict[str, Any] = c.dump()
    assert d['server'] == c.server.dump()
    assert d == {
        'character_name': None,
        'server': {'hostname': 'example.com', 'port': 1234}
    }
    c.populate_from_dict(d)
    assert c.dump() == d


def test_recursive_dump() -> None:
    """Test dumping with subsections."""
    c = RecursiveConfig()
    d: Dict[str, Any] = c.dump()
    assert d['account']['server'] == ServerConfig().dump()
    c.populate_from_dict(d)
    assert c.dump() == d


def test_set_value() -> None:
    """Test setting values."""
    c = ServerConfig()
    c.hostname.value = 'microsoft.com'
    c.port.value = 8080
    assert c.dump() == {
        'hostname': 'microsoft.com',
        'port': 8080
    }


def test_populate_from_dict() -> None:
    """Test Config.populate_from_dict."""
    s = ServerConfig()
    s.populate_from_dict({'hostname': 'google.com', 'port': 9000})
    assert s.hostname.value == 'google.com'
    assert s.port.value == 9000


def test_save() -> None:
    """Test config.save."""
    c = RecursiveConfig()
    p = Path('config.yaml')
    try:
        with p.open('w') as f:
            c.save(f)
        assert p.is_file()
        with p.open('r') as f:
            d = load(f, Loader=FullLoader)
        assert d == c.dump()
    finally:
        p.unlink()


def test_load() -> None:
    """Test Config.load."""
    p = Path('config.yaml')
    username: str = 'chrisnorman7'
    c: RecursiveConfig = RecursiveConfig()
    c.account.username.value = username
    d = c.dump()
    del d['account']['username']
    d['account']['password'] = 'IChangedItWoot!"'
    d['data_dir'] = '/home/test'
    try:
        with p.open('w') as f:
            dump(d, stream=f)
        with p.open('r') as f:
            c.load(f)
        assert c.data_dir.value == d['data_dir']
        assert c.account.username.value == username
        assert c.account.password.value == d['account']['password']
    finally:
        p.unlink()


def test_name_() -> None:
    """Test section name."""
    class SecondConfig(Config):
        __section_name__ = 'Second Configuration Page'

    class FirstConfig(Config):
        __section_name__ = 'First Configuration Page'
        second = SecondConfig()

    c = FirstConfig()
    assert c.__section_name__ == 'First Configuration Page'
    assert Config.__section_name__ is None
    assert c.second.__section_name__ == 'Second Configuration Page'
