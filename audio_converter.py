# ============================================================
# НАЧАЛО НА IMPORTS
# ============================================================

import os

import shutil

import subprocess

import sys

import tempfile

import threading

from importlib import import_module

from pathlib import Path

from typing import Any

from PySide6.QtCore import (
    QObject,
    QEvent,
    QSettings,
    QThread,
    QTimer,
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from language_manager import language_manager

from themes import get_theme

# ============================================================
# КРАЙ НА IMPORTS
# ============================================================


try:
    yt_dlp: Any = import_module("yt_dlp")

except ImportError:

    yt_dlp = None


class StopRequested(Exception):

    pass


class NavigationContextMenu(QMenu):

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent,
        )

        self._original_actions = {}

        self._source_menu: QMenu | None = None

        self._current_index = -1

        self._app = QApplication.instance()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setStyleSheet("""
            QMenu::item {
                padding: 6px 24px 6px 24px;
            }

            QMenu::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
        """)

    def add_original_actions(
        self,
        actions,
    ):

        for original_action in actions:

            if original_action.isSeparator():

                self.addSeparator()

                continue

            menu_action = self.addAction(
                original_action.icon(),
                original_action.text(),
            )

            menu_action.setShortcut(original_action.shortcut())

            menu_action.setToolTip(original_action.toolTip())

            menu_action.setStatusTip(original_action.statusTip())

            menu_action.setEnabled(True)

            self._original_actions[menu_action] = original_action

            menu_action.triggered.connect(
                lambda _checked=False, action=menu_action: self._trigger_original(
                    action
                )
            )

    def _navigation_actions(
        self,
    ):

        return [action for action in self.actions() if not action.isSeparator()]

    def _set_current_index(
        self,
        index,
    ):

        actions = self._navigation_actions()

        if not actions:

            self._current_index = -1

            return

        self._current_index = index % len(actions)

        self.setActiveAction(actions[self._current_index])

    def _move_selection(
        self,
        step,
    ):

        actions = self._navigation_actions()

        if not actions:

            return

        if self._current_index < 0:

            active_action = self.activeAction()

            if active_action in actions:

                self._current_index = actions.index(active_action)

            else:

                self._current_index = 0

        self._set_current_index(self._current_index + step)

    def _activate_menu_focus(
        self,
    ):

        if not self.isVisible():

            return

        self.setFocus(Qt.FocusReason.PopupFocusReason)

        actions = self._navigation_actions()

        if actions:

            self._set_current_index(0)

    def showEvent(
        self,
        event,
    ):

        super().showEvent(event)

        QTimer.singleShot(
            0,
            self._activate_menu_focus,
        )

    def keyPressEvent(
        self,
        event,
    ):

        key = event.key()

        if key == Qt.Key.Key_Down:

            self._move_selection(1)

            event.accept()

            return

        if key == Qt.Key.Key_Up:

            self._move_selection(-1)

            event.accept()

            return

        if key in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):

            actions = self._navigation_actions()

            if not actions:

                event.accept()

                return

            if self._current_index < 0:

                active_action = self.activeAction()

                if active_action in actions:

                    self._current_index = actions.index(active_action)

                else:

                    self._current_index = 0

            self._trigger_original(actions[self._current_index])

            event.accept()

            return

        super().keyPressEvent(event)

    def eventFilter(
        self,
        obj,
        event,
    ):

        if event.type() == QEvent.Type.KeyPress and self.isVisible():

            key = event.key()

            if key == Qt.Key.Key_Down:

                self._move_selection(1)

                return True

            if key == Qt.Key.Key_Up:

                self._move_selection(-1)

                return True

            if key in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):

                actions = self._navigation_actions()

                if actions:

                    if self._current_index < 0:

                        self._current_index = 0

                    self._trigger_original(actions[self._current_index])

                return True

        return super().eventFilter(
            obj,
            event,
        )

    def _trigger_original(
        self,
        menu_action,
    ):

        original_action = self._original_actions.get(menu_action)

        if original_action is None:

            return

        line_edit = self.parentWidget()

        if not isinstance(
            line_edit,
            QLineEdit,
        ):

            return

        action_text = original_action.text().replace("&", "").strip().casefold()

        if action_text == "delete":

            if line_edit.hasSelectedText():

                line_edit.del_()

            self.close()

            return

        if not original_action.isEnabled():

            return

        if action_text == "undo":

            line_edit.undo()

        elif action_text == "redo":

            line_edit.redo()

        elif action_text == "cut":

            line_edit.cut()

        elif action_text == "copy":

            line_edit.copy()

        elif action_text == "paste":

            line_edit.paste()

        elif action_text == "select all":

            line_edit.selectAll()

        else:

            original_action.trigger()

        self.close()


