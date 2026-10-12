import io
import json
import socket
import uuid
from datetime import date
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from photostudio.core import licensing, project_io
from photostudio.core.document import Document
from photostudio.core.pipeline import composite
from photostudio.imaging.watermark import apply_watermark

DEVICE = "PS-" + "-".join(["12345678"]*8)


@pytest.fixture
def authority():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    def signed(**updates):
        payload = {"version": 1, "product": licensing.PRODUCT, "license_type": licensing.LICENSE_TYPE,
                   "license_id": str(uuid.uuid4()), "payment_date": "12/10/2026",
                   "issue_date": "2026-10-12", "device_id": DEVICE,
                   "amount_usd": 10, "currency": "USD", "customer": "Test Customer"}
        payload.update(updates)
        raw = licensing.canonical_payload(payload)
        return "PSL1." + licensing.encode_part(raw) + "." + licensing.encode_part(key.sign(raw))
    return key, public, signed


def test_verifies_offline_and_persists_restart(tmp_path, authority, monkeypatch):
    _, public, signed = authority
    def no_network(*args, **kwargs):
        raise AssertionError("Activation must remain offline")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    manager = licensing.LicenseManager(tmp_path, DEVICE, public)
    token = signed()
    details = manager.activate(token)
    assert details["payment_date"] == "12/10/2026"
    assert uuid.UUID(details["license_id"])
    restarted = licensing.LicenseManager(tmp_path, DEVICE, public)
    assert restarted.is_active()
    assert restarted.details() == details
    with pytest.raises(licensing.LicenseError):
        manager.activate("bad-key")
    assert restarted.is_active()  # Invalid attempts cannot destroy a valid activation.


def test_tampering_wrong_device_unknown_authority_and_metadata(tmp_path, authority):
    _, public, signed = authority
    token = signed()
    prefix, body, signature = token.split(".")
    raw = json.loads(licensing._decode_part(body))
    raw["payment_date"] = "01/01/2020"
    tampered = prefix + "." + licensing.encode_part(licensing.canonical_payload(raw)) + "." + signature
    with pytest.raises(licensing.LicenseError, match="signature"):
        licensing.verify_license(tampered, DEVICE, public)
    with pytest.raises(licensing.LicenseError, match="another computer"):
        licensing.verify_license(token, "other-computer", public)
    other = Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with pytest.raises(licensing.LicenseError):
        licensing.verify_license(token, DEVICE, other)
    for kwargs in ({"product": "Other"}, {"payment_date": "bad"}, {"license_type": "subscription"},
                   {"license_id": "not-uuid"}, {"amount_usd": 0}, {"version": 2}):
        with pytest.raises(licensing.LicenseError):
            licensing.verify_license(signed(**kwargs), DEVICE, public)
    manager = licensing.LicenseManager(tmp_path, DEVICE, public)
    manager.activate(token)
    manager.path.write_text(tampered, encoding="ascii")
    assert not manager.is_active()


@pytest.mark.parametrize("key", ["", "PSL1.a.b", "PSL1.☃.a", "x"*17000, "{\"active\":true}"])
def test_invalid_keys_fail_clearly(key, authority):
    with pytest.raises(licensing.LicenseError):
        licensing.verify_license(key, DEVICE, authority[1])


def pdf_pixels(path):
    # Pillow writes the flattened RGB page as an embedded JPEG (DCTDecode).
    data = path.read_bytes()
    start = data.index(b"\xff\xd8")
    end = data.index(b"\xff\xd9", start)+2
    return np.asarray(Image.open(io.BytesIO(data[start:end])).convert("RGB"))


@pytest.mark.parametrize("fmt", ["png", "jpg", "pdf"])
def test_free_and_licensed_exports_share_policy_without_changing_project(fmt, tmp_path, authority):
    _, public, signed = authority
    pixels = np.full((400, 800, 4), (210, 220, 230, 255), dtype=np.uint8)
    doc = Document.from_image(pixels)
    manager = licensing.LicenseManager(tmp_path/"license", DEVICE, public)
    free = tmp_path/("free."+fmt)
    paid = tmp_path/("paid."+fmt)
    project_io.export_document(doc, free, fmt, license_manager=manager)
    free_pixels = pdf_pixels(free) if fmt == "pdf" else np.asarray(Image.open(free).convert("RGB"))
    manager.activate(signed())
    project_io.export_document(doc, paid, fmt, license_manager=manager)
    paid_pixels = pdf_pixels(paid) if fmt == "pdf" else np.asarray(Image.open(paid).convert("RGB"))
    assert np.max(np.abs(paid_pixels.astype(int)-pixels[..., :3].astype(int))) <= 3
    assert np.mean(np.abs(free_pixels[-40:].astype(float)-paid_pixels[-40:])) > 3
    assert np.max(np.abs(free_pixels[:300].astype(int)-paid_pixels[:300].astype(int))) <= 3
    assert np.array_equal(doc.layers[0].pixels, pixels) and len(doc.layers) == 1
    project = tmp_path/"editable.pstudio"
    project_io.save_project(doc, project)
    restored = project_io.load_project(project)
    assert np.array_equal(composite(restored), pixels)
    assert np.array_equal(project_io.export_pixels(doc, manager), pixels)


def test_watermark_preview_placement_alpha_and_original_pixels(tmp_path, authority):
    pixels = np.zeros((600, 600, 4), dtype=np.uint8)
    result = apply_watermark(pixels)
    assert np.any(result[-50:, :, 3] > 0)
    assert not np.any(result[:-50])
    assert not np.any(pixels)
    manager = licensing.LicenseManager(tmp_path, DEVICE, authority[1])
    doc = Document.from_image(pixels)
    assert np.array_equal(project_io.export_pixels(doc, manager), result)
    for shape in ((1, 1, 4), (10, 20, 4), (1000, 80, 4)):
        assert apply_watermark(np.zeros(shape, dtype=np.uint8)).shape == shape


