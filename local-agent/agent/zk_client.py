"""Thin standalone wrapper around pyzk — deliberately mirrors
backend/apps/attendance/zkteco.py::ZKTecoClient's shape. This agent runs in
its own process with no Django available, so it can't import that module
directly; this is "the same idea, twice" rather than a shared package.
"""
from zk import ZK


class ZKClient:
    def __init__(self, ip, port=4370, timeout=10):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def _connect(self):
        conn = ZK(self.ip, port=self.port, timeout=self.timeout, password=0, force_udp=False, ommit_ping=True)
        return conn.connect()

    def fetch_users(self):
        """Returns a list of pyzk User objects (user_id, name, privilege, card, ...)."""
        conn = self._connect()
        try:
            return conn.get_users()
        finally:
            conn.disconnect()

    def fetch_attendance_logs(self):
        """Returns a list of pyzk Attendance objects (user_id, timestamp, status, punch)."""
        conn = self._connect()
        try:
            return conn.get_attendance()
        finally:
            conn.disconnect()

    def device_info(self):
        conn = self._connect()
        try:
            return {
                "firmware_version": conn.get_firmware_version(),
                "device_name": conn.get_device_name(),
                "serial_number": conn.get_serialnumber(),
            }
        finally:
            conn.disconnect()
