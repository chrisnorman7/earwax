"""Test the Track class."""

from synthizer import StreamingGenerator

from earwax import Sound, SoundManager, Track, TrackTypes


def test_init() -> None:
    """Test initialisation."""
    t: Track = Track('file', 'sound.wav', TrackTypes.music)
    assert t.protocol == 'file'
    assert t.path == 'sound.wav'
    assert t.track_type is TrackTypes.music
    assert t.sound_manager is None
    assert t.sound is None
    t = Track('file', 'sound.wav', TrackTypes.ambiance)
    assert t.protocol == 'file'
    assert t.path == 'sound.wav'
    assert t.track_type is TrackTypes.ambiance
    assert t.sound_manager is None
    assert t.sound is None


def test_play(sound_manager: SoundManager, track: Track) -> None:
    """Test playing a track."""
    assert isinstance(track, Track)
    assert track.track_type is TrackTypes.ambiance
    track.play(sound_manager)
    assert track.sound_manager is sound_manager
    assert isinstance(track.sound, Sound)
    assert isinstance(track.sound.generator, StreamingGenerator)
    assert track.sound.generator.position == 0.0


def test_stop(track: Track, sound_manager: SoundManager) -> None:
    """Make sure we can stop the sound."""
    track.stop()
    assert track.sound is None
    assert track.sound_manager is None
    track.play(sound_manager)
    track.stop()
    assert track.sound is None
    assert track.sound_manager is None
