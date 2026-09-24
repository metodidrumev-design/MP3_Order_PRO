# ============================================================
# MP3 ORDER PRO - SETTINGS
# ============================================================

# ============================================================
# IMPORTS - НАЧАЛО
# ============================================================

import os

from PySide6.QtCore import (
    Qt,
    QSettings,
    QTimer,
    Signal,
    QEvent,
    QElapsedTimer,
)

from PySide6.QtGui import (
    QPixmap,
    QIcon,
)

from language_manager import language_manager

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QListWidget,
    QStackedWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QMessageBox,
)

# ============================================================
# IMPORTS - КРАЙ


# ============================================================


# ============================================================


class TimerDialog(QDialog):
    """
    Диалог за избор на интервал за автоматично запазване.

    Минимум: 1 минута
    Максимум: 30 минути
    """

    def __init__(self, parent=None, current_minutes=5):
        super().__init__(parent)

        self.setWindowTitle("Автоматично запазване")

        self.setModal(True)

        self.setFixedWidth(500)

        self._focus_return_timer = QTimer(self)

        self._focus_return_timer.setSingleShot(True)

        self._focus_return_timer.setInterval(1000)

        self._focus_return_timer.timeout.connect(self._focus_ok_button)

        try:
            current_minutes = int(current_minutes)
        except (TypeError, ValueError):
            current_minutes = 5

        current_minutes = max(1, min(30, current_minutes))

        self._build_ui(current_minutes)

    def _build_ui(self, current_minutes):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(24, 22, 24, 20)

        main_layout.setSpacing(16)

        # =====================================================
        # ЗАГЛАВИЕ
        # =====================================================

        title = QLabel(language_manager.get("autosave_title"))

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 19px;
                font-weight: bold;
                background: transparent;
            }
            """)

        main_layout.addWidget(title)

        # =====================================================
        # ОПИСАНИЕ
        # =====================================================

        description = QLabel(language_manager.get("autosave_interval_description"))

        description.setWordWrap(True)

        description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 13px;
                background: transparent;
            }
            """)

        main_layout.addWidget(description)

        # =====================================================
        # ЦЕНТРИРАНО ПОЛЕ ЗА ВРЕМЕ
        # =====================================================

        time_frame = QFrame()

        time_frame.setStyleSheet("""
            QFrame {
                background: #202124;
                border: 2px solid #3A3A3A;
                border-radius: 10px;
            }
            """)

        time_layout = QHBoxLayout(time_frame)

        time_layout.setContentsMargins(18, 14, 18, 14)

        time_layout.setSpacing(10)

        time_label = QLabel(language_manager.get("autosave_next"))

        time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            """)

        time_layout.addWidget(time_label)

        # =====================================================
        # SPIN BOX
        # =====================================================

        self.minutes_spin = QSpinBox()

        self.minutes_spin.setRange(1, 30)

        self.minutes_spin.setValue(current_minutes)

        self.minutes_spin.setSuffix(language_manager.get("autosave_minutes"))

        self.minutes_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.minutes_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.minutes_spin.setMinimumWidth(70)

        self.minutes_spin.setStyleSheet("""
            QSpinBox {
                color: white;
                background: #2A2A2A;
                border: 2px solid #4CAF50;
                border-radius: 7px;
                padding: 7px;
                font-size: 15px;
                font-weight: bold;
            }

            QSpinBox:focus {
                border: 2px solid #7CFC00;
            }

            QSpinBox::up-button,
            QSpinBox::down-button {
                width: 22px;
                background: #343434;
                border: none;
            }

            QSpinBox::up-button:hover,
            QSpinBox::down-button:hover {
                background: #4CAF50;
            }
            """)

        self.minutes_spin.valueChanged.connect(self._timer_value_changed)

        time_layout.addWidget(
            self.minutes_spin,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        time_suffix_label = QLabel(language_manager.get("autosave_suffix"))

        time_suffix_label.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 13px;
                border: none;
                background: transparent;
            }
            """)

        time_layout.addWidget(
            time_suffix_label,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        main_layout.addWidget(time_frame, 0, Qt.AlignmentFlag.AlignCenter)

        # =====================================================
        # БУТОНИ
        # =====================================================

        buttons_frame = QFrame()

        buttons_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }

            QPushButton {
                min-width: 105px;
                min-height: 34px;
                padding: 5px 14px;
                border-radius: 7px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#okButton {
                background: #2E7D32;
                color: white;
                border: 2px solid #4CAF50;
            }

            QPushButton#okButton:hover {
                background: #388E3C;
            }

            QPushButton#cancelButton {
                background: #303134;
                color: white;
                border: 2px solid #555555;
            }

            QPushButton#cancelButton:hover {
                background: #3A3A3A;
            }
            """)

        buttons_layout = QHBoxLayout(buttons_frame)

        buttons_layout.setContentsMargins(0, 0, 0, 0)

        buttons_layout.setSpacing(12)

        self.ok_button = QPushButton("OK")

        self.ok_button.setObjectName("okButton")

        self.cancel_button = QPushButton("Отказ")

        self.cancel_button.setObjectName("cancelButton")

        self.ok_button.clicked.connect(self.accept)

        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addStretch()

        buttons_layout.addWidget(self.ok_button)

        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        main_layout.addWidget(buttons_frame)

        # =====================================================
        # НАЧАЛЕН ФОКУС
        # =====================================================

        self.ok_button.setFocus()

    def _timer_value_changed(self, value):

        self.minutes_spin.setFocus(Qt.FocusReason.OtherFocusReason)

        self._focus_return_timer.start()

    def _focus_ok_button(self):

        self.ok_button.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event):

        # Enter върху OK
        if (
            event.key()
            in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            )
            and self.ok_button.hasFocus()
        ):

            self.accept()

            return

        # Esc -> Отказ
        if event.key() == Qt.Key.Key_Escape:

            self.reject()

            return

        # Стрелки върху полето
        if (
            event.key()
            in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
            )
            and self.minutes_spin.hasFocus()
        ):

            super().keyPressEvent(event)

            self.minutes_spin.setFocus(Qt.FocusReason.OtherFocusReason)

            self._focus_return_timer.start()

            return

        super().keyPressEvent(event)


class SettingsDialog(QDialog):
    settings_changed = Signal()
    """
    Главен прозорец за настройките.
    """

    def __init__(self, parent=None):

        super().__init__(parent)

        self.settings = QSettings("MP3_Order", "MP3_Order_PRO")

        from themes import get_theme

        self.current_theme = get_theme(
            self.settings.value(
                "theme_name",
                "Лилаво-синя",
                type=str,
            )
        )

        self.setWindowTitle(language_manager.get("settings_title"))

        self.setMinimumSize(820, 540)

        self.resize(900, 600)

        self.setModal(False)

        self._build_ui()

        self.load_settings()
        self._setup_keyboard_navigation()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(14, 14, 14, 14)

        main_layout.setSpacing(12)

        # =====================================================
        # ЛЯВА СТРАНА
        # =====================================================

        self.left_frame = QFrame()

        self.left_frame.setFixedWidth(220)

        self.left_frame.setStyleSheet("""
            QFrame {
                background: #202124;
                border: 2px solid #303134;
                border-radius: 10px;
            }
            """)

        left_layout = QVBoxLayout(self.left_frame)

        left_layout.setContentsMargins(8, 8, 8, 8)

        self.settings_title = QLabel(language_manager.get("settings_title"))

        self.settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_title.setStyleSheet("""
            QLabel {
                color: #7CFC00;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                background: transparent;
                border: none;
            }
            """)

        left_layout.addWidget(self.settings_title)

        self.settings_list = QListWidget()

        self.settings_list.keyPressEvent = self._settings_list_key_press

        self.settings_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: white;
                outline: none;
                font-size: 14px;
            }

            QListWidget::item {
                padding: 12px 10px;
                border-radius: 7px;
                margin: 2px 0;
            }

            QListWidget::item:hover {
                background: #303134;
            }

            QListWidget::item:selected {
                background: #2E7D32;
                color: white;
                font-weight: bold;
            }

            QListWidget:focus {
                border: 2px solid #7CFC00;
                border-radius: 8px;
            }
            """)

        left_layout.addWidget(self.settings_list)

        main_layout.addWidget(self.left_frame)

        # =====================================================
        # ДЯСНА СТРАНА
        # =====================================================

        self.right_frame = QFrame()

        self.right_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
            """)

        right_layout = QVBoxLayout(self.right_frame)

        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.setSpacing(10)

        # =====================================================
        # СТРАНИЦИ
        # =====================================================

        self.pages = QStackedWidget()

        self.pages.setStyleSheet("""
            QStackedWidget {
                background: #202124;
                border: 2px solid #303134;
                border-radius: 10px;
            }
            """)

        right_layout.addWidget(self.pages, 1)

        # =====================================================
        # БУТОН "ЗАТВОРИ"
        # =====================================================

        close_button_layout = QHBoxLayout()

        close_button_layout.setContentsMargins(0, 0, 10, 0)

        close_button_layout.addStretch()

        self.close_settings_button = QPushButton(language_manager.get("close"))

        self.close_settings_button.setMinimumSize(95, 36)

        self.close_settings_button.setStyleSheet("""
            QPushButton {
                background: #303134;
                color: white;
                border: 2px solid #555555;
                border-radius: 7px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #3A3A3A;
                border-color: #4CAF50;
            }

            QPushButton:pressed {
                background: #252525;
            }

            QPushButton:focus {
                border: 2px solid #7CFC00;
                outline: none;
            }
            """)

        self.close_settings_button.clicked.connect(self.reject)

        close_button_layout.addWidget(self.close_settings_button)

        right_layout.addLayout(close_button_layout)

        main_layout.addWidget(self.right_frame, 1)

        # =====================================================
        # СТРАНИЦА 1 - ПЛАВЕН ПРЕХОД
        # =====================================================

        self.fade_page = QWidget()

        fade_layout = QVBoxLayout(self.fade_page)

        fade_layout.setContentsMargins(24, 24, 24, 24)

        self.fade_title = QLabel(language_manager.get("fade_title"))

        self.fade_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
            """)

        fade_layout.addWidget(self.fade_title)

        self.fade_description = QLabel(language_manager.get("fade_description"))

        self.fade_description.setWordWrap(True)

        self.fade_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
            """)

        fade_layout.addWidget(self.fade_description)

        fade_layout.addSpacing(20)

        self.fade_enabled = QCheckBox(language_manager.get("fade_enabled"))

        self.fade_enabled.toggled.connect(self._fade_enabled_changed)

        self.fade_enabled.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 20px;
                padding: 6px 8px;
                border: 2px solid transparent;
                border-radius: 7px;
            }

            QCheckBox:focus {
                border: 2px solid #7CFC00;
                background: #252525;
            }
            """)

        fade_layout.addWidget(self.fade_enabled)

        fade_layout.addStretch()

        self.settings_list.addItem(language_manager.get("fade"))

        self.pages.addWidget(self.fade_page)

        # =====================================================
        # СТРАНИЦА 2 - FADE ВРЕМЕ
        # =====================================================

        self.fade_time_page = QWidget()

        fade_time_layout = QVBoxLayout(self.fade_time_page)

        fade_time_layout.setContentsMargins(24, 24, 24, 24)

        self.fade_time_title = QLabel(language_manager.get("fade_time_title"))

        self.fade_time_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
            """)

        fade_time_layout.addWidget(self.fade_time_title)

        self.fade_time_description = QLabel(
            language_manager.get("fade_time_description")
        )

        self.fade_time_description.setWordWrap(True)

        self.fade_time_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
            """)

        fade_time_layout.addWidget(self.fade_time_description)

        fade_time_layout.addSpacing(20)

        fade_time_row = QHBoxLayout()

        self.fade_time_label = QLabel(language_manager.get("fade_duration"))

        self.fade_time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                background: transparent;
            }
            """)

        self.fade_duration = QSpinBox()

        self.fade_duration.setRange(1, 30)

        self.fade_duration.setSuffix(language_manager.get("seconds"))

        self.fade_duration.setValue(3)
        self.fade_duration.valueChanged.connect(self._fade_duration_changed)

        self.fade_duration.setMaximumWidth(150)

        fade_time_row.addWidget(self.fade_time_label)

        fade_time_row.addWidget(self.fade_duration)

        fade_time_row.addStretch()

        fade_time_layout.addLayout(fade_time_row)

        fade_time_layout.addStretch()

        self.settings_list.addItem("⏱️ Fade Time")

        self.pages.addWidget(self.fade_time_page)

        # =====================================================
        # СТРАНИЦА 3 - AUTO SAVE
        # =====================================================

        self.autosave_page = QWidget()

        autosave_layout = QVBoxLayout(self.autosave_page)

        autosave_layout.setContentsMargins(24, 24, 24, 24)

        self.autosave_title = QLabel(language_manager.get("autosave_title"))

        self.autosave_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
            """)

        autosave_layout.addWidget(self.autosave_title)

        self.autosave_description = QLabel(language_manager.get("autosave_description"))

        self.autosave_description.setWordWrap(True)

        self.autosave_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
            """)

        autosave_layout.addWidget(self.autosave_description)

        autosave_layout.addSpacing(24)

        self.autosave_enabled = QCheckBox("☐ " + language_manager.get("disabled"))

        self.autosave_enabled.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 20px;
                padding: 6px 8px;
                border: 2px solid transparent;
                border-radius: 7px;
            }

            QCheckBox:focus {
                border: 2px solid #7CFC00;
                background: #252525;
            }
            """)

        self.autosave_enabled.toggled.connect(self._autosave_enabled_changed)

        autosave_layout.addWidget(self.autosave_enabled)

        self.autosave_button = QPushButton(language_manager.get("autosave_button"))

        self.autosave_button.setMinimumHeight(36)

        self.autosave_button.clicked.connect(self._open_autosave_timer)

        autosave_layout.addWidget(self.autosave_button)

        autosave_layout.addStretch()

        self.settings_list.addItem(language_manager.get("autosave_title"))

        self.pages.addWidget(self.autosave_page)

        # =====================================================
        # СТРАНИЦА 4 - КРАЙ НА СПИСЪКА
        # =====================================================

        self.end_page = QWidget()
        end_layout = QVBoxLayout(self.end_page)

        end_layout.setContentsMargins(24, 24, 24, 24)

        self.end_title = QLabel(language_manager.get("end_title"))

        self.end_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
            """)

        end_layout.addWidget(self.end_title)

        self.end_description = QLabel(language_manager.get("end_description"))

        self.end_description.setWordWrap(True)

        self.end_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
            """)

        end_layout.addWidget(self.end_description)

        end_layout.addSpacing(22)

        self.end_behavior = QComboBox()

        self.end_behavior.addItems(
            [
                language_manager.get("end_stop"),
                language_manager.get("end_repeat"),
            ]
        )

        self.end_behavior.setMinimumHeight(34)

        self.end_behavior.currentIndexChanged.connect(self._end_behavior_changed)

        self.end_behavior.setStyleSheet("""
            QComboBox {
                color: white;
                background: #303134;
                border: 2px solid #555555;
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 14px;
            }

            QComboBox:focus {
                border: 2px solid #7CFC00;
                background: #2A2A2A;
            }

            QComboBox QAbstractItemView {
                background: #202124;
                color: white;
                selection-background-color: #2E7D32;
                selection-color: white;
            }
            """)

        end_layout.addWidget(self.end_behavior)

        end_layout.addStretch()

        self.settings_list.addItem(language_manager.get("end_list_title"))

        self.pages.addWidget(self.end_page)

        # =====================================================
        # СТРАНИЦА 5 - ЦВЕТОВА ТЕМА
        # =====================================================

        self.theme_page = QWidget()

        theme_layout = QVBoxLayout(self.theme_page)

        theme_layout.setContentsMargins(24, 24, 24, 24)

        self.theme_title = QLabel(language_manager.get("theme_title"))

        self.theme_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
            """)

        theme_layout.addWidget(self.theme_title)

        self.theme_description = QLabel(language_manager.get("theme_description"))

        self.theme_description.setWordWrap(True)

        self.theme_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
            """)

        theme_layout.addWidget(self.theme_description)

        theme_layout.addSpacing(22)

        self.theme_combo = QComboBox()

        self.theme_combo.addItems(
            [
                language_manager.get("theme_purple_blue"),
                language_manager.get("theme_blue"),
                language_manager.get("theme_green"),
                language_manager.get("theme_red"),
                language_manager.get("theme_orange"),
                language_manager.get("theme_classic"),
            ]
        )

        self.theme_combo.currentTextChanged.connect(self._theme_changed)

        self.theme_combo.setMinimumHeight(40)

        self.theme_combo.setStyleSheet("""
            QComboBox {
                color: white;
                background: #303134;
                border: 2px solid #555555;
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 16px;
            }

            QComboBox:focus {
                border: 2px solid #7CFC00;
                background: #2A2A2A;
            }

            QComboBox QAbstractItemView {
                background: #202124;
                color: white;
                selection-background-color: #2E7D32;
                selection-color: white;
            }
            """)

        theme_layout.addWidget(self.theme_combo)

        theme_layout.addStretch()

        self.settings_list.addItem(language_manager.get("theme_list_title"))

        self.pages.addWidget(self.theme_page)

        # =====================================================
        # СТРАНИЦА 6 - ЕЗИК
        # =====================================================

        self.language_page = QWidget()

        language_layout = QVBoxLayout(self.language_page)
        language_layout.setContentsMargins(24, 24, 24, 24)

        language_title = QLabel(language_manager.get("language_title"))

        language_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)

        language_layout.addWidget(language_title)

        language_description = QLabel(language_manager.get("language_description"))

        language_description.setWordWrap(True)

        language_description.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 20px;
                background: transparent;
            }
        """)

        language_layout.addWidget(language_description)

        language_layout.addSpacing(20)

        self.language_combo = QComboBox()

        self.language_combo.addItem(language_manager.get("bulgarian"), "bg")

        self.language_combo.addItem(language_manager.get("english"), "en")

        self.language_combo.setMinimumHeight(34)

        self.language_combo.setStyleSheet("""
            QComboBox {
                background: #202124;
                color: white;
                border: 2px solid #555555;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 16px;
            }

            QComboBox QAbstractItemView {
                background: #202124;
                color: white;
                selection-background-color: #2E7D32;
                selection-color: white;
            }
        """)

        language_layout.addWidget(self.language_combo)

        language_layout.addStretch()

        self.settings_list.addItem(language_manager.get("language_list_title"))

        self.pages.addWidget(self.language_page)

        # =====================================================
        # СИГНАЛ ЗА ПРОМЯНА НА ЕЗИКА
        # =====================================================

        self.language_combo.currentIndexChanged.connect(self._language_changed)

        # =====================================================
        # СИГНАЛИ
        # =====================================================

        self.settings_list.currentRowChanged.connect(self.pages.setCurrentIndex)

        self.settings_list.setCurrentRow(0)

        # =====================================================
        # СТИЛ НА БУТОНА AUTO SAVE
        # =====================================================

        self.autosave_button.setStyleSheet(f"""
            QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 14px;
            }}

            QPushButton:hover {{
                background: {self.current_theme["accent"]};
                border-color: {self.current_theme["accent"]};
            }}

            QPushButton:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                outline: none;
            }}
        """)

    # =========================================================
    # КЛАВИАТУРНА НАВИГАЦИЯ
    # =========================================================

    def _focus_first_control(self):

        current_index = self.pages.currentIndex()

        if current_index == 0:
            self.fade_enabled.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_index == 1:
            self.fade_duration.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_index == 2:
            self.autosave_enabled.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_index == 3:
            self.end_behavior.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_index == 4:
            self.theme_combo.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_index == 5:
            self.language_combo.setFocus(Qt.FocusReason.OtherFocusReason)
            return

    def _return_focus_to_settings(self):

        self.settings_list.setFocus(Qt.FocusReason.OtherFocusReason)

        current_item = self.settings_list.currentItem()

        if current_item is not None:
            self.settings_list.scrollToItem(current_item)

    def _navigate_right(self):

        if self.settings_list.hasFocus():
            self._focus_first_control()

    def _settings_list_key_press(self, event):

        if event.key() == Qt.Key.Key_Right:
            self._navigate_right()
            event.accept()
            return

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self._navigate_right()
            event.accept()
            return

        QListWidget.keyPressEvent(self.settings_list, event)

    def eventFilter(self, obj, event):

        if event.type() == QEvent.Type.KeyPress:

            right_controls = (
                self.fade_enabled,
                self.fade_duration,
                self.autosave_enabled,
                self.autosave_button,
                self.end_behavior,
                self.theme_combo,
                self.close_settings_button,
            )

            if obj in right_controls:

                if event.key() == Qt.Key.Key_Left:
                    self._return_focus_to_settings()
                    event.accept()
                    return True

                if obj is self.autosave_button and event.key() in (
                    Qt.Key.Key_Return,
                    Qt.Key.Key_Enter,
                ):
                    obj.click()
                    event.accept()
                    return True

                if obj is self.end_behavior and event.key() in (
                    Qt.Key.Key_Return,
                    Qt.Key.Key_Enter,
                ):
                    self.end_behavior.showPopup()
                    event.accept()
                    return True

                if obj is self.close_settings_button and event.key() in (
                    Qt.Key.Key_Return,
                    Qt.Key.Key_Enter,
                ):
                    self.reject()
                    event.accept()
                    return True

        return super().eventFilter(obj, event)

    def _setup_keyboard_navigation(self):

        right_controls = (
            self.fade_enabled,
            self.fade_duration,
            self.autosave_enabled,
            self.autosave_button,
            self.end_behavior,
            self.theme_combo,
            self.close_settings_button,
        )

        for widget in right_controls:
            widget.installEventFilter(self)

    # =========================================================
    # AUTO SAVE TIMER
    # =========================================================

    def _open_autosave_timer(self):

        current_value_raw = self.settings.value("autosave_minutes", "5")

        try:

            current_value = int(str(current_value_raw))

        except (TypeError, ValueError):

            current_value = 5

        current_value = max(1, min(30, current_value))

        dialog = TimerDialog(self, current_value)

        if dialog.exec() == QDialog.DialogCode.Accepted:

            minutes = dialog.minutes_spin.value()

            self.settings.setValue("autosave_minutes", str(minutes))

            self.settings.sync()
            self.settings_changed.emit()

            self.autosave_button.setText(
                language_manager.get("autosave_interval_short").format(minutes=minutes)
            )

            # =====================================================
            # ЗВУК ПРИ ЗАПАЗВАНЕ
            # =====================================================

            try:

                import winsound

                winsound.MessageBeep(winsound.MB_OK)

            except Exception:

                pass

            # =====================================================
            # ПРОЗОРЕЦ ЗА ПОТВЪРЖДЕНИЕ
            # =====================================================

            message_dialog = QDialog(self)

            message_dialog.setWindowIcon(
                QIcon(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "assets",
                        "MP3_Order_Logo.png",
                    )
                )
            )

            message_dialog.setWindowTitle(language_manager.get("autosave_title"))

            message_dialog.setFixedSize(500, 180)

            message_dialog.setStyleSheet("""
                QDialog {
                    background: #202124;
                }

                QLabel {
                    color: white;
                    background: transparent;
                }

                QPushButton {
                    min-width: 90px;
                    min-height: 32px;
                    background: #2E7D32;
                    color: white;
                    border: 2px solid #4CAF50;
                    border-radius: 7px;
                    padding: 5px 14px;
                    font-size: 13px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background: #388E3C;
                }
            """)

            main_layout = QVBoxLayout(message_dialog)

            main_layout.setContentsMargins(12, 12, 12, 12)

            main_layout.setSpacing(8)

            # =====================================================
            # ТЕКСТ
            # =====================================================

            text_layout = QVBoxLayout()

            text_layout.setContentsMargins(12, 12, 12, 12)

            text_layout.setSpacing(5)

            title_label = QLabel(language_manager.get("autosave_saved"))

            title_label.setWordWrap(True)

            title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    background: transparent;
                }
            """)

            interval_label = QLabel(
                language_manager.get("autosave_interval").format(minutes=minutes)
            )

            interval_label.setStyleSheet("""
                QLabel {
                    color: #BDBDBD;
                    font-size: 20px;
                    background: transparent;
                }
            """)

            text_layout.addWidget(title_label)

            text_layout.addWidget(interval_label)

            text_layout.addStretch()

            main_layout.addLayout(text_layout)

            # =====================================================
            # БУТОН OK
            # =====================================================

            ok_button = QPushButton("OK")

            ok_button.clicked.connect(message_dialog.accept)

            button_layout = QHBoxLayout()

            button_layout.addStretch()

            button_layout.addWidget(ok_button)

            main_layout.addLayout(button_layout)

            message_dialog.exec()

    # =========================================================
    # ЗАПАЗВАНЕ НА FADE НАСТРОЙКИТЕ
    # =========================================================

    def _fade_enabled_changed(self, enabled):

        self.settings.setValue("fade_enabled", bool(enabled))

        # =====================================================
        # ПРОМЕНЯМЕ ТЕКСТА НА ОТМЕТКАТА
        # =====================================================

        if enabled:

            self.fade_enabled.setText("✅ " + language_manager.get("enabled"))

        else:

            self.fade_enabled.setText("☐ " + language_manager.get("disabled"))

        self.settings.sync()

        # =====================================================
        # УВЕДОМЯВАМЕ MP3_ORDER ЗА ПРОМЯНАТА
        # =====================================================

        self.settings_changed.emit()

        # =====================================================
        # СЪОБЩЕНИЕ + ЗВУК
        # =====================================================

        try:

            import winsound

            winsound.MessageBeep(winsound.MB_OK)

        except Exception:

            pass

        # =====================================================
        # СЪОБЩЕНИЕ
        # =====================================================

        message_box = QMessageBox(self)

        message_box.setStyleSheet("QLabel { font-size: 20px; }")

        message_box.setWindowTitle(language_manager.get("fade"))

        if enabled:

            message_box.setText(language_manager.get("fade_on_message"))

        else:

            message_box.setText(language_manager.get("fade_off_message"))

        message_box.exec()

        # =====================================================
        # УВЕДОМЯВАМЕ MP3_ORDER
        # =====================================================

        self.settings_changed.emit()

        # =====================================================
        # УВЕДОМЯВАМЕ MP3_ORDER
        # =====================================================

        self.settings_changed.emit()

    def _fade_duration_changed(self, value):

        self.settings.setValue("fade_duration", int(value))

        self.settings.sync()

    def _autosave_enabled_changed(self, enabled):

        # =====================================================
        # ЗАПАЗВАМЕ НОВАТА СТОЙНОСТ
        # =====================================================

        self.settings.setValue("autosave_enabled", bool(enabled))

        self.settings.sync()

        # =====================================================
        # ПРОМЕНЯМЕ ТЕКСТА НА ОТМЕТКАТА
        # =====================================================

        if enabled:

            self.autosave_enabled.setText("✅ " + language_manager.get("enabled"))

        else:

            self.autosave_enabled.setText("☐ " + language_manager.get("disabled"))

        # =====================================================
        # ЗВУК
        # =====================================================

        try:

            import winsound

            winsound.MessageBeep(winsound.MB_OK)

        except Exception:

            pass

        # =====================================================
        # СЪОБЩЕНИЕ ЗА ВКЛЮЧВАНЕ / ИЗКЛЮЧВАНЕ
        # =====================================================

        message_box = QMessageBox(self)

        message_box.setStyleSheet("QLabel { font-size: 20px; }")

        message_box.setWindowTitle(language_manager.get("autosave_title"))

        if enabled:

            message_box.setText(language_manager.get("autosave_on_message"))

        else:

            message_box.setText(language_manager.get("autosave_off_message"))

        message_box.exec()

        # =====================================================
        # СЪОБЩЕНИЕ ЗА ЗАДЪЛЖИТЕЛЕН РЕСТАРТ
        # =====================================================

        restart_message_box = QMessageBox(self)

        restart_message_box.setStyleSheet("QLabel { font-size: 20px; }")

        restart_message_box.setWindowTitle(language_manager.get("autosave_title"))

        if language_manager.is_bulgarian():

            restart_message_box.setText(
                "Моля, рестартирайте програмата,\n\n"
                "за да се приложи промяната в "
                "автоматичното запазване."
            )

            restart_button_text = "Рестартирай"

        else:

            restart_message_box.setText(
                "Please restart the program,\n\n"
                "to apply the change to "
                "automatic saving."
            )

            restart_button_text = "Restart"

        restart_button = restart_message_box.addButton(
            restart_button_text, QMessageBox.ButtonRole.AcceptRole
        )

        # =====================================================
        # ПОКАЗВАМЕ ПРОЗОРЕЦА И ДАВАМЕ ЕДИН СИГНАЛ
        # =====================================================

        from PySide6.QtCore import QTimer

        QTimer.singleShot(
            100,
            lambda: (__import__("winsound").MessageBeep(__import__("winsound").MB_OK)),
        )

        restart_message_box.exec()

        # =====================================================
        # РЕСТАРТИРАНЕ
        # =====================================================

        if restart_message_box.clickedButton() == restart_button:

            import sys
            import subprocess
            import os

            # =================================================
            # ОПРЕДЕЛЯМЕ КАКВО ДА СТАРТИРАМЕ
            # =================================================

            if getattr(sys, "frozen", False):

                restart_directory = os.path.dirname(sys.executable)

                launcher_exe = os.path.join(
                    restart_directory,
                    "launcher.exe",
                )

                if os.path.isfile(launcher_exe):

                    restart_command = [
                        launcher_exe,
                    ]

                else:

                    restart_command = [
                        sys.executable,
                    ]

            else:

                restart_command = [
                    sys.executable,
                    *sys.argv,
                ]

                restart_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

                restart_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

            # =================================================
            # НОВ НЕЗАВИСИМ PYINSTALLER ПРОЦЕС
            # =================================================

            restart_environment = os.environ.copy()

            restart_environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

            subprocess.Popen(
                restart_command,
                cwd=restart_directory,
                env=restart_environment,
                creationflags=(
                    subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                ),
            )

            # =================================================
            # ЗАТВАРЯМЕ ТЕКУЩИЯ ПРОЦЕС
            # =================================================

            app = QApplication.instance()

            if app is not None:

                app.quit()

    # =========================================================
    # ЗАПАЗВАНЕ НА НАСТРОЙКАТА "КРАЙ НА СПИСЪКА"
    # =========================================================

    def _end_behavior_changed(self, index):

        self.settings.setValue("end_behavior", int(index))

        self.settings.sync()

        # =====================================================
        # УВЕДОМЯВАМЕ MP3_ORDER ЗА ПРОМЯНАТА
        # =====================================================

        self.settings_changed.emit()

    # =====================================================
    # ЗАПАЗВАНЕ НА ЕЗИКА
    # =====================================================

    def _language_changed(self, index):

        language_code = self.language_combo.itemData(index)

        if not language_code:

            return

        old_language = language_manager.get_language()

        if language_code == old_language:

            return

        language_manager.set_language(language_code)

        if self.fade_enabled.isChecked():

            self.fade_enabled.setText("✅ " + language_manager.get("enabled"))

        else:

            self.fade_enabled.setText("☐ " + language_manager.get("disabled"))

        self.settings.sync()

        # =====================================================
        # ЗВУК
        # =====================================================

        try:

            import winsound

            winsound.MessageBeep(winsound.MB_OK)

        except Exception:

            pass

        # =====================================================
        # СЪОБЩЕНИЕ ЗА РЕСТАРТ
        # =====================================================

        message_box = QMessageBox(self)

        message_box.setStandardButtons(QMessageBox.StandardButton.NoButton)

        message_box.setWindowFlag(
            Qt.WindowType.WindowCloseButtonHint,
            False,
        )

        message_box.setStyleSheet("QLabel { font-size: 20px; }")

        message_box.setWindowTitle(language_manager.get("autosave_title"))

        message_box.setText(language_manager.get("autosave_restart_message"))

        restart_button = message_box.addButton(
            language_manager.get("restart"),
            QMessageBox.ButtonRole.AcceptRole,
        )

        message_box.setDefaultButton(restart_button)

        message_box.setEscapeButton(restart_button)

        restart_button.setFocus()

        def block_close(event):

            event.ignore()

        message_box.closeEvent = block_close

        message_box.exec()

        # =====================================================
        # РЕСТАРТИРАНЕ
        # =====================================================

        if message_box.clickedButton() == restart_button:

            import sys
            import subprocess
            import os

            # =================================================
            # ОПРЕДЕЛЯМЕ КАКВО ДА СТАРТИРАМЕ
            # =================================================

            if getattr(sys, "frozen", False):

                restart_directory = os.path.dirname(sys.executable)

                launcher_exe = os.path.join(
                    restart_directory,
                    "launcher.exe",
                )

                if os.path.isfile(launcher_exe):

                    restart_command = [
                        launcher_exe,
                    ]

                else:

                    restart_command = [
                        sys.executable,
                    ]

            else:

                restart_command = [
                    sys.executable,
                    *sys.argv,
                ]

                restart_directory = os.path.dirname(
                    os.path.abspath(sys.argv[0])
                )

            # =================================================
            # НОВ НЕЗАВИСИМ PYINSTALLER ПРОЦЕС
            # =================================================

            restart_environment = os.environ.copy()

            restart_environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

            subprocess.Popen(
                restart_command,
                cwd=restart_directory,
                env=restart_environment,
                creationflags=(
                    subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                ),
            )

            # =================================================
            # ЗАТВАРЯМЕ ТЕКУЩИЯ ПРОЦЕС
            # =================================================

            app = QApplication.instance()

            if app is not None:

                app.quit()

    # =========================================================
    # ЗАПАЗВАНЕ НА ЦВЕТОВАТА ТЕМА
    # =========================================================

    def _theme_changed(self, theme_name):

        from themes import set_theme, get_theme

        self.settings.setValue(
            "theme_name",
            theme_name,
        )

        self.settings.sync()

        if not set_theme(theme_name):

            theme_name = "Лилаво-синя"

        self.current_theme = get_theme(theme_name)

        # =====================================================
        # ЛЯВА СТРАНА
        # =====================================================

        self.left_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.current_theme["panel_bg"]};
                border: 2px solid {self.current_theme["accent"]};
                border-radius: 10px;
            }}
        """)

        self.settings_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                background: transparent;
                border: none;
            }}
        """)

        self.settings_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {self.current_theme["main_text"]};
                outline: none;
                font-size: 14px;
            }}

            QListWidget::item {{
                padding: 12px 10px;
                border-radius: 7px;
                margin: 2px 0;
            }}

            QListWidget::item:hover {{
                background: {self.current_theme["panel_bg_2"]};
            }}

            QListWidget::item:selected {{
                background: {self.current_theme["accent"]};
                color: {self.current_theme["main_text"]};
                font-weight: bold;
            }}

            QListWidget:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                border-radius: 8px;
            }}
        """)

        # =====================================================
        # ДЯСНА СТРАНА
        # =====================================================

        self.pages.setStyleSheet(f"""
            QStackedWidget {{
                background: {self.current_theme["panel_bg"]};
                border: 2px solid {self.current_theme["accent"]};
                border-radius: 10px;
            }}
        """)

        self.right_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        # =====================================================
        # БУТОН "ЗАТВОРИ"
        # =====================================================

        self.close_settings_button.setStyleSheet(f"""
            QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background: {self.current_theme["accent"]};
                border-color: {self.current_theme["accent"]};
            }}

            QPushButton:pressed {{
                background: {self.current_theme["button_bg"]};
            }}

            QPushButton:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                outline: none;
            }}
        """)

        # =====================================================
        # СТРАНИЦА 1
        # =====================================================

        self.fade_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)

        self.fade_description.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.fade_enabled.setStyleSheet(f"""
            QCheckBox {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                padding: 6px 8px;
                border: 2px solid transparent;
                border-radius: 7px;
            }}

            QCheckBox:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                background: {self.current_theme["panel_bg_2"]};
            }}
        """)

        # =====================================================
        # СТРАНИЦА 2
        # =====================================================

        self.fade_time_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)

        self.fade_time_description.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.fade_time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.fade_duration.setStyleSheet(f"""
            QSpinBox {{
                color: {self.current_theme["main_text"]};
                background: {self.current_theme["button_bg"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 5px 8px;
                font-size: 16px;
            }}

            QSpinBox:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
            }}
        """)

        # =====================================================
        # СТРАНИЦА 3
        # =====================================================

        self.autosave_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)

        self.autosave_description.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.autosave_enabled.setStyleSheet(f"""
            QCheckBox {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                padding: 6px 8px;
                border: 2px solid transparent;
                border-radius: 7px;
            }}

            QCheckBox:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                background: {self.current_theme["panel_bg_2"]};
            }}
        """)

        self.autosave_button.setStyleSheet(f"""
            QPushButton {{
                background: {self.current_theme["button_bg"]};
                color: {self.current_theme["main_text"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 14px;
            }}

            QPushButton:hover {{
                background: {self.current_theme["accent"]};
                border-color: {self.current_theme["accent"]};
            }}

            QPushButton:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                outline: none;
            }}
        """)

        # =====================================================
        # СТРАНИЦА 4
        # =====================================================

        self.end_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)

        self.end_description.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.end_behavior.setStyleSheet(f"""
            QComboBox {{
                color: {self.current_theme["main_text"]};
                background: {self.current_theme["button_bg"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 14px;
            }}

            QComboBox:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                background: {self.current_theme["panel_bg_2"]};
            }}

            QComboBox QAbstractItemView {{
                background: {self.current_theme["panel_bg"]};
                color: {self.current_theme["main_text"]};
                selection-background-color: {self.current_theme["accent"]};
                selection-color: {self.current_theme["main_text"]};
            }}
        """)

        # =====================================================
        # СТРАНИЦА 5
        # =====================================================

        self.theme_title.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["main_text"]};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)

        self.theme_description.setStyleSheet(f"""
            QLabel {{
                color: {self.current_theme["accent_light"]};
                font-size: 20px;
                background: transparent;
            }}
        """)

        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                color: {self.current_theme["main_text"]};
                background: {self.current_theme["button_bg"]};
                border: 2px solid {self.current_theme["button_border"]};
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 16px;
            }}

            QComboBox:focus {{
                border: 2px solid {self.current_theme["accent_light"]};
                background: {self.current_theme["panel_bg_2"]};
            }}

            QComboBox QAbstractItemView {{
                background: {self.current_theme["panel_bg"]};
                color: {self.current_theme["main_text"]};
                selection-background-color: {self.current_theme["accent"]};
                selection-color: {self.current_theme["main_text"]};
            }}
        """)

        # =====================================================
        # ПРОЗОРЕЦ НАСТРОЙКИ
        # =====================================================

        self.setStyleSheet(f"""
            QDialog {{
                background: {self.current_theme["window_bg"]};
                color: {self.current_theme["main_text"]};
            }}
        """)

        self.settings_changed.emit()

    # =========================================================
    # ЗАРЕЖДАНЕ НА НАСТРОЙКИТЕ
    # =========================================================

    def load_settings(self):

        fade_enabled_raw = self.settings.value("fade_enabled", False)

        fade_enabled = (
            fade_enabled_raw
            if isinstance(fade_enabled_raw, bool)
            else str(fade_enabled_raw).lower()
            in (
                "true",
                "1",
                "yes",
                "on",
            )
        )

        fade_duration_text = self.settings.value("fade_duration", "3", type=str)

        try:

            fade_duration = int(str(fade_duration_text))

        except (
            TypeError,
            ValueError,
        ):

            fade_duration = 3

        fade_duration = max(1, min(30, fade_duration))

        auto_dj_enabled_raw = self.settings.value("auto_dj_enabled", False)

        auto_dj_enabled = (
            auto_dj_enabled_raw
            if isinstance(auto_dj_enabled_raw, bool)
            else str(auto_dj_enabled_raw).lower()
            in (
                "true",
                "1",
                "yes",
                "on",
            )
        )

        autosave_enabled_raw = self.settings.value("autosave_enabled", False)

        autosave_enabled = (
            autosave_enabled_raw
            if isinstance(autosave_enabled_raw, bool)
            else str(autosave_enabled_raw).lower()
            in (
                "true",
                "1",
                "yes",
                "on",
            )
        )

        autosave_minutes_text = self.settings.value("autosave_minutes", "5", type=str)

        try:

            autosave_minutes = int(str(autosave_minutes_text))

        except (
            TypeError,
            ValueError,
        ):

            autosave_minutes = 5

        autosave_minutes = max(1, min(30, autosave_minutes))

        end_behavior_text = self.settings.value("end_behavior", "0", type=str)

        try:

            end_behavior = int(str(end_behavior_text))

        except (
            TypeError,
            ValueError,
        ):

            end_behavior = 0

        end_behavior = max(0, min(1, end_behavior))

        # =====================================================
        # ЦВЕТОВА ТЕМА
        # =====================================================

        theme_name = self.settings.value(
            "theme_name",
            "Лилаво-синя",
            type=str,
        )

        if theme_name not in (
            "Лилаво-синя",
            "Синя",
            "Зелена",
            "Червена",
            "Оранжева",
            "Класическа",
        ):

            theme_name = "Лилаво-синя"

            # =====================================================
            # ЗАРЕЖДАМЕ СТАРАТА СТОЙНОСТ БЕЗ ДА ЗАДЕЙСТВАМЕ
            # SIGNAL-а toggled
            # =====================================================

            # =====================================================
            # ПЛАВЕН ПРЕХОД
            # =====================================================

            previous_fade_state = self.fade_enabled.blockSignals(True)

            self.fade_enabled.setChecked(fade_enabled)

            self.fade_enabled.blockSignals(previous_fade_state)

            if fade_enabled:

                self.fade_enabled.setText("✅ " + language_manager.get("enabled"))

            else:

                self.fade_enabled.setText("☐ " + language_manager.get("disabled"))

        # =====================================================
        # AUTO SAVE
        # =====================================================

        previous_autosave_state = self.autosave_enabled.blockSignals(True)

        self.autosave_enabled.setChecked(autosave_enabled)

        self.autosave_enabled.blockSignals(previous_autosave_state)

        if autosave_enabled:

            self.autosave_enabled.setText("✅ " + language_manager.get("enabled"))

        else:

            self.autosave_enabled.setText("☐ " + language_manager.get("disabled"))

        # =====================================================
        # ОСТАНАЛИТЕ НАСТРОЙКИ
        # =====================================================

        self.fade_duration.setValue(fade_duration)

        self.autosave_button.setText(
            language_manager.get("autosave_interval_short").format(
                minutes=autosave_minutes
            )
        )

        self.end_behavior.setCurrentIndex(end_behavior)

        # =====================================================
        # ЗАРЕЖДАНЕ НА ЦВЕТОВАТА ТЕМА
        # =====================================================

        theme_index = self.theme_combo.findText(theme_name)

        if theme_index >= 0:

            previous_theme_state = self.theme_combo.blockSignals(True)

            self.theme_combo.setCurrentIndex(theme_index)

            self.theme_combo.blockSignals(previous_theme_state)

        # =====================================================
        # ЗАРЕЖДАНЕ НА ЕЗИКА
        # =====================================================

        language_code = language_manager.get_language()

        language_index = self.language_combo.findData(language_code)

        if language_index >= 0:

            previous_language_state = self.language_combo.blockSignals(True)

            self.language_combo.setCurrentIndex(language_index)

            self.language_combo.blockSignals(previous_language_state)


# ============================================================
# КРАЙ НА SETTINGS
# ============================================================
