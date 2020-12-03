"""Provides the Track class."""

from typing import Optional

from attr import Factory, attrib, attrs

try:
    from synthizer import Context, Source, StreamingGenerator
except ModuleNotFoundError:
    StreamingGenerator = None
    Context = None
    Source = None


@attrs(auto_attribs=True)
class Track:
    """A music track.

    A track that plays while a :class:`earwax.BoxLevel` object is top of the
    levels stack.

    :ivar ~earwax.Track.protocol: The ``protocol`` argument to pass to
        ``synthizer.StreamingGenerator````.

    :ivar ~earwax.Track.path: The ``path`` argument to pass to
        ``synthizer.StreamingGenerator``.

    :ivar ~earwax.Track.generator: The ``synthizer.BufferGenerator`` instance
        to play through.

        This value is initialised as part of the :meth:`~earwax.Track.play`
        method.
    """

    protocol: str
    path: str
    generator: Optional[StreamingGenerator] = attrib(
        default=Factory(type(None)), init=False
    )

    def play(self, ctx: Context, source: Source) -> None:
        """Play this track on a loop.

        To alter how ``sound_path`` is played, override
        :meth:`earwax.Track.load_sound`.

        :param ctx: The ``synthizer.Context`` instance to play through.

        :param source: The source to connect :attr:`self.generator
            <earwax.Track.generator>` to.
        """
        self.generator = StreamingGenerator(ctx, self.protocol, self.path)
        source.add_generator(self.generator)
        self.generator.looping = True

    def stop(self) -> None:
        """Stop this track playing."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