class NavigationLineEdit(QLineEdit):

    def contextMenuEvent(
        self,
        event,
    ):

        standard_menu = self.createStandardContextMenu()

        menu = NavigationContextMenu(self)

        menu._source_menu = standard_menu
        menu.add_original_actions(standard_menu.actions())

        actions = menu._navigation_actions()

        if actions:

            menu._set_current_index(0)

        app = QApplication.instance()

        if app is not None:

            app.installEventFilter(menu)

        try:

            menu.exec(event.globalPos())

        finally:

            if app is not None:

                app.removeEventFilter(menu)


class NavigationComboBox(QComboBox):

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(
        self,
        event,
    ):

        if event.key() == Qt.Key.Key_Down:

            if not self.view().isVisible():

                self.showPopup()

                event.accept()

                return

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):

            if self.view().isVisible():

                self.hidePopup()

                event.accept()

                return

        super().keyPressEvent(event)


class NavigationButton(QPushButton):

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setAutoDefault(False)

        self.setDefault(False)

    def keyPressEvent(
        self,
        event,
    ):

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):

            self.click()

            event.accept()

            return

        super().keyPressEvent(event)

    def keyReleaseEvent(
        self,
        event,
    ):

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):

            event.accept()

            return

        super().keyReleaseEvent(event)


