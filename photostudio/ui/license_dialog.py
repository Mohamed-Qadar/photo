"""English-only manual payment instructions and offline activation."""
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFileDialog, QScrollArea, QWidget)
from ..core.licensing import LicenseError, MAX_KEY_LENGTH

INSTRUCTIONS = """Remove the PhotoStudio watermark with a one-time payment of $10.

Send $10 via EVC Plus to 0611354800.

After payment, send your payment confirmation SMS and PhotoStudio Device ID to Mohamed by email or WhatsApp.

Once your payment is verified, you will receive your personal license key.

Enter your license key below to activate watermark-free exports."""


class LicenseDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Remove Watermark")
        self.resize(660, 740)
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        title = QLabel("$10 USD — One-time Payment")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)
        label = QLabel("Perpetual watermark removal for one computer. All editing features remain free.")
        label.setWordWrap(True)
        layout.addWidget(label)
        instructions = QLabel(INSTRUCTIONS)
        instructions.setWordWrap(True)
        instructions.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(instructions)
        contact = QLabel("EVC Plus: 0611354800\nContact: Mohamed\nEmail: mohamedqadar280@gmail.com\nWhatsApp / Phone: +252611354800")
        contact.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(contact)
        self.copy_payment = self.button(layout, "Copy payment number", lambda: self.copy("0611354800"))
        row = QHBoxLayout()
        layout.addLayout(row)
        self.email = self.button(row, "Contact by email", lambda: self.open_link("mailto:mohamedqadar280@gmail.com"))
        self.whatsapp = self.button(row, "Contact by WhatsApp", lambda: self.open_link("https://wa.me/252611354800"))
        self.phone = self.button(row, "Call Mohamed", lambda: self.open_link("tel:+252611354800"))
        layout.addWidget(QLabel("PhotoStudio Device ID"))
        self.device = QLineEdit(manager.device_id)
        self.device.setReadOnly(True)
        layout.addWidget(self.device)
        self.copy_device = self.button(layout, "Copy Device ID", lambda: self.copy(manager.device_id))
        layout.addWidget(QLabel("Enter License Key"))
        self.key = QPlainTextEdit()
        self.key.setPlaceholderText("Paste your complete PSL1 license key here")
        self.key.setMaximumHeight(100)
        layout.addWidget(self.key)
        row = QHBoxLayout()
        layout.addLayout(row)
        self.import_file = self.button(row, "Import License File", self.import_license)
        self.activate_button = self.button(row, "Activate License", self.activate)
        self.activate_button.setDefault(True)
        self.activate_button.setStyleSheet("QPushButton { background: #2459b8; color: white; font-weight: 600; } QPushButton:hover { background: #306acb; }")
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self.status)
        self.message = QLabel()
        self.message.setWordWrap(True)
        outer.addWidget(self.message)
        self.close_button = self.button(outer, "Close", self.accept)
        self.refresh_status()

    def button(self, layout, label, callback):
        button = QPushButton(label)
        button.setMinimumHeight(32)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    def copy(self, text):
        QApplication.clipboard().setText(text)
        self.message.setText("Copied to clipboard.")

    def open_link(self, url):
        if not QDesktopServices.openUrl(QUrl(url)):
            self.message.setText("Could not open a contact application. Use the contact details shown above.")

    def refresh_status(self):
        try:
            details = self.manager.details()
            if details:
                self.status.setText("License Status: License Activated\nPayment date: " + details["payment_date"] +
                                    "\nLicense ID: " + details["license_id"] + "\nPerpetual — no expiry.")
            else:
                self.status.setText("License Status: Free — exports include the PhotoStudio watermark.")
        except (LicenseError, OSError, UnicodeError) as exc:
            self.status.setText("License Status: Inactive — " + str(exc))

    def activate(self):
        try:
            self.manager.activate(self.key.toPlainText())
        except (LicenseError, OSError) as exc:
            self.message.setText(str(exc))
        else:
            self.message.setText("License Activated. Future exports will be watermark-free.")
            self.key.clear()
        self.refresh_status()

    def import_license(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import License File", "", "PhotoStudio License (*.pslicense);;Text files (*.txt)")
        if path:
            try:
                from pathlib import Path
                file = Path(path)
                if file.stat().st_size > MAX_KEY_LENGTH:
                    raise LicenseError("License file is too large.")
                self.key.setPlainText(file.read_text(encoding="utf-8"))
                self.message.setText("License file loaded. Click Activate License to verify and save it.")
            except (OSError, UnicodeError, LicenseError) as exc:
                self.message.setText(str(exc))
