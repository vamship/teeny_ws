"""
A tiny web server module for Micropython applications running on
microcontrollers such as the ESP32 and ESP8266. Supports fixed responses,
chunked responses and web socket communication.
"""

import re
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, socket

from teeny_logger import Logger

from .http import HttpRequest, HttpResponse

logger = Logger("serv")

# Default routes to use if no matching routes are found
DEFAULT_ROUTES = {}

# Default handler to report that a route did not match
NOT_FOUND_HANDLER = lambda req: HttpResponse(404)

# Represents a socket level event that is triggered when a connection is
# established or dropped. This is not well documented, but is inferred based on
# the code here:
# https://github.com/micropython/micropython-lib/blob/394cbfc98a333dd1d4db35fb69379c72c30337f3/micropython/net/webrepl/webrepl.py#L104
SOCK_EVENT_CONN_CHANGED = 20


class WebServer:
    """A simple, non-blocking HTTP server that delegates request handling to
    user-defined route handlers that can be matched against specific path
    patterns
    """

    def __init__(self, routes: dict[string, callable]):
        """Initialize the HTTP server with user-defined routes."""
        self._routes = routes

    def _create_connection_handler(self) -> callable:
        """Creates and returns a connection handler function that can accept
        and process incoming connections."""

        def _handle_connection(sock: socket) -> None:
            """Handle a connection event on the socket. Invoked by the socket
            when a connection is established, and is responsible for processing
            the request and sending a response.

            :param sock: The socket that received the connection.
            """
            conn, addr = sock.accept()
            logger.info(f"HTTP client connected [{addr}]")

            try:
                # Extract http request from the connection.
                request = HttpRequest(conn)

                logger.debug(f"Http verb [{request.verb}]")
                route_set = self._routes.get(request.verb, DEFAULT_ROUTES)

                # Assume that the request path is not found by default.
                handler = NOT_FOUND_HANDLER
                for path_pattern in route_set.keys():
                    logger.debug(
                        f"Checking pattern [{path_pattern}] for [{request.path}]"
                    )

                    if re.match(path_pattern, request.path):
                        # If the path pattern matches, use the corresponding
                        # handler and break out of the loop.
                        logger.debug(f"Found matching route: [{path_pattern}]")
                        handler = route_set[path_pattern]
                        break

                logger.debug("Invoking request handler")
                response = handler(request)
            except Exception as err:
                logger.error(f"Error processing request: [{str(err)}]")
                response = HttpResponse(500)
                response.set_text_body("Unexpected error while processing request")
            response.send(conn)
            logger.info(f"Sent response to [{addr}]")

            # We're not closing our connection here because it interrupts the
            # response to the client. The connection should close automatically
            # when the socket is garbage collected. This solution is less than
            # ideal, but it might the best we can do.

        return _handle_connection

    def start(self) -> None:
        """Start the HTTP server."""

        # Initialize a socket and bind to all interfaces on port 80
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", 80))

        # Listen for incoming connections; Allow up to 5 queued connections
        sock.listen(5)

        connection_handler = self._create_connection_handler()
        sock.setsockopt(SOL_SOCKET, SOCK_EVENT_CONN_CHANGED, connection_handler)
        logger.info("HTTP server started, listening on port 80.")
