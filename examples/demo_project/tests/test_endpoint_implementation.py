import pytest
from demo.components.my_operation import MyRequest, MyResponse
from demo.domain.my_operation import MyOperationImpl

from contracts.testing import make_request


@pytest.mark.asyncio
async def test_my_endpoint_implementation():
    # Create the endpoint implementation
    ep = MyOperationImpl(1)
    # Create a new request message
    request = make_request(
        MyOperationImpl.request(
            MyRequest(1),
            device_id="test",
        )
    )
    # Call the endpoint implementation
    await ep.handle(request)
    # Check the response
    assert request.response_data() == MyResponse(success=True, result=2)