class ConverterWorker(QObject):

    progress = Signal(int)

    status = Signal(str)

    finished = Signal(bool, str)

    def __init__(
        self,
        sources: list[dict[str, str]],
        output_folder: str,
        output_format: str,
        quality: str,
        stop_event: threading.Event,
        ffmpeg_path: str,
        ffprobe_path: str | None,
    ):

        super().__init__()

        self.sources = sources

        self.output_folder = output_folder

        self.output_format = output_format

        self.quality = quality

        self.stop_event = stop_event

        self.ffmpeg_path = ffmpeg_path

        self.ffprobe_path = ffprobe_path

    def run(self):

        try:

            total = len(self.sources)

            if total == 0:

                self.finished.emit(
                    False,
                    language_manager.get("converter_no_sources"),
                )

                return

            for index, source in enumerate(self.sources):

                self._check_stop()

                display_name = source["value"]

                self.status.emit(
                    language_manager.get(
                        "converter_processing",
                        current=str(index + 1),
                        total=str(total),
                        name=os.path.basename(display_name),
                    )
                )

                base_progress = int(index * 100 / total)

                file_progress_size = 100 / total

                if source["type"] == "url":

                    downloaded_file = self.download_url(
                        source["value"],
                        index,
                        base_progress,
                        file_progress_size,
                    )

                    try:

                        self.convert_file(
                            downloaded_file,
                            index,
                            base_progress,
                            file_progress_size,
                            start_ratio=0.60,
                        )

                    finally:

                        try:

                            os.remove(downloaded_file)

                        except OSError:

                            pass

                else:

                    self.convert_file(
                        source["value"],
                        index,
                        base_progress,
                        file_progress_size,
                        start_ratio=0.00,
                    )

            self.progress.emit(100)

            self.finished.emit(
                True,
                language_manager.get("converter_success"),
            )

        except StopRequested:

            self.finished.emit(
                False,
                language_manager.get("converter_stopped"),
            )

        except Exception as error:

            self.finished.emit(
                False,
                language_manager.get(
                    "converter_operation_error",
                    error=str(error),
                ),
            )

    def _check_stop(
        self,
    ):

        if self.stop_event.is_set():

            raise StopRequested()

    def download_url(
        self,
        url: str,
        index: int,
        base_progress: int,
        file_progress_size: float,
    ) -> str:

        del index

        self._check_stop()

        if yt_dlp is None:

            raise RuntimeError(language_manager.get("converter_missing_yt_dlp"))

        temp_dir = tempfile.mkdtemp(prefix="mp3_order_converter_")

        def progress_hook(data: dict[str, Any]):

            self._check_stop()

            status = data.get("status")

            if status == "downloading":

                downloaded = data.get(
                    "downloaded_bytes",
                    0,
                )

                total_bytes = (
                    data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                )

                if total_bytes:

                    percent = downloaded * 100 / total_bytes

                    overall = base_progress + file_progress_size * 0.60 * percent / 100

                    self.progress.emit(
                        min(
                            100,
                            int(overall),
                        )
                    )

            elif status == "finished":

                overall = base_progress + file_progress_size * 0.60

                self.progress.emit(
                    min(
                        100,
                        int(overall),
                    )
                )

        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(
                temp_dir,
                "%(title)s.%(ext)s",
            ),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "restrictfilenames": False,
            "windowsfilenames": True,
            "overwrites": True,
        }

        self.status.emit(
            language_manager.get(
                "converter_downloading",
                url=url,
            )
        )

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                ydl.download([url])

        except Exception:

            if self.stop_event.is_set():

                raise StopRequested()

            raise

        files: list[str] = []

        for filename in os.listdir(temp_dir):

            full_path = os.path.join(
                temp_dir,
                filename,
            )

            if os.path.isfile(full_path):

                files.append(full_path)

        if not files:

            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )

            raise RuntimeError(language_manager.get("converter_no_downloaded_file"))

        downloaded_file = max(
            files,
            key=os.path.getmtime,
        )

        final_file = os.path.join(
            tempfile.gettempdir(),
            os.path.basename(downloaded_file),
        )

        shutil.copy2(
            downloaded_file,
            final_file,
        )

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )

        return final_file

    def convert_file(
        self,
        input_file: str,
        index: int,
        base_progress: int,
        file_progress_size: float,
        start_ratio: float,
    ):

        del index

        self._check_stop()

        extension = self.get_output_extension()

        source_name = Path(input_file).stem

        output_file = self.create_unique_output_path(
            source_name,
            extension,
        )

        duration = self.get_duration(input_file)

        command = self.build_ffmpeg_command(
            input_file,
            output_file,
        )

        self.status.emit(
            language_manager.get(
                "converter_converting",
                name=os.path.basename(input_file),
            )
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
        )

        stdout = process.stdout

        if stdout is None:

            process.kill()

            raise RuntimeError(language_manager.get("converter_ffmpeg_output_error"))

        try:

            while True:

                self._check_stop()

                line = stdout.readline()

                if line:

                    line = line.strip()

                    if line.startswith("out_time_ms="):

                        value = line.split(
                            "=",
                            1,
                        )[1]

                        try:

                            out_time_us = int(value)

                        except ValueError:

                            out_time_us = 0

                        if duration > 0:

                            converted_seconds = out_time_us / 1_000_000

                            percent = min(
                                100,
                                (converted_seconds * 100 / duration),
                            )

                            relative_start = start_ratio

                            relative_available = 1.0 - relative_start

                            overall = base_progress + file_progress_size * (
                                relative_start + relative_available * percent / 100
                            )

                            self.progress.emit(
                                min(
                                    100,
                                    int(overall),
                                )
                            )

                elif process.poll() is not None:

                    break

            return_code = process.wait()

            self._check_stop()

            if return_code != 0:

                raise RuntimeError(language_manager.get("converter_ffmpeg_failed"))

            self.progress.emit(
                min(
                    100,
                    int(base_progress + file_progress_size),
                )
            )

        finally:

            if process.poll() is None:

                process.terminate()

                try:

                    process.wait(timeout=2)

                except subprocess.TimeoutExpired:

                    process.kill()

    def build_ffmpeg_command(
        self,
        input_file: str,
        output_file: str,
    ) -> list[str]:

        fmt = self.output_format

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            input_file,
            "-vn",
        ]

        if fmt == "MP3":

            command += [
                "-codec:a",
                "libmp3lame",
                "-b:a",
                self.quality,
            ]

        elif fmt == "WAV":

            command += [
                "-codec:a",
                "pcm_s16le",
                "-ar",
                self.quality,
            ]

        elif fmt == "FLAC":

            command += [
                "-codec:a",
                "flac",
                "-ar",
                self.quality,
            ]

        elif fmt == "AAC":

            command += [
                "-codec:a",
                "aac",
                "-b:a",
                self.quality,
            ]

        elif fmt == "OGG":

            command += [
                "-codec:a",
                "libvorbis",
                "-b:a",
                self.quality,
            ]

        command += [
            "-progress",
            "pipe:1",
            "-nostats",
            output_file,
        ]

        return command

    def get_output_extension(
        self,
    ) -> str:

        extensions = {
            "MP3": ".mp3",
            "WAV": ".wav",
            "FLAC": ".flac",
            "AAC": ".m4a",
            "OGG": ".ogg",
        }

        return extensions[self.output_format]

    def get_duration(
        self,
        filename: str,
    ) -> float:

        if not self.ffprobe_path:

            return 0.0

        command = [
            self.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=30,
            )

            value = result.stdout.strip()

            return float(value)

        except Exception:

            return 0.0

    def create_unique_output_path(
        self,
        source_name: str,
        extension: str,
    ) -> str:

        safe_name = source_name.strip()

        if not safe_name:

            safe_name = "converted_audio"

        safe_name = "".join(
            character if character not in '<>:"/\\|?*' else "_"
            for character in safe_name
        )

        output_path = os.path.join(
            self.output_folder,
            safe_name + extension,
        )

        counter = 2

        while os.path.exists(output_path):

            output_path = os.path.join(
                self.output_folder,
                f"{safe_name} ({counter}){extension}",
            )

            counter += 1

        return output_path


