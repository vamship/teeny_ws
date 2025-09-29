from socket import SOL_SOCKET, socket

from teeny_logger import Logger
from websocket import websocket

# Represents a socket level event that is triggered when a connection is
# established or dropped. This is not well documented, but is inferred based on
# the code here:
# https://github.com/micropython/micropython-lib/blob/394cbfc98a333dd1d4db35fb69379c72c30337f3/micropython/net/webrepl/webrepl.py#L104
SOCK_EVENT_CONN_CHANGED = 20

logger = Logger("wses")


class WebSockSession:
    """Manages a session with an open web socket. Can be inherited and
    customized by subclasses"""

    def __init__(self, sock: socket) -> None:
        """Initializes the session with the given socket connection."""
        self._sock = sock
        self._close_handler = None
        self._id = id(self)

        # Disable blocking and setup an event handler for when the connection is
        # closed
        self._sock.setblocking(False)
        self._sock.setsockopt(SOL_SOCKET, SOCK_EVENT_CONN_CHANGED, self._close_handler)

        # The significance of the second parameter (True) is not known at this
        # time. There is no documentation for this, but it is inferred from the
        # code here:
        # https://github.com/AdrianCX/crawlspacebot/blob/6b16b97a4549cb4cb3f3cf811565071c7e5e47bd/src/ws_connection.py#L16
        self._websock = websocket(sock, True)

    @property
    def id(self) -> int:
        """Returns the unique identifier for this session."""
        return self._id

    def read(self) -> bytes:
        """Reads data from the WebSocket."""
        return self._websock.read()

    def write(self, data: bytes) -> None:
        """Writes data to the WebSocket.

        :param data: The data to write to the WebSocket.
        """
        self._websock.write(data)

    def set_close_handler(self, handler: callable) -> None:
        """Sets a handler function to be called when the WebSocket connection
        is closed.

        :param handler: A callable function that takes no parameters and returns
        nothing.
        """
        logger.debug(f"Close handler registered [{self._id}]")
        self._close_handler = handler

    def close(self) -> None:
        """Closes the WebSocket connection."""
        logger.info(f"Closing WebSocket connection [{self._id}]")

        self._websock.close()

        # Remove the event handler for connection changes
        self._sock.setsockopt(SOL_SOCKET, SOCK_EVENT_CONN_CHANGED, None)

        # Close the underlying socket
        self._sock.close()

        # Release the WebSocket object
        self._websock = None

        if self._close_handler:
            logger.debug(f"Invoking websocket close handler [{self._id}]")
            self._close_handler(self)

    def process(self) -> None:
        """Method that can be called periodically to receive and process
        messages from the websocket connection. This method provides the basic
        logic to read a message from the connection and handle any exceptions
        that may occur.

        Child classes can override the `_process` method to process the read
        messages and implement custom application-specific logic.
        """
        try:
            message = self.read()
            if not message:
                return
            self._process(message)
        except Exception as err:
            logger.error(
                f"Error processing WebSocket message: [{self._id}] [{str(err)}]"
            )
            self.close()

    def _process(self, message: bytes) -> None:
        """Processes a message received from the WebSocket. This method is
        intended to be overridden by child classes to implement
        application-specific logic.

        :param message: The message received from the WebSocket connection.
        """
        pass
