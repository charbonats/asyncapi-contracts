from __future__ import annotations

import logging
from dataclasses import dataclass

from contracts import Request

from ..components.my_operation import MyOperation, MyResponse

logger = logging.getLogger("my-endpoint")


@dataclass
class MyOperationImpl(MyOperation):
    """An example of operation implementation.

    Usage of @dataclass is purely optional.
    Endpoint implementation only needs to inherit from the endpoint class.
    """

    foo: int

    async def handle(self, request: Request[MyOperation]) -> None:
        """Signature is constrained by endpoint definition."""

        params = request.params()
        logger.debug(f"Received request for device: {params.device_id}")

        data = request.payload()
        logger.debug(f"Request data is: {data}")

        result = data.value + self.foo

        # Reply to the request
        await request.respond(MyResponse(success=True, result=result))

        # We could also respond with an error
        # await request.respond_error(409, "Conflict", data=MyResponse(success=False, result=0))
