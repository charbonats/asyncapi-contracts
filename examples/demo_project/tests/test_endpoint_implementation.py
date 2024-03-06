import pytest

from demo.domain.my_endpoint import MyEndpointImplementation
from demo.contract.my_endpoint import MyRequest, MyResponse

from contracts.testing import make_message


@pytest.mark.asyncio
async def test_my_endpoint_implementation():
    # Create the endpoint implementation
    ep = MyEndpointImplementation(1)
    # Create a new request message
    request = make_message(
        MyEndpointImplementation.request(
            MyRequest(1),
            device_id="test",
        )
    )
    # Call the endpoint implementation
    await ep.handle(request)
    # Check the response
    assert request.response_data() == MyResponse(result=2)
