"""Provides various mixin classes for used with other objects."""

from datetime import datetime
from inspect import isclass
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type,
                    get_args, get_origin)

from attr import attrs
from typing_inspect import is_union_type

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object

if TYPE_CHECKING:
    from .game import Game
    from .types import EventType


@attrs(auto_attribs=True)
class DismissibleMixin:
    """Make any :class:`Level` subclass dismissible.

    :ivar ~earwax.mixins.DismissibleMixin.dismissible: Whether or not it should
        be possible to dismiss this level.
    """

    dismissible: bool = True

    def dismiss(self) -> None:
        """Dismiss the currently active level.

        By default, when used by :class:`earwax.Menu` and
        :class:`earwax.Editor`, this method is called when the escape key is
        pressed, and only if :attr:`self.dismissible
        <earwax.level.DismissibleMixin.dismissible>` evaluates to ``True``.

        The default implementation simply calls :meth:`~earwax.Game.pop_level`
        on the attached :class:`earwax.Game` instance, and announces the
        cancellation.
        """
        if self.dismissible:
            self.game: 'Game'
            self.game.pop_level()
            self.game.output('Cancel.')


@attrs(auto_attribs=True)
class TitleMixin:
    """Add a title to any :class:`Level` subclass.

    :ivar ~earwax.level.TitleMixin.title: The title of this instance.
    """

    title: str


@attrs(auto_attribs=True)
class CoordinatesMixin:
    """Add 3d coordinates to any object."""

    x: float
    y: float
    z: float

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        """Return ``self.x``, ``self.y``, and ``self.z`` as a tuple."""
        return self.x, self.y, self.z


class RegisterEventMixin(EventDispatcher):
    """Allow registering and binding events in one function."""

    def register_event(self, func: 'EventType') -> str:
        """Register an event type from a function.

        This function uses ``func.__name__`` to register an event type,
        eliminating possible typos in event names.

        :param func: The function whose name will be used.
        """
        return self.register_event_type(func.__name__)

    def register_and_bind(self, func: 'EventType') -> 'EventType':
        """Register and bind a new event.

        This is the same as::

            level.register_event_type('f')

            @level.event
            def f() -> None:
                pass

        :param func: The function whose name will be registered, and which will
            be bound to this instance.
        """
        self.register_event(func)
        return self.event(func)


