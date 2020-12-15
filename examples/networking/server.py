"""An example server."""

import logging

from earwax_server import Server

s = Server()


@s.event
def on_data(ctx, data):
    """Handle incoming data."""
    ctx.send_raw(data)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    s.run(1234)
