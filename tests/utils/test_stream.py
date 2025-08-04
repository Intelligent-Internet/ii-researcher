import pytest
import json
from ii_researcher.utils.stream import EventMessage, StreamManager


def test_event_message_creation():
    """Test EventMessage creation and to_dict conversion"""
    event_type = "test_event"
    data = {"key": "value"}

    message = EventMessage(event_type=event_type, data=data)

    assert message.event_type == event_type
    assert message.data == data

    dict_message = message.to_dict()
    assert dict_message["type"] == event_type
    assert dict_message["data"] == data
    assert "timestamp" in dict_message
    assert isinstance(dict_message["timestamp"], float)


@pytest.mark.asyncio
async def test_stream_manager_create_event_message():
    """Test StreamManager's create_event_message method"""
    manager = StreamManager()
    event_type = "test_event"
    data = {"key": "value"}

    await manager.create_event_message(event_type, data)

    # Get the event from queue
    event = await manager.queue.get()

    assert event["type"] == event_type
    assert event["data"] == data
    assert "timestamp" in event
    assert isinstance(event["timestamp"], float)


def test_stream_manager_create_error_event():
    """Test StreamManager's create_error_event method"""
    manager = StreamManager()
    error_message = "Test error"

    error_event_str = manager.create_error_event(error_message)

    # Parse the SSE formatted string
    event_data = json.loads(error_event_str.split("data: ")[1].strip())

    assert event_data["type"] == "error"
    assert event_data["data"]["message"] == error_message
    assert "timestamp" in event_data


def test_stream_manager_create_complete_event():
    """Test StreamManager's create_complete_event method"""
    manager = StreamManager()
    final_report = {"status": "completed"}

    complete_event_str = manager.create_complete_event(final_report)

    # Parse the SSE formatted string
    event_data = json.loads(complete_event_str.split("data: ")[1].strip())

    assert event_data["type"] == "complete"
    assert event_data["data"]["final_report"] == final_report
    assert "timestamp" in event_data


def test_stream_manager_create_close_event():
    """Test StreamManager's create_close_event method"""
    manager = StreamManager()

    close_event_str = manager.create_close_event()

    # Parse the SSE formatted string
    event_data = json.loads(close_event_str.split("data: ")[1].strip())

    assert event_data["type"] == "stream_closed"
    assert event_data["data"]["reason"] == "Connection closed"
    assert "timestamp" in event_data
