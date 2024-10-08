import pytest
from unittest.mock import AsyncMock

from demo_app.di_setup import auth_service, orm_service
from src.services.config_service import ConfigService
from src.services.routing_service import RoutingService
from src.event_bus import Event, EventBus
from src.core.request import Request
from src.services.security.authentication_service import AuthenticationService


# HTTP
@pytest.mark.asyncio
async def test_add_and_remove_route():
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a route
    routing_service.add_route('/test', 'GET', handler)

    # Create the expected regex pattern for the path '/test'
    regex_path = r'^/test$'

    # Check that the route is correctly added as a regex pattern
    assert regex_path in routing_service.routes
    assert 'GET' in routing_service.routes[regex_path]

    # Remove the route
    routing_service.remove_route('/test', 'GET')

    # Check that the route is correctly removed
    assert regex_path not in routing_service.routes


@pytest.mark.asyncio
async def test_route_to_correct_handler(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    routing_service.add_route('/test', 'GET', handler)

    # Create a mock request object
    scope = {'path': '/test', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create a mock event and pass the request object
    event = Event(name='http.request.received', data={
        'request': request,  # Pass the request object here
        'send': AsyncMock()
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the correct handler was called
    handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_handle_404(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    # Create a mock event that should trigger a 404
    mock_send = AsyncMock()
    event = Event(name='http.request.received', data={
        'scope': {'path': '/nonexistent', 'method': 'GET'},
        'send': mock_send
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the 404 handler was called and sent the correct response
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 404,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b'Not Found',
    })


@pytest.mark.asyncio
async def test_multiple_routes_and_methods(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler_get = AsyncMock()
    handler_post = AsyncMock()

    # Add routes for both GET and POST methods
    routing_service.add_route('/test', 'GET', handler_get)
    routing_service.add_route('/test', 'POST', handler_post)

    # Create a mock request object
    scope = {'path': '/test', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create and route a GET event
    event_get = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock()
    })
    await routing_service.route_event(event_get)
    handler_get.assert_called_once_with(event_get)
    handler_post.assert_not_called()

    scope = {'path': '/test', 'method': 'POST'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create and route a POST event
    event_post = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock()
    })
    await routing_service.route_event(event_post)
    handler_post.assert_called_once_with(event_post)


@pytest.mark.asyncio
async def test_route_with_int_param(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a route with an integer parameter
    routing_service.add_route('/page/<int:id>', 'GET', handler)

    # Create a mock request object for a path with a matching integer parameter
    scope = {'path': '/page/45', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create a mock event and pass the request object
    event = Event(name='http.request.received', data={
        'request': request,  # Pass the request object here
        'send': AsyncMock()
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the correct handler was called with path parameter 'id' = 45
    handler.assert_called_once_with(event)
    assert event.data['path_params'] == {'id': '45'}


@pytest.mark.asyncio
async def test_route_with_str_param(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a route with a string parameter
    routing_service.add_route('/user/<str:username>', 'GET', handler)

    # Create a mock request object for a path with a matching string parameter
    scope = {'path': '/user/johndoe', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create a mock event and pass the request object
    event = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock()
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the correct handler was called with path parameter 'username' = 'johndoe'
    handler.assert_called_once_with(event)
    assert event.data['path_params'] == {'username': 'johndoe'}


@pytest.mark.asyncio
async def test_route_with_multiple_params(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a route with multiple parameters (int and string)
    routing_service.add_route('/page/<int:id>/user/<str:username>', 'GET', handler)

    # Create a mock request object with matching parameters
    scope = {'path': '/page/45/user/johndoe', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create a mock event and pass the request object
    event = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock()
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the correct handler was called with both parameters extracted
    handler.assert_called_once_with(event)
    assert event.data['path_params'] == {'id': '45', 'username': 'johndoe'}


@pytest.mark.asyncio
async def test_handle_404_for_unmatched_param_route(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    # Add a route that expects an integer parameter
    routing_service.add_route('/page/<int:id>', 'GET', AsyncMock())

    # Create a mock request object that doesn't match the parameter type (string instead of int)
    scope = {'path': '/page/abc', 'method': 'GET'}
    receive = AsyncMock()
    request = Request(scope, receive)

    # Create a mock event and pass the request object
    mock_send = AsyncMock()
    event = Event(name='http.request.received', data={
        'request': request,
        'send': mock_send
    })

    # Route the event, which should trigger a 404
    await routing_service.route_event(event)

    # Ensure the 404 handler was called and sent the correct response
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 404,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b'Not Found',
    })

# Websockets
@pytest.mark.asyncio
async def test_websocket_route_add_and_remove():
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a WebSocket route
    routing_service.add_route('/ws', 'WEBSOCKET', handler)

    # Create the expected regex pattern for the WebSocket path '/ws'
    regex_path = r'^/ws$'

    # Check that the WebSocket route is correctly added as a regex pattern
    assert regex_path in routing_service.routes
    assert 'WEBSOCKET' in routing_service.routes[regex_path]

    # Remove the WebSocket route
    routing_service.remove_route('/ws', 'WEBSOCKET')

    # Check that the WebSocket route is correctly removed
    assert regex_path not in routing_service.routes


@pytest.mark.asyncio
async def test_route_to_correct_websocket_handler(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a WebSocket route
    routing_service.add_route('/ws', 'WEBSOCKET', handler)

    # Create a mock request object
    scope = {'path': '/ws', 'type': 'websocket'}
    receive = AsyncMock()
    send = AsyncMock()
    request = Request(scope, receive)

    # Create a mock WebSocket event and pass the request object
    event = Event(name='websocket.connection.received', data={
        'request': request,
        'send': send,
        'receive': receive
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure the correct handler was called
    handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_handle_websocket_disconnect(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a WebSocket route
    routing_service.add_route('/ws', 'WEBSOCKET', handler)

    # Create a mock request object for WebSocket
    scope = {'path': '/ws', 'type': 'websocket'}
    receive = AsyncMock()
    send = AsyncMock()
    receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello Server!'},
        {'type': 'websocket.disconnect'}
    ]
    request = Request(scope, receive)

    # Create a mock WebSocket event
    event = Event(name='websocket.connection.received', data={
        'request': request,
        'send': send,
        'receive': receive
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure that the WebSocket handler was called
    handler.assert_called_once_with(event)

    # Check if disconnect was handled properly
    await receive()
    handler.assert_called()


@pytest.mark.asyncio
async def test_handle_websocket_binary_message(monkeypatch):
    event_bus = EventBus()
    config_service = AsyncMock()
    auth_service = AsyncMock()
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, config_service=config_service)

    handler = AsyncMock()

    # Add a WebSocket route
    routing_service.add_route('/ws', 'WEBSOCKET', handler)

    # Create a mock request object for WebSocket
    scope = {'path': '/ws', 'type': 'websocket'}
    receive = AsyncMock()
    send = AsyncMock()
    receive.side_effect = [
        {'type': 'websocket.receive', 'bytes': b'\x00\x01\x02'},
        {'type': 'websocket.disconnect'}
    ]
    request = Request(scope, receive)

    # Create a mock WebSocket event
    event = Event(name='websocket.connection.received', data={
        'request': request,
        'send': send,
        'receive': receive
    })

    # Route the event
    await routing_service.route_event(event)

    # Ensure that the WebSocket handler was called
    handler.assert_called_once_with(event)

    # Check if binary message was handled properly
    await receive()
    handler.assert_called()
