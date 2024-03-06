from __future__ import annotations

import datetime
from typing import Any, AsyncContextManager, Callable, Iterable

from nats.aio.client import Client as NatsClient
from nats_contrib import micro

from nats_contrib.micro.api import Endpoint, Service
from nats_contrib.micro.client import Client as BaseMicroClient
from nats_contrib.micro.client import ServiceError
from nats_contrib.micro.request import Request as MicroRequest
from contracts.specification.renderer import create_docs_server
from contracts.application import Application, validate
from contracts.interfaces.client import OperationError, Reply, Client as BaseClient
from contracts.interfaces.server import Server as BaseServer
from contracts.message import Message, OT
from contracts.operation import Operation, OperationRequest
from contracts.types import E, ParamsT, R, T


async def _add_operation(
    service: Service,
    operation: Operation[Any, Any, Any, Any, Any],
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
                        payload = operation.spec.error.type_adapter.encode(data)
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
    endpoints: Iterable[Operation[Any, Any, Any, Any, Any]],
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
    return await ctx.enter(server.add_application(app, *endpoints))


class MicroServer(BaseServer[Service]):
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
        *endpoints: Operation[Any, Any, Any, Any, Any],
    ) -> AsyncContextManager[Service]:
        all_endpoints = validate(app, endpoints)
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
                for endpoint in all_endpoints:
                    await _add_operation(srv, endpoint, queue_group)
                return srv

            async def __aexit__(self, *args: Any) -> None:
                await srv.stop()

        return Ctx()


class MicroMessage(Message[OT]):
    """A message received as a request."""

    def __init__(
        self,
        request: MicroRequest,
        operation: OT,
    ) -> None:
        data = operation.spec.request.type_adapter.decode(request.data())
        params = operation.spec.address.get_params(request.subject())
        self._request = request
        self._data = data
        self._params = params
        self._response_type_adapter = operation.spec.response.type_adapter
        self._error_type_adapter = operation.spec.error.type_adapter
        self._status_code = operation.spec.status_code
        self._error_content_type = operation.spec.error.content_type
        self._response_content_type = operation.spec.response.content_type

    def params(
        self: MicroMessage[Operation[Any, ParamsT, Any, Any, Any]],
    ) -> ParamsT:
        return self._params

    def payload(self: MicroMessage[Operation[Any, Any, T, Any, Any]]) -> T:
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
        if self._error_content_type:
            headers["Content-Type"] = self._error_content_type
        response = self._error_type_adapter.encode(data)
        await self._request.respond_error(code, description, response, headers)


class Client(BaseClient):
    def __init__(
        self,
        client: NatsClient,
    ) -> None:
        self._client = BaseMicroClient(client)

    async def send(
        self,
        request: OperationRequest[ParamsT, T, R, E],
        headers: dict[str, str] | None = None,
        timeout: float = 1,
    ) -> Reply[ParamsT, T, R, E]:
        """Send a request."""
        data = request.spec.request.type_adapter.encode(request.payload)
        try:
            response = await self._client.request(
                request.subject,
                data,
                headers=headers,
                timeout=timeout,
            )
        except ServiceError as e:
            return Reply(request, None, None, OperationError(e.code, e.description))
        return Reply(
            request,
            response.data,
            response.headers or {},
            None,
        )
