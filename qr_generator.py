#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyqt5>=5.15.11",
#     "segno>=1.6.6",
# ]
# ///
"""
QR Code Generator Application
A PyQt5 application that takes a string input and generates a QR code.
"""

import sys
import segno
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class QRGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.qr_image = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("QR Code Generator")
        self.setGeometry(300, 300, 500, 600)

        # Create layout
        layout = QVBoxLayout()

        # Input label
        input_label = QLabel("Enter text to encode:")
        layout.addWidget(input_label)

        # Text input area
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(100)
        layout.addWidget(self.text_input)

        # Generate button
        self.generate_button = QPushButton("Generate QR Code")
        self.generate_button.clicked.connect(self.generate_qr)
        layout.addWidget(self.generate_button)

        # QR code display label
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.qr_label)

        # Save button
        self.save_button = QPushButton("Save QR Code")
        self.save_button.clicked.connect(self.save_qr)
        self.save_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.save_button)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def generate_qr(self):
        text = self.text_input.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text to encode.")
            return

        try:
            # Generate QR code
            qr_code = segno.make(text, error="h")  # High error correction

            # Convert to image
            # Create a temporary PNG in memory
            import io

            buffer = io.BytesIO()
            qr_code.save(buffer, kind="png", scale=10)

            # Load the image from buffer to QImage
            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())

            # Convert to pixmap and display
            self.qr_image = QPixmap.fromImage(qimg)
            self.qr_label.setPixmap(
                self.qr_image.scaled(
                    300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

            self.save_button.setEnabled(True)
            self.status_label.setText("QR Code generated successfully!")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate QR code:\n{str(e)}"
            )

    def save_qr(self):
        if self.qr_image is None:
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            "",
            "PNG Files (*.png);;All Files (*)",
            options=options,
        )

        if file_path:
            try:
                # Save the image
                if not self.qr_image.save(file_path):
                    raise Exception("Failed to save image")

                self.status_label.setText(f"QR Code saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save QR code:\n{str(e)}"
                )


def main():
    app = QApplication(sys.argv)
    window = QRGeneratorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
