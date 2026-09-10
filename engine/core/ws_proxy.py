import asyncio
import json
import logging
import os
import queue
import threading
import time
import urllib.parse

logger = logging.getLogger(__name__)

def _get_vm_and_ssh(vm_pk: int):
    from django.conf import settings
    from features.competitions.models import ProvisionedMachine

    vm = ProvisionedMachine.objects.select_related("machine_template").get(pk=vm_pk)

    ssh_user     = os.getenv("PROXMOX_SSH_USER", "root")
    ssh_password = os.getenv("PROXMOX_SSH_PASSWORD")
    ssh_key      = os.getenv("PROXMOX_SSH_KEY_PATH")

    if not ssh_password and not ssh_key:
        raise RuntimeError(
            "No SSH credentials — set PROXMOX_SSH_PASSWORD or PROXMOX_SSH_KEY_PATH"
        )

    connect_kwargs = {
        "username": ssh_user,
        "timeout": 15,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if ssh_key:
        connect_kwargs["key_filename"] = ssh_key
    else:
        connect_kwargs["password"] = ssh_password

    return vm, settings.PROXMOX["host"], connect_kwargs


def _ssh_bridge(vmid, host, connect_kwargs,
                put_output, in_q: queue.Queue, resize_q: queue.Queue,
                stop: threading.Event):
    """
    Daemon thread: SSH → PVE, exec qm terminal <vmid> with a PTY.

    in_q    — raw bytes to send to the SSH channel (keyboard input)
    resize_q — (cols, rows) tuples; triggers channel.resize_pty()
    """
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, **connect_kwargs)
    except Exception as exc:
        put_output(f"\r\n\x1b[31mSSH connection failed: {exc}\x1b[0m\r\n".encode())
        put_output(None)
        return

    channel = ssh.get_transport().open_session()
    # Start with a small PTY — the client sends a resize immediately after connect
    channel.get_pty(term="xterm-256color", width=80, height=24)
    channel.exec_command(f"qm terminal {vmid}")

    try:
        while not stop.is_set():
            # ── output from VM → browser ──────────────────────────────────
            if channel.recv_ready():
                data = channel.recv(4096)
                if not data:
                    break
                put_output(data)

            # ── keyboard input from browser → VM ──────────────────────────
            try:
                while True:
                    data = in_q.get_nowait()
                    if data is None:    # stop sentinel
                        return
                    channel.send(data)
            except queue.Empty:
                pass

            # ── PTY resize requests ───────────────────────────────────────
            try:
                while True:
                    cols, rows = resize_q.get_nowait()
                    channel.resize_pty(width=cols, height=rows)
            except queue.Empty:
                pass

            if channel.exit_status_ready():
                break

            time.sleep(0.01)

    except Exception as exc:
        logger.exception("SSH bridge error for vmid=%s", vmid)
        put_output(f"\r\n\x1b[31mTerminal error: {exc}\x1b[0m\r\n".encode())
    finally:
        try:
            channel.close()
        except Exception:
            pass
        ssh.close()
        put_output(None)


# ── ASGI handler ─────────────────────────────────────────────────────────────

async def console_ws_handler(scope, receive, send) -> None:
    from asgiref.sync import sync_to_async
    from core.console_tokens import consume_token

    event = await receive()
    if event.get("type") != "websocket.connect":
        return

    query = urllib.parse.parse_qs(scope.get("query_string", b"").decode())
    token = query.get("token", [None])[0]
    vm_pk = consume_token(token) if token else None

    if vm_pk is None:
        await send({"type": "websocket.accept"})
        await send({"type": "websocket.send", "text":
                    "\r\n\x1b[31mInvalid or expired token — refresh the page.\x1b[0m\r\n"})
        await send({"type": "websocket.close", "code": 4001})
        return

    await send({"type": "websocket.accept"})
    await send({"type": "websocket.send", "text": "\r\nConnecting to VM console…\r\n"})

    try:
        vm, host, connect_kwargs = await sync_to_async(_get_vm_and_ssh)(vm_pk)
    except Exception as exc:
        await send({"type": "websocket.send", "text":
                    f"\r\n\x1b[31mConfiguration error: {exc}\x1b[0m\r\n"})
        await send({"type": "websocket.close", "code": 4002})
        return

    loop = asyncio.get_event_loop()
    out_q:    asyncio.Queue = asyncio.Queue()
    in_q:     queue.Queue   = queue.Queue()
    resize_q: queue.Queue   = queue.Queue()
    stop = threading.Event()

    def put_output(data):
        loop.call_soon_threadsafe(out_q.put_nowait, data)

    threading.Thread(
        target=_ssh_bridge,
        args=(vm.vmid, host, connect_kwargs, put_output, in_q, resize_q, stop),
        daemon=True,
    ).start()

    async def browser_to_ssh():
        while True:
            msg = await receive()
            if msg.get("type") == "websocket.disconnect":
                return
            if msg.get("type") != "websocket.receive":
                continue

            if msg.get("bytes"):
                # Raw binary → keyboard input
                in_q.put(msg["bytes"])
            elif msg.get("text"):
                # Text → JSON control message
                try:
                    ctrl = json.loads(msg["text"])
                    if ctrl.get("type") == "resize":
                        cols = int(ctrl["cols"])
                        rows = int(ctrl["rows"])
                        if cols > 0 and rows > 0:
                            resize_q.put((cols, rows))
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass  # ignore malformed control messages

    async def ssh_to_browser():
        while True:
            data = await out_q.get()
            if data is None:
                return
            if isinstance(data, bytes):
                await send({"type": "websocket.send", "bytes": data})
            else:
                await send({"type": "websocket.send", "text": data})

    done, pending = await asyncio.wait(
        [asyncio.ensure_future(browser_to_ssh()),
         asyncio.ensure_future(ssh_to_browser())],
        return_when=asyncio.FIRST_COMPLETED,
    )
    stop.set()
    in_q.put(None)
    for task in pending:
        task.cancel()

    try:
        await send({"type": "websocket.close", "code": 1000})
    except Exception:
        pass
