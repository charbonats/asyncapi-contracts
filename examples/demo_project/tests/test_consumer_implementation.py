import pytest
from demo.components.my_consumer import MyEvent, MyEventData
from demo.domain.my_consumer import MyConsumerImpl

from contracts.testing import make_message


@pytest.mark.asyncio
async def test_my_consumer_implementation():
    # Create the endpoint implementation
    con = MyConsumerImpl()
    # Create a new request message
    request = make_message(
        MyEvent.publish(
            MyEventData(1, 123456),
            location="kitchen",
            device_id="test",
        )
    )
    # Call the consumer implementation
    await con.handle(request)
    # Check that event was acked
    assert request.acknowledged()
