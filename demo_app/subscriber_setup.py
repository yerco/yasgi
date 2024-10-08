from demo_app.subscribers.logging_subscriber import log_request_response
from demo_app.subscribers.timing_subscriber import request_received, request_completed
from demo_app.subscribers.event_log_subscriber import log_event_to_db


def register_subscribers(event_bus):
    event_bus.subscribe("http.request.completed", log_request_response)

    event_bus.subscribe('http.request.received', request_received)
    event_bus.subscribe('http.request.completed', request_completed)

    event_bus.subscribe("user.logout.success", log_event_to_db)
    event_bus.subscribe("user.logout.failure", log_event_to_db)
    event_bus.subscribe("user.login.success", log_event_to_db)
    event_bus.subscribe("user.login.failure", log_event_to_db)
