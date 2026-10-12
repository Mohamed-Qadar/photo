# Offline watermark-removal license

All application features remain free. Only exports and export previews carry
`Developed by Eng. Mohamed Ibrahim Abdi` when no valid license exists. PNG, JPG
and PDF share the same export renderer. Source images, document layers, project
thumbnails, saved projects and the editing canvas are unaffected.

Customers open File / Help → Remove Watermark. The English dialog shows the $10
one-time price, EVC Plus 0611354800, email mohamedqadar280@gmail.com, WhatsApp/phone
+252611354800, and the Device ID. Copy controls and contact links are provided;
contact links open the user's external application and do not send any message.
Payment is verified manually by Mohamed. Paste the issued key or import its
`.pslicense` file, then click Activate License. Successful activation shows payment
date and license ID. The license is perpetual, for one computer, with no expiry.

## Developer credentials

The production Ed25519 signing key was initialized locally at:

`C:\Users\Moha-qadar\.photostudio-signing\watermark-ed25519.pem`

This is outside the repository and Windows package. Its Windows ACL permits only
the current user and SYSTEM. Keep a secure offline backup: losing it prevents issuing
keys for the public verification key bundled in this build. It is an unencrypted
PKCS8 PEM protected by filesystem permissions; do not email it, paste it into chat,
copy it into the checkout, or include it in a release. Only
`photostudio/resources/license_public_key.txt` is public and bundled.

The separate developer CLI `tool/license_generator.py` is not imported by the
application or included in the PyInstaller package. It refuses credentials,
customer license outputs and issuance records inside this checkout. After manually
verifying payment, use PowerShell (replace the example customer/date/device):

```powershell
.venv\Scripts\python.exe tool/license_generator.py issue `
  --private-key C:\Users\Moha-qadar\.photostudio-signing\watermark-ed25519.pem `
  --customer "Example Customer" --payment-date 2026-10-12 --amount 10 `
  --device-id "PS-PASTE-THE-COMPLETE-CUSTOMER-DEVICE-ID" `
  --output C:\Users\Moha-qadar\.photostudio-signing\issued\customer.pslicense `
  --records C:\Users\Moha-qadar\.photostudio-signing\issued\records.jsonl `
  --payment-verified
```

The CLI prints a unique license ID and a single encoded activation key. Copy the
key, or send only the generated `.pslicense` file, through email or WhatsApp.
The example Device ID is deliberately a placeholder; use the complete ID copied
from the customer's app. Amount must be 10 USD. Payment date input is YYYY-MM-DD;
signed metadata and the activation dialog display DD/MM/YYYY. Local JSONL records
include customer name and license metadata; keep them private. No real customer
data is checked in. To inspect an issued file:

```powershell
.venv\Scripts\python.exe tool/license_generator.py inspect C:\path\customer.pslicense --device-id "PS-CUSTOMER-DEVICE-ID"
```

`init --private-key <external-path>` provisions a new key pair only for an intentional
new trust root. Do not run it again for normal issuance: replacing the bundled public
key would invalidate existing licenses in builds using that replacement.

## Verification and persistence

`PSL1.<base64url payload>.<base64url signature>` signs canonical UTF-8 JSON with
Ed25519. The payload records format version, product, license type, random UUID
license ID, payment date, issue date, device fingerprint, customer, amount and
currency. Payment dates are metadata, never secrets or activation passwords.
Verification uses the bundled public key entirely offline, validates the signature,
schema/product/type and device binding, and never trusts an editable settings flag.
Keys signed by a different authority, altered keys and wrong-device keys fail clearly.
The signature proves authenticity, not confidentiality: the encoded metadata can
be decoded by anyone holding a key. Do not put payment SMS contents or sensitive
customer information in the payload. Cryptographic operations use the
[cryptography Ed25519 implementation](https://cryptography.io/en/46.0.4/hazmat/primitives/asymmetric/ed25519/).

Activation atomically saves the signed token under
`%LOCALAPPDATA%\PhotoStudio\watermark-license.pslicense`. Each future export
verifies it again. Restarting the app preserves activation. An invalid activation
attempt does not replace a previously valid stored license. Invalid stored files
fall back to watermarked exports; they never disable editing or project access.

Windows Device IDs hash MachineGuid with a product-specific prefix; reinstalling
PhotoStudio normally preserves them. Windows reinstall/machine cloning can change
or duplicate that identity. Unsupported systems use their machine ID or a local
installation ID. This is practical offline device binding, not tamper-proof hardware
attestation. Fully offline perpetual licenses cannot be remotely revoked. Modified
application code can bypass watermark policy, and attribution can be edited out of
an exported image. No claim of impossible removal is made.

## QA

Tests cover offline signatures, malformed/tampered keys, wrong devices, metadata,
restart persistence, unique issuance, payment controls/links, PNG/JPG/PDF pixel
behavior, watermark placement, transparency and project compatibility. The packaged
smoke workflow loads the crypto backend and bundled public key, rejects an invalid
signature, opens the payment dialog and checks export-only attribution.
