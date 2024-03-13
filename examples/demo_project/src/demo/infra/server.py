from __future__ import annotations

import logging

from nats_contrib import micro

from contracts.backends.server.micro import create_micro_server
from contracts.server import Server

from ..app import app
from ..domain.my_operation import MyEndpointImplementation

logger = logging.getLogger("app")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def setup(ctx: micro.Context) -> None:
    """An example setup function to start a micro service."""
    # Log server bootstrap
    logger.info("Configuring the server")
    # Create the server
    server = await create_server(ctx)
    # Push a function to log server stopped
    ctx.push(
        lambda: logger.warning("Server is stopped"),
    )
    # Log server starting
    logger.info("Starting the server")
    # Start the server
    await ctx.enter(server)
    # Log server started
    logger.info("Server is started and listening to requests")
    # Push a function to be log server stopping
    ctx.push(lambda: logger.warning("Requesting the server to stop"))


async def create_server(ctx: micro.Context) -> Server:
    # Define the server first
    server = create_micro_server(
        ctx,
        # This will start an HTTP server listening on port 8000
        # The server returns the asyncapi spec on /asyncapi.json
        # and the documentation on /
        http_port=8000,
        docs_path="/docs",
        asyncapi_path="/asyncapi.json",
    )
    # Create endpoint instance
    # This could be async and connect to a remote database
    ep = MyEndpointImplementation(12)
    # Bind server operations to application
    server.bind(app, ep)
    return server
