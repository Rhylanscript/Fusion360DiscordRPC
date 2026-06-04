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
from lib.template import load as load_templates, render, build_tokens
from config.client import CLIENT_ID
from config.config import LARGE_IMAGE_KEY, POLL_INTERVAL


class PresenceManager:
    """
    Owns the Discord IPC connection and the background poll loop.

    LifeCycle:
        `start()`   - connect and begin polling
        `stop()`    - disconnect and stop polling
        `push()`    - manual presence refresh

    Ribbon Controls:
        `enable()`      - re-enable presence (toggle on)
        `disable()`     - suppress presence without disconnecting (toggle off)
        `reconnect()`   - close and reopen the IPC connection
        `set_privacy()` - toggle privacy mode (hides doc name)
 
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

        self._enabled: bool = True
        self._privacy: bool = False

        self._templates: dict[str, str] = load_templates()

    def reload_templates(self) -> None:
        """Reload templates from disk and push a fresh presence."""
        self._templates = load_templates()
        self.push()

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
        
        if not self._connect():
            self._ui.messageBox(
                "Fusion360DiscordRPC: Couldn't connect to Discord.\n"
                "Ensure Discord is running.\n"
                "Use the Reconnect button in the FusionKit tab once discord is open.",
                "Discord RPC"
            )
        
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


    # RIBBON CONTROL

    def enable(self) -> None:
        """Re-enables presence updates (called by toggle turn on)."""
        self._enabled = True
        self.push()

    def disable(self) -> None:
        """Suppress presence updates without disconnecting (called by toggle turning off)."""
        self._enabled = False
        if self._ipc: self._ipc.clear_activity()

    def set_privacy(self, enabled: bool) -> None:
        """Toggle the document privacy mode."""
        self._privacy = enabled
        self.push()

    def reconnect(self) -> bool:
        """
        Close the existing IPC conn and open a new one. Called
        by the reconnect button.

        Returns:
            True if reconnection is a success.
        """
        if self._ipc:
            try:
                self._ipc.close()
            except Exception:...

            self._ipc = None
        
        success = self._connect()
        if success:
            self._start_ts = int(time.time())
            self.push()

        return success

    
    # PRESENCE

    def push(self) -> None:
        """Read Fusion state and send a presence update."""
        if not self._ipc or not self._enabled: return

        details, state, large_text = self._get_fusion_state()
        self._ipc.set_activity({
            "details":      details,
            "state":        state,
            "start_ts":     self._start_ts,
            "large_image":  LARGE_IMAGE_KEY,
            "large_text":   large_text,
        })

    # FUSION STATE

    def _get_fusion_state(self) -> tuple[str, str, str]:
        """Return (details, state, large_text) strings from the current Fusion session."""

        try: 
            doc = self._app.activeDocument
            if doc is None: return self._templates["idle_text"], "", self._templates["large_text"]

            doc_name        = doc.name or "Untitled"
            component_count = self._get_component_count(doc)
            workspace       = self._get_workspace_name()
            app_version     = self._get_app_version()

            tokens = build_tokens(
                document_name   = doc_name,
                workspace       = workspace,
                component_count = component_count,
                app_version     = app_version,
            )

            if self._privacy:
                details = self._templates["privacy_text"]
            else:
                details = render(self._templates["details"], tokens)

            state       = render(self._templates["state"], tokens)
            large_text  = render(self._templates["large_text"], tokens)

            return details, state, large_text
        
        except Exception: return "Fusion 360", "", "Autodesk Fusion 360"

    def _get_component_count(self, doc: adsk.core.Document) -> str:
        """Return a list with component count string or empty if not available."""
        try:
            design = adsk.fusion.Design.cast(
                doc.products.itemByProductType("DesignProductType")
            )

            if not design: return ""

            count = design.rootComponent.allOccurrences.count + 1
            return f"{count} component{'s' if count != 1 else ''}"
        
        except Exception: return ""

    def _get_workspace_name(self) -> str:
        """Return a list with the active workspace name or empty if unavailable."""
        try:
            workspace = self._ui.activeWorkspace
            return workspace.name if workspace else ""
        except Exception: return ""

    def _get_app_version(self) -> str:
        try:
            return self._app.version
        except Exception: return ""

    # INTERNAL

    def _connect(self) -> bool:
        """Open a fresh IPC connection. Returns True on success."""
        ipc = DiscordIPC(CLIENT_ID)
        if ipc.connect():
            self._ipc = ipc
            return True
        return False

    def _poll_loop(self) -> None:
        """Periodically refresh presence so the elapsed timer ticks."""
        while not self._stop_event.wait(POLL_INTERVAL):
            try:
                self.push()
            except Exception:...

    @property
    def enabled(self) -> bool:
        return self._enabled