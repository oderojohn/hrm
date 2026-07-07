"""Core sync loop: poll each configured ZK device, store new punches locally,
then push whatever's still unpushed to the cloud. Called on a timer from
ui.py's background thread, or once for a manual "Sync Now"/"Test Connection".
"""
import json
import urllib.error
import urllib.request
from datetime import datetime

from agent import db
from agent.zk_client import ZKClient


def _log(callback, level, message):
    if callback:
        callback(datetime.now(), level, message)


def push_batch(cloud_url, api_key, device_name, device_ip, users, punches):
    """POSTs one batch to the cloud's sync push endpoint. Returns (ok, result)
    where result is the parsed JSON response on success, or an error string.
    """
    payload = {"device_name": device_name, "device_ip": device_ip, "users": users, "punches": punches}
    req = urllib.request.Request(
        cloud_url.rstrip("/") + "/api/attendance/sync/push/",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        method="POST",
    )
    # A first-time sync can carry months of backlog in one batch (hundreds of
    # punches), which takes the server longer than a typical steady-state
    # push — scale the timeout with batch size rather than using one fixed value.
    timeout = max(30, len(punches) // 2)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return False, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return False, str(e)


def sync_device(device_cfg, cloud_url, api_key, log_callback=None):
    """Runs one full poll+store+push cycle for a single configured device.
    Never raises — all errors are caught and logged so one bad device
    doesn't stop the others (sync_all loops over devices).
    """
    name, ip, port = device_cfg["name"], device_cfg["ip"], device_cfg.get("port", 4370)
    _log(log_callback, "info", f"[{name}] Connecting to {ip}:{port}...")

    try:
        client = ZKClient(ip, port)
        users = client.fetch_users()
        logs = client.fetch_attendance_logs()
    except Exception as exc:
        _log(log_callback, "error", f"[{name}] Could not reach device: {exc}")
        return {"device": name, "ok": False, "error": str(exc)}

    _log(
        log_callback,
        "info",
        f"[{name}] Device reachable — {len(users)} enrolled user(s), {len(logs)} punch record(s) on device.",
    )

    new_count = 0
    for entry in logs:
        raw_status = getattr(entry, "punch", None)
        if raw_status is None:
            raw_status = getattr(entry, "status", None)
        was_new = db.insert_punch(name, str(entry.user_id).strip(), entry.timestamp, raw_status)
        new_count += int(was_new)

    if new_count:
        _log(log_callback, "info", f"[{name}] Stored {new_count} newly-seen punch(es) locally.")
    else:
        _log(log_callback, "info", f"[{name}] No new punches since last check.")

    unpushed = db.get_unpushed_punches(name)
    if not unpushed:
        _log(log_callback, "info", f"[{name}] Nothing to push — up to date with the cloud.")
        return {"device": name, "ok": True, "new_local": new_count, "pushed": 0}

    _log(log_callback, "info", f"[{name}] Pushing {len(unpushed)} unpushed punch(es) to the cloud...")
    users_payload = [{"user_id": str(u.user_id).strip(), "name": u.name} for u in users]
    punches_payload = [
        {"user_id": p["device_user_id"], "timestamp": p["timestamp"], "raw_status": p["raw_status"]}
        for p in unpushed
    ]
    ok, result = push_batch(cloud_url, api_key, name, ip, users_payload, punches_payload)

    if ok:
        db.mark_pushed([p["id"] for p in unpushed])
        _log(log_callback, "success", f"[{name}] Push accepted: {result.get('detail', 'OK')}")
        return {"device": name, "ok": True, "new_local": new_count, "pushed": len(unpushed)}

    _log(log_callback, "error", f"[{name}] Push failed: {result}")
    return {"device": name, "ok": False, "error": str(result)}


def sync_all(config, log_callback=None):
    """Runs sync_device for every configured device, isolating failures —
    mirrors the cloud's own sync_all_devices isolation pattern."""
    db.init_db()
    results = []
    devices = config.get("devices", [])
    if not devices:
        _log(log_callback, "warn", "No devices configured — open Settings to add one.")
        return results
    for device_cfg in devices:
        results.append(sync_device(device_cfg, config["cloud_url"], config["api_key"], log_callback))
    return results
