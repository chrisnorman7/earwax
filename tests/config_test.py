from typing import Any, Dict, Optional

from earwax import Config, ConfigValue


class ServerConfig(Config):
    """Pretend server information."""

    hostname = ConfigValue('example.com')
    port = ConfigValue(1234)


class AccountConfig(Config):
    username = ConfigValue('test')
    password = ConfigValue('test123!')
    server: ServerConfig = ServerConfig()


class RecursiveConfig(Config):
    data_dir: str = '.'
    account: AccountConfig = AccountConfig()


class GameConfig(Config):
    """Pretend game configuration."""

    character_name = ConfigValue(None, type_=Optional[str])
    server: ServerConfig = ServerConfig()


def test_init():
    c: Config = Config()
    assert c.dump() == {}
    assert c.__config_subsections__ == {}
    assert c.__config_values__ == {}


def test_dump():
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
    c = RecursiveConfig()
    d: Dict[str, Any] = c.dump()
    assert d['account']['server'] == ServerConfig().dump()
    c.populate_from_dict(d)
    assert c.dump() == d
