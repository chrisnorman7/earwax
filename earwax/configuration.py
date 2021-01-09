"""Provides the Config class."""

from pathlib import Path
from typing import Optional

from .config import Config, ConfigValue


def dump_path(value: Optional[Path]) -> Optional[str]:
    """Return a path as a string.

    :param value: The path to convert.
    """
    if value is not None:
        return str(value)
    return None


def load_path(value: Optional[str]) -> Optional[Path]:
    """Load a path from a string.

    :param value: The string to convert to a path.
    """
    if value is not None:
        return Path(value)
    return None


class MenuConfig(Config):
    """The menu configuration section.

    :ivar ~earwax.configuration.default_item_select_sound: The default sound to
        play when a menu item is selected.

        If this value is ``None``, no sound will be played, unless specified by
        the selected menu item.

    :ivar ~earwax.configuration.default_item_activate_sound: The default sound
        to play when a menu item is activated.

        If this value is ``None``, no sound will be played, unless specified by
        the activated menu item.
    """

    __section_name__ = 'Menus'
    default_item_select_sound: ConfigValue[Optional[Path]] = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when moving through menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_select_sound.dump(dump_path)
    default_item_select_sound.load(load_path)

    default_item_activate_sound: ConfigValue[Optional[Path]] = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when activating items in menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_activate_sound.dump(dump_path)
    default_item_activate_sound.load(load_path)


class SpeechConfig(Config):
    """The speech configuration section.

    :ivar ~earwax.configuration.speak: Whether or not calls to
        :meth:`~earwax.Game.output` will produce speech.

    :ivar ~earwax.configuration.braille: Whether or not calls to
        :meth:`~earwax.Game.output` will produce braille.
    """

    __section_name__ = 'Speech and Braille'
    speak: ConfigValue[bool] = ConfigValue(True, name='Speech')
    braille: ConfigValue[bool] = ConfigValue(True, name='Braille')


class SoundConfig(Config):
    """Configure various aspects of the sound system.

    :ivar ~earwax.configuration.master_volume: The volume of
        :attr:`~earwax.Game.audio_context`.

        This value acts as a master volume, and should be changed with either
        :meth:`~earwax.Game.adjust_volume`, or :meth:`~earwax.Game.set_volume`.

    :ivar ~earwax.configuration.max_volume: The maximum volume allowed by
        :meth:`~earwax.Game.adjust_volume`.

    :ivar ~earwax.configuration.sound_volume: The volume of general sounds.

        This volume is used by earwax to set the volume of
        :attr:`~earwax.Game.interface_sound_manager` values.

    :ivar ~earwax.configuration.music_volume: The volume of game music.

        Earwax uses this value to set the volume of the
        :attr:`~earwax.Game.music_sound_manager` sound manager.

    :ivar ~earwax.configuration.ambiance_volume: The volume of game ambiances.

        Earwax uses this value to set the volume of the
        :attr:`~earwax.Game.ambiance_sound_manager` sound manager.

    :ivar ~earwax.configuration.default_cache_size: The default size (in bytes)
        for the default :attr:`~earwax.Game.buffer_cache` object.
    """

    __section_name__ = 'Sound'
    master_volume: ConfigValue[float] = ConfigValue(1.0, name='Master volume')
    max_volume: ConfigValue[float] = ConfigValue(1.0, name='Maximum volume')
    sound_volume: ConfigValue[float] = ConfigValue(0.5, name='Sound volume')
    music_volume: ConfigValue[float] = ConfigValue(0.4, name='Music volume')
    ambiance_volume: ConfigValue[float] = ConfigValue(
        0.4, name='Ambiance volume'
    )
    default_cache_size: ConfigValue[int] = ConfigValue(
        1024 ** 2 * 500, name='The size of the default sound cache in bytes'
    )


class EditorConfig(Config):
    """Configure various things about editors.

    :ivar ~earwax.configuration.hat_alphabet: The letters that can be entered
        by a controller's hat.
    """

    __section_name__ = 'Editors'
    hat_alphabet: ConfigValue = ConfigValue(
        ' abcdefghijklmnopqrstuvwxyz.,1234567890@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        '-#[]{}', name='Hat alphabet'
    )


class EarwaxConfig(Config):
    """The main earwax configuration.

    An instance of this value will be loaded to :attr:`earwax.Game.config`.

    It is advised to configure the game before calling :meth:`earwax.Game.run`.
    """

    __section_name__ = 'Earwax Configuration'
    menus: MenuConfig = MenuConfig()
    speech: SpeechConfig = SpeechConfig()
    sound: SoundConfig = SoundConfig()
    editors: EditorConfig = EditorConfig()
