"""Makes the importing of yaml easier on systems that don't support CDumper."""

from typing import List

from yaml import dump, load

try:
    from yaml import CDumper, CLoader
except ImportError:
    from yaml import Dumper as CDumper  # type: ignore[misc]
    from yaml import FullLoader as CLoader  # type: ignore[misc]

__all__: List[str] = ['dump', 'load', 'CDumper', 'CLoader']
