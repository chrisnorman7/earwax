"""Generates the earwax.cmd.subcommands.gui.keys module."""

from typing import List
from jinja2 import Environment, Template
from pathlib import Path
from earwax import hat_directions as _hat_directions
from pyglet.window import key

code: str = '''"""Provides keys for templates."""

from typing import List

# Modifiers:

modifiers: List[str] = [{% for modifier in modifiers %}
    '{{ modifier }}',{% endfor %}
]

# Keys:

keys: List[str] = [{% for key in keys %}
    '{{ key }}',{% endfor %}
]

# Hat directions:

hat_directions: List[str] = [{% for direction in hat_directions %}
    '{{ direction }}',{% endfor %}
]

'''

hat_directions: List[str] = [x for x in dir(_hat_directions) if x.isupper()]

keys: List[str] = []
modifiers: List[str] = []


def get_keys() -> None:
    """Build the keys and modifiers lists."""
    x: str
    for x in sorted(dir(key)):
        if x.isupper():
            if x.startswith('MOD_'):
                modifiers.append(x)
            else:
                keys.append(x)


def make_module() -> None:
    """Build the module."""
    filename: Path = Path.cwd() / 'earwax/cmd/subcommands/gui/keys.py'
    e: Environment = Environment()
    t: Template = e.from_string(code)
    rendered: str = t.render(
        keys=keys, modifiers=modifiers, hat_directions=hat_directions
    )
    with filename.open('w') as f:
        f.write(rendered)
    print('Modifiers: %d' % len(modifiers))
    print('Keys: %d' % len(keys))
    print('Hat Directions: %d' % len(hat_directions))


if __name__ == '__main__':
    get_keys()
    make_module()