class AudioConverter(QDialog):

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle(language_manager.get("converter_title"))

        self.setFixedSize(
            900,
            650,
        )

        self.setWindowFlag(
            Qt.WindowType.WindowContextHelpButtonHint,
            False,
        )

        self.sources: list[dict[str, str]] = []

        self.convert_thread: QThread | None = None

        self.worker: ConverterWorker | None = None

        self.stop_event = threading.Event()

        self._delete_confirmation_active = False

        self._delete_key_lock = False

        theme_settings = QSettings(
            "MP3_Order",
            "MP3_Order_PRO",
        )

        theme_name = str(
            theme_settings.value(
                "theme_name",
                "Лилаво-синя",
            )
        )

        self.current_theme = get_theme(theme_name)

        self.ffmpeg_path = self.find_executable("ffmpeg.exe")

        self.ffprobe_path = self.find_executable("ffprobe.exe")

        self.build_ui()

        self.apply_theme()

        self.center_window()

        self.update_quality_options()

        QTimer.singleShot(
            0,
            lambda: self.url_input.setFocus(Qt.FocusReason.OtherFocusReason),
        )

    def find_executable(
        self,
        executable_name: str,
    ) -> str:

        project_folder = Path(__file__).resolve().parent

        candidates = [
            (
                project_folder
                / "ffmpeg-n9.0-latest-win64-gpl-9.0"
                / "bin"
                / executable_name
            ),
            (project_folder / "ffmpeg" / "bin" / executable_name),
            (project_folder / executable_name),
        ]

        for path in candidates:

            if path.exists():

                return str(path)

        system_executable = shutil.which(executable_name)

        if system_executable:

            return system_executable

        return ""

    def build_ui(
        self,
    ):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(12)

        title_label = QLabel(language_manager.get("converter_header"))

        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(title_label)

        url_layout = QHBoxLayout()

        self.url_input = NavigationLineEdit()

        self.url_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.url_input.setPlaceholderText(
            language_manager.get("converter_url_placeholder")
        )

        self.add_url_button = NavigationButton(
            language_manager.get("converter_add_url")
        )

        url_layout.addWidget(self.url_input)

        url_layout.addWidget(self.add_url_button)

        main_layout.addLayout(url_layout)

        files_layout = QHBoxLayout()

        self.add_files_button = NavigationButton(
            language_manager.get("converter_add_files")
        )

        self.remove_file_button = NavigationButton(
            language_manager.get("converter_remove")
        )

        self.clear_files_button = NavigationButton(
            language_manager.get("converter_clear")
        )

        files_layout.addWidget(self.add_files_button)

        files_layout.addWidget(self.remove_file_button)

        files_layout.addWidget(self.clear_files_button)

        main_layout.addLayout(files_layout)

        self.files_list = QListWidget()

        self.files_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.files_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.files_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.files_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        main_layout.addWidget(self.files_list)

        self.files_list.installEventFilter(self)

        format_layout = QHBoxLayout()

        format_layout.addWidget(QLabel(language_manager.get("converter_format")))

        self.format_combo = NavigationComboBox()

        self.format_combo.addItems(
            [
                "MP3",
                "WAV",
                "FLAC",
                "AAC",
                "OGG",
            ]
        )

        format_layout.addWidget(self.format_combo)

        format_layout.addWidget(QLabel(language_manager.get("converter_quality")))

        self.quality_combo = NavigationComboBox()

        format_layout.addWidget(self.quality_combo)

        main_layout.addLayout(format_layout)

        output_layout = QHBoxLayout()

        self.output_path = QLineEdit()

        self.output_path.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.output_path.setPlaceholderText(
            language_manager.get("converter_output_placeholder")
        )

        self.output_button = NavigationButton(language_manager.get("converter_folder"))

        output_layout.addWidget(self.output_path)

        output_layout.addWidget(self.output_button)

        main_layout.addLayout(output_layout)

        self.status_label = QLabel(language_manager.get("converter_ready"))

        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(0)

        main_layout.addWidget(self.progress_bar)

        buttons_layout = QHBoxLayout()

        self.convert_button = NavigationButton(
            language_manager.get("converter_convert")
        )

        self.cancel_button = NavigationButton(language_manager.get("converter_stop"))

        self.cancel_button.setEnabled(False)

        buttons_layout.addWidget(self.convert_button)

        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

        self.add_files_button.clicked.connect(self.add_files)

        self.remove_file_button.clicked.connect(self.url_input.clear)

        self.clear_files_button.clicked.connect(self.clear_files)

        self.add_url_button.clicked.connect(self.add_url)

        self.url_input.returnPressed.connect(self.add_url)

        self.output_button.clicked.connect(self.choose_output_folder)

        self.format_combo.currentTextChanged.connect(self.update_quality_options)

        self.convert_button.clicked.connect(self.start_conversion)

        self.cancel_button.clicked.connect(self.stop_conversion)

    def apply_theme(
        self,
    ):

        theme = self.current_theme

        self.setStyleSheet(f"""
            QDialog {{
                background: {theme["window_bg"]};
                color: {theme["main_text"]};
            }}

            QLabel {{
                color: {theme["main_text"]};
            }}

            QLineEdit {{
                background: {theme["table_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                border-radius: 7px;
                padding: 6px;
                selection-background-color: {theme["table_selected"]};
                selection-color: {theme["main_text"]};
            }}

            QLineEdit:focus {{
                border: 2px solid {theme["accent"]};
            }}

            QListWidget {{
                background: {theme["table_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                border-radius: 7px;
                padding: 4px;
            }}

            QListWidget::item {{
                padding: 5px;
            }}

            QListWidget::item:selected {{
                background: {theme["table_selected"]};
                color: {theme["main_text"]};
            }}

            QComboBox {{
                background: {theme["button_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                border-radius: 7px;
                padding: 5px 8px;
            }}

            QComboBox:hover {{
                border: 1px solid {theme["accent"]};
            }}

            QComboBox:focus {{
                border: 2px solid {theme["accent"]};
            }}

            QComboBox QAbstractItemView {{
                background: {theme["table_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                selection-background-color: {theme["table_selected"]};
                selection-color: {theme["main_text"]};
            }}

            QPushButton {{
                background: {theme["button_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                border-radius: 7px;
                padding: 7px 12px;
            }}

            QPushButton:hover {{
                background: {theme["accent"]};
                color: {theme["main_text"]};
            }}

            QPushButton:pressed {{
                background: {theme["accent_light"]};
                color: {theme["main_text"]};
            }}

            QPushButton:focus {{
                background: {theme["accent_light"]};
                color: {theme["main_text"]};
                border: 3px solid {theme["accent"]};
                border-radius: 7px;
            }}

            QPushButton:disabled {{
                background: {theme["panel_bg_2"]};
                color: {theme["secondary_text"]};
                border: 1px solid {theme["button_border"]};
            }}

            QProgressBar {{
                background: {theme["table_bg"]};
                color: {theme["main_text"]};
                border: 1px solid {theme["button_border"]};
                border-radius: 7px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background: {theme["accent"]};
                border-radius: 6px;
            }}

            QScrollBar:vertical {{
                width: 14px;
                background: {theme["panel_bg_2"]};
                margin: 0px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background: {theme["accent"]};
                min-height: 30px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {theme["accent_light"]};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            """)

    def center_window(
        self,
    ):

        screen = QApplication.primaryScreen()

        if screen is None:

            return

        screen_geometry = screen.availableGeometry()

        window_geometry = self.frameGeometry()

        window_geometry.moveCenter(screen_geometry.center())

        self.move(window_geometry.topLeft())

    def focusNextPrevChild(
        self,
        next_widget: bool,
    ):

        focus_order = [
            self.url_input,
            self.add_url_button,
            self.add_files_button,
            self.remove_file_button,
            self.clear_files_button,
            self.files_list,
            self.format_combo,
            self.quality_combo,
            self.output_path,
            self.output_button,
            self.convert_button,
            self.cancel_button,
        ]

        current = self.focusWidget()

        if current not in focus_order:

            return super().focusNextPrevChild(next_widget)

        current_index = focus_order.index(current)

        step = 1 if next_widget else -1

        for _ in range(len(focus_order)):

            current_index = (current_index + step) % len(focus_order)

            target = focus_order[current_index]

            if target.isEnabled() and target.focusPolicy() != Qt.FocusPolicy.NoFocus:

                target.setFocus(Qt.FocusReason.TabFocusReason)

                return True

        return False

    def _release_delete_key_lock(
        self,
    ):

        self._delete_key_lock = False

    def eventFilter(
        self,
        obj,
        event,
    ):

        if isinstance(obj, QPushButton) and obj.property("_delete_confirmation_button"):

            if event.type() == QEvent.Type.KeyPress:

                if event.key() in (
                    Qt.Key.Key_Left,
                    Qt.Key.Key_Right,
                ):

                    message_box = obj.window()

                    buttons = message_box.findChildren(QPushButton)

                    if len(buttons) >= 2:

                        current_index = buttons.index(obj)

                        if event.key() == Qt.Key.Key_Left:

                            target_index = current_index - 1

                        else:

                            target_index = current_index + 1

                        if 0 <= target_index < len(buttons):

                            buttons[target_index].setFocus(
                                Qt.FocusReason.OtherFocusReason
                            )

                        return True

        if obj is self.files_list:

            key_method = getattr(
                event,
                "key",
                None,
            )

            if callable(key_method):

                if key_method() == Qt.Key.Key_Delete:

                    if event.type() == QEvent.Type.KeyPress:

                        if self._delete_key_lock:

                            return True

                        if event.isAutoRepeat():

                            return True

                        self._delete_key_lock = True

                        self.remove_selected()

                        QTimer.singleShot(
                            250,
                            self._release_delete_key_lock,
                        )

                        return True

                    if event.type() == QEvent.Type.KeyRelease:

                        return True

        return super().eventFilter(
            obj,
            event,
        )

    def update_quality_options(
        self,
    ):

        self.quality_combo.clear()

        fmt = self.format_combo.currentText()

        if fmt in {
            "MP3",
            "AAC",
            "OGG",
        }:

            self.quality_combo.addItems(
                [
                    "128 kbps",
                    "192 kbps",
                    "256 kbps",
                    "320 kbps",
                ]
            )

        else:

            self.quality_combo.addItems(
                [
                    "44100 Hz",
                    "48000 Hz",
                ]
            )

    def add_files(
        self,
    ):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            language_manager.get("converter_add_files"),
            "",
            (
                language_manager.get("converter_audio_filter")
                + ";;"
                + language_manager.get("converter_all_files")
            ),
        )

        for file_path in files:

            if self.source_exists(
                "file",
                file_path,
            ):

                continue

            self.add_source(
                "file",
                file_path,
            )

    def add_url(
        self,
    ):

        url = self.url_input.text().strip()

        if not url:

            QApplication.beep()

            QMessageBox.warning(
                self,
                language_manager.get("converter_missing_link_title"),
                language_manager.get("converter_missing_link"),
            )

            self.url_input.setFocus(Qt.FocusReason.OtherFocusReason)

            return

        if not (url.startswith("http://") or url.startswith("https://")):

            QApplication.beep()

            QMessageBox.warning(
                self,
                language_manager.get("converter_invalid_link_title"),
                language_manager.get("converter_invalid_link"),
            )

            self.url_input.setFocus(Qt.FocusReason.OtherFocusReason)

            return

        if self.source_exists(
            "url",
            url,
        ):

            QApplication.beep()

            QMessageBox.warning(
                self,
                language_manager.get("converter_duplicate_link_title"),
                language_manager.get("converter_duplicate_link"),
            )

            self.url_input.setFocus(Qt.FocusReason.OtherFocusReason)

            return

        self.add_source(
            "url",
            url,
        )

        self.url_input.clear()

        self.add_url_button.setFocus(Qt.FocusReason.OtherFocusReason)

    def add_source(
        self,
        source_type: str,
        value: str,
    ):

        self.sources.append(
            {
                "type": source_type,
                "value": value,
            }
        )

        if source_type == "url":

            url_number = sum(1 for source in self.sources if source["type"] == "url")

            text = f"🔗 {url_number}. " f"{value}"

        else:

            text = f"📁 " f"{os.path.basename(value)}"

        item = QListWidgetItem(text)

        item.setData(
            Qt.ItemDataRole.UserRole,
            {
                "type": source_type,
                "value": value,
            },
        )

        self.files_list.addItem(item)

    def source_exists(
        self,
        source_type: str,
        value: str,
    ) -> bool:

        for source in self.sources:

            if (
                source["type"] == source_type
                and source["value"].strip() == value.strip()
            ):

                return True

        return False

    def remove_selected(
        self,
    ):

        selected_rows = sorted(
            {self.files_list.row(item) for item in self.files_list.selectedItems()},
            reverse=True,
        )

        if not selected_rows:

            return

        selected_count = len(selected_rows)

        total_urls = sum(1 for source in self.sources if source["type"] == "url")

        selected_url_count = sum(
            1 for row in selected_rows if self.sources[row]["type"] == "url"
        )

        if selected_count == 1:

            if selected_url_count == 1:

                message = language_manager.get("converter_delete_selected_link")

            else:

                message = language_manager.get("converter_delete_selected_file")

        elif (
            total_urls > 1
            and selected_count == total_urls
            and selected_url_count == total_urls
        ):

            message = language_manager.get("converter_delete_all_links")

        elif selected_count > 1 and selected_url_count == selected_count:

            message = language_manager.get("converter_delete_selected_links").format(
                count=str(selected_count)
            )

        else:

            message = language_manager.get("converter_delete_selected_items").format(
                count=str(selected_count)
            )

        QApplication.beep()

        self._delete_confirmation_active = True

        try:

            message_box = QMessageBox(self)

            message_box.setIcon(QMessageBox.Icon.Question)

            message_box.setWindowTitle(language_manager.get("question"))

            message_box.setText(message)

            message_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            yes_button = message_box.button(QMessageBox.StandardButton.Yes)

            no_button = message_box.button(QMessageBox.StandardButton.No)

            if yes_button is not None:

                yes_button.setText(language_manager.get("yes"))

                yes_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

                yes_button.setProperty(
                    "_delete_confirmation_button",
                    True,
                )

                yes_button.installEventFilter(self)

                yes_button.setStyleSheet(f"""
                    QPushButton {{
                        min-width: 80px;
                        padding: 6px 14px;
                    }}

                    QPushButton:focus {{
                        border: 2px solid
                        {self.current_theme["accent"]};
                    }}
                    """)

            if no_button is not None:

                no_button.setText(language_manager.get("no"))

                no_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

                no_button.setProperty(
                    "_delete_confirmation_button",
                    True,
                )

                no_button.installEventFilter(self)

                no_button.setStyleSheet(f"""
                    QPushButton {{
                        min-width: 80px;
                        padding: 6px 14px;
                    }}

                    QPushButton:focus {{
                        border: 2px solid
                        {self.current_theme["accent"]};
                    }}
                    """)

            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)

            if yes_button is not None:

                QTimer.singleShot(
                    0,
                    lambda: yes_button.setFocus(Qt.FocusReason.OtherFocusReason),
                )

            reply = message_box.exec()

            if reply != QMessageBox.StandardButton.Yes:

                return

            for row in selected_rows:

                self.files_list.takeItem(row)

                self.sources.pop(row)

            url_number = 0

            for index, source in enumerate(self.sources):

                if source["type"] == "url":

                    url_number += 1

                    text = f"🔗 {url_number}. " f"{source['value']}"

                else:

                    text = f"📁 " f"{os.path.basename(source['value'])}"

                self.files_list.item(index).setText(text)

        finally:

            self._delete_confirmation_active = False

    def _ask_confirmation(
        self,
        message,
    ):

        message_box = QMessageBox(self)

        message_box.setIcon(QMessageBox.Icon.Question)

        message_box.setWindowTitle(language_manager.get("question"))

        message_box.setText(message)

        message_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        yes_button = message_box.button(QMessageBox.StandardButton.Yes)

        no_button = message_box.button(QMessageBox.StandardButton.No)

        if yes_button is not None:

            yes_button.setText(language_manager.get("yes"))

        if no_button is not None:

            no_button.setText(language_manager.get("no"))

        message_box.setDefaultButton(QMessageBox.StandardButton.No)

        return message_box.exec() == QMessageBox.StandardButton.Yes

    def clear_files(
        self,
    ):

        if not self.sources:

            return

        QApplication.beep()

        if not self._ask_confirmation(language_manager.get("converter_clear_message")):

            return

        self.files_list.clear()

        self.sources.clear()

    def choose_output_folder(
        self,
    ):

        folder = QFileDialog.getExistingDirectory(
            self,
            language_manager.get("converter_output_folder_title"),
        )

        if folder:

            self.output_path.setText(folder)

    def start_conversion(
        self,
    ):

        if not self.ffmpeg_path:

            QMessageBox.critical(
                self,
                language_manager.get("converter_no_ffmpeg_title"),
                language_manager.get("converter_no_ffmpeg"),
            )

            return

        if not self.sources:

            QMessageBox.warning(
                self,
                language_manager.get("converter_no_sources_title"),
                language_manager.get("converter_no_sources"),
            )

            return

        output_folder = self.output_path.text().strip()

        if not output_folder:

            QMessageBox.warning(
                self,
                language_manager.get("converter_no_output_title"),
                language_manager.get("converter_no_output"),
            )

            return

        if not os.path.isdir(output_folder):

            QMessageBox.warning(
                self,
                language_manager.get("converter_invalid_output_title"),
                language_manager.get("converter_invalid_output"),
            )

            return

        quality_text = self.quality_combo.currentText()

        if quality_text.endswith(" kbps"):

            quality = quality_text.replace(
                " kbps",
                "k",
            )

        else:

            quality = quality_text.replace(
                " Hz",
                "",
            )

        self.stop_event.clear()

        self.progress_bar.setValue(0)

        self.convert_button.setEnabled(False)

        self.cancel_button.setEnabled(True)

        self.url_input.setEnabled(False)

        self.files_list.setEnabled(False)

        self.add_files_button.setEnabled(False)

        self.add_url_button.setEnabled(False)

        self.remove_file_button.setEnabled(False)

        self.clear_files_button.setEnabled(False)

        self.output_button.setEnabled(False)

        self.format_combo.setEnabled(False)

        self.quality_combo.setEnabled(False)

        self.status_label.setText(language_manager.get("converter_prepare"))

        convert_thread = QThread()

        worker = ConverterWorker(
            self.sources.copy(),
            output_folder,
            self.format_combo.currentText(),
            quality,
            self.stop_event,
            self.ffmpeg_path,
            self.ffprobe_path,
        )

        self.convert_thread = convert_thread

        self.worker = worker

        worker.moveToThread(convert_thread)

        convert_thread.started.connect(worker.run)

        worker.progress.connect(self.progress_bar.setValue)

        worker.status.connect(self.status_label.setText)

        worker.finished.connect(self.conversion_finished)

        worker.finished.connect(convert_thread.quit)

        worker.finished.connect(worker.deleteLater)

        convert_thread.finished.connect(convert_thread.deleteLater)

        convert_thread.finished.connect(self.conversion_thread_finished)

        convert_thread.start()

    def stop_conversion(
        self,
    ):

        if self.convert_thread is None:

            return

        QApplication.beep()

        if not self._ask_confirmation(
            language_manager.get("converter_stop_confirmation")
        ):

            return

        self.status_label.setText(language_manager.get("converter_status_stopping"))

        self.stop_event.set()

        self.cancel_button.setEnabled(False)

    def conversion_finished(
        self,
        success: bool,
        message: str,
    ):

        self.convert_button.setEnabled(True)

        self.cancel_button.setEnabled(False)

        self.url_input.setEnabled(True)

        self.files_list.setEnabled(True)

        self.add_files_button.setEnabled(True)

        self.add_url_button.setEnabled(True)

        self.remove_file_button.setEnabled(True)

        self.clear_files_button.setEnabled(True)

        self.output_button.setEnabled(True)

        self.format_combo.setEnabled(True)

        self.quality_combo.setEnabled(True)

        if success:

            self.progress_bar.setValue(100)

            self.status_label.setText(language_manager.get("converter_success_status"))

            QMessageBox.information(
                self,
                language_manager.get("converter_success_title"),
                language_manager.get("converter_success"),
            )

        else:

            self.status_label.setText(message)

            if message != language_manager.get("converter_stopped"):

                QMessageBox.warning(
                    self,
                    language_manager.get("converter_title"),
                    message,
                )

    def reject(
        self,
    ):

        if self.convert_thread is not None and self.convert_thread.isRunning():

            QApplication.beep()

            return

        super().reject()

    def conversion_thread_finished(
        self,
    ):

        self.convert_thread = None

        self.worker = None

    def closeEvent(
        self,
        event,
    ):

        if self.convert_thread is not None:

            self.stop_event.set()

            self.convert_thread.quit()

            self.convert_thread.wait(5000)

        event.accept()
