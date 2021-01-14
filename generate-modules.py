"""Generates the earwax.cmd.subcommands.gui.keys module."""

from inspect import isclass
from pathlib import Path
from typing import Any, List

import wx
from jinja2 import Environment, Template
from pyglet.window import key, mouse
from synthizer import GlobalFdnReverb, Context, initialized

from earwax import hat_directions as _hat_directions

keys_code: str = '''"""Provides keys for templates."""

from typing import List

# Modifiers:

modifiers: List[str] = [{% for modifier in modifiers %}
    '{{ modifier }}',{% endfor %}
]

# Keys:

keys: List[str] = [{% for key in keys %}
    '{{ key }}',{% endfor %}
]

# Mouse buttons:

mouse_buttons: List[str] = [{% for button in mouse_buttons %}
    '{{ button }}',{% endfor %}
]

# Hat directions:

hat_directions: List[str] = [{% for direction in hat_directions %}
    '{{ direction }}',{% endfor %}
]

'''

hat_directions: List[str] = [x for x in dir(_hat_directions) if x.isupper()]

keys: List[str] = []
modifiers: List[str] = []
mouse_buttons: List[str] = sorted(x for x in dir(mouse) if x.isupper())

wx_code: str = '''"""Provides a pretend WX module."""

'''

wx_lines: List[str] = []


def get_keys() -> None:
    """Build the keys and modifiers lists."""
    x: str
    for x in sorted(dir(key)):
        if x.isupper():
            if x.startswith('MOD_'):
                modifiers.append(x)
            else:
                keys.append(x)


def make_keys_module() -> None:
    """Build the module."""
    filename: Path = Path.cwd() / 'earwax/cmd/keys.py'
    e: Environment = Environment()
    t: Template = e.from_string(keys_code)
    rendered: str = t.render(
        keys=keys, modifiers=modifiers, hat_directions=hat_directions,
        mouse_buttons=mouse_buttons
    )
    with filename.open('w') as f:
        f.write(rendered)
    print('Modifiers: %d' % len(modifiers))
    print('Keys: %d' % len(keys))
    print('Hat Directions: %d' % len(hat_directions))


def get_wx_lines() -> None:
    """Get all the wx lines."""
    x: str
    for x in dir(wx):
        value: Any = getattr(wx, x)
        value_str: str
        if x.startswith('_'):
            continue
        elif isclass(value):
            value_str = 'object'
        elif isinstance(value, int):
            value_str = str(value)
        elif isinstance(value, (str, bytes)):
            value_str = repr(value)
        elif isinstance(value, wx.PyEventBinder):
            value_str = 'object()'
        else:
            print(f'Skipping {x} = {value!r}')
            continue
        wx_lines.append(f'{x} = {value_str}')
    print('Pretend wx attributes: %d' % len(wx_lines))


def make_wx_module() -> None:
    """Make a pretend wx module."""
    filename: Path = Path.cwd() / 'earwax/cmd/subcommands/gui/pretend_wx.py'
    with filename.open('w') as f:
        f.write(wx_code + '\n'.join(wx_lines) + '\n')


def make_reverb_module() -> None:
    """Make a typed reverb module."""
    code: str = '"""Provides the Reverb class."""\n\nfrom attr import attrs\n'
    code += '\n\n@attrs(auto_attribs=True)\nclass Reverb:\n'
    code += '    """A reverb class with type hints.\n\n    '
    code += 'This module is automatically generated.\n    """\n\n'
    with initialized():
        c: Context = Context()
        r: GlobalFdnReverb = GlobalFdnReverb(c)
        name: str
        value: Any
        for name in dir(r):
            value = getattr(r, name)
            if isinstance(value, float):
                code += f'    {name}: float = {value}\n'
        r.destroy()
    with Path('earwax/reverb.py').open('w') as f:
        f.write(code)


if __name__ == '__main__':
    get_keys()
    make_keys_module()
    get_wx_lines()
    make_wx_module()
    make_reverb_module()
