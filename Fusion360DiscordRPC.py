"""
`Fusion360DiscordRPC.py`
Fusion360 add in entrypoint.

Responsibilities:
    `run()`     - wire up the presencemanager and event handlers
    `stop()`    - tear everything down CALMLY

Requires FusionkitRibbonAPI for ribbon controls (degrades 
gracefully if absent).

All business logic lives in `commands/` and `handlers/`.
"""
import sys
import os

# Ensure the addin dir is on sys.path so relative imports work
# inside fusions python environment
_base = os.path.dirname(os.path.abspath(__file__))
if _base not in sys.path: sys.path.insert(0, _base)

import adsk.core
import adsk.fusion

from commands.presence import PresenceManager
from commands import ribbon
from handlers.document import DocumentActivatedHandler, DocumentCreatedHandler

# ------------------------------------------
#                MODULE STATE
# ------------------------------------------

_manager: PresenceManager | None = None
_handlers: list = []

# ------------------------------------------
#              ADD-IN LIFECYCLE
# ------------------------------------------

def run(context) -> None:
    global _manager, _handlers

    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        _manager = PresenceManager(app, ui)
        _manager.start()

        ribbon.setup(_manager, ui)

        _handlers = _register_handlers(app, _manager)

    except Exception as e:
        import traceback
        ui.messageBox(
            f"Fusion360DiscordRPC failed to start:\n{traceback.format_exc()}",
            "Discord RPC - Error"
        )

def stop(context) -> None:
    global _manager, _handlers

    _handlers.clear()
    ribbon.teardown()

    if _manager:
        _manager.stop()
        _manager = None
    
# ------------------------------------------
#            EVENT REGISTRATION
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
