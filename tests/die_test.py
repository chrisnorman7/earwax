from pytest import raises

from earwax import Die


class OnRollWorks(Exception):
    pass


def test_init() -> None:
    d: Die = Die()
    assert d.sides == 6
    d = Die(4)
    assert d.sides == 4


def test_roll() -> None:
    d: Die = Die()
    assert isinstance(d.roll(), int)


def test_on_roll() -> None:
    d: Die = Die()

    @d.event
    def on_roll(value: int) -> None:
        raise OnRollWorks(value)

    with raises(OnRollWorks) as exc:
        d.roll()
    assert isinstance(exc.value.args[0], int)
