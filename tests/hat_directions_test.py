from earwax.hat_directions import DEFAULT, DOWN, LEFT, RIGHT, UP


def test_default() -> None:
    assert DEFAULT == (0, 0)


def test_up() -> None:
    assert UP == (0, 1)


def test_down() -> None:
    assert DOWN == (0, -1)


def test_left() -> None:
    assert LEFT == (-1, 0)


def test_right() -> None:
    assert RIGHT == (1, 0)
