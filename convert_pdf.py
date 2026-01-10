#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyqt5>=5.15.11",
# ]
# ///
import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


class PDFConverterWorker(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str, bool)  # text, is_error
    conversion_complete = pyqtSignal(bool, str)  # success, output_path

    def __init__(self, input_file, density):
        super().__init__()
        self.input_file = input_file
        self.density = density

    def run(self):
        input_path = Path(self.input_file)
        density = self.density

        # Validate input file exists
        if not input_path.exists():
            self.status_update.emit("Error: Input file does not exist.", True)
            self.conversion_complete.emit(False, "")
            return

        # Create output file path
        output_path = input_path.with_name(f"{input_path.stem}_converted.pdf")

        # Update progress
        self.progress_update.emit(10)
        self.status_update.emit("Processing PDF...")

        try:
            # Create temporary directory
            temp_dir = "/tmp/convert_pdf"
            os.makedirs(temp_dir, exist_ok=True)

            # Generate a unique temporary file name
            import uuid

            temp_base_name = f"temp_{uuid.uuid4().hex}"
            temp_file_pattern = os.path.join(temp_dir, f"{temp_base_name}-%d.jpg")

            # Step 1: Convert PDF to images with specified density
            cmd1 = f'magick -density {density} "{input_path}" "{temp_file_pattern}"'
            result1 = os.system(cmd1)

            if result1 != 0:
                self.status_update.emit(
                    f"Error converting {input_path.name} to images", True
                )
                # Clean up temp directory
                self.cleanup_temp_files(temp_dir)
                self.conversion_complete.emit(False, "")
                return

            self.progress_update.emit(50)
            self.status_update.emit("Creating output PDF...")

            # Step 2: Combine the images back into a PDF
            temp_images_pattern = os.path.join(temp_dir, f"{temp_base_name}-*.jpg")
            cmd2 = f'magick "{temp_images_pattern}" "{output_path}"'
            result2 = os.system(cmd2)

            if result2 != 0:
                self.status_update.emit("Error creating PDF from images", True)
                # Clean up temp directory
                self.cleanup_temp_files(temp_dir)
                self.conversion_complete.emit(False, "")
                return

            self.progress_update.emit(90)
            self.status_update.emit("Finalizing...")

            # Step 3: Remove all temp files
            self.cleanup_temp_files(temp_dir)

            # Conversion successful
            self.progress_update.emit(100)
            self.status_update.emit(f"Successfully converted to {output_path.name}")

            self.conversion_complete.emit(True, str(output_path))

        except Exception as e:
            self.status_update.emit(f"An error occurred: {str(e)}", True)
            # Attempt to clean up temp files even if there's an exception
            self.cleanup_temp_files(temp_dir)
            self.conversion_complete.emit(False, "")

    def cleanup_temp_files(self, temp_dir):
        """Remove all temporary files"""
        try:
            import shutil

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {str(e)}")


class PDFConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Converter")
        self.setGeometry(100, 100, 600, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Input file selection
        input_label = QLabel("Input PDF File:")
        input_label.setFont(QFont("Arial", 10))
        main_layout.addWidget(input_label)

        input_hbox = QHBoxLayout()
        self.input_line_edit = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        input_hbox.addWidget(self.input_line_edit)
        input_hbox.addWidget(self.browse_button)
        main_layout.addLayout(input_hbox)

        # Density setting
        density_label = QLabel("Density (DPI):")
        density_label.setFont(QFont("Arial", 10))
        main_layout.addWidget(density_label)

        density_hbox = QHBoxLayout()
        self.density_combo = QComboBox()
        self.density_combo.addItems(["72", "150", "300", "600"])
        self.density_combo.setCurrentText("300")
        density_desc_label = QLabel(
            "Dots Per Inch - controls output quality (higher = better quality)"
        )
        density_desc_label.setStyleSheet("color: gray;")
        density_hbox.addWidget(self.density_combo)
        density_hbox.addWidget(density_desc_label)
        main_layout.addLayout(density_hbox)

        # Convert button
        self.convert_button = QPushButton("Optimize PDF")
        self.convert_button.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.convert_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: blue;")
        main_layout.addWidget(self.status_label)

        # Spacer to push everything to the top
        main_layout.addStretch()

        # Initialize worker thread
        self.worker = None

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a PDF file", "", "PDF files (*.pdf);;All files (*)"
        )
        if file_path:
            self.input_line_edit.setText(file_path)

    def start_conversion(self):
        input_file = self.input_line_edit.text()
        if not input_file:
            QMessageBox.critical(self, "Error", "Please select an input file.")
            return

        # Disable the convert button during processing
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting conversion...")
        self.status_label.setStyleSheet("color: blue;")

        # Start the conversion in a separate thread
        self.worker = PDFConverterWorker(input_file, self.density_combo.currentText())
        self.worker.progress_update.connect(self.update_progress)
        self.worker.status_update.connect(self.update_status)
        self.worker.conversion_complete.connect(self.on_conversion_complete)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, text, is_error=False):
        self.status_label.setText(text)
        if is_error:
            self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setStyleSheet("color: blue;")

    def on_conversion_complete(self, success, output_path):
        if success and output_path:
            self.update_progress(100)
            reply = QMessageBox.question(
                self,
                "Success",
                f"Successfully converted!\n\nOutput: {output_path}\n\nOpen the PDF file?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if os.name == "nt":  # Windows
                    os.system(f'start "" "{output_path}"')
                elif os.name == "posix":  # macOS/Linux
                    os.system(f'open "{output_path}"')

        self.enable_controls()

    def enable_controls(self):
        self.convert_button.setEnabled(True)
        # Hide progress bar after 2 seconds
        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))


def pdf_converter():
    app = QApplication(sys.argv)
    window = PDFConverterGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    pdf_converter()
