from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse
from starlette.routing import Route

from .builder import build_spec

if TYPE_CHECKING:
    from ..application import Application

STATIC = Path(__file__).parent.joinpath("static")
DEFAULT_CSS = STATIC.joinpath("default.min.css")
SCRIPT_JS = STATIC.joinpath("asyncapi-web-component.js")
FAVICON = STATIC.joinpath("favicon.ico")


def create_docs_app(
    app: Application,
    docs_path: str = "/",
    asyncapi_path: str = "/asyncapi.json",
    static_path: str = "/static",
) -> Starlette:
    schema = build_spec(app)
    docs = get_html(
        f"{app.name} - {app.version}",
        asyncapi_path,
        static_path + "/default.min.css",
        static_path + "/asyncapi-web-component.js",
        favicon="/favicon.ico",
    )

    async def get_async_api(request: Request) -> PlainTextResponse:
        return PlainTextResponse(
            schema.export_json(indent=0), media_type="application/json"
        )

    async def get_docs(request: Request) -> HTMLResponse:
        return HTMLResponse(docs)

    async def get_css(request: Request) -> FileResponse:
        return FileResponse(DEFAULT_CSS)

    async def get_js(request: Request) -> FileResponse:
        return FileResponse(SCRIPT_JS)

    async def get_favicon(request: Request) -> FileResponse:
        return FileResponse(FAVICON)

    return Starlette(
        debug=True,
        routes=[
            Route(asyncapi_path, get_async_api),
            Route(docs_path, get_docs),
            Route(static_path + "/default.min.css", get_css),
            Route(static_path + "/asyncapi-web-component.js", get_js),
            Route("/favicon.ico", get_favicon),
        ],
    )


def create_docs_server(
    app: Application,
    port: int = 8000,
    docs_path: str = "/",
    asyncapi_path: str = "/asyncapi.json",
) -> Server:
    asgi_app = create_docs_app(app, docs_path=docs_path, asyncapi_path=asyncapi_path)
    cfg = uvicorn.Config(
        app=asgi_app,
        port=port,
        loop="asyncio",
        access_log=True,
        log_level=None,
        log_config=None,
    )
    server = Server(cfg)
    return server


class Server(uvicorn.Server):
    """A custom Uvicorn server that can be used as an async context manager."""

    def __init__(self, config: uvicorn.Config) -> None:
        super().__init__(config)
        # Track the asyncio task used to run the server
        self.task: asyncio.Task[None] | None = None

    # Override because we're catching signals ourselves
    def install_signal_handlers(self) -> None:
        pass

    async def __aenter__(self) -> "Server":
        self.task = asyncio.create_task(self.serve())
        return self

    async def __aexit__(self, *args: object, **kwargs: object) -> None:
        self.should_exit = True
        if self.task:
            await asyncio.wait([self.task])
            if self.task.cancelled():
                return
            err = self.task.exception()
            if err:
                raise err


def get_html(
    title: str,
    asyncapi: str,
    css: str,
    js: str,
    favicon: str,
) -> str:
    return f"""<html>
<style>
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}

  code {{
    font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
      monospace;
  }}
</style>
<head>
    <title>{title}</title>
    <link rel="icon" href="{favicon}" type="image/x-icon" />
</head>
<body>
  <asyncapi-component schemaUrl="{asyncapi}"
    cssImportPath="{css}">
  </asyncapi-component>
  <script src="{js}" defer></script>
</body>

</html>
"""
