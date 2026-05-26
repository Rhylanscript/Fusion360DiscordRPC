"""
`Fusion360DiscordRPC.py`
Fusion360 add in entrypoint.

Hooks into Fusion360's workspace events and pushes RPC
updates to discord through the local IPC socket. 
(established from `discord_ipc.py`)
"""

import adsk.core
import adsk.fusion

import time
import threading

# try resolving import?
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_ipc import DiscordIPC, CLIENT_ID

# ------------------------------------------
#                   CONFIG
# ------------------------------------------

POLL_INTERVAL = 15              # seconds between presence refreshes
LARGE_IMAGE_KEY = "fusion360"   # image key registered in Discord Dev Portal

# ------------------------------------------
#               MODULE STATE
# ------------------------------------------

_app: adsk.core.Application | None = None
_ui: adsk.core.UserInterface | None = None
_handlers = []
_ipc: DiscordIPC | None = None
_start_ts: int = 0
_poll_thread: threading.Thread | None = None
_stop_event = threading.Event()

# ------------------------------------------
#             ADD-IN LIFECYCLE
# ------------------------------------------

def run(context):
    global _app, _ui, _ipc, _start_ts, _poll_thread

    # temp debug log
    import pathlib
    _log = pathlib.Path.home() / "fusionrpc_debug.txt"
    _log.write_text("run() called\n")

    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        _log.write_text("got app and ui\n")

        if not CLIENT_ID:
            _ui.messageBox(
                "Fusion360DiscordRPC: No CLIENT_ID set.\n"
                "Open discord_ipc.py and fill in your Discord application ID.",
                "Discord RPC"
            )
            return
        
        _ipc = DiscordIPC(CLIENT_ID)
        connected = _ipc.connect()
        _log.write_text(f"connected: {connected}\n")

        if not connected:
            _ui.messageBox(
                "Fusion360DiscordRPC: Could not connect to Discord IPC.\n"
                "Make sure Discord is running.",
                "Discord RPC"
            )
            return
        
        _start_ts = int(time.time())

        # push initial presence
        _push_presence()

        # hook doc events for instant updates
        _register_handlers()

        # background poll so elapsed timer stays fresh
        _stop_event.clear()
        _poll_thread = threading.Thread(target=_poll_loop, daemon=True)
        _poll_thread.start()
    except Exception as e:
        import traceback
        _log.write_text(f"EXCEPTION:\n{traceback.format_exc()}\n")
        raise


def stop(context):
    global _ipc, _poll_thread

    _stop_event.set()

    if _ipc:
        _ipc.clear_activity()
        _ipc.close()
        _ipc = None

    _handlers.clear()

# ------------------------------------------
#              PRESENCE LOGIC
# ------------------------------------------

def _push_presence():
    """Read fusion state and send a presence update"""
    if not _ipc: return

    details, state = _get_fusion_state()

    _ipc.set_activity({
        "details": details,
        "state": state,
        "start_ts": _start_ts,
        "large_image": LARGE_IMAGE_KEY,
        "large_text": "Autodesk Fusion 360",
    })

def _get_fusion_state() -> tuple[str, str]:
    """Return (details, state) strings describing the current fusion session."""
    try: 
        if _app is None or _ui is None: return "Fusion 360", ""

        doc = _app.activeDocument
        if doc is None: return "Idle", "No document open"

        doc_name = doc.name or "Untitled"

        # component count
        details = f"Designing \"{doc_name}\""
        state_parts = []

        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            if design:
                root = design.rootComponent
                count = root.allOccurrences.count + 1   # add the root as a component itself
                state_parts.append(f"{count} component{'s' if count != 1 else ''}")

        except Exception:...

        # get active workspace
        try:
            workspace = _ui.activeWorkspace
            if workspace: state_parts.append(workspace.name)

        except Exception:...

        state = " · ".join(state_parts) if state_parts else "Fusion 360"
        return details, state
    
    except Exception:
        return "Fusion 360", ""
    
# ------------------------------------------
#               EVENT HANDLERS
# ------------------------------------------

class _DocumentActivatedHandler(adsk.core.DocumentEventHandler):
    def notify(self, args: adsk.core.DocumentEventArgs) -> None:
        _push_presence()

class _DocumentCreatedHandler(adsk.core.DocumentEventHandler):
    def notify(self, args: adsk.core.DocumentEventArgs) -> None:
        _push_presence()

def _register_handlers():
    if _app is None: return

    h1 = _DocumentActivatedHandler()
    _app.documentActivated.add(h1)
    _handlers.append(h1)

    h2 = _DocumentCreatedHandler()
    _app.documentCreated.add(h2)
    _handlers.append(h2)


# ------------------------------------------
#               BACKGROUND POLL
# ------------------------------------------

def _poll_loop():
    """Periodically refresh presence so the elapsed timer ticks."""
    while not _stop_event.wait(POLL_INTERVAL):
        try: 
            _push_presence()
        except Exception:...