"""Provides various type classes used by Earwax."""

from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List,
                    Optional, Tuple)

from .promises.staggered_promise import (StaggeredPromiseFunctionType,
                                         StaggeredPromiseGeneratorType)
from .promises.threaded_promise import ThreadedPromiseFunctionType

if TYPE_CHECKING:
    from .action import Action

NoneGenerator = Generator[None, None, None]
OptionalGenerator = Optional[NoneGenerator]
ActionFunctionType = Callable[[], OptionalGenerator]
HatDirection = Tuple[int, int]
ActionListType = List['Action']
ReleaseGeneratorDictType = Dict[int, NoneGenerator]
JoyButtonReleaseGeneratorDictType = Dict[Tuple[str, int], NoneGenerator]
MotionFunctionType = Callable[[], None]
MotionsType = Dict[int, MotionFunctionType]
StaggeredPromiseFunctionType = StaggeredPromiseFunctionType
StaggeredPromiseGeneratorType = StaggeredPromiseGeneratorType
ThreadedPromiseFunctionType = ThreadedPromiseFunctionType
EventType = Callable[..., Any]
