"""Provides the ConfigMenu class,."""

from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, Tuple

from attr import Factory, attrib, attrs
from typing_inspect import get_args, is_union_type

from ..action import OptionalGenerator
from ..config import Config, ConfigValue
from ..editor import Editor
from ..speech import tts
from .file_menu import FileMenu
from .menu import Menu

TypeHandlerFunc = Callable[[ConfigValue], OptionalGenerator]
TitleFunc = Callable[[ConfigValue, str], str]


class UnknownTypeError(Exception):
    """An exception which will be thrown if a :class:`~earwax.ConfigMenu`
    instance doesn't know how to handle the given type."""


@attrs(auto_attribs=True)
class TypeHandler:
    """A type handler for use with :class:`~earwax.ConfigMenu` instances.

    :ivar ~earwax.TypeHandler.title: A function that will
        return a string which can be used as the title for the menu item
        generated by this handler.

    :ivar ~earwax.TypeHandler.func: The function that will be
        called when this handler is required.
    """

    title: TitleFunc
    func: TypeHandlerFunc


@attrs(auto_attribs=True)
class ConfigMenu(Menu):
    """A menu that allows the user to set values on configuration sections.

    If an option is present with a type the menu doesn't know how to handle,
    :class:`earwax.UnknownTypeError` will be raised.

    :ivar ~ConfigMenu.config: The configuration section this menu will
        configure.

    :ivar ~earwax.ConfigMenu.type_handlers: Functions to handle the types this
        menu knows about.

        New types can be handled with the
        :meth:`~earwax.ConfigMenu.type_handler` method.
    """

    config: Config = attrib()

    @config.default
    def earwax_config(instance: 'ConfigMenu') -> Config:
        return instance.game.config

    type_handlers: Dict[object, TypeHandler] = attrib(
        default=Factory(dict), init=False
    )

    def __attrs_post_init__(self) -> None:
        """Add default type handlers, and populate the menu."""
        super().__attrs_post_init__()
        # Here we iterate over all members of the object, and pull the correct
        # sections and values from the appropriate dictionaries.
        name: str
        subsection: Config
        value: ConfigValue
        cls: object = type(self.config)
        for name in cls.__dict__:
            if name in self.config.__config_subsections__:
                subsection = self.config.__config_subsections__[name]
                name = self.get_subsection_name(subsection, name)
                self.item(f'{name}...')(self.subsection_menu(subsection, name))
            elif name in self.config.__config_values__:
                value = self.config.__config_values__[name]
                name = self.get_option_name(value, name)
                self.add_item(name, self.option_menu(value, name))
        # Now, let's add us some type handlers.
        self.type_handler(
            bool, lambda o, n: 'Disable' if o.value else 'Enable'
        )(self.handle_bool)
        self.type_handler(type(None), lambda option, name: 'Clear Value')(
            self.clear_value
        )
        self.type_handler(str, lambda option, name: 'Enter String')(
            self.handle_string
        )
        self.type_handler(int, lambda option, name: 'Enter Integer')(
            self.handle_int
        )
        self.type_handler(float, lambda option, name: 'Enter Float')(
            self.handle_float
        )
        self.type_handler(Path, lambda option, name: 'Select a path')(
            self.handle_path
        )

    def handle_bool(self, option: ConfigValue) -> None:
        """Toggle a boolean value.

        Used by the default :class:`~earwax.TypeHandler` that
        handles boolean values.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.
        """
        option.value = not option.value
        tts.speak('Enabled' if option.value else 'Disabled')
        self.game.pop_level()

    def clear_value(self, option: ConfigValue) -> None:
        """Sets ``option.value`` to ``None``.

        Used by the default :class:`~earwax.TypeHandler` that
        handles nullable values.

        :param option: The :class:`~earwax.ConfigValue` instance whose value
            should be set to ``None``.
        """
        option.value = None
        tts.speak('Cleared.')
        self.game.pop_level()

    def handle_string(self, option: ConfigValue) -> Generator[
        None, None, None
    ]:
        """Allow editing strings.

        Used by the default :class:`~earwax.TypeHandler` that
        handles string values.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.
        """

        def inner(value: str):
            """Set the option value."""
            self.set_value(option, value)()
            self.game.pop_level()

        yield
        tts.speak(f'Enter value: {option.value}')
        self.game.push_level(Editor(self.game, inner, text=option.value or ''))

    def handle_int(self, option: ConfigValue) -> Generator[
        None, None, None
    ]:
        """Allow editing integers.

        Used by the default :class:`~earwax.TypeHandler` that
        handles integer values.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.
        """

        def inner(value: str):
            """Set the option value."""
            if not value:
                value = '0'
            try:
                self.set_value(option, int(value))()
            except ValueError:
                tts.speak('You must enter a number.')
            finally:
                self.game.pop_level()

        yield
        tts.speak(f'Enter value: {option.value}')
        self.game.push_level(
            Editor(self.game, inner, text=str(option.value) or '')
        )

    def handle_float(self, option: ConfigValue) -> Generator[
        None, None, None
    ]:
        """Allow editing floats.

        Used by the default :class:`~earwax.TypeHandler` that
        handles float values.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.
        """

        def inner(value: str):
            """Set the option value."""
            if not value:
                value = '0.0'
            try:
                self.set_value(option, float(value))()
            except ValueError:
                tts.speak('You must enter a number.')
            finally:
                self.game.pop_level()

        yield
        tts.speak(f'Enter value: {option.value}')
        self.game.push_level(
            Editor(self.game, inner, text=str(option.value) or '')
        )

    def handle_path(self, option: ConfigValue) -> Generator[None, None, None]:
        """Allow selecting files and folders.

        Used by the default :class:`~earwax.TypeHandler` that
        handles ``pathlib.Path`` values.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.
        """

        def inner(value: Optional[Path]) -> None:
            """Set the value."""
            self.set_value(option, value)()
            self.game.pop_level()

        yield
        t: object = option.type_
        empty_label: Optional[str] = None
        if is_union_type(t) and type(None) in get_args(t):
            empty_label = 'Clear'
        fm: FileMenu = FileMenu(
            self.game, 'Select Path',
            path=option.value.parent if isinstance(option.value, Path) else
            Path.cwd(), func=inner,
            empty_label=empty_label
        )
        self.game.push_level(fm)

    def type_handler(self, type_: object, title: TitleFunc) -> Callable[
        [TypeHandlerFunc], TypeHandlerFunc
    ]:
        """A decorator for adding type handlers::

            from datetime import datetime, timedelta
            from earwax import ConfigMenu, tts

            m = ConfigMenu(pretend_config, 'Options', game)

            @m.type_handler(datetime, lambda option, name: 'Add a week')
            def add_week(option):
                '''Add a week to the current value.'''
                option.value += timedelta(days=7)
                tts.speak('Added a week.')
                m.game.pop_level()

        Handlers can do anything menu item functions can do, including creating
        more menus, and yielding.

        :param type_: The type this handler should be registered for.

        :param title: A function which will return the title for the menu item
            for this handler.
        """

        def inner(func: TypeHandlerFunc) -> TypeHandlerFunc:
            """Create and store the
            :class:`earwax.TypeHandler` instance."""
            self.type_handlers[type_] = TypeHandler(title, func)
            return func

        return inner

    def get_subsection_name(self, subsection: Config, name: str) -> str:
        """Gets the name for the given subsection.

        The provided ``name`` argument will be the attribute name, so should
        only be used if the subsection has no ``__section_name__``
        attribute.

        :param subsection: The :class:`~earwax.Config` instance whose name
            should be returned.

        :param name: The name of the attribute that holds the subsection.
        """
        if subsection.__section_name__ is not None:
            return subsection.__section_name__
        return name

    def get_option_name(self, option: ConfigValue, name: str) -> str:
        """Gets the name for the given option.

        The provided ``name`` argument will be the attribute name, so should
        only be used if the option has no ``__section_name__`` attribute.

        :param option: The :class:`~earwax.ConfigValue` instance whose name
            should be returned.

        :param name: The name of the attribute that holds the option.
        """
        if option.name is not None:
            return option.name
        return name

    def subsection_menu(self, subsection: Config, name: str) -> Callable[
        [], Generator[None, None, None]
    ]:
        """Used to add a menu for the given subsection.

        By default, creates a new :class:`earwax.ConfigMenu` instance, and
        returns a function that - when called - will push it onto the stack.

        :param subsection: The :class:`~earwax.Config` instance to create a
            menu for.

        :param name: The proper name of the subsection, returned by
            :meth:`~earwax.ConfigMenu.get_subsection_name`.
        """

        def inner() -> Generator[None, None, None]:
            """Push the previously created menu onto the level stack."""
            yield
            m: ConfigMenu = ConfigMenu(self.game, name, config=subsection)
            self.game.push_level(m)

        return inner

    def option_menu(self, option: ConfigValue, name: str) -> Callable[
        [], Generator[None, None, None]
    ]:
        """Used to add a menu for the given option.

        If the type of the provided option is a ``Union`` type (like
        ``Optional[str]``), then an entry for editing each type will be added
        to the menu. Otherwise, there will be only one entry.

        The only special case is when the type is a tuple of values. If this
        happens, the menu will instead be populated with a list of entries
        corrisponding to the values of the tuple.

        At the end of the menu, there will be an option to restore the default
        value.

        :param option: The :class:`~earwax.ConfigValue` instance to generate a
            menu for.

        :param name: The proper name of the given option, as returned by
            :meth:`~earwax.ConfigMenu.get_option_name`.
        """

        def inner() -> Generator[None, None, None]:
            """Create and push the menu."""
            yield
            printable_value: str = option.value_to_string()
            t: object = type(option.value)
            if option.value_converters is not None and \
               t in option.value_converters:
                printable_value = option.value_converters[t](option)
            m: Menu = Menu(self.game, f'{name}: {printable_value}')
            types: Tuple[object]
            if is_union_type(option.type_):
                types = get_args(option.type_)
            else:
                types = (option.type_,)
            type_: object
            for type_ in types:
                if isinstance(type_, tuple):
                    value: Any
                    for value in type_:
                        m.add_item(
                            f'{"* " if option.value == value else ""}'
                            f'{repr(value)}', self.set_value(option, value)
                        )
                elif type_ in self.type_handlers:
                    handler: TypeHandler = self.type_handlers[type_]
                    title: str = handler.title(option, name)
                    m.add_item(
                        title, self.activate_handler(handler, option)
                    )
                else:
                    raise UnknownTypeError(type_)
            m.add_item(
                f'Restore Default ({repr(option.default)})',
                self.set_value(option, option.default)
            )
            self.game.push_level(m)

        return inner

    def set_value(
        self, option: ConfigValue, value: Any, message: str = 'Done.'
    ) -> Callable[[], None]:
        """Returns a callable that can be used to set the value of the provided
        option to the provided value.

        This method returns a callable because it is used extensively by
        :meth:`~earwax.ConfigMenu.option_menu`, and a bunch of lambdas becomes
        less readable. Plus, Mypy complains about them.

        :param option: The :class:`~earwax.ConfigValue` instance to work on.

        :param value: The value to set ``option.value`` to.

        :param message: The message to be spoken after setting the value.
        """

        def inner():
            option.value = value
            tts.speak(message)
            self.game.pop_level()

        return inner

    def activate_handler(
        self, handler: TypeHandler, option: ConfigValue
    ) -> Callable[[], OptionalGenerator]:
        """Activates the given handler with the given configuration value.

        Used by the :meth:`~earwax.ConfigMenu.option_menu` method when building
        menus.

        :param handler: The :class:`~earwax.TypeHandler` instance that should
            be activated.

        :param option: The :class:`~earwax.ConfigValue`
            instance the handler should work with.
        """

        def inner() -> OptionalGenerator:
            """Actually call the handler's func."""
            return handler.func(option)

        return inner
