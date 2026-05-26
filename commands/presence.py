"""
`commands/presence.py`

Reads Fusion360 state and pushes rich presence updates
to discord.
"""

import time
import threading

import adsk.core
import adsk.fusion

from lib.discord_ipc import DiscordIPC
from config.CLIENT import CLIENT_ID
from config.config import LARGE_IMAGE_KEY, POLL_INTERVAL


class PresenceManager:
    """
    Owns the Discord IPC connection and the background poll loop.
 
    Usage:
        ```python
        manager = PresenceManager(app, ui)
        if not manager.start():
            # > failed to connect
            return
        manager.push()      # manual refresh
        manager.stop()      # on add-in stop
        ```
    """

    def __init__(
        self,
        app: adsk.core.Application,
        ui: adsk.core.UserInterface
    ) -> None:
        self._app = app
        self._ui = ui

        self._ipc: DiscordIPC | None = None
        self._start_ts: int = 0
        
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # LIFECYCLE

    def start(self) -> bool:
        """
        Connect to Discord IPC and begin the poll loop

        Returns:
            True if connected successfully
        """

        if not CLIENT_ID:
            self._ui.messageBox(
                "Fusion360DiscordRPC: CLIENT_ID is not set.\n"
                "Open/create CLIENT.py and paste your Discord application ID.",
                "Discord RPC",
            )
            return False
        
        self._ipc = DiscordIPC(CLIENT_ID)
        if not self._ipc.connect():
            self._ui.messageBox(
                "Fusion360DiscordRPC: Couldn't connect to Discord.\n"
                "Ensure Discord is running.",
                "Discord RPC"
            )
            return False
        
        self._start_ts = int(time.time())
        self.push()

        self._stop_event.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        return True
    
    def stop(self) -> None:
        """Disconnect from Discord and stop poll loop"""
        self._stop_event.set()

        if self._ipc:
            self._ipc.clear_activity()
            self._ipc.close()
            self._ipc = None
    
    # PRESENCE

    def push(self) -> None:
        """Read Fusion state and send a presence update."""
        if not self._ipc: return

        details, state = self._get_fusion_state()
        self._ipc.set_activity({
            "details": details,
            "state": state,
            "start_ts": self._start_ts,
            "large_image": LARGE_IMAGE_KEY,
            "large_text": "Autodesk Fusion 360"
        })

    # FUSION STATE

    def _get_fusion_state(self) -> tuple[str, str]:
        """Return (details, state) strings from the current Fusion session."""

        try: 
            doc = self._app.activeDocument
            if doc is None: return "Idle", "No Document Open"

            doc_name = doc.name or "Untitled"
            details = f'Designing "{doc_name}"'
            state_parts: list[str] = []

            state_parts += self._get_component_info(doc)
            state_parts += self._get_workspace_info()

            state = " · ".join(state_parts) if state_parts else "Fusion 360"
            return details, state
        
        except Exception: return "Fusion 360", ""

    def _get_component_info(self, doc: adsk.core.Document) -> list[str]:
        """Return a list with component count string or empty if not available."""
        try:
            design = adsk.fusion.Design.cast(
                doc.products.itemByProductType("DesignProductType")
            )

            if not design: return []

            count = design.rootComponent.allOccurrences.count + 1
            return [f"{count} component{'s' if count != 1 else ''}"]
        
        except Exception: return []

    def _get_workspace_info(self) -> list[str]:
        """Return a list with the active workspace name or empty if unavailable."""
        try:
            workspace = self._ui.activeWorkspace
            return [workspace.name] if workspace else []
        except Exception: return []

    # BACKGROUND POLLING

    def _poll_loop(self) -> None:
        """Periodically refresh presence so the elapsed timer ticks."""
        while not self._stop_event.wait(POLL_INTERVAL):
            try:
                self.push()
            except Exception:...