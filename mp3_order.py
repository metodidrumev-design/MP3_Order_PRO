# Начало на imports
# ======================================

import sys
import os
import ctypes

import shutil
import re
import threading

from typing import cast

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QTextEdit,
    QPlainTextEdit,
    QMenuBar,
    QMenu,
    QFrame,
    QSizePolicy,
    QSlider,
    QProgressBar,
)

from PySide6.QtCore import (
    Qt,
    QMimeData,
    Signal,
    QTimer,
    QElapsedTimer,
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
)

from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QShortcut,
    QAction,
    QIcon,
    QPixmap,
)

from mutagen.mp3 import MP3
from mutagen.id3 import ID3

import vlc

from audio_splitter import AudioSplitter
from accessibility import AccessibilityManager
from accessibility_ui import AccessibilityUI
from language_manager import language_manager
from updater import check_for_update

# =================
# Край на imports


# ===== ПЪТ КЪМ ЛОГОТО =====

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_DIR, "assets", "MP3_Order_Logo.png")


songs = []


edited_tags = {}
undo_stack = []


def song_info(path):

    filename = os.path.splitext(os.path.basename(path))[0]

    # Маха номера отпред
    filename = re.sub(r"^(?:\s*\d+\s*-\s*)+", "", filename)

    title = ""
    artist = ""

    # Опитва да раздели по първото " - "
    parts = filename.split(" - ", 1)

    if len(parts) == 2:

        artist = parts[0].strip()

        artist = re.sub(r"^(?:\d+\s*)+", "", artist).strip()

        title = parts[1].strip()

        # Премахва излишни думи от заглавието
        title = re.sub(r"\(.*?Official.*?\)", "", title, flags=re.IGNORECASE)

        title = re.sub(r"\[.*?Official.*?\]", "", title, flags=re.IGNORECASE)

        title = re.sub(r"Official Music Video", "", title, flags=re.IGNORECASE)

        title = re.sub(r"Official Video", "", title, flags=re.IGNORECASE)

        title = re.sub(r"Official Audio", "", title, flags=re.IGNORECASE)

        title = re.sub(r"Lyrics", "", title, flags=re.IGNORECASE)

        title = re.sub(r"\bHD\b", "", title, flags=re.IGNORECASE)

        title = re.sub(r"\bHQ\b", "", title, flags=re.IGNORECASE)

        title = re.sub(r"\s+", " ", title).strip(" -")

    else:

        title = filename.strip()

    try:

        audio = MP3(path, ID3=ID3)

        if audio.tags:

            # Проверка на ID3 заглавие
            if "TIT2" in audio.tags:

                temp_title = str(audio.tags["TIT2"]).strip()

                bad_titles = {
                    "",
                    "-",
                    "--",
                    "/",
                    "\\",
                    "0",
                    "00",
                    "000",
                    ".",
                    "..",
                    "_",
                    "- 0",
                    "0 -",
                    "-0",
                    "0-",
                    "0`0`0",
                    ",",
                    ",,",
                    ", ,",
                    '""',
                    "''",
                }

                if temp_title not in bad_titles:

                    title = temp_title

            # Проверка на ID3 изпълнител
            if "TPE1" in audio.tags:

                temp_artist = str(audio.tags["TPE1"]).strip()

                bad_artists = {
                    "",
                    "-",
                    "--",
                    "/",
                    "\\",
                    "0",
                    "00",
                    "000",
                    ".",
                    "..",
                    "_",
                    ",",
                    ",,",
                    ", ,",
                    '""',
                    "''",
                }

                if temp_artist not in bad_artists:

                    artist = temp_artist

        total_seconds = int(audio.info.length)

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        duration = f"{minutes:02}:{seconds:02}"

    except Exception:

        duration = "00:00"

    # Последна проверка за безсмислено заглавие
    bad_titles = {
        "",
        "-",
        "--",
        "/",
        "\\",
        "0",
        "00",
        "000",
        ".",
        "..",
        "_",
        "- 0",
        "0 -",
        "-0",
        "0-",
        "0`0`0",
        ",",
        ",,",
        ", ,",
        '""',
        "''",
    }

    if title.strip() in bad_titles:

        title = filename

    # =========================================================
    # АКО ИМА РЕДАКЦИЯ В ПРОГРАМАТА
    # =========================================================

    if path in edited_tags:

        if "title" in edited_tags[path]:

            title = edited_tags[path]["title"]

        if "artist" in edited_tags[path]:

            artist = edited_tags[path]["artist"]

    return title, artist, duration


