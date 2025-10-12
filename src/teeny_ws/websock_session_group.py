from teeny_logger import Logger

from .websock_session import WebSockSession

logger = Logger("wseg")
_default_group = None


class WebSockSessionGroup:
    """Class that manages a group of websocket sessions. This method can be
    used to invoke periodic methods on each session within the group.
    """

    def __init__(self, name="default") -> None:
        """Initializes the session group."""
        self._name = name
        self._sessions = []
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Flag that indicates whether or not the group is running (i.e.,
        polling and processing requests over one or more websocket sessions)
        """
        return self._is_running

    @property
    def name(self) -> str:
        """The name of the current group"""
        return self._name

    def add_connection(self, session: WebSockSession) -> None:
        """Adds a new web socket session to the group.

        :param session: A websocket session object represeting the web socket
        session.
        """
        logger.info(f"Added new connection [{session.id}]")
        session.set_close_handler(self.remove_connection)
        self._sessions.append(session)

    def remove_connection(self, session: WebSockSession) -> None:
        """Removes a WebSocket connection from the manager.

        :param session: The web socket session to remove from the group.
        """
        logger.info(f"Removed connection [{self._name}] [{session.id}]")
        self._sessions.remove(session)

    def start(self) -> None:
        """Method that periodically invokes the process methods on each of the
        active sessions within the group.
        """
        import time

        logger.info(f"Starting web socket group [{self._name}]")
        self._is_running = True
        while self._is_running:
            # --- HACK ---
            # Adding a small sleep here to allow interrupts triggered by other
            # threads to be processed.
            time.sleep(0.0005)
            for session in self._sessions:
                session.process()

    def stop(self) -> None:
        """Stops processing messages within the group"""
        logger.info(f"Stopping websocket group [{self._name}]")
        self._is_running = False


def get_default_group() -> WebSockSessionGroup:
    """Returns the default session group. If it does not exist, it will be
    created.

    :return: The default session group.
    """
    global _default_group
    if _default_group is None:
        _default_group = WebSockSessionGroup()
    return _default_group
