"""Offline verification only. Signing credentials never belong in this package."""
from __future__ import annotations

import base64
from datetime import datetime, date
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .recovery import data_root

PRODUCT = "PhotoStudio"
LICENSE_TYPE = "perpetual-watermark-removal-one-device"
PUBLIC_KEY_PATH = Path(__file__).resolve().parent.parent / "resources" / "license_public_key.txt"
MAX_KEY_LENGTH = 16384


class LicenseError(ValueError):
    pass


def canonical_payload(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def encode_part(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_part(value):
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def device_id():
    """Domain-separated machine fingerprint; Windows survives app reinstall."""
    identity = None
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography",
                                0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                identity = winreg.QueryValueEx(key, "MachineGuid")[0]
        except OSError:
            pass
    else:
        for path in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
            try:
                identity = path.read_text().strip()
                if identity:
                    break
            except OSError:
                pass
    if not identity:
        # Unsupported platforms use an installation ID, rather than an unstable MAC.
        path = data_root() / "device-id.txt"
        try:
            identity = path.read_text(encoding="ascii").strip()
        except FileNotFoundError:
            identity = str(uuid.uuid4())
            with path.open("x", encoding="ascii") as stream:
                stream.write(identity)
    digest = hashlib.sha256(("PhotoStudio-device-v1:" + str(identity).strip().lower()).encode()).hexdigest().upper()
    return "PS-" + "-".join(digest[i:i+8] for i in range(0, 64, 8))


def verify_license(token, expected_device, public_key=None):
    """Verify signature over exact bytes, then validate product, schema and binding."""
    try:
        token = "".join(str(token).split())
        if len(token) > MAX_KEY_LENGTH:
            raise ValueError()
        prefix, body, signature = token.split(".")
        if prefix != "PSL1":
            raise ValueError()
        raw, sig = _decode_part(body), _decode_part(signature)
        key = public_key if public_key is not None else bytes.fromhex(PUBLIC_KEY_PATH.read_text(encoding="ascii").strip())
        Ed25519PublicKey.from_public_bytes(key).verify(sig, raw)
    except (ValueError, TypeError, OSError, InvalidSignature) as exc:
        raise LicenseError("Invalid license key or signature. Check that you copied the complete key.") from exc
    try:
        payload = json.loads(raw)
        if canonical_payload(payload) != raw or payload["version"] != 1:
            raise ValueError()
        if payload["product"] != PRODUCT or payload["license_type"] != LICENSE_TYPE:
            raise ValueError()
        uuid.UUID(payload["license_id"])
        payment = datetime.strptime(payload["payment_date"], "%d/%m/%Y").date()
        issued = date.fromisoformat(payload["issue_date"])
        if payment > issued or payload["amount_usd"] != 10 or payload["currency"] != "USD":
            raise ValueError()
        if not isinstance(payload["device_id"], str):
            raise ValueError()
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise LicenseError("This license has invalid metadata or is for a different product.") from exc
    if payload["device_id"] != expected_device:
        raise LicenseError("This license belongs to another computer. Send this computer's Device ID to Mohamed.")
    return payload


class LicenseManager:
    def __init__(self, root=None, device=None, public_key=None):
        self.root = Path(root) if root is not None else data_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "watermark-license.pslicense"
        self.device_id = device if device is not None else device_id()
        self.public_key = public_key

    def details(self):
        try:
            if self.path.stat().st_size > MAX_KEY_LENGTH:
                raise LicenseError("Stored license is too large.")
            return verify_license(self.path.read_text(encoding="utf-8"), self.device_id, self.public_key)
        except FileNotFoundError:
            return None

    def is_active(self):
        # Never trust a settings boolean, cached flag or unsigned metadata.
        try:
            return self.details() is not None
        except (LicenseError, OSError, UnicodeError):
            return False

    def activate(self, token):
        details = verify_license(token, self.device_id, self.public_key)
        normalized = "".join(token.split())
        fd, temporary = tempfile.mkstemp(prefix=".license-", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="ascii") as stream:
                stream.write(normalized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return details