def test_device_id_is_stable():
    assert licensing.device_id() == licensing.device_id()
    assert licensing.device_id().startswith("PS-")


def test_visible_export_preview_tracks_activation_without_touching_editor(qtbot, monkeypatch, tmp_path, authority):
    from photostudio.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QLabel
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    win.license_manager = licensing.LicenseManager(tmp_path/"active", DEVICE, authority[1])
    win.controller.new_document(800, 400)
    doc = win.controller.document
    original = composite(doc).copy()
    previews = []
    def inspect(dialog):
        pixmap = next(label.pixmap() for label in dialog.findChildren(QLabel) if label.pixmap() and not label.pixmap().isNull())
        previews.append(pixmap.toImage().copy())
        return 0
    monkeypatch.setattr(QDialog, "exec", inspect)
    win.on_export_preview()
    win.license_manager.activate(authority[2]())
    win.on_export_preview()
    assert previews[0].pixelColor(400, 385).value() < 255
    assert previews[1].pixelColor(400, 385).value() == 255
    assert np.array_equal(composite(doc), original)
    win.controller._dirty = False
    win.close()


@pytest.mark.parametrize("dark", [True, False])
def test_payment_dialog_buttons_have_readable_theme_colors(qtbot, tmp_path, authority, dark):
    from photostudio.ui.license_dialog import LicenseDialog
    from photostudio.ui import theme
    from PySide6.QtWidgets import QPushButton
    from PySide6.QtGui import QPalette, QColor
    theme.ensure_fonts()
    dialog = LicenseDialog(licensing.LicenseManager(tmp_path, DEVICE, authority[1]))
    qtbot.addWidget(dialog)
    tokens = theme.DARK if dark else theme.LIGHT
    dialog.setStyleSheet(theme.stylesheet(tokens))
    dialog.show()
    for button in dialog.findChildren(QPushButton):
        assert button.text().strip() and button.height() >= 32
        foreground = button.palette().color(QPalette.ColorRole.ButtonText)
        background = button.palette().color(QPalette.ColorRole.Button)
        assert foreground != background
        assert foreground == QColor("white" if button is dialog.activate_button else tokens["text"])


def test_generator_issues_unique_keys_and_rejects_workspace_secrets(tmp_path, monkeypatch):
    from tool import license_generator as generator
    secret = tmp_path/"signing.pem"
    public = tmp_path/"public.txt"
    generator.initialize(secret, public)
    monkeypatch.setattr(generator, "PUBLIC_KEY_PATH", public)
    monkeypatch.setattr(licensing, "PUBLIC_KEY_PATH", public)
    kwargs = dict(private_path=secret, customer="Example Customer", payment_date=date.today().isoformat(), device=DEVICE)
    first, one = generator.issue(**kwargs)
    second, two = generator.issue(**kwargs)
    assert first["license_id"] != second["license_id"] and one != two
    assert licensing.verify_license(one, DEVICE)["payment_date"] == date.today().strftime("%d/%m/%Y")
    with pytest.raises(ValueError, match="outside"):
        generator.external_path(generator.REPOSITORY/"private.pem")
    with pytest.raises(ValueError, match="overwrite"):
        generator.initialize(secret, public)
    with pytest.raises(ValueError, match="10 USD"):
        generator.issue(**kwargs, amount=1)
    output, records = tmp_path/"issued.pslicense", tmp_path/"records.jsonl"
    generator.main(["issue", "--private-key", str(secret), "--customer", "Example Customer",
                    "--payment-date", date.today().isoformat(), "--device-id", DEVICE,
                    "--output", str(output), "--records", str(records), "--payment-verified"])
    issued = licensing.verify_license(output.read_text(encoding="ascii"), DEVICE)
    assert json.loads(records.read_text(encoding="utf-8"))["license_id"] == issued["license_id"]


def test_payment_dialog_actions_activation_import_and_english(qtbot, tmp_path, authority, monkeypatch):
    from photostudio.ui.license_dialog import LicenseDialog, INSTRUCTIONS
    from photostudio.ui import i18n
    from PySide6.QtWidgets import QApplication, QFileDialog
    from PySide6.QtGui import QDesktopServices
    old_language = i18n.LANGUAGE
    i18n.set_language("so")
    manager = licensing.LicenseManager(tmp_path, DEVICE, authority[1])
    dialog = LicenseDialog(manager)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.windowTitle() == "Remove Watermark"
    assert "Send $10 via EVC Plus to 0611354800." in INSTRUCTIONS
    dialog.copy_payment.click()
    assert QApplication.clipboard().text() == "0611354800"
    dialog.copy_device.click()
    assert QApplication.clipboard().text() == DEVICE
    urls = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: urls.append(url.toString()) or True)
    dialog.email.click(); dialog.whatsapp.click(); dialog.phone.click()
    assert urls == ["mailto:mohamedqadar280@gmail.com", "https://wa.me/252611354800", "tel:+252611354800"]
    dialog.key.setPlainText("invalid")
    dialog.activate_button.click()
    assert "Invalid license" in dialog.message.text()
    assert not manager.is_active()
    file = tmp_path/"sent.pslicense"
    file.write_text(authority[2](), encoding="ascii")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(file), ""))
    dialog.import_file.click()
    dialog.activate_button.click()
    assert "License Activated" in dialog.status.text()
    assert "12/10/2026" in dialog.status.text()
    assert manager.is_active()
    dialog.close_button.click()
    i18n.set_language(old_language)
