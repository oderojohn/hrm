"""Thin wrapper around a Hikvision ISAPI Time & Attendance controller (e.g.
DS-K1A85xx) — mirrors zk_client.py's shape (fetch_users/fetch_attendance_logs
returning objects with .user_id/.name or .user_id/.timestamp/.punch) so
sync_engine.py can poll either device brand through the same pipeline.

Verified directly against a real DS-K1A8503MF-B unit: JSON responses via
?format=json, HTTP Digest auth, paginated search endpoints.
"""
import time
from datetime import datetime
from types import SimpleNamespace

import requests
from requests.auth import HTTPDigestAuth

PAGE_SIZE = 30

# Hikvision's own anti-brute-force "Illegal Login Lock" counts rapid digest
# auth handshakes as suspicious regardless of whether they succeed — a burst
# of back-to-back paginated requests can trip it (confirmed against a real
# DS-K1A8503MF-B: it locked out after ~18 unpaced requests). A small gap
# between pages keeps routine syncing well clear of that threshold.
PAGE_DELAY_SECONDS = 1.5

# Separately from the lockout above, this device's embedded auth service has
# also been observed returning a spurious, transient 401 on an otherwise-valid
# request — confirmed by a follow-up request seconds later succeeding with the
# exact same credentials. A short retry absorbs that flakiness instead of
# failing the whole sync cycle over what turned out to be a one-off blip.
UNAUTHORIZED_RETRY_ATTEMPTS = 2
UNAUTHORIZED_RETRY_DELAY_SECONDS = 4

# Hikvision's own attendanceStatus classification, when the device has T&A
# schedule/reader-mode rules configured — mapped onto the exact same
# raw_status convention the cloud already understands for ZKTeco devices
# (0/4=IN, 1/5=OUT), so no backend changes are needed to support a second
# device brand. Until T&A rules are configured on the device, every event
# comes through as "undefined" (mapped to None here) and the cloud's own
# open/close session-pairing fallback takes over — the same fallback
# already handling ambiguous ZKTeco punches.
_STATUS_TO_RAW = {
    "checkIn": 0,
    "breakIn": 0,
    "overtimeIn": 0,
    "checkOut": 1,
    "breakOut": 1,
    "overtimeOut": 1,
}


class HikvisionClient:
    def __init__(self, ip, port=80, username="admin", password="", timeout=15):
        self.base_url = f"http://{ip}:{port}"
        self.auth = HTTPDigestAuth(username, password)
        self.timeout = timeout

    def _request(self, method, path, json_body=None):
        url = f"{self.base_url}{path}?format=json"
        attempts = UNAUTHORIZED_RETRY_ATTEMPTS + 1
        for attempt in range(attempts):
            resp = requests.request(method, url, json=json_body, auth=self.auth, timeout=self.timeout)
            if resp.status_code != 401 or attempt == attempts - 1:
                resp.raise_for_status()
                return resp
            time.sleep(UNAUTHORIZED_RETRY_DELAY_SECONDS)

    def _post(self, path, body):
        return self._request("POST", path, body).json()

    def fetch_users(self):
        """Returns [SimpleNamespace(user_id=str, name=str), ...]."""
        users = []
        position = 0
        while True:
            data = self._post(
                "/ISAPI/AccessControl/UserInfo/Search",
                {
                    "UserInfoSearchCond": {
                        "searchID": "1",
                        "searchResultPosition": position,
                        "maxResults": PAGE_SIZE,
                    }
                },
            )
            search = data.get("UserInfoSearch", {})
            entries = search.get("UserInfo", [])
            for entry in entries:
                users.append(SimpleNamespace(user_id=str(entry["employeeNo"]).strip(), name=entry.get("name", "")))
            position += PAGE_SIZE
            if not entries or position >= search.get("totalMatches", 0):
                break
            time.sleep(PAGE_DELAY_SECONDS)
        return users

    def fetch_attendance_logs(self):
        """Returns [SimpleNamespace(user_id=str, timestamp=datetime, punch=int|None), ...]."""
        logs = []
        position = 0
        while True:
            data = self._post(
                "/ISAPI/AccessControl/AcsEvent",
                {
                    "AcsEventCond": {
                        "searchID": "2",
                        "searchResultPosition": position,
                        "maxResults": PAGE_SIZE,
                        "major": 0,
                        "minor": 0,
                        "startTime": "1970-01-01T00:00:00+00:00",
                        "endTime": "2037-12-31T23:59:59+00:00",
                    }
                },
            )
            search = data.get("AcsEvent", {})
            entries = search.get("InfoList", [])
            for entry in entries:
                employee_no = (entry.get("employeeNoString") or "").strip()
                if not employee_no:
                    continue  # system/alarm event, not tied to an enrolled user
                logs.append(
                    SimpleNamespace(
                        user_id=employee_no,
                        timestamp=datetime.fromisoformat(entry["time"]),
                        punch=_STATUS_TO_RAW.get(entry.get("attendanceStatus", "undefined")),
                    )
                )
            position += PAGE_SIZE
            if not entries or position >= search.get("totalMatches", 0):
                break
            time.sleep(PAGE_DELAY_SECONDS)
        return logs

    def device_info(self):
        return self._request("GET", "/ISAPI/System/deviceInfo").json()
