# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pymupdf>=1.27.2.3",
#     "pyqt5>=5.15.11",
# ]
# ///
"""Convert PDF pages to images with GUI or CLI interface."""

import argparse
import os
import sys
from pathlib import Path

import pymupdf


def create_images_from_pdf(pdf_path: str, output_dir: str, dpi: int = 300) -> list[str]:
    """Convert each page of a PDF to an image.

    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Directory to save the output images.
        dpi: Resolution for the generated images (default: 300).

    Returns:
        List of paths to the generated image files.
    """
    doc = pymupdf.open(pdf_path)
    image_paths = []

    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        output_path = os.path.join(output_dir, f"page-{page.number}.png")
        pix.save(output_path)
        image_paths.append(output_path)

    doc.close()
    return image_paths


def validate_output_directory(output_dir: str) -> None:
    """Validate that the output directory exists and is empty or doesn't exist.

    Args:
        output_dir: Path to the output directory.

    Raises:
        ValueError: If the directory exists and contains PNG files.
    """
    if os.path.exists(output_dir):
        if not os.path.isdir(output_dir):
            raise ValueError(f"Output path exists but is not a directory: {output_dir}")

        # Check if directory contains any PNG files
        png_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".png")]
        if png_files:
            raise ValueError(
                f"Output directory '{output_dir}' already exists and contains {len(png_files)} PNG file(s). "
                "Please remove it or choose a different location."
            )


def setup_gui():
    """Set up and return the PyQt5 GUI components."""
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QFileDialog,
        QSpinBox,
        QMessageBox,
    )
    from PyQt5.QtCore import Qt

    class PDFConverterGUI(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()

        def init_ui(self):
            self.setWindowTitle("PDF to Images Converter")
            self.setMinimumWidth(500)

            layout = QVBoxLayout()

            # PDF file selection
            pdf_layout = QHBoxLayout()
            pdf_layout.addWidget(QLabel("PDF File:"))
            self.pdf_input = QLineEdit()
            self.pdf_input.setReadOnly(True)
            pdf_layout.addWidget(self.pdf_input)
            self.pdf_button = QPushButton("Browse...")
            self.pdf_button.clicked.connect(self.browse_pdf)
            pdf_layout.addWidget(self.pdf_button)
            layout.addLayout(pdf_layout)

            # Output directory selection
            output_layout = QHBoxLayout()
            output_layout.addWidget(QLabel("Output Location:"))
            self.output_input = QLineEdit()
            self.output_input.setReadOnly(True)
            output_layout.addWidget(self.output_input)
            self.output_button = QPushButton("Browse...")
            self.output_button.clicked.connect(self.browse_output)
            output_layout.addWidget(self.output_button)
            layout.addLayout(output_layout)

            # DPI setting
            dpi_layout = QHBoxLayout()
            dpi_layout.addWidget(QLabel("DPI:"))
            self.dpi_spinbox = QSpinBox()
            self.dpi_spinbox.setMinimum(50)
            self.dpi_spinbox.setMaximum(1200)
            self.dpi_spinbox.setValue(300)
            dpi_layout.addWidget(self.dpi_spinbox)
            dpi_layout.addStretch()
            layout.addLayout(dpi_layout)

            # Convert button
            self.convert_button = QPushButton("Convert")
            self.convert_button.clicked.connect(self.convert_pdf)
            self.convert_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            layout.addWidget(self.convert_button)

            self.setLayout(layout)

        def browse_pdf(self):
            """Open file dialog to select PDF file."""
            pdf_path, _ = QFileDialog.getOpenFileName(
                self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*)"
            )
            if pdf_path:
                self.pdf_input.setText(pdf_path)

        def browse_output(self):
            """Open directory dialog to select output location."""
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Output Location"
            )
            if output_dir:
                self.output_input.setText(output_dir)

        def convert_pdf(self):
            """Convert the selected PDF to images."""
            pdf_path = self.pdf_input.text().strip()
            output_dir = self.output_input.text().strip()
            dpi = self.dpi_spinbox.value()

            # Validate inputs
            if not pdf_path:
                QMessageBox.warning(self, "Error", "Please select a PDF file.")
                return

            if not os.path.exists(pdf_path):
                QMessageBox.warning(self, "Error", f"PDF file not found: {pdf_path}")
                return

            if not output_dir:
                # Default to the directory containing the PDF
                output_dir = os.path.dirname(pdf_path)

            # Create output directory name based on PDF filename
            pdf_name = Path(pdf_path).stem
            target_dir = os.path.join(output_dir, pdf_name)

            try:
                # Validate output directory
                validate_output_directory(target_dir)

                # Create output directory if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)

                # Convert PDF to images
                image_paths = create_images_from_pdf(pdf_path, target_dir, dpi)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully converted {len(image_paths)} pages to images.\n"
                    f"Images saved in: {target_dir}",
                )
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    return QApplication(sys.argv), PDFConverterGUI()


def main():
    """Main entry point for the PDF to images converter."""
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to images with GUI or CLI interface."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode instead of GUI mode.",
    )
    parser.add_argument(
        "--pdf", type=str, help="Path to the input PDF file (required in CLI mode)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for the generated images (defaults to PDF name without extension in CLI mode).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for the generated images (default: 300).",
    )

    args = parser.parse_args()

    if args.cli:
        # CLI mode
        if not args.pdf:
            print("Error: --pdf is required in CLI mode.", file=sys.stderr)
            sys.exit(1)

        pdf_path = os.path.abspath(args.pdf)
        pdf_name = Path(pdf_path).stem

        # Default output directory is PDF name without extension
        if args.output is None:
            output_dir = pdf_name
        else:
            output_dir = os.path.abspath(args.output)
        target_dir = os.path.join(output_dir, pdf_name)

        try:
            # Validate output directory
            validate_output_directory(target_dir)

            # Create output directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)

            # Convert PDF to images
            image_paths = create_images_from_pdf(pdf_path, target_dir, args.dpi)

            print(f"Successfully converted {len(image_paths)} pages to images.")
            print(f"Images saved in: {target_dir}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: An error occurred: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        # GUI mode
        app, window = setup_gui()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
