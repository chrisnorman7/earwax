"""Provides the ReverbEditor class."""

from enum import Enum
from typing import Callable, Generator, List, Optional

from attr import Factory, attrib, attrs

from ..editor import Editor
from ..pyglet import key
from ..reverb import Reverb
from .menu import Menu, MenuItem

try:
    from synthizer import GlobalFdnReverb
except ModuleNotFoundError:
    GlobalFdnReverb = object


class ValueAdjustments(Enum):
    """Possible value adjustments for menu actions."""

    default = 0
    decrement = 1
    increment = 2


@attrs(auto_attribs=True)
class ReverbSetting:
    """A setting for reverb."""

    name: str
    description: str
    min: float
    max: float
    default: float
    increment: float = 0.05


reverb_settings: List[ReverbSetting] = [
    ReverbSetting(
        'mean_free_path', 'The mean free path of the simulated environment',
        min=0.0, max=0.5, default=0.02,
    ),
    ReverbSetting(
        't60', 'The T60 of the reverb',
        min=0.0, max=100.0, default=1.0, increment=5.0
    ),
    ReverbSetting(
        'late_reflections_lf_rolloff', 'A multiplicative factor on T60 for '
        'the low frequency band',
        min=0.0, max=2.0, default=1.0
    ),
    ReverbSetting(
        'late_reflections_lf_reference', 'Where the low band of the feedback '
        'equalizer ends',
        min=0.0, max=22050.0, default=200.0, increment=500.0
    ),
    ReverbSetting(
        'late_reflections_hf_rolloff', 'A multiplicative factor on T60 for '
        'the high frequency band',
        min=0.0, max=2.0, default=0.5
    ),
    ReverbSetting(
        'late_reflections_hf_reference', 'Where the high band of the '
        'equalizer starts',
        min=0.0, max=22050.0, default=500.0, increment=500.0
    ),
    ReverbSetting(
        'late_reflections_diffusion', 'Controls the diffusion of the late '
        'reflections as a percent',
        min=0.0, max=1.0, default=1.0
    ),
    ReverbSetting(
        'late_reflections_modulation_depth', 'The depth of the modulation of '
        'the delay lines on the feedback path in seconds',
        min=0.0, max=0.3, default=0.01
    ),
    ReverbSetting(
        'late_reflections_modulation_frequency', 'The frequency of the '
        'modulation of the delay lines in the feedback paths',
        min=0.01, max=100.0, default=0.5, increment=5.0
    ),
    ReverbSetting(
        'late_reflections_delay', 'The delay of the late reflections relative '
        'to the input in seconds',
        min=0.0, max=0.5, default=0.01
    ),
    ReverbSetting(
        'gain', 'The volume of the reverb',
        min=0.0, max=1.0, default=1.0
    ),
]


@attrs(auto_attribs=True)
class ReverbEditor(Menu):
    """A menu for editing reverbs."""

    reverb: GlobalFdnReverb = attrib()

    @reverb.default
    def get_default_reverb(instance: 'ReverbEditor') -> GlobalFdnReverb:
        """Raise an error."""
        raise RuntimeError('You must supply a reverb.')

    settings: Reverb = attrib()

    @settings.default
    def get_default_settings(instance: 'ReverbEditor') -> Reverb:
        """Raise an error."""
        raise RuntimeError('You must provide a settings object.')

    setting_items: List[MenuItem] = Factory(list)

    def __attrs_post_init__(self) -> None:
        """Add actions and items."""
        setting: ReverbSetting
        for setting in reverb_settings:
            value: float = getattr(self.settings, setting.name)
            item: MenuItem = self.add_item(
                self.edit_value(setting, value),
                title=f'{setting.description} ({value})'
            )
            self.setting_items.append(item)
        self.action(
            'Restore setting to default', symbol=key.BACKSPACE,
            joystick_button=3
        )(self.adjust_value(ValueAdjustments.default))
        self.action(
            'Increment setting value', symbol=key.RIGHT, joystick_button=1
        )(self.adjust_value(ValueAdjustments.increment))
        self.action(
            'Decrement setting value', symbol=key.LEFT, joystick_button=2
        )(self.adjust_value(ValueAdjustments.decrement))
        return super().__attrs_post_init__()

    def reset(self) -> None:
        """Reload this menu."""
        self.game.pop_level()
        m: ReverbEditor = ReverbEditor(  # type: ignore[misc]
            self.game, self.title,  # type: ignore[arg-type]
            reverb=self.reverb, settings=self.settings,
            dismissible=self.dismissible, position=self.position
        )
        item: MenuItem
        for item in self.items:
            if item not in self.setting_items:
                m.items.append(item)
        self.game.push_level(m)

    def set_value(self, setting: ReverbSetting, value: float) -> None:
        """Set the value."""
        if setting.min is not None and value < setting.min:
            value = setting.min
        if setting.max is not None and value > setting.max:
            value = setting.max
        setattr(self.reverb, setting.name, value)
        setattr(self.settings, setting.name, value)
        self.reset()

    def edit_value(
        self, setting: ReverbSetting, value: float
    ) -> Callable[[], Generator[None, None, None]]:
        """Edit the given value."""

        def inner() -> Generator[None, None, None]:
            e: Editor = Editor(self.game, text=str(value))

            @e.event
            def on_submit(text: float) -> None:
                value: float
                try:
                    value = float(text)
                except ValueError:
                    self.game.pop_level()
                    return self.game.output(f'Invalid value: {text}.')
                else:
                    self.game.pop_level()
                    self.set_value(setting, value)

            self.game.output(
                f'Enter a value between {setting.min} and {setting.max}: '
                f'{value}'
            )
            yield
            self.game.push_level(e)

        return inner

    def adjust_value(self, amount: ValueAdjustments) -> Callable[[], None]:
        """Restore the current menu item to the default."""

        def inner() -> None:
            item: Optional[MenuItem] = self.current_item
            if item in self.setting_items:
                index: int = self.setting_items.index(item)
                setting: ReverbSetting = reverb_settings[index]
                value: float = getattr(self.settings, setting.name)
                if amount is ValueAdjustments.default:
                    self.set_value(setting, setting.default)
                elif amount is ValueAdjustments.increment:
                    self.set_value(setting, value + setting.increment)
                elif amount is ValueAdjustments.decrement:
                    self.set_value(setting, value - setting.increment)
                else:
                    raise RuntimeError(f'Invalid adjustment: {amount!r}.')

        return inner
