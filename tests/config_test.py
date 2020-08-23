from typing import Any, Dict, Optional

from attr import attrs

from earwax import Config


@attrs(auto_attribs=True)
class ServerConfig(Config):
    """Pretend server information."""

    hostname: str = 'example.com'
    port: int = 1234


@attrs(auto_attribs=True)
class AccountConfig(Config):
    username: str = 'test'
    password: str = 'test123!'
    server: ServerConfig = ServerConfig()


@attrs(auto_attribs=True)
class RecursiveConfig(Config):
    data_dir: str = '.'
    account: AccountConfig = AccountConfig()


@attrs(auto_attribs=True)
class GameConfig(Config):
    """Pretend game configuration."""

    character_name: Optional[str] = None
    server: ServerConfig = ServerConfig()


def test_init():
    c = Config()
    assert c.dump() == {}
    assert len(c.__attrs_attrs__) == 0


def test_dump():
    c: GameConfig = GameConfig()
    d: Dict[str, Any] = c.dump()
    assert d['server'] == c.server.dump()
    assert d == {
        'character_name': None,
        'server': {'hostname': 'example.com', 'port': 1234}
    }
    assert GameConfig.from_dict(d) == c


def test_recursive_dump() -> None:
    c = RecursiveConfig()
    d: Dict[str, Any] = c.dump()
    assert d['account']['server'] == ServerConfig().dump()
    assert RecursiveConfig.from_dict(d) == c
