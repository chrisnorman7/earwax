"""Provides the sound subsystem."""

from synthizer import Buffer

buffers = {}


def get_buffer(context, protocol, path):
    """Get a Buffer instance. Buffers are cached in the buffers dictionary, so
    if there is already a buffer with the given protocol and path, it will be
    returned. Otherwise, a new buffer will be created, and added to
    the dictionary."""
    url = f'{protocol}://{path}'
    if url not in buffers:
        buffers[url] = Buffer.from_stream(context, protocol, path)
    return buffers[url]