class SongTableWidget(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._drag_row = -1
        self._drop_row = -1
        self._mouse_down_pos = None

        # Вътрешното Qt влачене е изключено.
        # Разместването на песните се управлява от нашите mouse events.
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setDragEnabled(False)

        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self.auto_scroll)
        self._scroll_direction = 0

        self.setMouseTracking(True)

        self.setStyleSheet(f"""

        QTableWidget::item:hover {{

            background: transparent;

            border: none;

        }}

        """)

    def mousePressEvent(self, event):

        # Десен бутон -> не променя селекцията
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:

            row = self.rowAt(event.position().toPoint().y())

            # Празните редове не могат да се избират/влачат.
            if row < 0 or row >= len(songs):
                self._drag_row = -1
                self._drop_row = -1
                self._mouse_down_pos = None
                self.clearSelection()
                self.setCurrentCell(-1, -1)
                return

            self._drag_row = row
            self._drop_row = row
            self._mouse_down_pos = event.position().toPoint()

            self.clearSelection()
            self.selectRow(row)
            self.setCurrentCell(row, 1)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        # Ако няма заредени песни, не позволяваме
        # на Qt да маркира празните клетки.
        if not songs:

            self.clearSelection()
            self.setCurrentCell(-1, -1)
            self._scroll_direction = 0
            self._scroll_timer.stop()

            event.accept()
            return

        if (
            self._drag_row < 0
            or self._mouse_down_pos is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return

        current_pos = event.position().toPoint()
        y = current_pos.y()
        margin = 30

        self.setCursor(Qt.CursorShape.ClosedHandCursor)

        # Определяме целевата песен. Празните редове се свеждат до
        # последната реална песен, така че маркерът никога да не стои под нея.
        if songs:
            target_row = self.rowAt(y)
            last_row = len(songs) - 1

            if target_row < 0:
                target_row = 0
            elif target_row > last_row:
                target_row = last_row

            self._drop_row = target_row

            self.clearSelection()
            self.selectRow(target_row)
            self.setCurrentCell(target_row, 1)

        # Автоматично превъртане нагоре.
        if y < margin:

            first_index = self.model().index(0, 1)
            self._scroll_direction = -5

            if first_index.isValid():
                first_rect = self.visualRect(first_index)

                if first_rect.top() >= 0:
                    self._scroll_direction = 0
                    self._scroll_timer.stop()
                elif not self._scroll_timer.isActive():
                    self._scroll_timer.start(20)

        # Автоматично превъртане надолу.
        elif y > self.viewport().height() - margin:

            last_row = len(songs) - 1
            last_index = self.model().index(last_row, 1)
            self._scroll_direction = 5

            if last_index.isValid():
                last_rect = self.visualRect(last_index)
                viewport_bottom = self.viewport().rect().bottom()

                # Последната песен вече е долу -> повече надолу няма.
                if last_rect.bottom() <= viewport_bottom:
                    self._scroll_direction = 0
                    self._scroll_timer.stop()
                elif not self._scroll_timer.isActive():
                    self._scroll_timer.start(20)

        else:

            self._scroll_direction = 0
            self._scroll_timer.stop()

        event.accept()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            from_row = self._drag_row
            to_row = self._drop_row

            if 0 <= from_row < len(songs) and 0 <= to_row < len(songs):
                if from_row != to_row:

                    # Запазва състоянието за CTRL + Z
                    window = self.window()
                    push = getattr(window, "push_undo", None)

                    if callable(push):
                        push()

                    # Само песните си разменят местата.
                    # Номерата не се пипат.
                    songs[from_row], songs[to_row] = (songs[to_row], songs[from_row])

                    refresh_method = getattr(window, "refresh", None)

                    if callable(refresh_method):
                        refresh_method()

                    self.clearSelection()
                    self.selectRow(to_row)
                    self.setCurrentCell(to_row, 1)
                    self.setFocus()

            self._drag_row = -1
            self._drop_row = -1
            self._mouse_down_pos = None
            self._scroll_direction = 0
            self._scroll_timer.stop()
            self.unsetCursor()

            event.accept()
            return

        super().mouseReleaseEvent(event)

    def auto_scroll(self):

        if self._scroll_direction == 0 or not songs:
            self._scroll_direction = 0
            self._scroll_timer.stop()
            return

        bar = self.verticalScrollBar()

        if self._scroll_direction > 0:

            last_row = len(songs) - 1
            last_index = self.model().index(last_row, 1)

            if last_index.isValid():

                viewport_bottom = self.viewport().rect().bottom()

                # Проверяваме края ПРЕДИ движение.
                last_rect = self.visualRect(last_index)

                if last_rect.bottom() <= viewport_bottom:

                    self._scroll_direction = 0
                    self._scroll_timer.stop()

                    self._drop_row = last_row
                    self.clearSelection()
                    self.selectRow(last_row)
                    self.setCurrentCell(last_row, 1)

                    return

        elif self._scroll_direction < 0:

            first_index = self.model().index(0, 1)

            if first_index.isValid():

                first_rect = self.visualRect(first_index)

                if first_rect.top() >= 0:

                    self._scroll_direction = 0
                    self._scroll_timer.stop()

                    self._drop_row = 0
                    self.clearSelection()
                    self.selectRow(0)
                    self.setCurrentCell(0, 1)

                    return

        new_value = bar.value() + self._scroll_direction

        new_value = max(bar.minimum(), min(new_value, bar.maximum()))

        if new_value == bar.value():
            self._scroll_direction = 0
            self._scroll_timer.stop()
            return

        bar.setValue(new_value)

        # Проверяваме отново СЛЕД последната стъпка.
        if self._scroll_direction > 0:

            last_row = len(songs) - 1
            last_index = self.model().index(last_row, 1)

            if last_index.isValid():

                last_rect = self.visualRect(last_index)

                if last_rect.bottom() <= self.viewport().rect().bottom():

                    self._scroll_direction = 0
                    self._scroll_timer.stop()

                    self._drop_row = last_row
                    self.clearSelection()
                    self.selectRow(last_row)
                    self.setCurrentCell(last_row, 1)

    def keyPressEvent(self, event):

        # TAB -> директно към първия бутон вляво
        if event.key() == Qt.Key.Key_Tab:

            window = self.window()

            first_button = window.findChild(QPushButton, "addFilesButton")

            if first_button is not None:

                first_button.setFocus(Qt.FocusReason.TabFocusReason)

                return

            # Резервен вариант
            window.focusNextPrevChild(True)

            return

        # SHIFT + TAB -> предишен контрол
        elif event.key() == Qt.Key.Key_Backtab:
            self.window().focusNextPrevChild(False)
            return

        # F3 -> Маркира първата песен в списъка
        elif event.key() == Qt.Key.Key_F3:

            if songs:
                self.clearSelection()
                self.selectRow(0)
                self.setCurrentCell(0, 1)
                self.setFocus()

                item = self.item(0, 1)
                if item:
                    self.scrollToItem(
                        item, QAbstractItemView.ScrollHint.PositionAtCenter
                    )

            return

        # CTRL + Z -> Undo (работи на BG и EN)
        elif event.matches(QKeySequence.StandardKey.Undo):

            window = self.window()

            undo = getattr(window, "undo_last", None)

            if callable(undo):
                undo()

            return

        # CTRL + A -> маркира всички песни
        # Работи независимо дали клавиатурата е BG или EN.
        elif (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and event.nativeScanCode() == 30
        ):

            if songs:

                selection = self.selectionModel()

                top_left = self.model().index(0, 0)
                bottom_right = self.model().index(
                    len(songs) - 1, self.columnCount() - 1
                )

                selection.select(
                    QItemSelection(top_left, bottom_right),
                    QItemSelectionModel.SelectionFlag.Select
                    | QItemSelectionModel.SelectionFlag.Rows,
                )

            return

        # СТРЕЛКА НАДОЛУ -> следващата видима песен
        elif event.key() == Qt.Key.Key_Down:

            current_row = self.currentRow()

            for row in range(current_row + 1, len(songs)):

                if not self.isRowHidden(row):

                    self.clearSelection()
                    self.selectRow(row)
                    self.setCurrentCell(row, 1)

                    item = self.item(row, 1)

                    if item:
                        self.scrollToItem(
                            item, QAbstractItemView.ScrollHint.PositionAtCenter
                        )

                    return

            return

        # СТРЕЛКА НАГОРЕ -> предишната видима песен
        elif event.key() == Qt.Key.Key_Up:

            current_row = self.currentRow()

            for row in range(current_row - 1, -1, -1):

                if not self.isRowHidden(row):

                    self.clearSelection()
                    self.selectRow(row)
                    self.setCurrentCell(row, 1)

                    item = self.item(row, 1)

                    if item:
                        self.scrollToItem(
                            item, QAbstractItemView.ScrollHint.PositionAtCenter
                        )

                    return

            return

        # DELETE -> Изтрива избраната песен
        elif event.key() == Qt.Key.Key_Delete:

            window = self.window()

            remove_method = getattr(window, "remove", None)

            if callable(remove_method):
                remove_method()

            return

        super().keyPressEvent(event)


class MP3Order(QWidget):

    def __init__(self):

        super().__init__()
        self.apply_theme_settings()
        self._current_list_file = None
        self.playing_index = -1
        self.f3_last_path = None
        self.playing_path = None
        self._file_menu_selected = False
        self.accessibility = AccessibilityManager(self)
        self.accessibility_ui = AccessibilityUI(self)
        self.language_manager = language_manager

        self.setWindowTitle(self.language_manager.get("app_title"))

        # ===== ИКОНА НА ПРОГРАМАТА =====

        self.setWindowIcon(QIcon(LOGO_PATH))

        self.resize(1200, 800)

        self.setMinimumSize(900, 600)

        self.showMaximized()

        self._pending_update = None

        self._update_thread = threading.Thread(
            target=self._check_for_update_background,
            daemon=True,
        )

        self._update_thread.start()

        QTimer.singleShot(1000, self._check_update_result)

        self.setAcceptDrops(True)

        # ===== VLC PLAYER =====

        self.vlc_instance = vlc.Instance()

        if self.vlc_instance is None:
            raise RuntimeError(self.language_manager.get("vlc_init_error"))

        self.vlc_player = self.vlc_instance.media_player_new()

        # ===== VLC PROGRESS TIMER =====

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(50)
        self.progress_timer.timeout.connect(self.update_progress)

        # ===== MENU BAR =====

        menu_bar = QMenuBar(self)

        # =====================================================
        # МЕНЮ „ФАЙЛ“
        # =====================================================

        file_menu = QMenu(self.language_manager.get("file_menu"), self)

        file_menu.setStyleSheet("""
            QMenu {
                background: #303134;
                color: white;
                border: 1px solid #555;
                padding: 4px;
            }

            QMenu::item {
                background: transparent;
                color: white;
                padding: 8px 30px 8px 12px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background: #1E88E5;
                color: white;
            }

            QMenu::separator {
                height: 1px;
                background: #555;
                margin: 4px 8px;
            }
        """)

        new_list_action = QAction(self.language_manager.get("new_project"), self)

        new_list_action.triggered.connect(self.new_list)

        open_list_action = QAction(self.language_manager.get("open_project"), self)

        open_list_action.triggered.connect(self.open_list)

        save_list_action = QAction(self.language_manager.get("save_project"), self)

        save_list_action.triggered.connect(self.save_list)

        save_as_action = QAction(self.language_manager.get("save_project_as"), self)

        save_as_action.triggered.connect(self.save_list_as)

        file_menu.addAction(new_list_action)

        file_menu.addAction(open_list_action)

        file_menu.addAction(save_list_action)

        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction(self.language_manager.get("exit"), self)

        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

        # Добавяме „Файл“
        menu_bar.addMenu(file_menu)

        # =====================================================
        # ДИРЕКТЕН БУТОН „НАСТРОЙКИ“
        # =====================================================

        settings_action = QAction(self.language_manager.get("settings"), self)

        settings_action.triggered.connect(self.open_settings)

        # Настройки е директно меню-бутона,
        # без QMenu и без подменю.
        menu_bar.addAction(settings_action)

        # =====================================================
        # РАЗДЕЛЯНЕ НА MP3
        # =====================================================

        splitter_action = QAction(self.language_manager.get("split_mp3"), self)

        splitter_action.triggered.connect(self.open_audio_splitter)

        menu_bar.addAction(splitter_action)

        # =====================================================
        # ЗАПАЗВАМЕ MENU BAR
        # =====================================================

        self.menu_bar = menu_bar

        # =====================================================
        # ОСНОВЕН СТИЛ НА MP3_ORDER
        # =====================================================

        self.setStyleSheet(f"""
                    QWidget {{
                        background: {self.current_theme["window_bg"]};
                        color: {self.current_theme["main_text"]};
                        font-size: 14px;
                    }}


                    QPushButton {{

                        background: {self.current_theme["button_bg"]};
                        color: {self.current_theme["main_text"]};
                        border: 1px solid {self.current_theme["button_border"]};
                        padding: 8px;
                        border-radius: 8px;

                    }}

                    QPushButton:focus {{

                        border: 3px solid {self.current_theme["accent_light"]};
                        outline: none;

                    }}

                    QPushButton:hover {{

                        background: {self.current_theme["accent"]};

                    }}


                    QTableWidget {{

                        background: {self.current_theme["table_bg"]};
                        color: {self.current_theme["main_text"]};
                        gridline-color: {self.current_theme["table_grid"]};

                    }}

                    QTableWidget::item:selected {{

                        background: {self.current_theme["table_selected"]};
                        color: {self.current_theme["main_text"]};

                    }}

                    QTableWidget::item:selected:active {{

                        background: {self.current_theme["table_selected"]};
                        color: {self.current_theme["main_text"]};

                    }}


                    QHeaderView::section {{

                        background: {self.current_theme["header_bg"]};
                        color: {self.current_theme["main_text"]};
                        padding: 6px;

                    }}


                    QMenuBar::item:selected {{

                        background: {self.current_theme["accent"]};
                        color: {self.current_theme["main_text"]};
                        border-radius: 4px;

                    }}

                """)

        main_layout = QHBoxLayout(self)

        main_layout.setMenuBar(self.menu_bar)
        # ===== ЦЕНТРАЛНА ЛЕНТА ЗА ЗАРЕЖДАНЕ =====

        self.loading_overlay = QFrame(self)

        self.loading_overlay.setFixedSize(520, 150)

        self.loading_overlay.setStyleSheet("""
            QFrame {
                background: #202124;
                border: 2px solid #6878D8;
                border-radius: 16px;
            }

            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                background: transparent;
            }

            QProgressBar {
                background: #303134;
                border: 1px solid #666;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-size: 14px;
                font-weight: bold;
                min-height: 24px;
            }

            QProgressBar::chunk {
                background: #22C55E;
                border-radius: 7px;
            }
        """)

        loading_layout = QVBoxLayout(self.loading_overlay)

        loading_layout.setContentsMargins(25, 20, 25, 20)

        loading_layout.setSpacing(12)

        self.loading_label = QLabel(self.language_manager.get("loading_songs"))

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_progress = QProgressBar()

        self.loading_progress.setRange(0, 100)

        self.loading_progress.setValue(0)

        loading_layout.addWidget(self.loading_label)

        loading_layout.addWidget(self.loading_progress)

        self.loading_overlay.hide()

        self.loading_overlay.raise_()

        button_panel = QVBoxLayout()

        right_panel = QVBoxLayout()

        self.table = SongTableWidget()

        self.table.itemChanged.connect(self.save_edited_cell)

        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setCurrentCell(-1, -1)

        self.drop_label = QLabel(self.language_manager.get("drop_mp3"))

        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_label.setStyleSheet(f"""
            QLabel {{
                border: 3px dashed {self.current_theme["accent"]};
                border-radius: 12px;
                color: {self.current_theme["accent_light"]};
                font-size: 22px;
                font-weight: bold;
                background: {self.current_theme["panel_bg"]};
            }}
        """)

        self.drop_label.hide()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                self.language_manager.get("table_number"),
                self.language_manager.get("table_song"),
                self.language_manager.get("table_artist"),
                self.language_manager.get("table_time"),
            ]
        )

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)

        self.table.setDragEnabled(False)

        self.table.setAcceptDrops(True)

        self.table.setDropIndicatorShown(True)

        self.table.setDragDropOverwriteMode(False)

        header = self.table.horizontalHeader()

        header.setStyleSheet(f"""
            QHeaderView::section {{
                background: {self.current_theme["header_bg"]};
                color: {self.current_theme["main_text"]};
                border: 1px solid {self.current_theme["table_grid"]};
                font-size: 18px;
                font-weight: bold;
            }}
        """)

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.horizontalHeader().setStretchLastSection(False)

        self.table.verticalHeader().setVisible(False)

        self.table.setShowGrid(True)

        self.table.setGridStyle(Qt.PenStyle.SolidLine)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.current_theme["table_bg"]};
                color: {self.current_theme["main_text"]};
                gridline-color: {self.current_theme["table_grid"]};
                border: none;
                selection-background-color: {self.current_theme["table_selected"]};
                selection-color: {self.current_theme["main_text"]};
            }}

            QTableWidget::item:hover {{
                background: transparent;
                border: none;
            }}
        """)

        self.table.setRowCount(25)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

        self.table.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                width: 12px;
                background: {self.current_theme["table_bg"]};
                border: none;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {self.current_theme["accent_light"]};
                min-height: 40px;
                border-radius: 6px;
                border: none;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {self.current_theme["accent"]};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: transparent;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: {self.current_theme["window_bg"]};
            }}
        """)

        # ===== Търсачка =====

        search_layout = QHBoxLayout()

        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText(
            "🔍 " + self.language_manager.get("search_placeholder")
        )

        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                color: {self.current_theme["main_text"]};
                background: {self.current_theme["table_bg"]};
                border: 1px solid {self.current_theme["table_grid"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
                font-weight: bold;
            }}

            QLineEdit:focus {{
                border: 1px solid {self.current_theme["accent"]};
            }}
        """)

        self.search_button = QPushButton("🔍 " + self.language_manager.get("search"))

        self.search_button.setStyleSheet(f"""
            QPushButton {{
                color: {self.current_theme["main_text"]};
                background: {self.current_theme["button_bg"]};
                border: 1px solid {self.current_theme["button_border"]};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 18px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background: {self.current_theme["accent"]};
            }}

            QPushButton:pressed {{
                background: {self.current_theme["button_bg"]};
            }}
        """)

        self.search_button.clicked.connect(self.search_song)

        self.search_edit.returnPressed.connect(self.play_searched_song)

        self.search_edit.textChanged.connect(self.search_song)

        self.search_edit.installEventFilter(self)

        self.search_button.setMinimumWidth(100)

        search_layout.addWidget(self.search_edit)

        search_layout.addWidget(self.search_button)

        right_panel.addLayout(search_layout)

        # ===== ПАНЕЛ „СЕГА СВИРИ“ =====

        self.now_playing_frame = QFrame()

        self.now_playing_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.current_theme["panel_bg"]};
                border: 2px solid {self.current_theme["accent"]};
                border-radius: 10px;
            }}
        """)

        now_playing_layout = QVBoxLayout(self.now_playing_frame)

        now_playing_layout.setContentsMargins(16, 10, 16, 10)

        now_playing_layout.setSpacing(2)

        self.now_playing_title = QLabel(self.language_manager.get("now_playing"))

        self.now_playing_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 13px;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)

        self.now_playing_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.now_playing_label = QLabel(self.language_manager.get("no_song"))

        self.now_playing_label.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 18px;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)

        self.now_playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.now_playing_label.setWordWrap(True)

        now_playing_layout.addWidget(self.now_playing_title)

        now_playing_layout.addWidget(self.now_playing_label)

        right_panel.addWidget(self.now_playing_frame)

        # таблицата отива вдясно

        right_panel.addWidget(self.drop_label)

        right_panel.addWidget(self.table, 1)

        # ===== ПАНЕЛ ЗА УПРАВЛЕНИЕ =====

        player_panel = QFrame()
        self.player_panel = player_panel

        player_panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 {self.current_theme["panel_bg"]},
                    stop:0.5 {self.current_theme["panel_bg_2"]},
                    stop:1 {self.current_theme["panel_bg_3"]}
                );
                border: 2px solid {self.current_theme["accent"]};
                border-radius: 16px;
            }}

            QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 1px solid {self.current_theme["button_border"]};
                border-radius: 10px;
                padding: 9px 16px;
                font-size: 17px;
                font-weight: bold;
            }}

            /* ===== TOOLTIP ===== */

            QToolTip {{
                background: {self.current_theme["tooltip_bg"]};
                color: {self.current_theme["tooltip_text"]};
                border: 2px solid {self.current_theme["tooltip_border"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
                font-weight: bold;
            }}

            /* ⏮ Предишна */
            QPushButton#previousButton:hover {{
                background: {self.current_theme["previous"]};
                border: 2px solid {self.current_theme["previous_border"]};
            }}

            QPushButton#previousButton:pressed {{
                background: {self.current_theme["previous_pressed"]};
                border: 4px solid {self.current_theme["previous_border"]};
                padding-top: 13px;
                padding-bottom: 5px;
            }}

            /* ▶ Пускане */
            QPushButton#playButton:hover {{
                background: {self.current_theme["play"]};
                border: 2px solid {self.current_theme["play_border"]};
            }}

            QPushButton#playButton:pressed {{
                background: {self.current_theme["play_pressed"]};
                border: 4px solid {self.current_theme["play_border"]};
                padding-top: 13px;
                padding-bottom: 5px;
            }}

            /* ⏸ Пауза */
            QPushButton#pauseButton:hover {{
                background: {self.current_theme["pause"]};
                border: 2px solid {self.current_theme["pause_border"]};
            }}

            QPushButton#pauseButton:pressed {{
                background: {self.current_theme["pause_pressed"]};
                border: 4px solid {self.current_theme["pause_border"]};
                padding-top: 13px;
                padding-bottom: 5px;
            }}

            /* ⏹ Стоп */
            QPushButton#stopButton:hover {{
                background: {self.current_theme["stop"]};
                border: 2px solid {self.current_theme["stop_border"]};
            }}

            QPushButton#stopButton:pressed {{
                background: {self.current_theme["stop_pressed"]};
                border: 4px solid {self.current_theme["stop_border"]};
                padding-top: 13px;
                padding-bottom: 5px;
            }}

            /* ⏭ Следваща */
            QPushButton#nextButton:hover {{
                background: {self.current_theme["next"]};
                border: 2px solid {self.current_theme["next_border"]};
            }}

            QPushButton#nextButton:pressed {{
                background: {self.current_theme["next_pressed"]};
                border: 4px solid {self.current_theme["next_border"]};
                padding-top: 13px;
                padding-bottom: 5px;
            }}
        """)

        player_layout = QHBoxLayout(player_panel)

        player_layout.setContentsMargins(12, 8, 12, 8)

        player_layout.setSpacing(10)

        previous_button = QPushButton("⏮")
        previous_button.setObjectName("previousButton")
        previous_button.clicked.connect(self.previous_song)
        previous_button.setToolTip(self.language_manager.get("previous_song"))

        play_button = QPushButton("▶")
        play_button.setObjectName("playButton")
        play_button.clicked.connect(self.play_song)
        play_button.setToolTip(self.language_manager.get("play_song"))

        pause_button = QPushButton("⏸")
        pause_button.setObjectName("pauseButton")
        pause_button.clicked.connect(self.pause_song)
        pause_button.setToolTip(self.language_manager.get("pause_song"))

        stop_button = QPushButton("⏹")
        stop_button.setObjectName("stopButton")
        stop_button.clicked.connect(self.stop_song)
        stop_button.setToolTip(self.language_manager.get("stop_song"))

        next_button = QPushButton("⏭")
        next_button.setObjectName("nextButton")
        next_button.clicked.connect(self.next_song)
        next_button.setToolTip(self.language_manager.get("next_song"))

        player_layout.addStretch()

        player_layout.addWidget(previous_button)

        player_layout.addWidget(play_button)

        player_layout.addWidget(pause_button)

        player_layout.addWidget(stop_button)

        player_layout.addWidget(next_button)

        player_layout.addStretch()

        # ===== ПРОГРЕС ЛЕНТА =====

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_time_label.setMinimumWidth(50)

        self.current_time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)

        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)

        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #555;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -4px 0;
                background: #1E88E5;
                border-radius: 7px;
            }

            QSlider::sub-page:horizontal {
                background: #1E88E5;
                border-radius: 3px;
            }
        """)

        self.remaining_time_label = QLabel("-00:00")
        self.remaining_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remaining_time_label.setMinimumWidth(55)

        self.remaining_time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        # Влачене с мишката
        self.progress_slider.sliderPressed.connect(self.progress_slider_pressed)

        self.progress_slider.sliderMoved.connect(self.progress_slider_moved)

        self.progress_slider.sliderReleased.connect(self.progress_slider_released)

        progress_layout.addWidget(self.current_time_label)

        progress_layout.addWidget(self.progress_slider)

        progress_layout.addWidget(self.remaining_time_label)

        # ===== ПОДРЕЖДАНЕ ПОД ТАБЛИЦАТА =====

        right_panel.addLayout(progress_layout)

        # Центрираме панела за управление
        player_row = QHBoxLayout()

        player_row.addStretch()
        player_row.addWidget(player_panel)
        player_row.addStretch()

        right_panel.addLayout(player_row)

        # При стартиране прогресът и времето са скрити
        self.current_time_label.hide()
        self.progress_slider.hide()
        self.remaining_time_label.hide()

        # ===== ПАНЕЛ С БУТОНИ ОТЛЯВО =====

        control_panel = QVBoxLayout()
        control_panel.setSpacing(8)

        # Добавяне на песни

        add_files = QPushButton(self.language_manager.get("add_songs"))
        add_files.setObjectName("addFilesButton")
        add_files.clicked.connect(self.add_files)  # type: ignore
        add_files.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        add_folder = QPushButton(self.language_manager.get("add_folder"))
        add_folder.clicked.connect(self.add_folder)
        add_folder.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Подреждане

        up = QPushButton(self.language_manager.get("move_up"))
        up.clicked.connect(self.move_up)
        up.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        down = QPushButton(self.language_manager.get("move_down"))
        down.clicked.connect(self.move_down)
        down.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        remove = QPushButton(self.language_manager.get("remove"))

        remove_method = getattr(self, "remove", None)

        if callable(remove_method):

            remove.clicked.connect(remove_method)

        remove.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Nero

        check = QPushButton(self.language_manager.get("check_order"))
        check.clicked.connect(self.check_order)
        check.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        split = QPushButton(self.language_manager.get("automatic_split"))
        split.clicked.connect(self.auto_split)
        split.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        edit_tags = QPushButton(self.language_manager.get("edit_id3"))
        edit_tags.clicked.connect(self.edit_tags)
        edit_tags.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        export = QPushButton(self.language_manager.get("export_nero"))
        export.clicked.connect(self.export)
        export.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ===== ВЕРТИКАЛНО ПОДРЕЖДАНЕ =====

        control_panel.addWidget(add_files)

        control_panel.addSpacing(8)

        control_panel.addWidget(add_folder)

        control_panel.addSpacing(15)

        control_panel.addWidget(up)

        control_panel.addSpacing(8)

        control_panel.addWidget(down)

        control_panel.addSpacing(8)

        control_panel.addWidget(remove)

        control_panel.addSpacing(15)

        control_panel.addWidget(check)

        control_panel.addSpacing(8)

        control_panel.addWidget(split)

        control_panel.addSpacing(8)

        control_panel.addWidget(edit_tags)

        control_panel.addSpacing(8)

        control_panel.addWidget(export)

        # ===== SAVE STATUS =====

        self.save_status_label = QLabel(self.language_manager.get("changes_saved"))

        self.save_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.save_status_label.setStyleSheet("""
            QLabel {
                color: #22C55E;
                background: #202020;
                border: 2px solid #22C55E;
                border-radius: 8px;
                font-size: 19px;
                font-weight: bold;
                padding: 0px;
                margin-top: 15px;
            }
        """)

        self.save_status_label.hide()

        # Добавяме фиксирано място за надписа
        control_panel.addSpacing(30)

        self.save_status_container = QFrame()

        self.save_status_container.setFixedWidth(300)

        self.save_status_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.save_status_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Fixed,
        )

        self.save_status_container.setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )

        status_layout = QVBoxLayout(self.save_status_container)

        status_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        status_layout.addWidget(self.save_status_label)

        control_panel.addWidget(self.save_status_container)

        # Таймер за автоматично скриване
        self.save_status_timer = QTimer(self)
        self.save_status_timer.setSingleShot(True)

        self.save_status_timer.timeout.connect(self.save_status_label.hide)

        # добавяме панелите към главния прозорец

        button_panel.addLayout(control_panel)

        # ===== ЛОГО ДОЛУ ВЛЯВО =====

        self.bottom_logo = QLabel()

        logo_pixmap = QPixmap(LOGO_PATH)

        if not logo_pixmap.isNull():

            self.bottom_logo.setPixmap(
                logo_pixmap.scaled(
                    120,
                    120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self.bottom_logo.setFixedSize(140, 140)

        self.bottom_logo.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )

        self.bottom_logo.setStyleSheet("background: transparent; border: none;")

        # Натиска логото максимално надолу
        button_panel.addStretch(1)

        button_panel.addWidget(self.bottom_logo, 0, Qt.AlignmentFlag.AlignLeft)

        # Добавяме левия панел обратно към главния layout
        main_layout.addLayout(button_panel, 0)

        main_layout.addSpacing(20)

        main_layout.addLayout(right_panel, 1)

        main_layout.addStretch()

        app = QApplication.instance()

        if app is not None:
            app.installEventFilter(self)

        self.setTabOrder(add_files, add_folder)
        self.setTabOrder(add_folder, up)
        self.setTabOrder(up, down)
        self.setTabOrder(down, remove)
        self.setTabOrder(remove, check)
        self.setTabOrder(check, split)
        self.setTabOrder(split, edit_tags)
        self.setTabOrder(edit_tags, export)

        self.setFocus()

        # ===== AUTO SAVE TIMER =====

        self.autosave_timer = QTimer(self)

        self.autosave_elapsed = QElapsedTimer()

        self.autosave_timer.setTimerType(Qt.TimerType.PreciseTimer)

        self.autosave_timer.setSingleShot(False)

        self.autosave_timer.timeout.connect(self.auto_save_project)

        self.autosave_timer.stop()

        self.start_autosave_from_settings()

        # ===== СВЪРЗВАМЕ ДОСТЪПНОСТТА С ИНТЕРФЕЙСА =====

        self.accessibility_ui.setup()

        # =====================================================
        # ЗАРЕЖДАМЕ FADE НАСТРОЙКИТЕ ПРИ СТАРТИРАНЕ
        # =====================================================

        self.apply_fade_settings()

    def dragEnterEvent(self, event):

        if event.mimeData().hasUrls():

            self.drop_label.show()

            self.table.hide()

            event.acceptProposedAction()

        else:

            event.ignore()

    def dragLeaveEvent(self, event):

        self.drop_label.hide()

        self.table.show()

        event.accept()

    def dropEvent(self, event):

        # Скрива надписа и показва таблицата
        self.drop_label.hide()
        self.table.show()

        # =====================================================
        # СЪБИРАМЕ ВСИЧКИ MP3 ФАЙЛОВЕ ОТ DROP
        # =====================================================

        files_to_add = []

        for url in event.mimeData().urls():

            path = url.toLocalFile()

            # =================================================
            # MP3 ФАЙЛ
            # =================================================

            if os.path.isfile(path):

                if path.lower().endswith(".mp3"):

                    if path not in files_to_add:

                        files_to_add.append(path)

            # =================================================
            # ПАПКА
            # =================================================

            elif os.path.isdir(path):

                folder_mp3_files = [
                    os.path.join(path, file)
                    for file in os.listdir(path)
                    if file.lower().endswith(".mp3")
                ]

                for file in folder_mp3_files:

                    if file not in files_to_add:

                        files_to_add.append(file)

        # Няма MP3 файлове
        if not files_to_add:

            event.acceptProposedAction()
            return

        # =====================================================
        # ПОКАЗВАМЕ ЛЕНТАТА
        # =====================================================

        total_files = len(files_to_add)

        self.loading_progress.setRange(0, total_files)

        self.loading_progress.setValue(0)

        self.loading_label.setText(
            self.language_manager.get(
                "loading_song_progress",
                current=str(0),
                total=str(total_files),
            )
        )

        x = (self.width() - self.loading_overlay.width()) // 2

        y = (self.height() - self.loading_overlay.height()) // 2

        self.loading_overlay.move(x, y)

        self.loading_overlay.show()
        self.loading_overlay.raise_()

        QApplication.processEvents()

        # =====================================================
        # ЗАРЕЖДАНЕ НА MP3 ФАЙЛОВЕТЕ
        # =====================================================

        for index, path in enumerate(files_to_add, start=1):

            # =================================================
            # ДУБЛИРАНА ПЕСЕН
            # =================================================

            if path in songs:

                QApplication.beep()

                msg = QMessageBox(self)

                msg.setWindowTitle(self.language_manager.get("duplicate_title"))

                msg.setText(self.language_manager.get("song_already_loaded"))

                msg.setInformativeText(
                    self.language_manager.get("replace_song_question")
                )

                msg.setIcon(QMessageBox.Icon.Question)

                yes = msg.addButton(
                    self.language_manager.get("yes"), QMessageBox.ButtonRole.YesRole
                )

                no = msg.addButton(
                    self.language_manager.get("no"), QMessageBox.ButtonRole.NoRole
                )

                msg.setDefaultButton(no)

                no.setFocus()

                msg.exec()

                # Ако е „Не“
                if msg.clickedButton() == no:

                    self.loading_progress.setValue(index)

                    self.loading_label.setText(
                        self.language_manager.get(
                            "loading_song_progress",
                            current=str(index),
                            total=str(total_files),
                        )
                    )

                    QApplication.processEvents()

                    continue

                # Ако е „Да“
                songs.remove(path)

            # =================================================
            # ДОБАВЯМЕ ПЕСЕНТА
            # =================================================

            songs.append(path)

            # =================================================

            # ОБНОВЯВАМЕ ПРОГРЕСА
            # =================================================

            self.loading_progress.setValue(index)

            self.loading_label.setText(
                self.language_manager.get(
                    "loading_song_progress",
                    current=str(index),
                    total=str(total_files),
                )
            )

            QApplication.processEvents()

        # =====================================================
        # ОБНОВЯВАМЕ ТАБЛИЦАТА
        # =====================================================

        self.refresh()

        # Връщаме фокуса към таблицата
        if songs:

            current_row = self.table.currentRow()

            if current_row < 0 or current_row >= len(songs):

                current_row = 0

            self.table.selectRow(current_row)

            self.table.setCurrentCell(current_row, 1)

            self.table.setFocus(Qt.FocusReason.OtherFocusReason)

            # =====================================================
            # ПОКАЗВАМЕ 100%
            # =====================================================

            self.loading_progress.setValue(total_files)

            self.loading_label.setText(
                self.language_manager.get(
                    "loading_folder_complete",
                    total=str(total_files),
                )
            )

            QApplication.processEvents()

        # =====================================================
        # ОСТАВА ВИДИМА 1 СЕКУНДА
        # =====================================================

        QTimer.singleShot(1000, self.loading_overlay.hide)

        # Връща нормалния изглед
        self.drop_label.hide()
        self.table.show()

        event.acceptProposedAction()

    def pause_song(self):

        if self.vlc_player is None:
            return

        # Ако песента свири -> пауза
        if self.vlc_player.is_playing():

            self.vlc_player.pause()

            if hasattr(self, "now_playing_label"):

                if self.playing_path:

                    song_name = os.path.basename(self.playing_path)

                    self.now_playing_label.setText(
                        self.language_manager.get("paused") + "\n" + song_name
                    )

        else:

            # Ако е на пауза -> продължаваме
            self.vlc_player.play()

            if hasattr(self, "now_playing_label"):

                if self.playing_path:

                    song_name = os.path.basename(self.playing_path)

                    self.now_playing_label.setText(
                        self.language_manager.get("now_playing_status")
                        + "\n"
                        + song_name
                    )

    def stop_song(self):

        if self.vlc_player is not None:

            self.vlc_player.stop()

        if self.progress_timer.isActive():

            self.progress_timer.stop()

        self.progress_slider.setValue(0)

        # Скриваме прогреса след Stop
        self.progress_slider.hide()
        self.current_time_label.hide()
        self.remaining_time_label.hide()

        # ===== ОБНОВЯВАМЕ „СЕГА СВИРИ“ =====

        if hasattr(self, "now_playing_label"):

            if self.playing_path:

                song_name = os.path.basename(self.playing_path)

                self.now_playing_label.setText(
                    self.language_manager.get("stopped") + "\n" + song_name
                )

            else:

                self.now_playing_label.setText(self.language_manager.get("stopped"))

    # =========================================================
    # AUTO NEXT SONG
    # ПЛАВЕН ПРЕХОД ПРИ АВТОМАТИЧНА СМЯНА
    # =========================================================

    def auto_next_song(self):

        if not songs:
            return

        if self.playing_index < 0:
            return

        next_index = self.playing_index + 1

        if next_index >= len(songs):
            return

        file_path = songs[next_index]

        if not os.path.isfile(file_path):
            return

        # =====================================================
        # RUNTIME НАСТРОЙКИ ЗА FADE
        # =====================================================

        fade_enabled = getattr(self, "fade_enabled_runtime", False)

        fade_duration = getattr(self, "fade_duration_runtime", 3)

        try:

            fade_duration = int(fade_duration)

        except (TypeError, ValueError):

            fade_duration = 3

        fade_duration = max(1, min(30, fade_duration))
        # =========================================================
        # DEBUG - FADE НАСТРОЙКИ
        # =========================================================

        # =====================================================
        # FADE Е ИЗКЛЮЧЕН
        # =====================================================

        if not fade_enabled:

            next_button = self.findChild(QPushButton, "nextButton")

            if next_button is not None:

                next_button.setDown(True)

                QTimer.singleShot(400, lambda: next_button.setDown(False))

            self.playing_index = next_index
            self.playing_path = file_path

            try:

                assert self.vlc_instance is not None

                media = self.vlc_instance.media_new(file_path)

                self.vlc_player.set_media(media)

                self.highlight_playing_song()

                self.current_time_label.show()
                self.progress_slider.show()
                self.remaining_time_label.show()

                self.vlc_player.audio_set_volume(100)

                self.vlc_player.play()

                self.progress_timer.start()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    self.language_manager.get("play_error_title"),
                    self.language_manager.get("play_error") + f"\n\n{e}",
                )

            return

        # =====================================================
        # СПИРАМЕ СТАРИТЕ FADE ТАЙМЕРИ
        # =====================================================

        if hasattr(self, "_fade_timer"):

            if self._fade_timer is not None:

                self._fade_timer.stop()
                self._fade_timer.deleteLater()

            self._fade_timer = None

        if hasattr(self, "_fade_in_timer"):

            if self._fade_in_timer is not None:

                self._fade_in_timer.stop()
                self._fade_in_timer.deleteLater()

            self._fade_in_timer = None

        # =====================================================
        # СТАРТИРАМЕ FADE-OUT
        # =====================================================

        self._fade_volume = 100

        self._fade_timer = QTimer(self)

        self._fade_timer.setInterval(50)

        steps = max(1, int((fade_duration * 1000) / 50))

        volume_step = 100 / steps

        self._fade_timer.timeout.connect(
            lambda: self._fade_out_and_start_next(
                file_path, next_index, volume_step, fade_duration
            )
        )

        self._fade_timer.start()

    # =========================================================
    # FADE-OUT → СЛЕДВАЩА ПЕСЕН → FADE-IN
    # =========================================================

    def _fade_out_and_start_next(
        self, file_path, next_index, volume_step, fade_duration
    ):

        if self.vlc_player is None:
            return

        # =====================================================
        # FADE-OUT НА ТЕКУЩАТА ПЕСЕН
        # =====================================================

        self._fade_volume -= volume_step

        new_volume = max(0, int(self._fade_volume))

        self.vlc_player.audio_set_volume(new_volume)

        if self._fade_volume > 13:
            return

        # =====================================================
        # СТАРАТА ПЕСЕН Е НА 0%
        # =====================================================

        self._fade_volume = 0

        self.vlc_player.audio_set_volume(0)

        # =====================================================
        # СПИРАМЕ FADE-OUT TIMER
        # =====================================================

        if self._fade_timer is not None:

            self._fade_timer.stop()
            self._fade_timer.deleteLater()

            self._fade_timer = None

        # =====================================================
        # ПУСКАМЕ СЛЕДВАЩАТА ПЕСЕН
        # =====================================================

        next_button = self.findChild(QPushButton, "nextButton")

        if next_button is not None:

            def press_next_button():

                next_button.setDown(True)

                next_button.setStyleSheet("""
                    QPushButton {
                        background: #B66A00;
                        color: white;
                        border: 4px solid #FFE0A3;
                        border-radius: 10px;
                        padding-top: 13px;
                        padding-bottom: 5px;
                        font-size: 17px;
                        font-weight: bold;
                    }
                """)

                next_button.repaint()

                QTimer.singleShot(
                    400,
                    lambda: (next_button.setDown(False), next_button.setStyleSheet("")),
                )

            QTimer.singleShot(0, press_next_button)

        self.playing_index = next_index
        self.playing_path = file_path

        try:

            assert self.vlc_instance is not None

            media = self.vlc_instance.media_new(file_path)

            self.vlc_player.set_media(media)

            self.highlight_playing_song()

            self.current_time_label.show()
            self.progress_slider.show()
            self.remaining_time_label.show()

            # =================================================
            # НУЛИРАМЕ ПРОГРЕСА ВЕДНАГА
            # =================================================

            self.progress_timer.stop()

            self.progress_slider.blockSignals(True)

            self.progress_slider.setValue(0)

            self.progress_slider.blockSignals(False)

            self.current_time_label.setText("00:00")

            self.remaining_time_label.setText("-00:00")

            # =================================================
            # НОВАТА ПЕСЕН ЗАПОЧВА ОТ 0% ЗВУК
            # =================================================

            self.vlc_player.audio_set_volume(0)

            self.vlc_player.play()

            self.progress_timer.start()

            # =================================================
            # FADE-IN НА НОВАТА ПЕСЕН
            # =================================================

            steps = max(1, int((fade_duration * 1000) / 50))

            fade_in_step = 100 / steps

            self._fade_volume = 0

            # =================================================
            # СПИРАМЕ СТАР FADE-IN TIMER
            # =================================================

            if self._fade_in_timer is not None:

                self._fade_in_timer.stop()
                self._fade_in_timer.deleteLater()

                self._fade_in_timer = None

            # =================================================
            # СЪЗДАВАМЕ НОВ FADE-IN TIMER
            # =================================================

            self._fade_in_timer = QTimer(self)

            self._fade_in_timer.setInterval(50)

            def fade_in():

                if self.vlc_player is None:
                    return

                self._fade_volume += fade_in_step

                new_volume = min(100, int(self._fade_volume))

                self.vlc_player.audio_set_volume(new_volume)

                # =============================================
                # FADE-IN Е ЗАВЪРШИЛ
                # =============================================

                if self._fade_volume >= 100:

                    self._fade_volume = 100

                    self.vlc_player.audio_set_volume(100)

                    fade_in_timer = self._fade_in_timer

                    if fade_in_timer is not None:

                        fade_in_timer.stop()
                        fade_in_timer.deleteLater()

                    self._fade_in_timer = None

            self._fade_in_timer.timeout.connect(fade_in)

            self._fade_in_timer.start()

        except Exception as e:

            QMessageBox.critical(
                self,
                self.language_manager.get("play_error_title"),
                self.language_manager.get("play_error") + f"\n\n{e}",
            )

    def next_song(self):

        if not songs:
            return

        current_row = self.table.currentRow()

        if current_row < 0:
            current_row = 0
        else:
            current_row += 1

        if current_row >= len(songs):
            current_row = 0

        self.table.selectRow(current_row)
        self.table.setCurrentCell(current_row, 1)
        self.table.setFocus()

        next_button = self.findChild(QPushButton, "nextButton")

        if next_button is not None:

            next_button.setDown(True)

            QTimer.singleShot(400, lambda: next_button.setDown(False))

        self.play_song()

    def previous_song(self):

        if not songs:
            return

        current_row = self.table.currentRow()

        if current_row <= 0:
            current_row = len(songs) - 1
        else:
            current_row -= 1

        self.table.selectRow(current_row)
        self.table.setCurrentCell(current_row, 1)
        self.table.setFocus()

        previous_button = self.findChild(QPushButton, "previousButton")

        if previous_button is not None:

            def press_previous_button():

                previous_button.setDown(True)

                previous_button.setStyleSheet("""
                    QPushButton {
                        background: #44227A;
                        color: white;
                        border: 4px solid #F0E7FF;
                        border-radius: 10px;
                        padding-top: 13px;
                        padding-bottom: 5px;
                        font-size: 17px;
                        font-weight: bold;
                    }
                """)

                previous_button.repaint()

                QTimer.singleShot(
                    400,
                    lambda: (
                        previous_button.setDown(False),
                        previous_button.setStyleSheet(""),
                    ),
                )

            QTimer.singleShot(0, press_previous_button)

        self.play_song()

    def progress_slider_pressed(self):

        # Запомняме дали песента е свирила
        self._was_playing_before_seek = self.vlc_player.is_playing()

        # Спираме само обновяването на визуалната лента.
        # Самата песен ПРОДЪЛЖАВА да свири.
        if self.progress_timer.isActive():

            self.progress_timer.stop()

    def progress_slider_moved(self, value):

        # Докато влачим с мишката,
        # местим само визуалната точка.
        # VLC не се мести постоянно.
        self.progress_slider.setValue(value)

    def progress_slider_released(self):

        if self.vlc_player is None:
            return

        total_time = self.vlc_player.get_length()

        if total_time <= 0:
            return

        # Взимаме точно позицията, на която сме пуснали мишката.
        value = self.progress_slider.value()

        new_time = int((value / 1000.0) * total_time)

        # Едно единствено преместване на VLC
        # след отпускане на мишката.
        self.vlc_player.set_time(new_time)

        # Ако песента е свирила преди влаченето,
        # продължава от новата позиция.
        if getattr(self, "_was_playing_before_seek", False):

            self.vlc_player.play()

        # Връщаме автоматичното движение на лентата.
        if self.vlc_player.is_playing():

            self.progress_timer.start()

    # =========================================================
    # UPDATE PROGRESS
    # ПРОГРЕС НА ПЕСЕНТА + АВТОМАТИЧЕН FADE
    # =========================================================

    def update_progress(self):

        if self.vlc_player is None:
            return

        position = self.vlc_player.get_position()

        if position < 0:
            return

        total_time = self.vlc_player.get_length()
        current_time = self.vlc_player.get_time()

        # =====================================================
        # FADE НАСТРОЙКИ
        # =====================================================

        fade_enabled = getattr(self, "fade_enabled_runtime", False)

        fade_duration = getattr(self, "fade_duration_runtime", 3)

        try:

            fade_duration = int(fade_duration)

        except (
            TypeError,
            ValueError,
        ):

            fade_duration = 3

        fade_duration = max(1, min(30, fade_duration))

        # =====================================================
        # ПРОВЕРЯВАМЕ ДАЛИ ИМА СЛЕДВАЩА ПЕСЕН
        # =====================================================

        has_next_song = 0 <= self.playing_index < len(songs) - 1

        # =====================================================
        # СТАРТИРАМЕ FADE ПРЕДИ КРАЯ
        # =====================================================

        if (
            fade_enabled
            and has_next_song
            and total_time > 0
            and current_time >= 0
            and getattr(self, "_fade_timer", None) is None
        ):

            remaining_ms = total_time - current_time

            fade_start_ms = fade_duration * 1000

            if remaining_ms <= fade_start_ms:

                print(
                    "FADE START:",
                    "remaining =",
                    round(remaining_ms / 1000, 2),
                    "sec",
                    "| fade =",
                    fade_duration,
                    "sec",
                )

                self.auto_next_song()

                return

        # =====================================================
        # ПЕСЕНТА Е СТИГНАЛА КРАЯ
        # =====================================================

        song_ended = total_time > 0 and current_time >= total_time - 500

        if song_ended:

            self.progress_timer.stop()

            # =================================================
            # СПИСЪКЪТ Е ПРАЗЕН
            # =================================================

            if not songs:

                self.progress_slider.setValue(0)

                self.current_time_label.setText("00:00")

                self.remaining_time_label.setText("-00:00")

                self.progress_slider.hide()
                self.current_time_label.hide()
                self.remaining_time_label.hide()

                # =================================================
                # ПАЗИМ ИНФОРМАЦИЯТА ЗА ПОСЛЕДНАТА ПЕСЕН
                # =================================================

                self.now_playing_label.setText(
                    self.language_manager.get("no_playlist_loaded")
                )

                return

            # =================================================
            # НОВИ ПЕСНИ СА ДОБАВЕНИ,
            # ДОКАТО СТАРАТА Е СВИРИЛА
            # =================================================

            if self.playing_path is not None and self.playing_path not in songs:

                self.table.clearSelection()

                self.table.selectRow(0)

                self.table.setCurrentCell(0, 1)

                self.table.setFocus()

                self.play_song()

                return

            # =================================================
            # ИМА ОЩЕ ПЕСНИ
            # =================================================

            current_row = self.playing_index

            if 0 <= current_row < len(songs) - 1:

                # Ако Fade вече върви,
                # не го стартираме втори път.

                if getattr(self, "_fade_timer", None) is None:

                    self.auto_next_song()

                return

            # =================================================
            # ПОСЛЕДНА ПЕСЕН В СПИСЪКА
            # =================================================

            from PySide6.QtCore import QSettings

            settings = QSettings("MP3_Order", "MP3_Order_PRO")

            end_behavior_raw = settings.value("end_behavior", "0")

            try:
                end_behavior = int(str(end_behavior_raw))
            except (TypeError, ValueError):
                end_behavior = 0

            # =================================================
            # СПИРА ВЪЗПРОИЗВЕЖДАНЕТО
            # =================================================

            if end_behavior == 0:

                self.progress_slider.setValue(0)
                self.current_time_label.setText("00:00")
                self.remaining_time_label.setText("-00:00")

                self.progress_slider.hide()
                self.current_time_label.hide()
                self.remaining_time_label.hide()

                self.playing_index = -1
                self.playing_path = None

                self.now_playing_label.setText(
                    self.language_manager.get("no_playlist_loaded")
                )

                return

            # =================================================
            # ПОВТАРЯ СПИСЪКА
            # =================================================

            if end_behavior == 1:

                if not songs:
                    return

                first_song = songs[0]

                if not os.path.isfile(first_song):
                    return

                self.table.clearSelection()
                self.table.selectRow(0)
                self.table.setCurrentCell(0, 1)
                self.table.setFocus()

                self.playing_index = 0
                self.playing_path = first_song

                try:
                    assert self.vlc_instance is not None

                    media = self.vlc_instance.media_new(first_song)
                    self.vlc_player.set_media(media)

                    self.highlight_playing_song()

                    self.current_time_label.show()
                    self.progress_slider.show()
                    self.remaining_time_label.show()

                    self.vlc_player.audio_set_volume(100)
                    self.vlc_player.play()

                    self.progress_timer.start()

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        self.language_manager.get("play_error_title"),
                        self.language_manager.get("play_error") + f"\n\n{e}",
                    )

                return

        # =====================================================
        # ПОКАЗВАМЕ ТЕКУЩОТО И ОСТАВАЩОТО ВРЕМЕ
        # =====================================================

        if total_time > 0:

            current_ms = max(0, current_time)

            remaining_ms = max(0, total_time - current_ms)

            current_seconds = current_ms // 1000

            remaining_seconds = remaining_ms // 1000

            current_minutes = current_seconds // 60

            current_seconds %= 60

            remaining_minutes = remaining_seconds // 60

            remaining_seconds %= 60

            self.current_time_label.setText(
                f"{current_minutes:02d}:" f"{current_seconds:02d}"
            )

            self.remaining_time_label.setText(
                f"-{remaining_minutes:02d}:" f"{remaining_seconds:02d}"
            )

        # =====================================================
        # АКО ПЕСЕНТА Е СПРЯНА
        # =====================================================

        if not self.vlc_player.is_playing():

            return

        # =====================================================
        # ОБНОВЯВАМЕ ПРОГРЕС ЛЕНТАТА
        # =====================================================

        value = int(position * 1000)

        self.progress_slider.blockSignals(True)

        self.progress_slider.setValue(value)

        self.progress_slider.blockSignals(False)

    def highlight_playing_song(self):

        # ===== ОЦВЕТЯВАНЕ НА СВИРЕЩАТА ПЕСЕН =====

        for row in range(self.table.rowCount()):

            for column in range(self.table.columnCount()):

                item = self.table.item(row, column)

                if item is not None:

                    item.setBackground(self.table.palette().base())

        # Няма запомнена свиреща песен
        if not self.playing_path:

            return

        # Търсим песента по точния файл
        for row, path in enumerate(songs):

            if path == self.playing_path:

                self.playing_index = row

                for column in range(self.table.columnCount()):

                    item = self.table.item(row, column)

                    if item is not None:

                        item.setBackground(QColor("#244B3A"))

                return

    def refresh(self):

        self.table.blockSignals(True)

        scroll = self.table.verticalScrollBar().value()

        self.table.setRowCount(0)

        for i, path in enumerate(songs):

            title, artist, duration = song_info(path)

            row = self.table.rowCount()

            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))

            title_item = QTableWidgetItem(title)
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            artist_item = QTableWidgetItem(artist)
            artist_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            title_item.setData(Qt.ItemDataRole.UserRole, path)

            self.table.setItem(row, 1, title_item)
            self.table.setItem(row, 2, artist_item)
            self.table.setItem(row, 3, QTableWidgetItem(duration))

        # Няма песни -> запазваме празната таблица
        if not songs:

            self.table.setRowCount(50)

            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            self.table.verticalScrollBar().setEnabled(False)

            self.table.verticalScrollBar().setValue(0)

        else:

            # Запазваме празните редове до 50 песни
            self.table.setRowCount(max(50, len(songs)))

            # Scrollbar се показва чак при повече от 50 песни
            if len(songs) > 50:

                self.table.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAsNeeded
                )

                self.table.verticalScrollBar().setEnabled(True)

            else:

                self.table.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )

                self.table.verticalScrollBar().setEnabled(False)

                self.table.verticalScrollBar().setValue(0)

                self.table.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )

        self.table.verticalScrollBar().setValue(scroll)

        self.table.blockSignals(False)

        # Ако няма песни – няма активна клетка
        if not songs:

            self.table.clearSelection()

            self.table.setCurrentCell(-1, -1)

            self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

            self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        else:

            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

            self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Празна таблица = без сиви маркери
        if not songs:

            self.table.clearSelection()

            self.table.setCurrentIndex(QModelIndex())

            self.table.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, False)

        else:

            self.table.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # ===== СТИЛ НА ТАБЛИЦАТА =====

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.current_theme["table_bg"]};
                color: {self.current_theme["main_text"]};
                gridline-color: {self.current_theme["table_grid"]};
                border: none;
                selection-background-color: {self.current_theme["table_selected"]};
                selection-color: {self.current_theme["main_text"]};
            }}

            QTableWidget::item:hover {{
                background: transparent;
                border: none;
            }}

            QTableWidget::item:selected {{
                background: {self.current_theme["table_selected"]};
                color: {self.current_theme["main_text"]};
            }}

            QTableWidget::item:selected:hover {{
                background: {self.current_theme["table_selected"]};
                color: {self.current_theme["main_text"]};
            }}
        """)

    # =========================================================
    # PLAY SONG
    # ПУСКАНЕ НА ПЕСЕНТА
    # =========================================================

    def play_song(self):

        if not songs:
            return

        current_row = self.table.currentRow()

        if current_row < 0 or current_row >= len(songs):

            current_row = 0

        file_path = songs[current_row]

        self.playing_index = current_row
        self.playing_path = file_path

        # =====================================================
        # ОБНОВЯВАМЕ „СЕГА СВИРИ“
        # =====================================================

        if hasattr(self, "now_playing_label"):

            song_name = os.path.basename(file_path)

            self.now_playing_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    background: transparent;
                    border: none;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)

            self.now_playing_label.setText(song_name)

        # =====================================================
        # ОБНОВЯВАМЕ ЗЕЛЕНИЯ МАРКЕР
        # =====================================================

        self.highlight_playing_song()

        if not os.path.isfile(file_path):

            QMessageBox.warning(
                self,
                self.language_manager.get("error"),
                self.language_manager.get("song_file_missing"),
            )

            return

        # =====================================================
        # СПИРАМЕ ПРЕДИШЕН FADE-IN
        # =====================================================

        if hasattr(self, "_fade_in_timer"):

            fade_in_timer = self._fade_in_timer

            if fade_in_timer is not None:

                fade_in_timer.stop()
                fade_in_timer.deleteLater()

            self._fade_in_timer = None

        try:

            assert self.vlc_instance is not None

            media = self.vlc_instance.media_new(file_path)

            self.vlc_player.set_media(media)

            # =================================================
            # ПОКАЗВАМЕ ПРОГРЕСА
            # =================================================

            self.current_time_label.show()
            self.progress_slider.show()
            self.remaining_time_label.show()

            # =================================================
            # ПРОВЕРЯВАМЕ FADE НАСТРОЙКИТЕ
            # =================================================

            fade_enabled = getattr(self, "fade_enabled_runtime", False)

            fade_duration = getattr(self, "fade_duration_runtime", 3)

            try:

                fade_duration = int(fade_duration)

            except (
                TypeError,
                ValueError,
            ):

                fade_duration = 3

            fade_duration = max(1, min(30, fade_duration))

            # =================================================
            # ПЛУВЕН ПРЕХОД Е ИЗКЛЮЧЕН
            # ПУСКАМЕ НОРМАЛНО НА 100%
            # =================================================

            if not fade_enabled:

                self.vlc_player.audio_set_volume(100)

                self.vlc_player.play()

                self.progress_timer.start()

                return

            # =================================================
            # FADE-IN НА НОВОПУСНАТАТА ПЕСЕН
            # ЗАПОЧВАМЕ ОТ 0%
            # =================================================

            self.vlc_player.audio_set_volume(0)

            self.vlc_player.play()

            self.progress_timer.start()

            # =================================================
            # ИЗЧИСЛЯВАМЕ СТЪПКАТА НА УВЕЛИЧАВАНЕ
            # =================================================

            steps = max(1, int((fade_duration * 1000) / 50))

            fade_in_step = 100 / steps

            self._fade_volume = 0

            # =================================================
            # FADE-IN ТАЙМЕР
            # =================================================

            self._fade_in_timer = QTimer(self)

            self._fade_in_timer.setInterval(50)

            def fade_in():

                if self.vlc_player is None:

                    return

                self._fade_volume += fade_in_step

                new_volume = min(100, int(self._fade_volume))

                self.vlc_player.audio_set_volume(new_volume)

                # =============================================
                # FADE-IN Е ЗАВЪРШИЛ
                # =============================================

                if self._fade_volume >= 100:

                    self._fade_volume = 100

                    self.vlc_player.audio_set_volume(100)

                    # =========================================
                    # СПИРАМЕ FADE-IN ТАЙМЕРА
                    # =========================================

                    fade_in_timer = self._fade_in_timer

                    if fade_in_timer is not None:

                        fade_in_timer.stop()
                        fade_in_timer.deleteLater()

                    self._fade_in_timer = None

            self._fade_in_timer.timeout.connect(fade_in)

            self._fade_in_timer.start()

        except Exception as e:

            QMessageBox.critical(
                self,
                self.language_manager.get("play_error_title"),
                self.language_manager.get("play_error") + f"\n\n{e}",
            )
            # =========================================================================
            #        Край на блока:
            # ------------------------------------------------------------

    def open_list(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.language_manager.get("open_list"),
            "",
            self.language_manager.get("mp3_list_filter"),
        )

        if not file_path:
            return

        file_name = os.path.basename(file_path)

        # ===== ЦЕНТРИРАМЕ ПАНЕЛА =====

        x = (self.width() - self.loading_overlay.width()) // 2
        y = (self.height() - self.loading_overlay.height()) // 2

        self.loading_overlay.move(x, y)

        # ===== ПОКАЗВАМЕ ПРОГРЕСА =====

        self.loading_label.setText(
            self.language_manager.get("loading_project", file_name=file_name)
        )

        self.loading_progress.setRange(0, 100)

        self.loading_progress.setValue(0)

        self.loading_overlay.show()

        self.loading_overlay.raise_()

        QApplication.processEvents()

        # Запомняме кой списък е отворен
        self._current_list_file = file_path

        try:

            with open(file_path, "r", encoding="utf-8") as file:

                loaded_lines = [line.strip() for line in file if line.strip()]

            self.loading_progress.setValue(25)

            QApplication.processEvents()

            # ===== ТЪРСИМ ЗАПАЗЕНАТА F3 ПЕСЕН =====

            saved_f3_path = None

            loaded_songs = []

            for line in loaded_lines:

                if line.startswith("#F3_LAST_PATH="):

                    saved_f3_path = line[len("#F3_LAST_PATH=") :]

                else:

                    loaded_songs.append(line)

            self.loading_progress.setValue(50)

            QApplication.processEvents()

            # ===== ПРОВЕРЯВАМЕ MP3 ФАЙЛОВЕТЕ =====

            valid_songs = [
                path
                for path in loaded_songs
                if (os.path.isfile(path) and path.lower().endswith(".mp3"))
            ]

            self.loading_progress.setValue(75)

            QApplication.processEvents()

            if not valid_songs:

                self.loading_overlay.hide()

                QMessageBox.warning(
                    self,
                    self.language_manager.get("no_songs_title"),
                    self.language_manager.get("invalid_mp3_list"),
                )

                return

            # ===== ЗАПАЗВАМЕ СТАРОТО СЪСТОЯНИЕ ЗА CTRL + Z =====

            self.push_undo()

            songs.clear()

            songs.extend(valid_songs)

            self.search_edit.clear()

            self.table.clearSelection()

            self.table.setCurrentCell(-1, -1)

            # ===== ВЪЗСТАНОВЯВАМЕ F3 ПОЗИЦИЯТА =====

            if saved_f3_path is not None and saved_f3_path in songs:

                self.f3_last_path = saved_f3_path

            else:

                self.f3_last_path = None

            # ===== ОБНОВЯВАМЕ ТАБЛИЦАТА =====

            self.refresh()

            # ===== ЗАВЪРШЕНО =====

            self.loading_progress.setValue(100)

            self.loading_label.setText(
                self.language_manager.get(
                    "loading_list_complete",
                    file_name=file_name,
                )
            )

            QApplication.processEvents()

            # ===== ОСТАВА ВИДИМО 2 СЕКУНДИ =====

            QTimer.singleShot(2000, self.loading_overlay.hide)

        except Exception as e:

            self.loading_overlay.hide()

            QMessageBox.critical(
                self,
                self.language_manager.get("error"),
                self.language_manager.get("open_list_error") + f"\n\n{e}",
            )

    def save_list(self, show_message=True):

        if not songs:

            QMessageBox.information(
                self,
                self.language_manager.get("no_songs_title"),
                self.language_manager.get("no_songs_to_save"),
            )

            return

        file_path = getattr(self, "_current_list_file", None)

        # Ако няма избран файл,
        # използваме „Запази списък като...“
        if not file_path:

            self.save_list_as()

            return

        # ===== ЗАПАЗВАМЕ ТЕКУЩО ИЗБРАНАТА ПЕСЕН ЗА F3 =====

        current_row = self.table.currentRow()

        if 0 <= current_row < len(songs):

            self.f3_last_path = songs[current_row]

        try:

            with open(file_path, "w", encoding="utf-8") as file:

                # Записваме песните
                for path in songs:

                    file.write(path + "\n")

                # Записваме последната F3 позиция
                if self.f3_last_path is not None:

                    file.write("#F3_LAST_PATH=" + self.f3_last_path + "\n")

            QApplication.beep()

            # При нормално „Запази списък“
            # прозорецът си остава както досега.
            if show_message:

                QMessageBox.information(
                    self,
                    self.language_manager.get("save_success_title"),
                    self.language_manager.get("save_success"),
                )

            # При Ctrl+S показваме само надписа вляво.
            else:

                self.save_status_label.setVisible(True)

                self.save_status_timer.stop()

                self.save_status_timer.start(5000)

        except Exception as e:

            QMessageBox.critical(
                self,
                self.language_manager.get("error"),
                self.language_manager.get("save_error") + f"\n\n{e}",
            )

    def open_settings(self):

        from settings import SettingsDialog

        dialog = SettingsDialog(self)

        dialog.settings_changed.connect(self.apply_autosave_settings)

        dialog.settings_changed.connect(self.apply_fade_settings)

        dialog.settings_changed.connect(self.apply_theme_settings)

        # =====================================================
        # НАСТРОЙКИТЕ БЛОКИРАТ ОСНОВНИЯ ПРОЗОРЕЦ
        # =====================================================

        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.settings_dialog = dialog

        # =====================================================
        # ОБНОВЯВАНЕ НА ЕЗИКА СЛЕД ЗАТВАРЯНЕ НА НАСТРОЙКИТЕ
        # =====================================================

        def update_language():

            self.search_edit.setPlaceholderText(
                "🔍 " + self.language_manager.get("search_placeholder")
            )

            self.search_button.setText("🔍 " + self.language_manager.get("search"))

            self._file_menu_selected = False

        dialog.finished.connect(update_language)

        dialog.show()

        # Запазваме препратка към прозореца с настройки
        self.settings_dialog = dialog

    # =========================================================
    # ЗАРЕЖДАНЕ НА НАСТРОЙКИТЕ ЗА ПЛАВЕН ПРЕХОД
    # =========================================================

    def apply_fade_settings(self):

        from PySide6.QtCore import QSettings

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        # ===== ПЛАВЕН ПРЕХОД ВКЛЮЧЕН / ИЗКЛЮЧЕН =====

        fade_enabled_raw = settings.value("fade_enabled", False)

        if isinstance(fade_enabled_raw, bool):

            fade_enabled = fade_enabled_raw

        else:

            fade_enabled = str(fade_enabled_raw).strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        # ===== ПРОДЪЛЖИТЕЛНОСТ НА FADE =====

        fade_duration_raw = settings.value("fade_duration", "3")

        try:

            fade_duration = int(str(fade_duration_raw).strip())

        except (
            TypeError,
            ValueError,
        ):

            fade_duration = 3

        fade_duration = max(1, min(30, fade_duration))

        # ===== ЗАПАЗВАМЕ АКТИВНИТЕ СТОЙНОСТИ В MP3_ORDER =====

        self.fade_enabled_runtime = fade_enabled

        self.fade_duration_runtime = fade_duration

    # =====================================================
    # ОБНОВЯВАНЕ НА ЦВЕТОВАТА ТЕМА ВЕЧЕ ОТВОРЕН ПРОЗОРЕЦ
    # =====================================================

    def refresh_theme_styles(self):

        self.setStyleSheet(f"""
            QWidget {{
                background: {self.current_theme["window_bg"]};
                color: {self.current_theme["main_text"]};
                font-size: 14px;
            }}

            QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 1px solid {self.current_theme["button_border"]};
                padding: 8px;
                border-radius: 8px;
            }}

            QPushButton:focus {{
                border: 3px solid {self.current_theme["accent_light"]};
                outline: none;
            }}

            QPushButton:hover {{
                background: {self.current_theme["accent"]};
            }}

            QTableWidget {{
                background: {self.current_theme["table_bg"]};
                color: {self.current_theme["main_text"]};
                gridline-color: {self.current_theme["table_grid"]};
            }}

            QTableWidget::item:selected {{
                background: {self.current_theme["table_selected"]};
                color: {self.current_theme["main_text"]};
            }}

            QTableWidget::item:selected:active {{
                background: {self.current_theme["table_selected"]};
                color: {self.current_theme["main_text"]};
            }}

            QHeaderView::section {{
                background: {self.current_theme["header_bg"]};
                color: {self.current_theme["main_text"]};
                padding: 6px;
            }}

            QMenuBar::item:selected {{
                background: {self.current_theme["accent"]};
                color: {self.current_theme["main_text"]};
                border-radius: 4px;
            }}
        """)

        if hasattr(self, "player_panel"):

            self.player_panel.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(
                        x1:0, y1:0,
                        x2:1, y2:0,
                        stop:0 {self.current_theme["panel_bg"]},
                        stop:0.5 {self.current_theme["panel_bg_2"]},
                        stop:1 {self.current_theme["panel_bg_3"]}
                    );
                    border: 2px solid {self.current_theme["accent"]};
                    border-radius: 16px;
                }}

                QPushButton {{
                    background: {self.current_theme["button_bg"]};
                    color: {self.current_theme["main_text"]};
                    border: 1px solid {self.current_theme["button_border"]};
                    border-radius: 10px;
                    padding: 9px 16px;
                    font-size: 17px;
                    font-weight: bold;
                }}

                QToolTip {{
                    background: {self.current_theme["tooltip_bg"]};
                    color: {self.current_theme["tooltip_text"]};
                    border: 2px solid {self.current_theme["tooltip_border"]};
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 18px;
                    font-weight: bold;
                }}

                QPushButton#previousButton:hover {{
                    background: {self.current_theme["previous"]};
                    border: 2px solid {self.current_theme["previous_border"]};
                }}

                QPushButton#previousButton:pressed {{
                    background: {self.current_theme["previous_pressed"]};
                    border: 4px solid {self.current_theme["previous_border"]};
                    padding-top: 13px;
                    padding-bottom: 5px;
                }}

                QPushButton#playButton:hover {{
                    background: {self.current_theme["play"]};
                    border: 2px solid {self.current_theme["play_border"]};
                }}

                QPushButton#playButton:pressed {{
                    background: {self.current_theme["play_pressed"]};
                    border: 4px solid {self.current_theme["play_border"]};
                    padding-top: 13px;
                    padding-bottom: 5px;
                }}

                QPushButton#pauseButton:hover {{
                    background: {self.current_theme["pause"]};
                    border: 2px solid {self.current_theme["pause_border"]};
                }}

                QPushButton#pauseButton:pressed {{
                    background: {self.current_theme["pause_pressed"]};
                    border: 4px solid {self.current_theme["pause_border"]};
                    padding-top: 13px;
                    padding-bottom: 5px;
                }}

                QPushButton#stopButton:hover {{
                    background: {self.current_theme["stop"]};
                    border: 2px solid {self.current_theme["stop_border"]};
                }}

                QPushButton#stopButton:pressed {{
                    background: {self.current_theme["stop_pressed"]};
                    border: 4px solid {self.current_theme["stop_border"]};
                    padding-top: 13px;
                    padding-bottom: 5px;
                }}

                QPushButton#nextButton:hover {{
                    background: {self.current_theme["next"]};
                    border: 2px solid {self.current_theme["next_border"]};
                }}

                QPushButton#nextButton:pressed {{
                    background: {self.current_theme["next_pressed"]};
                    border: 4px solid {self.current_theme["next_border"]};
                    padding-top: 13px;
                    padding-bottom: 5px;
                }}
            """)

        if hasattr(self, "table"):

            self.table.setStyleSheet(f"""
                QTableWidget {{
                    background: {self.current_theme["table_bg"]};
                    color: {self.current_theme["main_text"]};
                    gridline-color: {self.current_theme["table_grid"]};
                    border: none;
                    selection-background-color: {self.current_theme["table_selected"]};
                    selection-color: {self.current_theme["main_text"]};
                }}

                QTableWidget::item:hover {{
                    background: transparent;
                    border: none;
                }}
            """)

            header = self.table.horizontalHeader()

            header.setStyleSheet(f"""
                QHeaderView::section {{
                    background: {self.current_theme["header_bg"]};
                    color: {self.current_theme["main_text"]};
                    border: 1px solid {self.current_theme["table_grid"]};
                    font-size: 18px;
                    font-weight: bold;
                }}
            """)

        if hasattr(self, "search_edit"):

            self.table.verticalScrollBar().setStyleSheet(f"""
                QScrollBar:vertical {{
                    width: 12px;
                    background: {self.current_theme["table_bg"]};
                    border: none;
                    margin: 0px;
                }}

                QScrollBar::handle:vertical {{
                    background: {self.current_theme["accent_light"]};
                    min-height: 40px;
                    border-radius: 6px;
                    border: none;
                }}

                QScrollBar::handle:vertical:hover {{
                    background: {self.current_theme["accent"]};
                }}

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {{
                    height: 0px;
                    border: none;
                    background: transparent;
                }}

                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {{
                    background: {self.current_theme["window_bg"]};
                }}
            """)

            self.search_edit.setStyleSheet(f"""
                QLineEdit {{
                    color: {self.current_theme["main_text"]};
                    background: {self.current_theme["table_bg"]};
                    border: 1px solid {self.current_theme["table_grid"]};
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 18px;
                    font-weight: bold;
                }}

                QLineEdit:focus {{
                    border: 1px solid {self.current_theme["accent"]};
                }}
            """)

        if hasattr(self, "search_button"):

            self.search_button.setStyleSheet(f"""
                QPushButton {{
                    color: {self.current_theme["main_text"]};
                    background: {self.current_theme["button_bg"]};
                    border: 1px solid {self.current_theme["button_border"]};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 18px;
                    font-weight: bold;
                }}

                QPushButton:hover {{
                    background: {self.current_theme["accent"]};
                }}

                QPushButton:pressed {{
                    background: {self.current_theme["button_bg"]};
                }}
            """)

        if hasattr(self, "now_playing_frame"):

            self.now_playing_frame.setStyleSheet(f"""
                QFrame {{
                    background: {self.current_theme["panel_bg"]};
                    border: 2px solid {self.current_theme["accent"]};
                    border-radius: 10px;
                }}
            """)

        if hasattr(self, "now_playing_title"):

            self.now_playing_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.current_theme["accent_light"]};
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }}
            """)

        if hasattr(self, "now_playing_label"):

            self.now_playing_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.current_theme["main_text"]};
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }}
            """)

    # =====================================================
    # ПРИЛАГАНЕ НА ЦВЕТОВАТА ТЕМА
    # =====================================================

    def apply_theme_settings(self):

        from PySide6.QtCore import QSettings
        from themes import set_theme, get_theme

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        theme_name = settings.value(
            "theme_name",
            "Лилаво-синя",
            type=str,
        )

        if not set_theme(theme_name):
            theme_name = "Лилаво-синя"

        self.current_theme = get_theme(theme_name)

        self.setStyleSheet(f"""
            QWidget {{
                background: {self.current_theme["window_bg"]};
                color: {self.current_theme["main_text"]};
            }}
            """)
        self.refresh_theme_styles()

    def apply_autosave_settings(self):

        from PySide6.QtCore import QSettings

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        # ===== ПРОЧИТАМЕ AUTO SAVE =====

        autosave_enabled_raw = settings.value("autosave_enabled", False)

        if isinstance(autosave_enabled_raw, bool):

            autosave_enabled = autosave_enabled_raw

        else:

            autosave_enabled = str(autosave_enabled_raw).strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        # ===== AUTO SAVE ИЗКЛЮЧЕН =====

        if not autosave_enabled:

            self.autosave_timer.stop()

            return

        # ===== ПРОЧИТАМЕ ИНТЕРВАЛА =====

        autosave_minutes_raw = settings.value("autosave_minutes", "5")

        try:

            autosave_minutes = int(str(autosave_minutes_raw).strip())

        except (TypeError, ValueError):

            autosave_minutes = 5

        autosave_minutes = max(1, min(30, autosave_minutes))

        # ===== РЕСТАРТИРАМЕ ТАЙМЕРА С НОВИЯ ИНТЕРВАЛ =====

        self.autosave_timer.stop()

        self.autosave_elapsed.restart()

        self.autosave_timer.start(autosave_minutes * 60 * 1000)

    def start_autosave_from_settings(self):

        from PySide6.QtCore import QSettings

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        # ===== ПРОЧИТАМЕ ДАЛИ AUTO SAVE Е ВКЛЮЧЕН =====

        autosave_enabled_raw = settings.value("autosave_enabled", False)

        if isinstance(autosave_enabled_raw, bool):

            autosave_enabled = autosave_enabled_raw

        else:

            autosave_enabled = str(autosave_enabled_raw).strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        # ===== ПРОВЕРКА =====

        # ===== AUTO SAVE ИЗКЛЮЧЕН =====

        if not autosave_enabled:

            self.autosave_timer.stop()

            return

        # ===== ПРОЧИТАМЕ ИНТЕРВАЛА =====

        autosave_minutes_raw = settings.value("autosave_minutes", "5")

        try:

            autosave_minutes = int(str(autosave_minutes_raw).strip())

        except (TypeError, ValueError):

            autosave_minutes = 5

        autosave_minutes = max(1, min(30, autosave_minutes))

        # ===== СТАРТИРАМЕ ТАЙМЕРА =====

        interval_ms = autosave_minutes * 60 * 1000

        self.autosave_timer.stop()

        self.autosave_elapsed.restart()

        self.autosave_timer.start(interval_ms)

    def auto_save_project(self):

        elapsed_ms = self.autosave_elapsed.elapsed()

        if not songs:

            return

        file_path = getattr(self, "_current_list_file", None)

        if not file_path:

            return

        try:

            self.save_list(show_message=False)

            # =================================================
            # СЪЩОТО СЪОБЩЕНИЕ КАТО ПРИ РЪЧЕН SAVE
            # =================================================

            self.save_status_label.show()

            self.save_status_timer.stop()

            self.save_status_timer.start(5000)

            # =================================================
            # СЪЩИЯТ ЗВУК КАТО ПРИ РЪЧЕН SAVE
            # =================================================

            try:

                QApplication.beep()

            except Exception:

                pass

        except Exception:

            pass

    def save_list_as(self):

        if not songs:

            QMessageBox.information(
                self,
                self.language_manager.get("no_songs_title"),
                self.language_manager.get("no_songs_to_save"),
            )

            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.language_manager.get("save_list_as_title"),
            "",
            self.language_manager.get("mp3_list_filter"),
        )

        if not file_path:

            return

        if not file_path.lower().endswith(".m3plist"):

            file_path += ".m3plist"

        # ===== ЗАПАЗВАМЕ ТЕКУЩО ИЗБРАНАТА ПЕСЕН ЗА F3 =====

        current_row = self.table.currentRow()

        if 0 <= current_row < len(songs):

            self.f3_last_path = songs[current_row]

        try:

            with open(file_path, "w", encoding="utf-8") as file:

                # Записваме песните
                for path in songs:

                    file.write(path + "\n")

                # Записваме последната F3 позиция
                if self.f3_last_path is not None:

                    file.write("#F3_LAST_PATH=" + self.f3_last_path + "\n")

            # Запомняме точно избрания файл
            self._current_list_file = file_path

            QApplication.beep()

            QMessageBox.information(
                self,
                self.language_manager.get("save_success_title"),
                self.language_manager.get("save_success"),
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                self.language_manager.get("error"),
                self.language_manager.get("save_error") + f"\n\n{e}",
            )

    def open_audio_splitter(self):

        self.audio_splitter = AudioSplitter(self)

        self.audio_splitter.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.audio_splitter.setGeometry(236, 30, 1566, 906)

        self.audio_splitter.show()

    # =====================================================
    # ВРЪЩАМЕ AUDIO SPLITTER НА ФОКУС ПРИ ВЪЗСТАНОВЯВАНЕ
    # =====================================================

    def changeEvent(self, event):

        super().changeEvent(event)

        if event.type() == QEvent.Type.WindowStateChange:

            if (
                hasattr(self, "audio_splitter")
                and self.audio_splitter is not None
                and self.audio_splitter.isVisible()
            ):

                if self.isMinimized():

                    self.set_audio_splitter_taskbar_visible(False)

                else:

                    self.set_audio_splitter_taskbar_visible(True)

                    QTimer.singleShot(100, self.restore_audio_splitter_focus)

    def set_audio_splitter_taskbar_visible(self, visible):

        if not hasattr(self, "audio_splitter") or self.audio_splitter is None:

            return

        if sys.platform.startswith("win"):

            try:

                hwnd = int(self.audio_splitter.winId())

                GWL_EXSTYLE = -20

                WS_EX_APPWINDOW = 0x00040000

                WS_EX_TOOLWINDOW = 0x00000080

                SWP_NOSIZE = 0x0001

                SWP_NOMOVE = 0x0002

                SWP_NOZORDER = 0x0004

                SWP_FRAMECHANGED = 0x0020

                user32 = ctypes.windll.user32

                ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

                if visible:

                    ex_style |= WS_EX_APPWINDOW

                    ex_style &= ~WS_EX_TOOLWINDOW

                else:

                    ex_style &= ~WS_EX_APPWINDOW

                    ex_style |= WS_EX_TOOLWINDOW

                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

                user32.SetWindowPos(
                    hwnd,
                    0,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
                )

            except Exception as e:

                print("AUDIO SPLITTER TASKBAR ERROR:", e)

    def restore_audio_splitter_focus(self):

        if (
            not hasattr(self, "audio_splitter")
            or self.audio_splitter is None
            or not self.audio_splitter.isVisible()
        ):

            return

        self.audio_splitter.showNormal()

        self.audio_splitter.raise_()

        self.audio_splitter.activateWindow()

        self.audio_splitter.setFocus()

    def new_list(self):

        if not songs:

            return

        msg = QMessageBox(self)

        msg.setWindowTitle(self.language_manager.get("new_list_title"))

        msg.setText(self.language_manager.get("new_list_question"))

        msg.setIcon(QMessageBox.Icon.Question)

        yes = msg.addButton(
            self.language_manager.get("yes"), QMessageBox.ButtonRole.YesRole
        )

        no = msg.addButton(
            self.language_manager.get("no"), QMessageBox.ButtonRole.NoRole
        )

        msg.setDefaultButton(no)

        no.setFocus()

        msg.exec()

        if msg.clickedButton() == no:

            return

        # Запазваме стария списък за CTRL + Z
        self.push_undo()

        # Изчистваме списъка само от програмата
        songs.clear()
        edited_tags.clear()

        # Изчистваме търсачката
        self.search_edit.clear()

        # Изчистваме селекцията
        self.table.clearSelection()

        self.table.setCurrentCell(-1, -1)

        # Обновяваме таблицата
        self.refresh()

    def push_undo(self):

        undo_stack.append({"songs": songs.copy(), "edited": edited_tags.copy()})

    def undo_last(self):

        if not undo_stack:
            return

        state = undo_stack.pop()

        songs[:] = state["songs"]

        edited_tags.clear()

        edited_tags.update(state["edited"])

        self.refresh()

    def save_edited_cell(self, item):

        row = item.row()

        col = item.column()

        if row >= len(songs):
            return

        self.push_undo()

        path = songs[row]

        if path not in edited_tags:

            edited_tags[path] = {}

        if col == 1:

            edited_tags[path]["title"] = item.text().strip()

        elif col == 2:

            edited_tags[path]["artist"] = item.text().strip()

    def update_song_order(self):

        # Разместването с мишката се обработва
        # директно в SongTableWidget.dropEvent().
        return

    def add_files(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.language_manager.get("select_mp3_files"),
            "",
            self.language_manager.get("mp3_files_filter"),
        )

        # Натиснат е ESC или Cancel
        if not files:

            self.table.clearSelection()

            self.table.setCurrentCell(-1, -1)

            self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            return

        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ===== ПОКАЗВАМЕ ЛЕНТАТА ЗА ЗАРЕЖДАНЕ =====

        total_files = len(files)

        self.loading_progress.setRange(0, total_files)

        self.loading_progress.setValue(0)

        self.loading_label.setText(
            self.language_manager.get(
                "loading_song_progress",
                current="0",
                total=str(total_files),
            )
        )

        # Центрираме панела
        x = (self.width() - self.loading_overlay.width()) // 2

        y = (self.height() - self.loading_overlay.height()) // 2

        self.loading_overlay.move(x, y)

        self.loading_overlay.show()

        self.loading_overlay.raise_()

        QApplication.processEvents()

        # ===== ЗАРЕЖДАНЕ =====

        for index, file in enumerate(files, start=1):

            if file in songs:

                # Звук при появяване на съобщението
                QApplication.beep()

                msg = QMessageBox(self)

                msg.setWindowTitle(self.language_manager.get("duplicate_title"))

                msg.setText(self.language_manager.get("song_already_loaded"))

                msg.setInformativeText(
                    self.language_manager.get("replace_song_question")
                )

                msg.setIcon(QMessageBox.Icon.Question)

                yes = msg.addButton(
                    self.language_manager.get("yes"),
                    QMessageBox.ButtonRole.YesRole,
                )

                no = msg.addButton(
                    self.language_manager.get("no"),
                    QMessageBox.ButtonRole.NoRole,
                )

                msg.setDefaultButton(no)

                no.setFocus()

                msg.exec()

                if msg.clickedButton() == no:

                    self.loading_progress.setValue(index)

                    self.loading_label.setText(
                        self.language_manager.get(
                            "loading_song_progress",
                            current=str(index),
                            total=str(total_files),
                        )
                    )

                    QApplication.processEvents()

                    continue

                songs.remove(file)

            songs.append(file)

            # Обновяваме прогреса
            self.loading_progress.setValue(index)

            self.loading_label.setText(
                self.language_manager.get(
                    "loading_song_progress",
                    current=str(index),
                    total=str(total_files),
                )
            )

            QApplication.processEvents()

        # ===== ОБНОВЯВАМЕ ТАБЛИЦАТА =====

        self.refresh()

        # Връщаме фокуса към таблицата
        if songs:

            current_row = self.table.currentRow()

            if current_row < 0 or current_row >= len(songs):

                current_row = 0

            self.table.selectRow(current_row)

            self.table.setCurrentCell(current_row, 1)

            self.table.setFocus(Qt.FocusReason.OtherFocusReason)

        # Показваме завършеното състояние
        self.loading_progress.setValue(total_files)

        self.loading_label.setText(
            self.language_manager.get(
                "loading_song_complete",
                total=str(total_files),
            )
        )

        QApplication.processEvents()

        # ===== ОСТАВА ВИДИМА ПОНЕ 1 СЕКУНДА =====

        QTimer.singleShot(1000, self.loading_overlay.hide)

    def add_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            self.language_manager.get("choose_folder"),
        )

        # Натиснат е ESC или Cancel
        if not folder:

            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)

            self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            return

        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ===== НАМИРАМЕ MP3 ФАЙЛОВЕТЕ =====

        folder_mp3_files = [
            os.path.join(folder, file)
            for file in os.listdir(folder)
            if file.lower().endswith(".mp3")
        ]

        if not folder_mp3_files:

            return

        # ===== ПРОВЕРКА ЗА ДУБЛИРАНЕ =====

        duplicate = any(file in songs for file in folder_mp3_files)

        if duplicate:

            # Звук при появяване на съобщението
            QApplication.beep()

            msg = QMessageBox(self)

            msg.setWindowTitle(self.language_manager.get("duplicate_title"))

            msg.setText(self.language_manager.get("folder_already_loaded"))

            msg.setInformativeText(self.language_manager.get("replace_folder_question"))

            msg.setIcon(QMessageBox.Icon.Question)

            yes = msg.addButton(
                self.language_manager.get("yes"), QMessageBox.ButtonRole.YesRole
            )

            no = msg.addButton(
                self.language_manager.get("no"), QMessageBox.ButtonRole.NoRole
            )

            msg.setDefaultButton(no)

            no.setFocus()

            msg.exec()

            if msg.clickedButton() == no:

                return

            # Премахваме старите песни от тази папка
            songs[:] = [path for path in songs if not path.startswith(folder + os.sep)]

            # ===== ПОКАЗВАМЕ ЛЕНТАТА =====

            total_files = len(folder_mp3_files)

            self.loading_progress.setRange(0, total_files)

            self.loading_progress.setValue(0)

            self.loading_label.setText(
                self.language_manager.get(
                    "loading_folder_progress",
                    current=str(0),
                    total=str(total_files),
                )
            )

            # Центрираме панела
            x = (self.width() - self.loading_overlay.width()) // 2

            y = (self.height() - self.loading_overlay.height()) // 2

            self.loading_overlay.move(x, y)

            self.loading_overlay.show()
            self.loading_overlay.raise_()

            QApplication.processEvents()

            # ===== ЗАРЕЖДАМЕ ПЕСНИТЕ =====

            for index, path in enumerate(folder_mp3_files, start=1):

                if path not in songs:

                    songs.append(path)

                self.loading_progress.setValue(index)

                self.loading_label.setText(
                    self.language_manager.get(
                        "loading_folder_progress",
                        current=str(index),
                        total=str(total_files),
                    )
                )

                QApplication.processEvents()

        # ===== ОБНОВЯВАМЕ ТАБЛИЦАТА =====

        self.refresh()

        # Връщаме фокуса към таблицата
        if songs:

            current_row = self.table.currentRow()

            if current_row < 0 or current_row >= len(songs):

                current_row = 0

            self.table.selectRow(current_row)

            self.table.setCurrentCell(current_row, 1)

            self.table.setFocus(Qt.FocusReason.OtherFocusReason)

        # Показваме завършеното състояние
        self.loading_progress.setValue(total_files)

        self.loading_label.setText(
            self.language_manager.get(
                "loading_folder_complete",
                total=str(total_files),
            )
        )

        QApplication.processEvents()

        # ===== ОСТАВА ВИДИМА ПОНЕ 1 СЕКУНДА =====

        QTimer.singleShot(1000, self.loading_overlay.hide)

    def move_row(self, from_row, to_row):

        if from_row == to_row:
            return

        bar = self.table.verticalScrollBar()
        scroll = bar.value()

        # ===== ЗАПОМНЯМЕ ТОЧНО КОЯ ПЕСЕН СВИРИ =====

        playing_path = None

        if 0 <= self.playing_index < len(songs):

            playing_path = songs[self.playing_index]

        # ===== ПРЕМЕСТВАМЕ ПЕСЕНТА В СПИСЪКА =====

        songs.insert(to_row, songs.pop(from_row))

        # ===== НАМИРАМЕ НОВИЯ РЕД НА СВИРЕЩАТА ПЕСЕН =====

        if playing_path is not None:

            try:

                self.playing_index = songs.index(playing_path)

            except ValueError:

                self.playing_index = -1

            # ===== ОБНОВЯВАМЕ ТАБЛИЦАТА =====

            self.table.blockSignals(True)

            self.table.setRowCount(0)

            for i, path in enumerate(songs):

                title, artist, duration = song_info(path)

                row = self.table.rowCount()

                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))

                title_item = QTableWidgetItem(title)
                title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                artist_item = QTableWidgetItem(artist)
                artist_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                title_item.setData(Qt.ItemDataRole.UserRole, path)

                self.table.setItem(row, 1, title_item)
                self.table.setItem(row, 2, artist_item)
                self.table.setItem(row, 3, QTableWidgetItem(duration))

            self.table.setRowCount(max(50, len(songs)))

            self.table.blockSignals(False)
            self.highlight_playing_song()

        # ===== НЕ ЗАПОЧВАМЕ НОВО ЗАРЕЖДАНЕ =====

    def move_up(self):

        row = self.table.currentRow()

        if row <= 0:
            return

        self.move_row(row, row - 1)

        self.table.setCurrentCell(row - 1, 1)
        self.table.selectRow(row - 1)

    def move_down(self):

        row = self.table.currentRow()

        if row < 0 or row >= len(songs) - 1:
            return

        self.move_row(row, row + 1)

        self.table.setCurrentCell(row + 1, 1)
        self.table.selectRow(row + 1)

    def remove(self):

        class DirectionalMessageBox(QMessageBox):

            def keyPressEvent(self, event):

                # ← -> Да
                if event.key() == Qt.Key.Key_Left:

                    buttons = self.buttons()

                    if len(buttons) >= 2:

                        buttons[0].setFocus()

                    event.accept()
                    return

                # → -> Не
                elif event.key() == Qt.Key.Key_Right:

                    buttons = self.buttons()

                    if len(buttons) >= 2:

                        buttons[1].setFocus()

                    event.accept()
                    return

                # ↑ / ↓ -> нищо не правят
                elif event.key() in (
                    Qt.Key.Key_Up,
                    Qt.Key.Key_Down,
                ):

                    event.accept()
                    return

                super().keyPressEvent(event)

        # =========================================================
        # НАМИРАМЕ ИЗБРАНИТЕ РЕАЛНИ ПЕСНИ
        # =========================================================

        selected_rows = sorted(
            {
                index.row()
                for index in self.table.selectionModel().selectedRows()
                if 0 <= index.row() < len(songs)
            },
            reverse=True,
        )

        # Ако няма маркиран ред, използваме текущия ред
        if not selected_rows:

            current_row = self.table.currentRow()

            if 0 <= current_row < len(songs):

                selected_rows = [current_row]

            else:

                return

        # =========================================================
        # ПРОВЕРЯВАМЕ ДАЛИ СА ИЗБРАНИ ВСИЧКИ РЕАЛНИ ПЕСНИ
        # =========================================================

        all_songs_selected = (
            len(songs) > 1
            and len(selected_rows) == len(songs)
            and set(selected_rows) == set(range(len(songs)))
        )

        # =========================================================
        # ОПРЕДЕЛЯМЕ ТЕКСТА НА ПОТВЪРЖДЕНИЕТО
        # =========================================================

        # Само една песен
        if len(selected_rows) == 1:

            question = self.language_manager.get("delete_selected_song_question")

        # Всички реални песни са избрани
        elif all_songs_selected:

            question = self.language_manager.get("delete_all_songs_question")

        # Няколко, но не всички
        else:

            question = self.language_manager.get("delete_selected_songs_question")

        # =========================================================
        # ПОТВЪРЖДЕНИЕ
        # =========================================================

        QApplication.beep()

        msg = DirectionalMessageBox(self)

        msg.setWindowTitle(self.language_manager.get("question"))

        msg.setText(question)

        msg.setIcon(QMessageBox.Icon.Question)

        yes = msg.addButton(
            self.language_manager.get("yes"), QMessageBox.ButtonRole.YesRole
        )

        no = msg.addButton(
            self.language_manager.get("no"), QMessageBox.ButtonRole.NoRole
        )

        # По подразбиране фокусът е върху „Не“
        msg.setDefaultButton(no)

        no.setFocus()

        # =========================================================
        # ВРЕМЕННО СПИРАМЕ GLOBAL EVENT FILTER
        # =========================================================

        app = QApplication.instance()

        if app is not None:

            app.removeEventFilter(self)

        msg.exec()

        # =========================================================
        # ВРЪЩАМЕ GLOBAL EVENT FILTER
        # =========================================================

        if app is not None:

            app.installEventFilter(self)

        # =========================================================
        # АКО Е НАТИСНАТО „НЕ“
        # =========================================================

        if msg.clickedButton() == no:

            return

        # =========================================================
        # ПОТВЪРЖДЕНИЕ „ДА“
        # =========================================================

        QApplication.beep()

        # Запазваме състоянието за CTRL + Z
        self.push_undo()

        # =========================================================
        # ИЗТРИВАМЕ ОТЗАД НАПРЕД
        # =========================================================

        for row in selected_rows:

            if 0 <= row < len(songs):

                songs.pop(row)

        # Обновяваме таблицата
        self.refresh()

        # =========================================================
        # АКО ОСТАВАТ ПЕСНИ
        # =========================================================

        if songs:

            new_row = min(
                selected_rows[-1],
                len(songs) - 1,
            )

            self.table.selectRow(new_row)

            self.table.setCurrentCell(new_row, 1)

        # =========================================================
        # АКО СПИСЪКЪТ Е НАПЪЛНО ПРАЗЕН
        # =========================================================

        else:

            # =====================================================
            # ВАЖНО:
            # НЕ СПИРАМЕ ТЕКУЩАТА ПЕСЕН!
            # НЕ НУЛИРАМЕ playing_path!
            # НЕ СПИРАМЕ progress_timer!
            # =====================================================

            # Само махаме избора от таблицата
            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)
            self.table.show()

            # Ако в момента няма реално свиреща песен,
            # тогава можем веднага да покажем празния списък.
            if self.vlc_player is None or not self.vlc_player.is_playing():

                self.playing_index = -1
                self.playing_path = None

                self.progress_timer.stop()

                self.progress_slider.setValue(0)

                self.progress_slider.hide()
                self.current_time_label.hide()
                self.remaining_time_label.hide()

                self.now_playing_label.setText(
                    self.language_manager.get("no_playlist_loaded")
                )

                # Ако песента В МОМЕНТА СВИРИ:
                # оставяме я да продължи до края.

                # =====================================================
                # СЪОБЩЕНИЕ ЗА УСПЕШНО ИЗТРИВАНЕ
                # =====================================================

                QApplication.beep()

                done = QMessageBox(self)

                done.setWindowTitle(self.language_manager.get("success"))

                done.setText(self.language_manager.get("delete_success"))

                done.setIcon(QMessageBox.Icon.Information)

                ok = done.addButton(
                    self.language_manager.get("ok"), QMessageBox.ButtonRole.AcceptRole
                )

                done.setDefaultButton(ok)

                ok.setFocus()

                done.exec()

    def check_order(self):

        if not songs:

            QMessageBox.warning(
                self,
                self.language_manager.get("no_songs_title"),
                self.language_manager.get("add_songs_first"),
            )

            return

        total_seconds = 0

        text = self.language_manager.get("nero_queue") + "\n"
        text += "=" * 45 + "\n\n"

        for i, path in enumerate(songs, start=1):

            title, artist, duration = song_info(path)

            audio = MP3(path)

            total_seconds += int(audio.info.length)

            text += f"{i:02d}. {title} ({duration})\n"

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        text += "\n" + "=" * 45 + "\n"
        text += (
            self.language_manager.get("nero_total_songs").format(count=len(songs))
            + "\n"
        )

        text += (
            self.language_manager.get("nero_total_time").format(
                minutes=minutes, seconds=seconds
            )
            + "\n\n"
        )

        if total_seconds <= 80 * 60:

            text += self.language_manager.get("nero_within_limit")

        else:

            text += self.language_manager.get("nero_over_limit")

        dialog = QDialog(self)

        dialog.setWindowTitle(self.language_manager.get("nero_check_title"))

        dialog.resize(700, 800)

        layout = QVBoxLayout(dialog)

        text_box = QPlainTextEdit()

        text_box.setPlainText(text)

        text_box.setReadOnly(True)

        layout.addWidget(text_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)

        buttons.accepted.connect(dialog.accept)

        layout.addWidget(buttons)

        dialog.setStyleSheet(f"""
            QDialog {{
                background: {self.current_theme["window_bg"]};
                color: {self.current_theme["main_text"]};
            }}

            QPlainTextEdit {{
                background: {self.current_theme["table_bg"]};
                color: {self.current_theme["main_text"]};
                border: 2px solid {self.current_theme["accent"]};
                border-radius: 8px;
                padding: 8px;
                font-size: 15px;
            }}

            QDialogButtonBox QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 18px;
                font-weight: bold;
            }}

            QDialogButtonBox QPushButton:hover {{
                background: {self.current_theme["accent"]};
                border-color: {self.current_theme["accent"]};
            }}

            QDialogButtonBox QPushButton:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
            }}
        """)

        dialog.exec()

    def auto_split(self):

        if not songs:

            QMessageBox.warning(
                self,
                self.language_manager.get("no_songs_title"),
                self.language_manager.get("add_songs_first"),
            )
            return

        fixed = 0
        warning = []

        for row, path in enumerate(songs):

            filename = os.path.splitext(os.path.basename(path))[0]

            # маха номерата отпред
            filename = re.sub(r"^(?:\s*\d+\s*-\s*)+", "", filename)

            if " - " in filename:

                artist, title = filename.split(" - ", 1)

                self.table.setItem(row, 1, QTableWidgetItem(title.strip()))
                self.table.setItem(row, 2, QTableWidgetItem(artist.strip()))

                fixed += 1

            else:

                warning.append(filename)

        text = self.language_manager.get(
            "auto_split_success_summary",
            count=str(fixed),
        )

        if warning:

            text += self.language_manager.get("auto_split_warning_header")
            text += "=" * 45 + "\n\n"

            for song in warning:

                text += f"• {song}\n"

        else:

            text += self.language_manager.get("auto_split_complete")

            dialog = QDialog(self)

            dialog.setWindowTitle(self.language_manager.get("automatic_split_title"))

            dialog.resize(700, 800)

            layout = QVBoxLayout(dialog)

            text_box = QPlainTextEdit()

            text_box.setPlainText(text)

            text_box.setReadOnly(True)

            layout.addWidget(text_box)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)

            buttons.accepted.connect(dialog.accept)

            layout.addWidget(buttons)

            dialog.exec()

    def edit_tags(self):

        row = self.table.currentRow()

        if row < 0:

            QMessageBox.warning(
                self,
                self.language_manager.get("no_selected_song_title"),
                self.language_manager.get("no_selected_song_text"),
            )

            return

        path = songs[row]

        title, artist, duration = song_info(path)

        dialog = QDialog(self)

        dialog.setMinimumWidth(550)
        dialog.setFixedHeight(180)

        dialog.setWindowTitle(self.language_manager.get("edit_id3_title"))

        layout = QFormLayout(dialog)

        artist_edit = QLineEdit(artist)
        title_edit = QLineEdit(title)

        artist_edit.setMinimumWidth(420)
        title_edit.setMinimumWidth(420)

        layout.addRow(self.language_manager.get("artist"), artist_edit)

        layout.addRow(self.language_manager.get("song"), title_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(dialog.accept)

        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:

            new_artist = artist_edit.text().strip()
            new_title = title_edit.text().strip()

            if self.save_id3_tags(
                path,
                new_artist,
                new_title,
            ):

                # =================================================
                # ЗАПАЗВАМЕ И ВЪТРЕШНО В ПРОГРАМАТА
                # =================================================

                if path not in edited_tags:

                    edited_tags[path] = {}

                edited_tags[path]["artist"] = new_artist
                edited_tags[path]["title"] = new_title

        # =================================================
        # ОБНОВЯВАМЕ ТАБЛИЦАТА ВЕДНАГА
        # =================================================

        self.refresh()

        self.table.selectRow(row)

        QMessageBox.information(
            self,
            self.language_manager.get("success"),
            self.language_manager.get("id3_saved"),
        )

    def save_id3_tags(
        self,
        path,
        artist,
        title,
    ):

        from mutagen.easyid3 import EasyID3
        from mutagen.id3 import ID3

        try:

            # =================================================
            # ОПИТ ЗА ОТВАРЯНЕ НА СЪЩЕСТВУВАЩИТЕ ID3 ТАГОВЕ
            # =================================================

            try:

                audio = EasyID3(path)

            except Exception:

                # =================================================
                # АКО НЯМА EASYID3 ТАГОВЕ
                # СЪЗДАВАМЕ ID3 ТАГОВЕ ВЪВ ФАЙЛА
                # =================================================

                id3 = ID3()

                id3.save(path, v2_version=3)

                audio = EasyID3(path)

            # =================================================
            # ИЗПЪЛНИТЕЛ
            # =================================================

            audio["artist"] = [artist]

            # =================================================
            # ЗАГЛАВИЕ
            # =================================================

            audio["title"] = [title]

            # =================================================
            # ЗАПИСВАМЕ В СЪЩИЯ MP3 ФАЙЛ
            # =================================================

            audio.save()

            return True

        except Exception as e:

            QMessageBox.critical(
                self,
                self.language_manager.get("error"),
                self.language_manager.get("id3_save_error") + f"\n\n{e}",
            )

            return False

    def export(self):

        if not songs:

            QMessageBox.warning(
                self,
                self.language_manager.get("no_songs_title"),
                self.language_manager.get("add_songs_first"),
            )

            return

        folder = QFileDialog.getExistingDirectory(
            self,
            self.language_manager.get("choose_export_folder"),
        )

        if folder:

            export_folder = os.path.join(folder, "MP3_DISK_EXPORT")

            os.makedirs(export_folder, exist_ok=True)

            import re

            for i, path in enumerate(songs, start=1):

                name = os.path.basename(path)

                clean_name = re.sub(r"^\s*\d+\s*-\s*", "", name)

                new_name = f"{i:02d} - {clean_name}"

                destination_path = os.path.join(
                    os.fsdecode(export_folder),
                    new_name,
                )

                shutil.copy(
                    path,
                    destination_path,
                )

            QMessageBox.information(
                self,
                self.language_manager.get("success"),
                self.language_manager.get("nero_ready"),
            )

    def _check_update_result(self):

        if self._update_thread.is_alive():

            QTimer.singleShot(500, self._check_update_result)

            return

        if self._pending_update is None:

            return

        update_info = self._pending_update

        self._pending_update = None

        message_box = QMessageBox(self)

        message_box.setWindowTitle(language_manager.get("update_available_title"))

        message_box.setText(
            language_manager.get(
                "update_available_text",
                current_version=update_info.current_version,
                latest_version=update_info.latest_version,
            )
        )

        update_button = message_box.addButton(
            language_manager.get("update_button"),
            QMessageBox.ButtonRole.AcceptRole,
        )

        later_button = message_box.addButton(
            language_manager.get("update_later"),
            QMessageBox.ButtonRole.RejectRole,
        )

        message_box.setDefaultButton(update_button)

        message_box.exec()

        if message_box.clickedButton() is update_button:

            pass

    # =========================================================
    # ПРОВЕРКА ЗА ОБНОВЯВАНЕ ВЪВ ФОНОВ РЕЖИМ
    # =========================================================

    def _check_for_update_background(self):

        self._pending_update = check_for_update()

    # =========================================================
    # ЗАТВАРЯНЕ
    # =========================================================

    def closeEvent(self, event):

        if hasattr(self, "progress_timer"):

            self.progress_timer.stop()

        if hasattr(self, "autosave_timer"):

            self.autosave_timer.stop()

        if hasattr(self, "save_status_timer"):

            self.save_status_timer.stop()

        fade_timer = getattr(self, "_fade_timer", None)

        if fade_timer is not None:

            fade_timer.stop()
            fade_timer.deleteLater()
            self._fade_timer = None

        fade_in_timer = getattr(self, "_fade_in_timer", None)

        if fade_in_timer is not None:

            fade_in_timer.stop()
            fade_in_timer.deleteLater()
            self._fade_in_timer = None

        try:

            if self.vlc_player is not None:

                self.vlc_player.stop()
                self.vlc_player.release()

        except Exception:

            pass

        try:

            if self.vlc_instance is not None:

                self.vlc_instance.release()

        except Exception:

            pass

        event.accept()

    # ===== КЛАВИАТУРНИ КОМАНДИ =====
    def eventFilter(self, obj, event):

        # =========================================================
        # ALT / МЕНЮ
        # =========================================================

        # ALT -> превключва менюто „Файл“
        # ALT + SHIFT -> оставяме Windows да смени езика.
        if event.type() == event.Type.ShortcutOverride:

            if event.key() == Qt.Key.Key_Alt:

                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:

                    return super().eventFilter(obj, event)

                event.accept()

                return True

        # =========================================================
        # KEY PRESS
        # =========================================================

        if event.type() == event.Type.KeyPress:
            # TAB -> ако списъкът е празен,
            # директно към „➕ Добави песни“
            if event.key() == Qt.Key.Key_Tab and not songs:

                first_button = self.findChild(QPushButton, "addFilesButton")

                if first_button is not None:

                    first_button.setFocus(Qt.FocusReason.TabFocusReason)

                    return True

            # -----------------------------------------------------
            # ALT
            # -----------------------------------------------------

            if event.nativeScanCode() == 56:

                # ALT + SHIFT -> оставяме Windows да смени езика
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:

                    return super().eventFilter(obj, event)

                # Второ натискане на ALT -> затваряме менюто
                active_action = self.menu_bar.activeAction()

                if active_action is not None:

                    active_menu = active_action.menu()

                    if isinstance(active_menu, QMenu):

                        active_menu.close()
                        active_menu.hide()

                    self.menu_bar.clearFocus()

                    self.setFocus()

                    self._file_menu_selected = False

                    return True

                # Първо натискане на ALT -> активираме „Файл“
                self._file_menu_selected = True

                self.menu_bar.setFocus(Qt.FocusReason.ShortcutFocusReason)

                if self.menu_bar.actions():

                    self.menu_bar.setActiveAction(self.menu_bar.actions()[0])

                return True

            # -----------------------------------------------------
            # ENTER
            # -----------------------------------------------------

            if event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):

                widget = QApplication.focusWidget()

                # Ако менюто „Файл“ е отворено,
                # оставяме QMenu само да обработи Enter.
                if isinstance(widget, QMenu):

                    return super().eventFilter(obj, event)

                # ENTER върху таблицата -> пуска избраната песен
                if widget is self.table:

                    current_row = self.table.currentRow()

                    if 0 <= current_row < len(songs):

                        play_button = self.findChild(QPushButton, "playButton")

                        if play_button is not None:

                            play_button.setDown(True)

                            QTimer.singleShot(400, lambda: play_button.setDown(False))

                        self.play_song()

                    return True

                # ENTER върху бутон
                if isinstance(widget, QPushButton):

                    widget.click()

                    return True

            # -----------------------------------------------------
            # SPACE -> ПАУЗА / ПРОДЪЛЖИ
            # -----------------------------------------------------

            if event.key() == Qt.Key.Key_Space:

                widget = QApplication.focusWidget()

                # SPACE върху таблицата -> пауза / продължи
                if widget is self.table:

                    pause_button = self.findChild(QPushButton, "pauseButton")

                    if pause_button is not None:

                        pause_button.setDown(True)

                        QTimer.singleShot(400, lambda: pause_button.setDown(False))

                    self.pause_song()

                    return True

            # -----------------------------------------------------
            # CTRL + F
            # -----------------------------------------------------

            # Работи независимо от езика на клавиатурата
            # и независимо кой контрол е активен.
            if (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier
                and event.nativeScanCode() == 33
            ):

                if not songs:

                    return True

                if self.search_edit.hasFocus():

                    self.table.setFocus(Qt.FocusReason.ShortcutFocusReason)

                else:

                    self.search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)

                    self.search_edit.selectAll()

                return True

            # -----------------------------------------------------
            # DELETE
            # -----------------------------------------------------

            if event.key() == Qt.Key.Key_Delete and self.table.hasFocus():

                remove_method = getattr(self, "remove", None)

                if callable(remove_method):

                    remove_method()

                return True

            # -----------------------------------------------------
            # CTRL + Z
            # -----------------------------------------------------

            if event.matches(QKeySequence.StandardKey.Undo):

                undo_method = getattr(self, "undo_last", None)

                if callable(undo_method):

                    undo_method()

                return True

            # -----------------------------------------------------
            # CTRL + A
            # -----------------------------------------------------

            if (
                event.key() == Qt.Key.Key_A
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):

                if songs and self.table.hasFocus() and self.table.currentRow() >= 0:

                    self.table.setSelectionMode(
                        QAbstractItemView.SelectionMode.ExtendedSelection
                    )

                    self.table.selectAll()

                    self.table.setFocus()

                    return True

            # -----------------------------------------------------
            # ↑ / ↓ ОТ ТЪРСАЧКАТА
            # -----------------------------------------------------

            if obj is self.search_edit and event.key() in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
            ):

                visible_rows = [
                    row for row in range(len(songs)) if not self.table.isRowHidden(row)
                ]

                if visible_rows:

                    self.table.setFocus()

                    self.table.keyPressEvent(event)

                    return True

            # -----------------------------------------------------
            # CTRL + ↑ / ↓ → ПОДРЕЖДАНЕ НА ПЕСЕН
            # -----------------------------------------------------

            if event.type() == event.Type.KeyPress:

                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:

                    if event.key() in (
                        Qt.Key.Key_Up,
                        Qt.Key.Key_Down,
                    ):

                        current_row = self.table.currentRow()

                        if 0 <= current_row < len(songs):

                            if event.key() == Qt.Key.Key_Up:

                                target_row = current_row - 1

                            else:

                                target_row = current_row + 1

                            if 0 <= target_row < len(songs):

                                self.move_row(current_row, target_row)

                                self.table.setCurrentCell(target_row, 1)
                                self.table.selectRow(target_row)

                        return True

            # -----------------------------------------------------
            # SHIFT + ↑ / ↓
            # -----------------------------------------------------

            if (
                self.table.hasFocus()
                and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                and event.key()
                in (
                    Qt.Key.Key_Up,
                    Qt.Key.Key_Down,
                )
            ):

                current_row = self.table.currentRow()

                if 0 <= current_row < len(songs):

                    self.table.setSelectionMode(
                        QAbstractItemView.SelectionMode.ExtendedSelection
                    )

                    if event.key() == Qt.Key.Key_Down:

                        next_row = min(current_row + 1, len(songs) - 1)

                    else:

                        next_row = max(current_row - 1, 0)

                    selection_model = self.table.selectionModel()

                    current_index = self.table.currentIndex()

                    next_index = self.table.model().index(next_row, 1)

                    selection_model.select(
                        current_index, QItemSelectionModel.SelectionFlag.Select
                    )

                    selection_model.select(
                        next_index, QItemSelectionModel.SelectionFlag.Select
                    )

                    self.table.setCurrentCell(next_row, 1)

                return True

            # -----------------------------------------------------
            # CTRL + S
            # -----------------------------------------------------

            if (
                event.key() == Qt.Key.Key_S
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):

                if not songs:

                    return True

                file_path = getattr(self, "_current_list_file", None)

                if not file_path:

                    return True

                current_row = self.table.currentRow()

                if 0 <= current_row < len(songs):

                    self.f3_last_path = songs[current_row]

                try:

                    with open(file_path, "w", encoding="utf-8") as file:

                        for path in songs:

                            file.write(path + "\n")

                        if self.f3_last_path is not None:

                            file.write("#F3_LAST_PATH=" + self.f3_last_path + "\n")

                    QApplication.beep()

                    self.save_status_label.show()

                    self.save_status_timer.stop()

                    self.save_status_timer.start(5000)

                except Exception:

                    QMessageBox.critical(
                        self,
                        self.language_manager.get("error"),
                        self.language_manager.get("changes_save_error"),
                    )

                return True

            # -----------------------------------------------------
            # F3
            # -----------------------------------------------------

            if event.key() == Qt.Key.Key_F3:

                # Второ натискане на F3 -> излизаме от таблицата
                if self.table.hasFocus():

                    current_row = self.table.currentRow()

                    if 0 <= current_row < len(songs):

                        self.f3_last_path = songs[current_row]

                    self.table.clearSelection()

                    self.table.setCurrentIndex(QModelIndex())

                    self.setFocus()

                    return True

                # Следващо F3 -> връщаме последната запомнена песен
                if songs:

                    target_row = 0

                    if self.f3_last_path is not None and self.f3_last_path in songs:

                        target_row = songs.index(self.f3_last_path)

                    self.table.clearSelection()

                    self.table.selectRow(target_row)

                    self.table.setCurrentCell(target_row, 1)

                    self.table.setFocus()

                    self.f3_last_path = songs[target_row]

                    item = self.table.item(target_row, 1)

                    if item:

                        self.table.scrollToItem(
                            item, QAbstractItemView.ScrollHint.PositionAtCenter
                        )

                return True

            # -----------------------------------------------------
            # F5
            # -----------------------------------------------------

            if event.key() == Qt.Key.Key_F5:

                # Ако друг прозорец е активен
                # F5 не обновява таблицата на основния прозорец
                if QApplication.activeWindow() is not self:

                    return super().eventFilter(obj, event)

                self.refresh()

                msg = QMessageBox(self)

                msg.setWindowTitle(self.language_manager.get("refresh_title"))

                msg.setText(self.language_manager.get("refresh_success"))

                msg.setIcon(QMessageBox.Icon.Information)

                msg.exec()

                return True

            # -----------------------------------------------------
            # ← / → ПРЕВЪРТАНЕ НА ПЕСЕНТА
            # -----------------------------------------------------

            if event.key() in (
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
            ):

                # -------------------------------------------------
                # МЕНЮТО Е АКТИВНО
                # → СТРЕЛКИТЕ СА САМО ЗА НАВИГАЦИЯ В МЕНЮТО
                # → ПЕСЕНТА НЕ СЕ ПРЕВЪРТА
                # -------------------------------------------------

                if self._file_menu_selected:

                    return super().eventFilter(obj, event)

                # -------------------------------------------------
                # МЕНЮТО НЕ Е АКТИВНО
                # → ← / → ПРЕВЪРТАТ ПЕСЕНТА
                # -------------------------------------------------

                if self.vlc_player is not None:

                    current_time = self.vlc_player.get_time()
                    current_rate = self.vlc_player.get_rate()

                    total_time = self.vlc_player.get_length()

                    if current_time >= 0 and total_time > 0:

                        if event.key() == Qt.Key.Key_Left:

                            new_time = max(0, current_time - 5000)

                        else:

                            new_time = min(total_time, current_time + 5000)

                        self.vlc_player.set_time(new_time)
                        self.vlc_player.set_rate(current_rate)

                        return True

        # =========================================================
        # КЛИК ИЗВЪН ТАБЛИЦАТА
        # =========================================================

        if event.type() == event.Type.MouseButtonPress:

            if not self.table.geometry().contains(
                self.mapFromGlobal(event.globalPosition().toPoint())
            ):

                self.table.clearSelection()

        return super().eventFilter(obj, event)

    def search_song(self):

        text = self.search_edit.text().strip().lower()

        # Когато търсим нещо
        if text:

            found_row = -1

            for row in range(len(songs)):

                show = False

                for col in (0, 1, 2):

                    item = self.table.item(row, col)

                    if item and text in item.text().lower():

                        show = True

                        if found_row == -1:
                            found_row = row

                        break

                self.table.setRowHidden(row, not show)

            # Скриваме празните редове
            for row in range(len(songs), self.table.rowCount()):
                self.table.setRowHidden(row, True)

            if found_row >= 0:

                # Запомняме намерения ред
                self._last_search_row = found_row

                self.table.clearSelection()
                self.table.selectRow(found_row)
                self.table.setCurrentCell(found_row, 1)

                item = self.table.item(found_row, 1)

                if item:
                    self.table.scrollToItem(
                        item, QAbstractItemView.ScrollHint.PositionAtCenter
                    )

            return

        # Търсачката е изчистена -> показваме целия списък
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

        # Връщаме маркера на последно намерения ред
        if hasattr(self, "_last_search_row"):

            row = self._last_search_row

            if 0 <= row < len(songs):

                self.table.clearSelection()
                self.table.selectRow(row)
                self.table.setCurrentCell(row, 1)

                item = self.table.item(row, 1)

                if item:
                    self.table.scrollToItem(
                        item, hint=QAbstractItemView.ScrollHint.PositionAtCenter
                    )

    def play_searched_song(self):

        if not hasattr(self, "_last_search_row"):
            return

        row = self._last_search_row

        if 0 <= row < len(songs):

            self.table.clearSelection()
            self.table.selectRow(row)
            self.table.setCurrentCell(row, 1)

            self.play_song()

            self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)

            self.search_edit.setCursorPosition(len(self.search_edit.text()))


app = QApplication(sys.argv)


window = MP3Order()


window.show()


sys.exit(app.exec())
