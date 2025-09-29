"""
A tiny web server module for Micropython applications running on
microcontrollers such as the ESP32 and ESP8266. Supports fixed responses,
chunked responses and web socket communication.
"""

class WebServer:
    """ A simple, non-blocking HTTP server that delegates request handling to
    user-defined route handlers that can be matched against specific path
    patterns
    """

    def __init__(self, routes: dict[string, callable]):
        """ Initialize the HTTP server with user-defined routes. """
        self._routes = routes
