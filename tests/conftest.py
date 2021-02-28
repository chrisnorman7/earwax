"""Setup for tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from socket import AF_INET, SOCK_STREAM
from typing import Generator

from _pytest.fixtures import FixtureRequest
from cryptography.fernet import Fernet
from pyglet.window import Window
from pytest import fixture
from synthizer import (
    Context,
    GlobalFdnReverb,
    LoggingBackend,
    LogLevel,
    StreamingGenerator,
    configure_logging_backend,
    initialized,
    set_log_level,
)

from earwax import (
    ActionMap,
    Box,
    BoxLevel,
    BufferCache,
    DialogueTree,
    Door,
    Editor,
    Game,
    GameBoard,
    Level,
    MapEditor,
    MapEditorContext,
    Menu,
    NetworkConnection,
    Point,
    Sound,
    SoundManager,
    Track,
    TrackTypes,
)
from earwax.cmd.constants import scripts_directory
from earwax.cmd.project_credit import ProjectCredit

from .networking.pretend_socket import PretendSocket


@fixture(name="thread_pool", scope="session")
def get_thread_pool() -> ThreadPoolExecutor:
    """Get a new thread pool executor."""
    return ThreadPoolExecutor()


@fixture(name="level")
def get_level(game: Game) -> Level:
    """Get a new Level instance."""
    return Level(game)


@fixture(name="game")
def get_game(
    context: Context, thread_pool: ThreadPoolExecutor
) -> Generator[Game, None, None]:
    """Get a new ``Game`` instance."""
    g: Game = Game(audio_context=context, thread_pool=thread_pool)
    g.setup_run(None)
    assert g.ambiance_sound_manager is not None
    assert g.interface_sound_manager is not None
    assert g.music_sound_manager is not None
    yield g
    g.buffer_cache.destroy_all()
    g.ambiance_sound_manager.destroy_all()
    g.interface_sound_manager.destroy_all()
    g.music_sound_manager.destroy_all()


@fixture(name="menu")
def get_menu(game: Game) -> Menu:
    """Return an empty ``Menu`` instance."""
    return Menu(game, "Test Menu")


@fixture(name="editor")
def get_editor(game: Game, window: Window) -> Editor:
    """Return a new ``Editor`` instance.

    The default submit event handler closes the window.
    """
    e: Editor = Editor(game)

    @e.event
    def on_submit(text: str) -> None:
        if game.window is not None:
            game.window.close()

    return e


@fixture(scope="session", autouse=True)
def initialise_tests() -> Generator[None, None, None]:
    """Initialise and shutdown Synthizer."""
    configure_logging_backend(LoggingBackend.STDERR)
    set_log_level(LogLevel.DEBUG)
    with initialized():
        if not scripts_directory.is_dir():
            scripts_directory.mkdir()
        yield


@fixture(name="context", scope="session")
def get_context() -> Context:
    """Get a new Synthizer context."""
    return Context()


@fixture(name="box")
def get_box(game: Game) -> Box:
    """Get a new ``Box`` instance."""
    return Box(game, Point(1, 2, 3), Point(4, 5, 6))


@fixture(name="box_level")
def get_box_level(game: Game) -> BoxLevel:
    """Get a new ``BoxLevel`` instance."""
    return BoxLevel(game)


@fixture(name="board")
def get_gameboard(game: Game) -> GameBoard[int]:
    """Get a new ``GameBoard`` instance."""
    board: GameBoard[int] = GameBoard(game, Point(2, 2, 2), lambda p: 0)
    board.populate()
    return board


@fixture(name="window")
def get_window(request: FixtureRequest) -> Window:
    """Get a pyglet window with a sensible caption."""
    name: str = f"{request.function.__module__}.{request.function.__name__}"
    w: Window = Window(caption=name)
    yield w
    w.close()


@fixture(name="con")
def get_network_connection() -> NetworkConnection:
    """Get a new network connection."""
    return NetworkConnection()


@fixture(name="socket")
def get_socket() -> PretendSocket:
    """Get a pretend socket."""
    return PretendSocket(AF_INET, SOCK_STREAM)


@fixture(name="generator")
def get_streaming_generator(context: Context) -> StreamingGenerator:
    """Return a new ``StreamingGenerator`` instance."""
    return StreamingGenerator(context, "file", "sound.wav")


@fixture(name="sound_manager")
def get_sound_manager(
    buffer_cache: BufferCache, context: Context
) -> SoundManager:
    """Get a new sound manager instance."""
    return SoundManager(
        context, buffer_cache=buffer_cache, name="Test sound manager"
    )


@fixture(name="sound")
def get_sound(buffer_cache: BufferCache, context: Context) -> Sound:
    """Get a new sound."""
    return Sound.from_path(context, buffer_cache, Path("sound.wav"))


@fixture(name="track")
def get_track() -> Track:
    """Get a new track instance."""
    return Track("file", "sound.wav", TrackTypes.ambiance)


@fixture(name="reverb")
def get_reverb(context: Context) -> GlobalFdnReverb:
    """Get a new reverb object."""
    return GlobalFdnReverb(context)


@fixture(name="door")
def get_door() -> Door:
    """Get a door object."""
    p: Path = Path("sound.wav")
    return Door(open_sound=p, close_sound=p, closed_sound=p)


@fixture(name="dialogue_tree")
def get_dialogue_line() -> DialogueTree:
    """Get a new DialogueTree instance."""
    return DialogueTree()


@fixture(name="project_credit")
def get_project_credit() -> ProjectCredit:
    """Get a ProjectCredit instance."""
    return ProjectCredit("Test", "test.com", "sound.wav", True)


@fixture(name="buffer_cache")
def get_buffer_cache(game: Game) -> BufferCache:
    """Return a buffer cache."""
    return game.buffer_cache


@fixture(name="action_map")
def get_action_map() -> ActionMap:
    """Return a new ActionMap instance."""
    return ActionMap()


@fixture(name="map_editor")
def get_map_editor(game: Game) -> MapEditor:
    """Return a new map editor instance."""
    return MapEditor(game)


@fixture(name="map_editor_context")
def get_map_editor_context(map_editor: MapEditor) -> MapEditorContext:
    """Return an attached context."""
    return map_editor.context


@fixture(name="valid_key")
def get_valid_key() -> bytes:
    """Return the correct key for decrypting stuff."""
    return Fernet.generate_key()


@fixture(name="invalid_key")
def get_invalid_key() -> bytes:
    """Get the wrong key for decrypting stuff."""
    return Fernet.generate_key()
