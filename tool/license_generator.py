"""Developer-only manual issuance. Not imported or distributed by PhotoStudio."""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from photostudio.core.licensing import (PRODUCT, LICENSE_TYPE, PUBLIC_KEY_PATH,
                                      canonical_payload, encode_part, verify_license)

REPOSITORY = Path(__file__).resolve().parents[1]


def external_path(value):
    path = Path(value).expanduser().resolve()
    if path == REPOSITORY or REPOSITORY in path.parents:
        raise ValueError("Signing credentials and issuance records must stay outside the repository.")
    return path


def initialize(private_path, public_path):
    private_path = external_path(private_path)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    if private_path.exists():
        raise ValueError("Private key already exists; refusing to overwrite it.")
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption())
    fd = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(pem)
    if os.name == "nt":
        import subprocess
        account = os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]
        subprocess.run(["icacls", str(private_path), "/inheritance:r", "/grant:r",
                        account+":(F)", "*S-1-5-18:(F)"], check=True, capture_output=True)
    # Only the public verification bytes are safe to bundle/commit.
    public_path = Path(public_path)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()+"\n", encoding="ascii")


def issue(private_path, customer, payment_date, device, amount=10):
    if amount != 10:
        raise ValueError("Watermark removal costs 10 USD.")
    paid = date.fromisoformat(payment_date)
    if paid > date.today():
        raise ValueError("Payment date cannot be in the future.")
    import re
    if not re.fullmatch(r"PS-(?:[0-9A-F]{8}-){7}[0-9A-F]{8}", device):
        raise ValueError("Copy the complete PhotoStudio Device ID from the customer's app.")
    key = serialization.load_pem_private_key(external_path(private_path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("An Ed25519 private key is required.")
    expected = bytes.fromhex(PUBLIC_KEY_PATH.read_text(encoding="ascii").strip())
    if key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) != expected:
        raise ValueError("This signing key does not match the public key bundled with PhotoStudio.")
    payload = {"version": 1, "product": PRODUCT, "license_type": LICENSE_TYPE,
               "license_id": str(uuid.uuid4()), "customer": customer,
               "payment_date": paid.strftime("%d/%m/%Y"), "issue_date": date.today().isoformat(),
               "device_id": device, "amount_usd": amount, "currency": "USD"}
    raw = canonical_payload(payload)
    token = "PSL1." + encode_part(raw) + "." + encode_part(key.sign(raw))
    verify_license(token, device)
    return payload, token


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create signing credentials once, outside the repository")
    init.add_argument("--private-key", required=True)
    init.add_argument("--public-key", default=str(PUBLIC_KEY_PATH))
    create = sub.add_parser("issue", help="Issue only after manually verifying payment")
    create.add_argument("--private-key", required=True)
    create.add_argument("--customer", required=True)
    create.add_argument("--payment-date", required=True, help="YYYY-MM-DD")
    create.add_argument("--device-id", required=True)
    create.add_argument("--amount", type=int, default=10)
    create.add_argument("--output", required=True, help="External .pslicense file to send")
    create.add_argument("--records", required=True, help="External local JSONL issuance log")
    create.add_argument("--payment-verified", action="store_true", required=True)
    inspect = sub.add_parser("inspect", help="Verify and inspect a signed file without signing credentials")
    inspect.add_argument("file")
    inspect.add_argument("--device-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            initialize(args.private_key, args.public_key)
            print("Signing key created outside repository. Back it up securely; only the public key is bundled.")
        elif args.command == "issue":
            output, records = external_path(args.output), external_path(args.records)
            if output.exists():
                raise ValueError("Output already exists; refusing to overwrite it.")
            payload, token = issue(args.private_key, args.customer, args.payment_date, args.device_id, args.amount)
            output.parent.mkdir(parents=True, exist_ok=True)
            records.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(token+"\n", encoding="ascii")
            with records.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False)+"\n")
            print("License ID: " + payload["license_id"])
            print(token)
        else:
            print(json.dumps(verify_license(Path(args.file).read_text(encoding="utf-8"), args.device_id), indent=2))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
