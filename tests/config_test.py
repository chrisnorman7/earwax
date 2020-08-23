from pathlib import Path
from typing import Any, Dict, Optional

from earwax import Config, ConfigValue
from yaml import load, FullLoader, dump


class ServerConfig(Config):
    """Pretend server information."""

    hostname = ConfigValue('example.com')
    port = ConfigValue(1234)


class AccountConfig(Config):
    username = ConfigValue('test')
    password = ConfigValue('test123!')
    server: ServerConfig = ServerConfig()


class RecursiveConfig(Config):
    data_dir = ConfigValue('.')
    account: AccountConfig = AccountConfig()


class GameConfig(Config):
    """Pretend game configuration."""

    character_name = ConfigValue(None, type_=Optional[str])
    server: ServerConfig = ServerConfig()


def test_init() -> None:
    c: Config = Config()
    assert c.dump() == {}
    assert c.__config_subsections__ == {}
    assert c.__config_values__ == {}


def test_dump() -> None:
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


def test_set_value() -> None:
    c = ServerConfig()
    c.hostname.value = 'microsoft.com'
    c.port.value = 8080
    assert c.dump() == {
        'hostname': 'microsoft.com',
        'port': 8080
    }


def test_populate_from_dict() -> None:
    s = ServerConfig()
    s.populate_from_dict({'hostname': 'google.com', 'port': 9000})
    assert s.hostname.value == 'google.com'
    assert s.port.value == 9000


def test_save() -> None:
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
