from __future__ import annotations

from nats.aio.client import Client as NatsClient
from nats_contrib.micro.client import Client as BaseMicroClient
from nats_contrib.micro.client import ServiceError

from contracts.client import Client as BaseClient
from contracts.client import RawOperationError, RawReply


class Client(BaseClient):
    def __init__(
        self,
        client: NatsClient,
    ) -> None:
        self._client = BaseMicroClient(client)

    async def __send_event__(
        self,
        subject: str,
        payload: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Send an event."""
        await self._client.nc.publish(
            subject=subject,
            payload=payload,
            headers=headers,
        )

    async def __send_request__(
        self,
        subject: str,
        payload: bytes,
        headers: dict[str, str] | None = None,
        timeout: float = 1,
    ) -> RawReply:
        """Send a request."""
        try:
            response = await self._client.request(
                subject,
                payload,
                headers=headers,
                timeout=timeout,
            )
        except ServiceError as e:
            raise RawOperationError(e.code, e.description, e.headers, e.data) from e
        return RawReply(
            response.data,
            response.headers or {},
        )
