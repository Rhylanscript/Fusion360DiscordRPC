"""
`discord_ipc.py`

Minimal Discord rich presence IPC client.
"""

import json
import os
import socket
import struct
import sys
import uuid

from typing import Any, IO
from config import CLIENT_ID

OP_HANDSHAKE: int = 0
OP_FRAME: int = 1
OP_CLOSE: int = 2

def _get_ipc_path(pipe_num: int = 0) -> str:
    """Returns platform-specific IPC socket path."""
    if sys.platform == "win32":
        return f"\\\\.\\pipe\\discord-ipc-{pipe_num}"
    
    for env in ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP"):
        path = os.environ.get(env)
        if path: return os.path.join(path, f"discord-ipc-{pipe_num}")
    
    return f"/tmp/discord-ipc-{pipe_num}"

class DiscordIPC:
    """
    Lightweight Discord IPC connection for rich presence.
    
    Connection:
        connect:        establishes a connection through discord handshake
        close:          close the IPC connection established after `.connect()`

    RPC:
        set_activity:   Set the client activity status with a dictionary containing keys
        clear_activity: Removes the rich presence overlay
    """

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

        self._sock: socket.socket | None = None
        self._pipe: IO[bytes] | None = None

        self._connected = False

    # connection lifecycle

    def connect(self) -> bool:
        """
        Open IPC socket and do the discord handshake.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        for i in range(10):
            path = _get_ipc_path(i)
            try:
                if sys.platform == "win32":
                    # named pipes are openable with open() im pretty sure?
                    self._pipe = open(path, "r+b", buffering=0)
                    self._connected = True
                else:
                    self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    self._sock.connect(path)
                    self._connected = True
                break
            except Exception as e:
                print(f"IPC connect attempt {i} failed: {e}")
        
        if not self._connected: return False

        self._send(OP_HANDSHAKE, {"v": 1, "client_id": self.client_id})
        resp = self._recv()
        return resp is not None
    
    def close(self):
        """Close the IPC conn."""
        if not self._connected: return

        try:
            self._send(OP_CLOSE, {})
        except Exception as e:
            print(f"Error: {e}")

        if sys.platform == "win32":
            if self._pipe:
                self._pipe.close()
                self._pipe = None
        elif self._sock:
            self._sock.close()

        self._connected = False

    # rich presence
    
    def set_activity(self, activity: dict):
        """
        Push a rich presence update to discord.

        Activity dictionary keys (all are optional)
            details     str - first line of presence text
            state       str - second line
            start_ts    int - epoch seconds (for the 'elapsed' timer)
            large_image str - image key registered in dev portal
            large_text  str - tooltip on large image
            small_image str
            small_text  str 
        """
        if not self._connected: return

        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": self._build_activity(activity),
            },
            "nonce": str(uuid.uuid4()),
        }
        self._send(OP_FRAME, payload)
        self._recv()

    def clear_activity(self):
        """Remove rich presence overlay"""
        if not self._connected: return

        payload = {
            "cmd": "SET_ACTIVITY",
            "args": { "pid": os.getpid(), "activity": None },
            "nonce": str(uuid.uuid4()),
        }
        self._send(OP_FRAME, payload)
        self._recv()

    # HELPERS

    @staticmethod
    def _build_activity(a: dict) -> dict:
        activity = {}

        if "details" in a: activity["details"] = str(a["details"])[:128]
        if "state" in a: activity["state"] = str(a["state"])[:128]
        if "start_ts" in a: activity["timestamps"] = { "start": int(a["start_ts"]) }

        assets = {}

        if "large_image" in a: assets["large_image"] = a["large_image"]
        if "large_text" in a: assets["large_text"] = str(a["large_text"])[:128]
        if "small_image" in a: assets["small_image"] = a["small_image"]
        if "small_text" in a: assets["small_text"] = str(a["small_text"])[:128]

        if assets: activity["assets"] = assets

        return activity
    
    def _send(self, op: int, data: dict):
        payload = json.dumps(data).encode("utf-8")
        header = struct.pack("<II", op, len(payload))
        msg = header + payload

        if sys.platform == "win32":
            if self._pipe:
                self._pipe.write(msg)
                self._pipe.flush()  
        else:
            if self._sock: self._sock.sendall(msg)

    def _recv(self):
        try:
            header = self._read_exactly(8)
            if not header: return None

            op, length = struct.unpack("<II", header)
            body = self._read_exactly(length)
            if not body: return None

            return json.loads(body.decode("utf-8"))
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        

    def _read_exactly(self, n: int) -> bytes:
        buf = b""

        if sys.platform == "win32":
            if self._pipe:
                while len(buf) < n:
                    chunk = self._pipe.read(n - len(buf))
                    if not chunk: break
                    buf += chunk

        else:
            if self._sock:
                while len(buf) < n:
                    chunk = self._sock.recv(n - len(buf))
                    if not chunk: break
                    buf += chunk
        
        return buf
