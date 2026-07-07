"""Thin wrapper around pyzk for talking to a ZKTeco biometric attendance device."""
from django.conf import settings
from zk import ZK


class ZKTecoClient:
    def __init__(self, ip=None, port=None, timeout=10):
        self.ip = ip or settings.ZKTECO_DEVICE_IP
        self.port = port or settings.ZKTECO_DEVICE_PORT
        self.timeout = timeout

    def _connect(self):
        zk = ZK(
            self.ip,
            port=self.port,
            timeout=self.timeout,
            password=0,
            force_udp=False,
            ommit_ping=True,
        )
        return zk.connect()

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

    def push_user(self, user_id, name, privilege=0):
        """Creates or updates a user on the device. If a user with this user_id
        already exists, its internal slot (uid) is reused so this updates the
        existing enrollment rather than creating a duplicate.
        """
        conn = self._connect()
        try:
            existing = next((u for u in conn.get_users() if str(u.user_id) == str(user_id)), None)
            uid = existing.uid if existing else None
            conn.set_user(uid=uid, name=name[:24], privilege=privilege, user_id=str(user_id))
            return True
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
