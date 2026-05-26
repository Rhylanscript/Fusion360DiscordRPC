"""
`Fusion360DiscordRPC.py`
Fusion360 add in entrypoint.

Hooks into Fusion360's workspace events and pushes RPC
updates to discord through the local IPC socket. 
(established from `discord_ipc.py`)

Responsibilities:
    `run()`     - wire up the presencemanager and event handlers
    `stop()`    - tear everything down CALMLY

All business logic lives in `commands/` and `handlers/`.
"""
import sys
import os

# Ensure the addin dir is on sys.path so relative imports work
# inside fusions python environment
_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _base)

import adsk.core
import adsk.fusion

from commands.presence import PresenceManager
from handlers.document import DocumentActivatedHandler, DocumentCreatedHandler

# ------------------------------------------
#               MODULE STATE
# ------------------------------------------

_manager: PresenceManager | None = None
_handlers: list = []

# ------------------------------------------
#             ADD-IN LIFECYCLE
# ------------------------------------------

def run(context) -> None:
    global _manager, _handlers

    app = adsk.core.Application.get()
    ui = app.userInterface

    _manager = PresenceManager(app, ui)
    if not _manager.start(): return

    _handlers = _register_handlers(app, _manager)

def stop(context) -> None:
    global _manager, _handlers

    if _manager:
        _manager.stop()
        _manager = None

    _handlers.clear()
    
# ------------------------------------------
#             EVENT REGISTRATION
# ------------------------------------------

def _register_handlers(
        app: adsk.core.Application,
        manager: PresenceManager,
    ) -> list:

    """Register all Fusion event handlers and return them for later cleanup."""

    handlers = []

    activated = DocumentActivatedHandler(manager)
    app.documentActivated.add(activated)
    handlers.append(activated)

    created = DocumentCreatedHandler(manager)
    app.documentCreated.add(created)
    handlers.append(created)

    return handlers
