"""Registry dei PID per i job asincroni del JobManager.

Permette a qualsiasi worker del pod di verificare lo stato e terminare un job
a partire dal suo job_id, indipendentemente dal worker che lo ha avviato.
"""

import os
import signal

import psutil

# Each PID file stores two lines: the PID and the process create_time (float).
# The create_time acts as an identity token — if the PID has been recycled by
# the OS the create_time will not match, preventing accidental signals to the
# wrong process.

# Prefer an explicit override, then fall back to ~/.local/run/jm-pids.
_PID_DIR = os.getenv("JM_PID_DIR") or os.path.expanduser(
    os.path.join("~", ".local", "run", "jm-pids")
)


def _pid_path(job_id: str) -> str:
    os.makedirs(_PID_DIR, mode=0o700, exist_ok=True)
    return os.path.join(_PID_DIR, f"{job_id}.pid")


def register(job_id: str, pid: int) -> None:
    try:
        create_time = psutil.Process(pid).create_time()
    except psutil.NoSuchProcess:
        create_time = 0.0
    with open(_pid_path(job_id), "w") as f:
        f.write(f"{pid}\n{create_time}\n")


def unregister(job_id: str) -> None:
    try:
        os.remove(_pid_path(job_id))
    except FileNotFoundError:
        pass


def _read_entry(job_id: str) -> tuple:
    """Return (pid, create_time) or (None, None) if absent/corrupt."""
    try:
        with open(_pid_path(job_id)) as f:
            lines = f.read().strip().splitlines()
        pid = int(lines[0])
        create_time = float(lines[1]) if len(lines) > 1 else None
        return pid, create_time
    except (FileNotFoundError, ValueError, IndexError):
        return None, None


def _read_pid(job_id: str):
    pid, _ = _read_entry(job_id)
    return pid


def _identity_matches(pid: int, stored_create_time) -> bool:
    """Return True iff the live process at pid has the expected create_time."""
    try:
        return psutil.Process(pid).create_time() == stored_create_time
    except psutil.NoSuchProcess:
        return False


def is_alive(job_id: str) -> bool:
    pid, create_time = _read_entry(job_id)
    if pid is None:
        return False
    if not _identity_matches(pid, create_time):
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def kill_job(job_id: str, hard: bool = False) -> bool:
    """Send SIGTERM (or SIGKILL if hard=True) to the job's process and unregister it.

    Returns True if a PID file existed (signal sent or process already gone), False if
    no PID file was found. If the stored identity token does not match the live process
    (PID recycled), the stale file is removed without signalling. unregister() is always
    called on a True return.
    """
    pid, create_time = _read_entry(job_id)
    if pid is None:
        return False
    if not _identity_matches(pid, create_time):
        # PID was recycled — remove the stale file without touching the new process.
        unregister(job_id)
        return True
    try:
        os.kill(pid, signal.SIGKILL if hard else signal.SIGTERM)
    except ProcessLookupError:
        pass
    unregister(job_id)
    return True


def scan_stale() -> list:
    """Return job_ids whose PID files exist but whose process is no longer running."""
    stale = []
    try:
        for fname in os.listdir(_PID_DIR):
            if not fname.endswith(".pid"):
                continue
            job_id = fname[:-4]
            if not is_alive(job_id):
                stale.append(job_id)
    except FileNotFoundError:
        pass
    return stale
