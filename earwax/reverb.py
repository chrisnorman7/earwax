"""Reverb module."""

from attr import attrs

try:
    from synthizer import Context, GlobalFdnReverb
except ModuleNotFoundError:
    Context, GlobalFdnReverb = (object, object)


@attrs(auto_attribs=True)
class Reverb:
    """A reverb preset.

    This class can be used to make reverb presets, which you can then upgrade
    to full reverbs by way of the :meth:`~earwax.Reverb.make_reverb` method.
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

    def make_reverb(self, context: Context) -> GlobalFdnReverb:
        """Return a synthizer reverb built from this object.

        All the settings contained by this object will be present on the new
        reverb.

        :param context: The synthizer context to use.
        """
        r: GlobalFdnReverb = GlobalFdnReverb(context)
        r.gain = self.gain  # noqa: E501
        r.late_reflections_delay = self.late_reflections_delay  # noqa: E501
        r.late_reflections_diffusion = self.late_reflections_diffusion  # noqa: E501
        r.late_reflections_hf_reference = self.late_reflections_hf_reference  # noqa: E501
        r.late_reflections_hf_rolloff = self.late_reflections_hf_rolloff  # noqa: E501
        r.late_reflections_lf_reference = self.late_reflections_lf_reference  # noqa: E501
        r.late_reflections_lf_rolloff = self.late_reflections_lf_rolloff  # noqa: E501
        r.late_reflections_modulation_depth = self.late_reflections_modulation_depth  # noqa: E501
        r.late_reflections_modulation_frequency = self.late_reflections_modulation_frequency  # noqa: E501
        r.mean_free_path = self.mean_free_path  # noqa: E501
        r.t60 = self.t60  # noqa: E501
        return r