class DumpLoadMixin:
    """A mixin that allows any object to be dumped to and loaded from a dict.

    It is worth noting that only instance variables which have type hints (and
    thus end up in the ``__annotations__` dictionary) will be dumped and
    loaded.

    To dump an instance, use the :meth:`~earwax.mixins.DumpLoadMixin.dump`
    method, and to load, use the :meth:`~earwax.mixins.DumpLoadMixin.load`
    constructor.

    The ``__allowed_basic_types__`` list holds all the types which will be
    dumped without any modification.

    By default, the only collection types that are allowed are ``list``, and
    ``dict``.
    """

    __allowed_basic_types__: List[Type] = [
        str, int, float, bool, datetime, type(None)
    ]
    __type_key__: str = '__type__'
    __value_key__: str = '__value__'

    def _get_dump_value(self, type_: Type, value: Any) -> Any:
        """Get a value for dumping.

        :param value: The value that is present on the instance.
        """
        cls: Type[DumpLoadMixin] = type(self)
        value_type: Type = type(value)
        if value_type in self.__allowed_basic_types__:
            return value
        elif isclass(value_type) and issubclass(value_type, DumpLoadMixin):
            assert isinstance(value, DumpLoadMixin)
            return value.dump()
        elif isinstance(value, list):
            entry_type: Type = get_args(type_)[0]
            if entry_type in cls.__allowed_basic_types__:
                return value
            elif issubclass(entry_type, DumpLoadMixin):
                entry: DumpLoadMixin
                return [entry.dump() for entry in value]
        elif isinstance(value, dict):
            key_type: Type
            key_type, value_type = get_args(type_)
            # If the ``value_type`` is ``None`` when dumping is performed, the
            # type of the value will be used to dump the object. Otherwise,
            # this object will be the dumping object.
            value_dump_object: Optional[DumpLoadMixin] = None
            if issubclass(key_type, DumpLoadMixin):
                raise RuntimeError(
                    f'You cannot use {key_type!r} as a dictionary key, as '
                    'dumping would result in a dictionary being used as a '
                    'dictionary key, which Python does not allow.'
                    )
            if not issubclass(value_type, DumpLoadMixin):
                value_dump_object = self
            return_value: Dict[Any, Any] = {}
            for k, v in value.items():
                dump_object: DumpLoadMixin
                if value_dump_object is None:
                    dump_object = v
                else:
                    dump_object = self
                return_value[
                    self._get_dump_value(key_type, k)
                ] = dump_object._get_dump_value(value_type, v)
            return return_value
        else:
            raise RuntimeError(
                'Unable to dump value %r of type %r.' % (value, type_)
            )

    def dump(self) -> Dict[str, Any]:
        """Dump this instance as a dictionary."""
        cls: Type[DumpLoadMixin] = type(self)
        dump_value: Dict[str, Any] = {
            name: self._get_dump_value(type_, getattr(self, name))
            for name, type_ in cls.__annotations__.items()
        }
        return {cls.__type_key__: cls.__name__, cls.__value_key__: dump_value}

    @classmethod
    def _get_load_value(cls, expected_type: Type, value: Any) -> Any:
        """Return a loaded value.

        In the event that the dumped value represents a instance of
        :class:`earwax.mixins.DumpLoadValue`, the dictionary must have been
        returned by :meth:`earwax.mixins.DumpLoadMixin.dump`, so it contains
        both the dumped value, and the type annotation.

        This prevents errors with Union types representing multiple subclasses.

        If the type of the provided value is found in the
        :attr:`~earwax.mixins.DumpLoadMixin.__allowed_basic_types__` list, it
        will be returned as-is.

        If the type of the provided value is ``list``, then each element will
        be passed through this method and a list of the loaded values returned.

        If the type of the value is ``dict``, one of two things will occur:

        * If ``expected_type``

        :param value: The raw value to load.
        """
        type_: Type = type(value)
        origin: Optional[Type] = get_origin(expected_type)
        if type_ in cls.__allowed_basic_types__:
            return value
        elif type_ is list:
            entry_type: Type[Any] = get_args(expected_type)[0]
            if entry_type in cls.__allowed_basic_types__:
                return value
            elif issubclass(entry_type, DumpLoadMixin):
                return [entry_type.load(entry) for entry in value]
            return [entry_type.load(entry) for entry in value]
        elif isinstance(value, dict):
            if isclass(expected_type) and issubclass(
                expected_type, DumpLoadMixin
            ):
                return expected_type.load(value)
            elif origin is dict:
                key_type: Type
                value_type: Type
                key_type, value_type = get_args(expected_type)
                return {
                    cls._get_load_value(key_type, k): cls._get_load_value(
                        value_type, v
                    ) for k, v in value.items()
                }
            elif is_union_type(expected_type):
                type_name: Optional[str] = value.get(cls.__type_key__, None)
                t: Type[DumpLoadMixin]
                for t in get_args(expected_type):
                    if type_name == t.__name__:
                        return t._get_load_value(t, value)
                else:
                    raise RuntimeError(
                        'unable to load a union value without a type hint.'
                    )
            else:
                print(origin)

    @classmethod
    def load(cls, data: Dict[str, Any]) -> Any:
        """Load and return an instance from the provided data.

        It is worth noting that only keys that are also found in the
        ``__annotations__`` dictionary will be loaded. All others are ignored.

        :param data: The data to load from.
        """
        type_name: Optional[str] = data.get(cls.__type_key__, None)
        if type_name is None or type_name != cls.__name__:
            raise RuntimeError(
                'The provided value does ot appear to be a dump of %r: %r.' % (
                    cls, data
                )
            )
        data = data.get(cls.__value_key__, {})
        kwargs: Dict[str, Any] = {
            name: cls._get_load_value(type_, data[name])
            for name, type_ in cls.__annotations__.items()
        }
        return cls(**kwargs)  # type: ignore[call-arg]
