# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pyqt5>=5.15.11",
#     "yt-dlp",
# ]
# ///
import sys
from threading import Thread

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from yt_dlp import YoutubeDL


class LogSignal(QObject):
    log_signal = pyqtSignal(str)


class AsyncTask(Thread):
    def __init__(self, url, download_config, log_signal, write_subs=False):
        super().__init__()

        self.html = None
        self.url = url
        self.download_config = download_config
        self.log_signal = log_signal
        self.write_subs = write_subs

    def run(self):
        # Custom logger class to emit signals to the GUI
        class Logger:
            def __init__(self, log_signal):
                self.log_signal = log_signal

            def debug(self, msg):
                self.log_signal.log_signal.emit(f"DEBUG: {msg}")

            def warning(self, msg):
                self.log_signal.log_signal.emit(f"WARNING: {msg}")

            def error(self, msg):
                self.log_signal.log_signal.emit(f"ERROR: {msg}")

        logger_instance = Logger(self.log_signal)

        params = OPTIONS.get(self.download_config, OPTION_480P).copy()
        params["logger"] = logger_instance

        # Add subtitle option if selected
        if self.write_subs:
            params["writeautomaticsub"] = True
            params["subtitlesformat"] = "srt"

        print(params)

        with YoutubeDL(params) as ydl:
            ydl.download([self.url])


class LoadingHandler:
    def __init__(self):
        _in_progress = ["-", "\\", "|", "/"]
        self.loading_text = [f"Loading... {x}" for x in _in_progress]

    @property
    def initial_state(self):
        return self.loading_text[0]

    def next(self, state=None):
        if state in self.loading_text:
            index = self.loading_text.index(state)
            return self.loading_text[(index + 1) % len(self.loading_text)]
        else:
            return self.loading_text[0]


OPTION_480P = {
    "extract_flat": "discard_in_playlist",
    "format": "(mp4)[height<=480]+ba/(mp4)[height<=480] / wv*+ba/w",
    "fragment_retries": 10,
    "ignoreerrors": "only_download",
    "postprocessors": [
        {"key": "FFmpegConcat", "only_multi_video": True, "when": "playlist"}
    ],
    "retries": 10,
}

OPTION_AUDIO_ONLY = {
    "extract_flat": "discard_in_playlist",
    "format": "(mp4)wa",
    "fragment_retries": 10,
    "ignoreerrors": "only_download",
    "postprocessors": [
        {"key": "FFmpegConcat", "only_multi_video": True, "when": "playlist"}
    ],
    "retries": 10,
}

OPTION_144P = {
    "extract_flat": "discard_in_playlist",
    "format": "(mp4)[height<=144]+ba/(mp4)[height<=144] / wv*+wa/w",
    "fragment_retries": 10,
    "ignoreerrors": "only_download",
    "postprocessors": [
        {"key": "FFmpegConcat", "only_multi_video": True, "when": "playlist"}
    ],
    "retries": 10,
}

OPTIONS = {"144p": OPTION_144P, "480p": OPTION_480P, "audio-only": OPTION_AUDIO_ONLY}
OPTION_DEFAULT = "480p"

LOADING_INFO_DEFAULT = "Waiting..."


class YouTubeDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(100, 100, 600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create form layout for inputs
        form_group = QGroupBox("Download Settings")
        form_layout = QFormLayout(form_group)

        # URL input
        self.url_input = QLineEdit("<enter url here>")
        form_layout.addRow("URL:", self.url_input)

        # Download config combo
        self.download_config_combo = QComboBox()
        self.download_config_combo.addItems(list(OPTIONS.keys()))
        self.download_config_combo.setCurrentText(OPTION_DEFAULT)
        form_layout.addRow("Quality:", self.download_config_combo)

        # Subtitles checkbox
        self.subtitles_checkbox = QCheckBox("Download Subtitles")
        self.subtitles_checkbox.setChecked(False)
        form_layout.addRow("", self.subtitles_checkbox)

        # Add form group to main layout
        main_layout.addWidget(form_group)

        # Button to run job
        self.run_button = QPushButton("Run Job")
        self.run_button.clicked.connect(self.run_job)
        main_layout.addWidget(self.run_button)

        # Loading info label
        self.loading_label = QLabel(LOADING_INFO_DEFAULT)
        main_layout.addWidget(self.loading_label)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log_display)

        # Timer for loading animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loading_animation)
        self.current_loading_state = None

        # Loading handler
        self.loading_handler = LoadingHandler()

        # Log signal for thread communication
        self.log_signal = LogSignal()
        self.log_signal.log_signal.connect(self.append_log)

    def run_job(self):
        # Disable button and update label
        self.run_button.setEnabled(False)
        self.run_button.setText("Job is Running...")

        # Start loading animation
        self.current_loading_state = self.loading_handler.initial_state
        self.loading_label.setText(self.current_loading_state)
        self.timer.start(125)  # Update every 125ms

        # Create and start download thread
        url = self.url_input.text()
        config = self.download_config_combo.currentText()
        write_subs = self.subtitles_checkbox.isChecked()
        self.job = AsyncTask(url, config, self.log_signal, write_subs)
        self.job.start()

        # Check periodically if job is still running
        self.check_job_status()

    def check_job_status(self):
        if hasattr(self.job, "is_alive") and self.job.is_alive():
            # Continue checking
            QTimer.singleShot(500, self.check_job_status)  # Check every 500ms
        else:
            # Job finished
            self.timer.stop()
            self.loading_label.setText(LOADING_INFO_DEFAULT)
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Job")

    def update_loading_animation(self):
        if self.current_loading_state:
            self.current_loading_state = self.loading_handler.next(
                self.current_loading_state
            )
            self.loading_label.setText(self.current_loading_state)

    def append_log(self, message):
        self.log_display.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec_())
