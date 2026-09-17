from PySide6.QtCore import QObject, QEvent, Qt, QTimer

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QTableWidget,
    QComboBox,
    QCheckBox,
    QSlider,
    QProgressBar,
)

from language_manager import language_manager


class AccessibilityManager(QObject):
    """
    Централна система за достъпност на MP3_Order.

    Не използва собствен TTS.
    Подготвя интерфейса така, че screen reader като JAWS
    да получава ясни имена, описания, стойности и състояния.
    """

    def __init__(self, window):

        super().__init__(window)

        self.window = window

        self._last_announcement = ""

        app = QApplication.instance()

        if app is not None:

            app.installEventFilter(self)

        self.prepare_window()

    # =========================================================
    # ОСНОВНА НАСТРОЙКА
    # =========================================================

    def prepare_window(self):

        self.window.setAccessibleName("MP3 Order PRO")

        self.window.setAccessibleDescription(
            "Програма за управление, възпроизвеждане " "и подреждане на MP3 песни."
        )

    # =========================================================
    # РЕГИСТРИРАНЕ НА КОНТРОЛ
    # =========================================================

    def register(
        self,
        widget,
        name=None,
        description=None,
    ):

        if widget is None:
            return

        if name is not None:

            widget.setAccessibleName(str(name))

        if description is not None:

            widget.setAccessibleDescription(str(description))

    # =========================================================
    # ДОСТЪПНО ИМЕ
    # =========================================================

    def set_name(
        self,
        widget,
        name,
    ):

        if widget is None:
            return

        widget.setAccessibleName(str(name))

    # =========================================================
    # ДОСТЪПНО ОПИСАНИЕ
    # =========================================================

    def set_description(
        self,
        widget,
        description,
    ):

        if widget is None:
            return

        widget.setAccessibleDescription(str(description))

    # =========================================================
    # ДИНАМИЧНО СЪОБЩЕНИЕ
    # =========================================================

    def announce(
        self,
        text,
        delay=80,
    ):

        text = str(text).strip()

        if not text:
            return

        if text == self._last_announcement:
            return

        self._last_announcement = text

        self.window.setAccessibleDescription(text)

        QTimer.singleShot(
            delay,
            self._clear_announcement,
        )

    def _clear_announcement(self):

        self.window.setAccessibleDescription(
            "MP3 Order PRO - програма за управление на MP3 песни."
        )

    # =========================================================
    # БУТОН
    # =========================================================

    def setup_button(
        self,
        button,
        name=None,
        description=None,
    ):

        if button is None:
            return

        if name is None:

            name = button.text().strip()

        if description is None:

            description = f"Бутон: {name}"

        self.register(
            button,
            name,
            description,
        )

        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # =========================================================

    # ТЪРСАЧКА
    # =========================================================

    def setup_search(
        self,
        edit,
        name="Търсене на песни",
        description=(
            "Поле за търсене. " "Въведете номер, име на песен " "или име на изпълнител."
        ),
    ):

        if edit is None:
            return

        self.register(
            edit,
            name,
            description,
        )

        edit.setPlaceholderText("🔍 " + language_manager.get("search_placeholder"))

    # =========================================================
    # ТАБЛИЦА
    # =========================================================

    def setup_table(
        self,
        table,
    ):

        if table is None:
            return

        self.register(
            table,
            "Списък с песни",
            ("Таблица с песни. " "Колони: номер, песен, изпълнител и време."),
        )

        table.currentCellChanged.connect(
            lambda row, column, previous_row, previous_column: self._table_changed(
                table,
                row,
                column,
            )
        )

    def _table_changed(
        self,
        table,
        row,
        column,
    ):

        if row < 0:
            return

        if column < 0:
            column = 1

        item = table.item(
            row,
            column,
        )

        if item is None:
            return

        song_number = row + 1

        title_item = table.item(
            row,
            1,
        )

        artist_item = table.item(
            row,
            2,
        )

        duration_item = table.item(
            row,
            3,
        )

        title = title_item.text().strip() if title_item is not None else ""

        artist = artist_item.text().strip() if artist_item is not None else ""

        duration = duration_item.text().strip() if duration_item is not None else ""

        parts = [
            f"Ред {song_number}",
        ]

        if title:

            parts.append(f"Песен: {title}")

        if artist:

            parts.append(f"Изпълнител: {artist}")

        if duration:

            parts.append(f"Време: {duration}")

        text = ", ".join(parts)

        table.setAccessibleDescription(text)

    # =========================================================
    # ПРОГРЕС ЛЕНТА
    # =========================================================

    def setup_progress(
        self,
        progress,
        name="Прогрес",
        description="Лента за прогрес на операцията.",
    ):

        if progress is None:
            return

        self.register(
            progress,
            name,
            description,
        )

        progress.valueChanged.connect(
            lambda value: self._progress_changed(
                progress,
                value,
            )
        )

    def _progress_changed(
        self,
        progress,
        value,
    ):

        maximum = progress.maximum()

        if maximum <= 0:
            return

        percent = int((value / maximum) * 100)

        progress.setAccessibleDescription(f"Прогрес: {percent} процента.")

    # =========================================================
    # CHECKBOX
    # =========================================================

    def setup_checkbox(
        self,
        checkbox,
        name=None,
        description=None,
    ):

        if checkbox is None:
            return

        if name is None:

            name = checkbox.text().strip()

        if description is None:

            description = f"Настройка: {name}"

        self.register(
            checkbox,
            name,
            description,
        )

        checkbox.toggled.connect(
            lambda checked: self._checkbox_changed(
                checkbox,
                checked,
            )
        )

    def _checkbox_changed(
        self,
        checkbox,
        checked,
    ):

        name = checkbox.accessibleName()

        state = "включено" if checked else "изключено"

        checkbox.setAccessibleDescription(f"{name}: {state}.")

    # =========================================================
    # SLIDER
    # =========================================================

    def setup_slider(
        self,
        slider,
        name="Позиция",
        description="Плъзгач за позицията на песента.",
    ):

        if slider is None:
            return

        self.register(
            slider,
            name,
            description,
        )

        slider.valueChanged.connect(
            lambda value: slider.setAccessibleDescription(f"{name}: {value}")
        )

    # =========================================================
    # COMBOBOX
    # =========================================================

    def setup_combobox(
        self,
        combo,
        name=None,
        description=None,
    ):

        if combo is None:
            return

        if name is None:

            name = combo.currentText().strip()

        if description is None:

            description = f"Избор: {name}"

        self.register(
            combo,
            name,
            description,
        )

        combo.currentTextChanged.connect(
            lambda text: combo.setAccessibleDescription(f"{name}: избрано {text}")
        )

    # =========================================================
    # LABEL
    # =========================================================

    def setup_label(
        self,
        label,
        name=None,
    ):

        if label is None:
            return

        if name is None:

            name = label.text().strip()

        self.register(
            label,
            name,
            name,
        )

    # =========================================================
    # ФОКУС
    # =========================================================

    def focus(
        self,
        widget,
    ):

        if widget is None:
            return

        widget.setFocus(Qt.FocusReason.OtherFocusReason)

    # =========================================================
    # EVENT FILTER
    # =========================================================

    def eventFilter(
        self,
        obj,
        event,
    ):

        if event.type() == QEvent.Type.FocusIn:

            if isinstance(
                obj,
                QWidget,
            ):

                name = obj.accessibleName()

                description = obj.accessibleDescription()

                if name:

                    if not description:

                        obj.setAccessibleDescription(name)

        return False
