from __future__ import annotations

import datetime
from typing import Any, AsyncContextManager, Callable, Iterable

from nats.aio.client import Client as NatsClient
from nats_contrib import micro
from nats_contrib.micro.api import Endpoint, Service
from nats_contrib.micro.client import Client as BaseMicroClient
from nats_contrib.micro.request import Request as MicroRequest

from contracts.application import (
    Application,
    validate_consumers,
    validate_operations,
)
from contracts.abc.consumer import BaseConsumer
from contracts.abc.operation import BaseOperation
from contracts.abc.operation_request import OT, Request
from contracts.abc.server import Server as BaseServer
from contracts.asyncapi.renderer import create_docs_server
from contracts.core.types import ParamsT, T


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
) -> Service:
    """Start a micro server."""
    server = MicroServer(
        ctx.client,
        queue_group=queue_group,
        now=now,
        id_generator=id_generator,
        api_prefix=api_prefix,
    )
    if http_port is not None:
        http_server = create_docs_server(
            app, port=http_port, docs_path=docs_path, asyncapi_path=asyncapi_path
        )
        await ctx.enter(http_server)
    return await ctx.enter(server.add_application(app, *components))


class MicroServer(BaseServer[Service, Endpoint, Any]):
    def __init__(
        self,
        client: NatsClient,
        queue_group: str | None = None,
        now: Callable[[], datetime.datetime] | None = None,
        id_generator: Callable[[], str] | None = None,
        api_prefix: str | None = None,
    ) -> None:
        self._nc = client
        self._client = BaseMicroClient(client, api_prefix=api_prefix)
        self.queue_group = queue_group
        self.now = now
        self.id_generator = id_generator
        self.api_prefix = api_prefix

    def add_application(
        self,
        app: Application,
        *components: BaseOperation[Any, Any, Any, Any] | BaseConsumer[Any, Any, Any],
    ) -> AsyncContextManager[Service]:
        all_operations = validate_operations(app, components)
        _ = validate_consumers(app, components)
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

        class Ctx:
            async def __aenter__(self) -> Service:
                await srv.start()
                for endpoint in all_operations:
                    await _add_operation(srv, endpoint, queue_group)
                return srv

            async def __aexit__(self, *args: Any) -> None:
                await srv.stop()

        return Ctx()

    async def add_operation(
        self,
        app: Service,
        operation: BaseOperation[Any, Any, Any, Any],
        queue_group: str | None = None,
    ) -> Endpoint:
        return await _add_operation(app, operation, queue_group)

    async def add_consumer(
        self, app: Service, consumer: BaseConsumer[Any, Any, Any]
    ) -> Any:
        raise NotImplementedError


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
