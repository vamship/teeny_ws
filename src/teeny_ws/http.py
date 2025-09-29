from binascii import b2a_base64
from hashlib import sha1
from socket import socket

from micropython import const
from teeny_logger import Logger

logger = Logger("http")

# Websocket connection magic string
WS_MAGIC_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode("utf-8")

# Buffer size for chunked responses
STREAM_BUFFER_SIZE = const(1024)

# Mapping of http response codes to their messages
RESP_CODE_MESSAGES = {
    101: const("Switching Protocols"),
    200: const("Ok"),
    204: const("No Content"),
    404: const("Not Found"),
    500: const("Internal Server Error"),
    400: const("Bad Request"),
    418: const("I am a teapot"),
}

# Mapping of file extensions to content types
CONTENT_TYPES = {
    const(".html"): const("text/html"),
    const(".css"): const("text/css"),
    const(".js"): const("application/javascript"),
    const(".json"): const("application/json"),
    const(".png"): const("image/png"),
    const(".txt"): const("text/plain"),
    const(".gif"): const("image/gif"),
    const(".ico"): const("image/x-icon"),
    const(".svg"): const("image/svg+xml"),
}


class HttpRequest:
    """Class to represent an HTTP request. Can be initialized with a socket, and
    provides methods to parse and retrieve request details"""

    def __init__(self, sock: socket) -> None:
        """Initializes an HttpRequest using the specified connection object.

        :param sock: An open socket connection to read the request from.
        """
        self._sock = sock
        self._request_parsed = False
        self._headers_parsed = False
        self._verb = None
        self._path = None
        self._params = None
        self._headers = None

    def _parse_request(self) -> None:
        """Parses the request line - verb, path, and parameters - from the
        socket connection. This is an idempotent operation.
        """
        if self._request_parsed:
            return

        logger.debug("Parsing request line")

        request_bytes = self._sock.readline()
        request_line = request_bytes.decode("utf-8").strip()
        logger.debug(f"Request line: {request_line}")

        [self._verb, self._path, _] = request_line.split(" ")
        tokens = self._path.split("?")
        path = tokens[0]
        self._params = {}

        if len(tokens) > 1:
            query = tokens[1].split("&")
            for param in query:
                [key, value] = param.split("=", 1)
                self._params[key] = value

        self._request_parsed = True
        logger.debug(
            f"Parsed request: verb={self._verb}, path={self._path}, params={self._params}"
        )

    def _parse_headers(self) -> None:
        """Parses the headers from the socket connection."""
        if self._headers_parsed:
            return
        self._parse_request()

        logger.debug("Parsing headers")
        self._headers = {}
        while (header_line := self._sock.readline()) != b"\r\n":
            header_line = header_line.decode("utf-8").strip()
            [header_name, header_value] = header_line.split(":", 1)
            header_name = header_name.strip().lower()
            header_value = header_value.strip()
            self._headers[header_name] = header_value
            logger.debug(f"Parsed header: {header_name}={header_value}")

        self._headers_parsed = True

    @property
    def socket(self) -> socket:
        """Returns the socket connection associated with the request."""
        return self._sock

    @property
    def verb(self) -> str:
        """Returns the HTTP verb of the request."""
        self._parse_request()
        return self._verb

    @property
    def path(self) -> str:
        """Returns the request path of the request."""
        self._parse_request()
        return self._path

    def get_param(self, key: str) -> str:
        """Returns the value of a parameter given its key. If the parameter
        does not exist, None will be returned.

        :param key: The key (name) of the parameter.
        """
        self._parse_request()
        return self._params.get(key, None)

    def get_header(self, key: str) -> str:
        """Returns the value of a header given its key. If the header does not
        exist, None will be returned.

        :param key: The key (name) of the header.
        """
        self._parse_headers()
        return self._headers.get(key.lower(), None)


