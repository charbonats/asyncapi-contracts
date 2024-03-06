from __future__ import annotations

import logging

from contracts.backends.micro import start_micro_server
from nats_contrib import micro

from ..app import app
from ..domain.my_operation import MyEndpointImplementation

logger = logging.getLogger("app")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def setup(ctx: micro.Context) -> None:
    """An example setup function to start a micro service."""

    # Push a function to be called when the service is stopped
    ctx.push(lambda: logger.warning("Exiting the service"))

    logger.info("Configuring the service")

    # Mount the app
    await start_micro_server(
        ctx,
        app,
        [
            MyEndpointImplementation(12),
        ],
        # This will start an HTTP server listening on port 8000
        # The server returns the asyncapi spec on /asyncapi.json
        # and the documentation on /
        http_port=8000,
        docs_path="/docs",
        asyncapi_path="/asyncapi.json",
    )

    logger.info("Service is ready and listening to requests")
