import pytest
from demo.components.my_consumer import MyEvent, MyEventData
from demo.domain.my_producer import MyProducer

from contracts.testing import make_client


@pytest.mark.asyncio
async def test_my_producer():
    # Fixtures
    client = make_client()
    # Arrange
    prod = MyProducer(client)
    # Act
    await prod.produce()
    # Assert event published
    assert client.events_published == [
        MyEvent.publish(
            location="kitchen",
            device_id="thermometer",
            data=MyEventData(temperature=23.5, timestamp=123456),
        )
    ]
    # Assert bytes published
    assert client.adapter.messages_sent == [
        (
            "sensors.kitchen.thermometer",
            b'{"temperature":23.5,"timestamp":123456}',
            {},
        )
    ]