class HttpResponse:
    """Class that represents an HTTP response"""

    def __init__(self, code: int) -> None:
        """Initializes the http response using the specified response string
        :param code: The HTTP response code (e.g., 200, 404).
        """
        self._code = code
        self._headers = {}
        self._body = None
        self._stream_response = False
        self._close_connection = True

    def _send_headers(self, sock: socket) -> None:
        """Sends the headers of the response over the specified socket
        connection.

        PRIVATE: This is a private method that is not intended to be called
        directly by subclasses or external code.

        :param sock: The socket connection to send the response over.
        """
        total_bytes = 0
        header_count = 0
        for header_name, header_value in self._headers.items():
            count = sock.write(f"{header_name}: {header_value}\r\n".encode("utf-8"))
            total_bytes += count
            header_count += 1
        logger.debug(f"Sent [{header_count}] headers; [{count}] bytes")

        # Send header terminator
        sock.write("\r\n".encode("utf-8"))

    def _send_fixed_body(self, sock: socket) -> None:
        """Sends the body of the response as a fixed-length payload.

        PRIVATE: This is a private method that is not intended to be called
        directly by subclasses or external code.

        :param sock: The socket connection to send the response over.
        """
        total_bytes = sock.write(self._body or "")
        logger.debug(f"Sent body [{total_bytes}] bytes")

    def _send_chunked_body(self, sock: socket) -> None:
        """Sends the body of the response as a stream using chunked transfer
        encoding.

        PRIVATE: This is a private method that is not intended to be called
        directly by subclasses or external code.

        :param sock: The socket connection to send the response over.
        """
        with self._body as body:
            buffer = bytearray(STREAM_BUFFER_SIZE)
            chunk_count = 0
            total_bytes = 0
            while (chunk_size := body.readinto(buffer)) > 0:
                chunk = buffer[:chunk_size]
                total_bytes += sock.write(f"{chunk_size:x}\r\n".encode("utf-8"))
                total_bytes += sock.write(chunk)
                total_bytes += sock.write("\r\n".encode("utf-8"))
                chunk_count += 1
                logger.debug(
                    f"Sent [{chunk_count}] chunks [{total_bytes} ({chunk_size})] bytes"
                )
            total_bytes += sock.write("0\r\n\r\n".encode("utf-8"))
            logger.debug(f"Sent stream [{chunk_count}] chunks; [{total_bytes}] bytes")

    @property
    def code(self) -> int:
        """Returns the response code associated with the response."""
        return self._code

    @property
    def body(self) -> str:
        """Returns the response body."""
        return self._body

    @property
    def response_code_message(self) -> str:
        """Returns the message associated with the response code"""
        return RESP_CODE_MESSAGES.get(self._code, "NOT DEFINED")

    @property
    def close_connection(self) -> bool:
        """Returns True if the connection should be closed after sending the
        response, False otherwise. The default is True.
        """
        return self._close_connection

    @close_connection.setter
    def close_connection(self, value: bool) -> None:
        """Sets whether the connection should be closed after sending the
        response.

        :param value: True to close the connection after sending the response,
        False otherwise.
        """
        self._close_connection = value

    def set_header(self, key: str, value: str) -> None:
        """Sets a header for the response.

        :param key: The header key (name).
        :param value: The header value.
        """
        self._headers[key.lower()] = value

    def get_header(self, key: str) -> str:
        """Returns the value of a header given its key. If the header does not
        exist, None will be returned.

        :param key: The key (name) of the header.
        """
        return self._headers.get(key.lower(), None)

    def set_json_body(self, body: dict) -> None:
        """Sets the body of the response as a JSON string.

        :param body: The body of the response as a dictionary.
        """
        import json

        self.set_header("content-type", "application/json")
        self._body = json.dumps(body).encode("utf-8")

    def set_html_body(self, body: str) -> None:
        """Sets the body of the response as an HTML string. The body is
        converted to UTF-8 bytes before being set.

        :param body: The body of the response as a string.
        """
        self.set_header("content-type", "text/html")
        self._body = body.encode("utf-8")

    def set_text_body(self, body: str) -> None:
        """Sets the body of the response as a plain string. The body is
        converted to UTF-8 bytes before being set.

        :param body: The body of the response as a string.
        """
        self.set_header("content-type", "text/plain")
        self._body = body.encode("utf-8")

    def set_file_body(self, file_path: str, content_type: str = None) -> None:
        """Sets the body as the contents of the specified file. If an explicit
        content type is not specified, it will be inferred based on the
        type of the response is inferred based on the extension of the file.

        Note that all file extensions can be inferred from the extension. Common
        file extensions will be inferred, but if the extension is not
        recognized, 'application/octet-stream' will be used as the content type.

        The contents of the file are read and streamed to the client using a
        chunked transfer encoding.

        :param body: Name/path of the file to read the body from.
        :param content_type: The content type of the response
        """
        if content_type is None:
            ext = file_path.split(".")[-1]
            content_type = CONTENT_TYPES.get(f".{ext}", "application/octet-stream")
        self.set_header("content-type", content_type)
        self._body = open(file_path, "rb")
        self._stream_response = True

    def set_raw_body(self, content_type: str, body: bytes) -> None:
        """Sets the body of the response with the specified content type and
        body. The body is passed as-is, and is expected to be in bytes.

        :param content_type: The content type of the response
        :param body: The body of the response.
        """
        self.set_header("content-type", content_type)
        self._body = body

    def send(self, sock: socket) -> None:
        """Sends an HTTP response over the specified socket connection.

        :param sock: The socket connection to send the response over.
        """
        message = RESP_CODE_MESSAGES.get(self._code, "UNKNOWN")
        if self._stream_response:
            self.set_header("Transfer-Encoding", "chunked")
            logger.info(f"Sending chunked response: [{self._code}]")
        else:
            content_length = len(self._body) if self._body else 0
            self.set_header("Content-Length", content_length)
            logger.info(
                f"Sending fixed response: [{self._code}]; [{content_length}] bytes"
            )

        # Add/update response headers
        if self._close_connection:
            self.set_header("Connection", "close")

        # Send response line
        count = sock.write(f"HTTP/1.1 {str(self._code)} {message}\r\n")
        logger.debug(f"Sent HTTP response line [{count}] bytes")

        # Send headers
        self._send_headers(sock)

        # Send body
        if self._stream_response:
            self._send_chunked_body(sock)
        else:
            self._send_fixed_body(sock)


def create_ws_upgrade_response(req: HttpRequest) -> HttpResponse:
    """Create a WebSocket upgrade response. This is a utility function that can
    be used as part of a request handler that accepts a websocket upgrade
    request, and initiates a websocket session.

    :param req: The HttpRequest object containing the request initiated by the
    client.
    """

    web_key = req.get_header("Sec-WebSocket-Key")
    if not web_key:
        return HttpResponse(400, "Missing Sec-WebSocket-Key header")

    # Convert the Sec-WebSocket-Key to utf-8 so that it can be hashed.
    web_key = web_key.encode("utf-8")
    response_key = sha1(web_key + WS_MAGIC_STRING).digest()
    handshake_response = b2a_base64(response_key)[:-1]
    handshake_response = handshake_response.decode("utf-8")

    logger.debug(f"WebSocket handshake response key: {handshake_response}")
    response = HttpResponse(101)
    response.set_header("Upgrade", "websocket")
    response.set_header("Connection", "Upgrade")
    response.set_header("Sec-WebSocket-Accept", handshake_response)
    response.close_connection = False

    return response
