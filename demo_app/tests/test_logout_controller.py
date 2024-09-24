import pytest
from unittest.mock import AsyncMock

from src.core.session import Session
from src.event_bus import Event
from src.controllers.base_controller import BaseController

from demo_app.controllers.logout_controller import logout_controller
from demo_app.di_setup import di_container


@pytest.mark.asyncio
async def test_logout_controller_success(monkeypatch):
    # Create mock services
    mock_publisher_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_send = AsyncMock()

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'PublisherService': mock_publisher_service,
            'SessionService': mock_session_service,
        }
        return services[service_name]

    monkeypatch.setattr(di_container, 'get', mock_get)

    # Monkeypatch BaseController's send_response to track the response flow
    mock_send_response = AsyncMock()
    monkeypatch.setattr(BaseController, 'send_response', mock_send_response)

    session_id = "test-session-id"
    # Simulate a session
    session = Session(session_id=session_id, data={'user_id': 1})
    event = Event(name='http.request.received', data={'session': session, 'send': mock_send})

    # Call the logout_controller
    await logout_controller(event)

    # Check that the session service was called to delete the session
    mock_session_service.delete_session.assert_called_once_with('test-session-id')

    # Check that the publisher service was called for success
    mock_publisher_service.publish_logout_success.assert_called_once_with(1)

    # Assert that the send_response was called to send the response
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Check response content and headers
    assert response.content == "You have been logged out."
    assert any(b'set-cookie' in header for header in response.headers), "Expected 'set-cookie' header in response."


@pytest.mark.asyncio
async def test_logout_controller_failure(monkeypatch):
    # Create mock services
    mock_publisher_service = AsyncMock()
    mock_send = AsyncMock()

    # Monkeypatch the DI container to return the mocked PublisherService (no SessionService needed here)
    async def mock_get(service_name):
        services = {
            'PublisherService': mock_publisher_service,
        }
        return services[service_name]

    monkeypatch.setattr(di_container, 'get', mock_get)

    # Monkeypatch BaseController's send_text to track the response flow
    mock_send_text = AsyncMock()
    monkeypatch.setattr(BaseController, 'send_text', mock_send_text)

    # Simulate a missing session (no active session)
    event = Event(name='http.request.received', data={'session': None, 'send': mock_send})

    # Call the logout_controller
    await logout_controller(event)

    # Check that the publisher service was called for failure
    mock_publisher_service.publish_logout_failure.assert_called_once()

    # Assert that send_text was called with the appropriate error message
    mock_send_text.assert_called_once_with("No active session found.", status=400)
