"""Provides the Reverb class."""

from attr import attrs


@attrs(auto_attribs=True)
class Reverb:
    """A reverb class with type hints.

    This module is automatically generated.
    """

    gain: float = 1.0
    late_reflections_delay: float = 0.01
    late_reflections_diffusion: float = 1.0
    late_reflections_hf_reference: float = 500.0
    late_reflections_hf_rolloff: float = 0.5
    late_reflections_lf_reference: float = 200.0
    late_reflections_lf_rolloff: float = 1.0
    late_reflections_modulation_depth: float = 0.01
    late_reflections_modulation_frequency: float = 0.5
    mean_free_path: float = 0.02
    t60: float = 1.0
