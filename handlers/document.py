"""
`handlers/document.py`

Fusion360 document event handlers. Each handler calls 
back into the PresenceManager on relevant events.
"""

import adsk.core

from commands.presence import PresenceManager


class DocumentActivatedHandler(adsk.core.DocumentEventHandler):
    """Is referenced when user switches documents."""
    def __init__(self, manager: PresenceManager) -> None:
        super().__init__()
        self._manager = manager

    def notify(self, args: adsk.core.DocumentEventArgs) -> None:
        self._manager.push()

class DocumentCreatedHandler(adsk.core.DocumentEventHandler):
    """Is referenced when a new doc is created."""
    def __init__(self, manager: PresenceManager) -> None:
        super().__init__()
        self._manager = manager

    def notify(self, args: adsk.core.DocumentEventArgs) -> None:
        self._manager.push()