"""Test the Reverb class."""

from time import sleep

from synthizer import Context, GlobalFdnReverb

from earwax import Reverb


def test_init() -> None:
    """Test initialisation."""
    r: Reverb = Reverb(gain=0.5)
    assert r.gain == 0.5
    assert r.t60 == 1.0


def test_make_reverb(context: Context) -> None:
    """Test that we can create a reverb from the Reverb class."""
    r: Reverb = Reverb(t60=0.2, gain=0.5)
    gr: GlobalFdnReverb = r.make_reverb(context)
    sleep(0.2)
    assert gr.gain == 0.5
    assert gr.t60 == 0.2
    assert isinstance(gr, GlobalFdnReverb)
