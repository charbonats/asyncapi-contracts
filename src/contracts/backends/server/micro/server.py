from __future__ import annotations

import datetime
from contextlib import AsyncExitStack
from typing import Any, Callable, Iterable

from nats.aio.client import Client as NatsClient
from nats_contrib import micro
from nats_contrib.micro.api import Endpoint, Service
from nats_contrib.micro.client import Client as BaseMicroClient
from nats_contrib.micro.request import Request as MicroRequest

from contracts.abc.consumer import BaseConsumer
from contracts.abc.operation import BaseOperation
from contracts.abc.request import OT, Request
from contracts.application import Application
from contracts.asyncapi.renderer import create_docs_server
from contracts.core.types import ParamsT, T
from contracts.instance import Instance
from contracts.server import Server, ServerAdapter


async def _add_operation(
    service: Service,
    operation: BaseOperation[Any, Any, Any, Any],
    queue_group: str | None = None,
) -> Endpoint:
    """Add an operation to a service."""
    errors_to_catch = {e.origin: e for e in operation.spec.catch}

    async def handler(request: MicroRequest) -> None:
        try:
            await operation.handle(
                MicroMessage(
                    request,
                    operation,
                )
            )
        except BaseException as e:
            for err in errors_to_catch:
                if isinstance(e, err):
                    error = errors_to_catch[err]
                    code = error.code
                    description = error.description
                    data = error.fmt(e) if error.fmt else None
                    if data:
                        payload = operation.spec.reply_payload.type_adapter.encode(data)
                    else:
                        payload = b""
                    await request.respond_error(code, description, data=payload)
                    return
            raise

    return await service.add_endpoint(
        operation.spec.name,
        handler=handler,
        subject=operation.spec.address.get_subject(),
        metadata=operation.spec.metadata,
        queue_group=queue_group,
    )


def create_micro_server(
    ctx: micro.Context,
    queue_group: str | None = None,
    now: Callable[[], datetime.datetime] | None = None,
    id_generator: Callable[[], str] | None = None,
    api_prefix: str | None = None,
    http_port: int | None = None,
    docs_path: str = "/docs",
    asyncapi_path: str = "/asyncapi.json",
) -> Server:
    """Create a micro server."""
    adapter = MicroAdapter(
        ctx.client,
        queue_group=queue_group,
        now=now,
        id_generator=id_generator,
        api_prefix=api_prefix,
        http_port=http_port,
        docs_path=docs_path,
        asyncapi_path=asyncapi_path,
    )
    return Server(adapter)


async def start_micro_server(
    ctx: micro.Context,
    app: Application,
    components: Iterable[
        BaseOperation[Any, Any, Any, Any] | BaseConsumer[Any, Any, Any]
    ],
    queue_group: str | None = None,
    now: Callable[[], datetime.datetime] | None = None,
    id_generator: Callable[[], str] | None = None,
    api_prefix: str | None = None,
    http_port: int | None = None,
    docs_path: str = "/docs",
    asyncapi_path: str = "/asyncapi.json",
) -> Server:
    """Start a micro server."""
    server = create_micro_server(
        ctx,
        queue_group=queue_group,
        now=now,
        id_generator=id_generator,
        api_prefix=api_prefix,
        http_port=http_port,
        docs_path=docs_path,
        asyncapi_path=asyncapi_path,
    )
    server.bind(app, *components)
    return await ctx.enter(server)


class MicroInstance(Instance):
    def __init__(
        self,
        queue_group: str | None,
        service: Service,
        app: Application,
        operations: Iterable[BaseOperation[Any, Any, Any, Any]],
        consumers: Iterable[BaseConsumer[Any, Any, Any]],
        http_port: int | None = None,
        docs_path: str = "/docs",
        asyncapi_path: str = "/asyncapi.json",
    ) -> None:
        self.queue_group = queue_group
        self.service = service
        self.app = app
        self.operations = operations
        self.consumers = consumers
        self.http_port = http_port
        self.docs_path = docs_path
        self.asyncapi_path = asyncapi_path
        self.stack = AsyncExitStack()

    async def start(self) -> None:
        await self.stack.__aenter__()
        await self.stack.enter_async_context(self.service)
        for endpoint in self.operations:
            await _add_operation(self.service, endpoint)
        for consumer in self.consumers:
            raise NotImplementedError
        if self.http_port:
            server = create_docs_server(
                self.app,
                port=self.http_port,
                docs_path=self.docs_path,
                asyncapi_path=self.asyncapi_path,
            )
            await self.stack.enter_async_context(server)

    async def stop(self) -> None:
        await self.stack.aclose()


class MicroAdapter(ServerAdapter):
    def __init__(
        self,
        client: NatsClient,
        queue_group: str | None = None,
        now: Callable[[], datetime.datetime] | None = None,
        id_generator: Callable[[], str] | None = None,
        api_prefix: str | None = None,
        http_port: int | None = None,
        docs_path: str = "/docs",
        asyncapi_path: str = "/asyncapi.json",
    ) -> None:
        self._nc = client
        self._client = BaseMicroClient(client, api_prefix=api_prefix)
        self.queue_group = queue_group
        self.now = now
        self.id_generator = id_generator
        self.api_prefix = api_prefix
        self.http_port = http_port
        self.docs_path = docs_path
        self.asyncapi_path = asyncapi_path

    def create_instance(
        self,
        app: Application,
        operations: Iterable[BaseOperation[Any, Any, Any, Any]],
        consumers: Iterable[BaseConsumer[Any, Any, Any]],
    ) -> MicroInstance:
        """Add a new instance to the server."""
        queue_group = self.queue_group
        srv = micro.add_service(
            self._nc,
            name=app.name,
            version=app.version,
            description=app.description,
            metadata=app.metadata,
            queue_group=self.queue_group,
            now=self.now,
            id_generator=self.id_generator,
            api_prefix=self.api_prefix,
        )
        return MicroInstance(
            queue_group,
            srv,
            app,
            operations,
            consumers,
            http_port=self.http_port,
            docs_path=self.docs_path,
            asyncapi_path=self.asyncapi_path,
        )


class MicroMessage(Request[OT]):
    """A message received as a request."""

    def __init__(
        self,
        request: MicroRequest,
        operation: OT,
    ) -> None:
        data = operation.spec.payload.type_adapter.decode(request.data())
        params = operation.spec.address.get_params(request.subject())
        self._request = request
        self._data = data
        self._params = params
        self._response_type_adapter = operation.spec.reply_payload.type_adapter
        self._status_code = operation.spec.status_code
        self._response_content_type = operation.spec.reply_payload.content_type

    def params(
        self: MicroMessage[BaseOperation[Any, ParamsT, Any, Any]],
    ) -> ParamsT:
        return self._params

    def payload(self: MicroMessage[BaseOperation[Any, Any, T, Any]]) -> T:
        return self._data

    def headers(self) -> dict[str, str]:
        return self._request.headers()

    async def respond(
        self, data: Any = None, *, headers: dict[str, str] | None = None
    ) -> None:
        headers = headers or {}
        if self._response_content_type:
            headers["Content-Type"] = self._response_content_type
        response = self._response_type_adapter.encode(data)
        await self._request.respond_success(self._status_code, response, headers)

    async def respond_error(
        self,
        code: int,
        description: str,
        *,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        headers = headers or {}
        if self._response_content_type:
            headers["Content-Type"] = self._response_content_type
        response = self._response_type_adapter.encode(data)
        await self._request.respond_error(code, description, response, headers)
