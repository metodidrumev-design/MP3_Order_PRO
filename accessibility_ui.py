from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QLineEdit,
    QTableWidget,
    QProgressBar,
    QMenuBar,
    QMenu,
    QSlider,
    QLabel,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
)

from accessibility import AccessibilityManager


class AccessibilityUI(QObject):
    """
    Разширен accessibility слой за MP3_Order.

    Не използва собствен TTS.
    Не променя основната логика на програмата.
    Подготвя основния прозорец и AudioSplitter
    за screen reader като JAWS.
    """

    def __init__(self, window):

        super().__init__(window)

        self.window = window

        self.accessibility: AccessibilityManager = window.accessibility

        self._splitter_configured = False

        self.state_timer = QTimer(self)

        self.state_timer.setInterval(500)

        self.state_timer.timeout.connect(self.update_dynamic_state)

        self.state_timer.start()

    # =========================================================
    # ОСНОВНО СВЪРЗВАНЕ
    # =========================================================

    def setup(self):

        self.setup_search()

        self.setup_table()

        self.setup_progress()

        self.setup_buttons()

        self.setup_menus()

        self.setup_playback()

        self.setup_labels()

        self.setup_other_controls()

        self.setup_keyboard_commands()

        self.setup_audio_splitter()

    # =========================================================
    # ТЪРСАЧКА
    # =========================================================

    def setup_search(self):

        search_edit = getattr(
            self.window,
            "search_edit",
            None,
        )

        if isinstance(search_edit, QLineEdit):

            self.accessibility.setup_search(
                search_edit,
                "Търсене на песни",
                (
                    "Поле за търсене. "
                    "Въведете номер, име на песен "
                    "или име на изпълнител. "
                    "Натиснете Enter за възпроизвеждане."
                ),
            )

        search_button = getattr(
            self.window,
            "search_button",
            None,
        )

        if isinstance(search_button, QPushButton):

            self.accessibility.setup_button(
                search_button,
                "Търси",
                "Стартира търсене на песен.",
            )

    # =========================================================
    # ТАБЛИЦА
    # =========================================================

    def setup_table(self):

        table = getattr(
            self.window,
            "table",
            None,
        )

        if not isinstance(
            table,
            QTableWidget,
        ):

            return

        self.accessibility.setup_table(table)

        table.setAccessibleName("Списък с песни")

        table.setAccessibleDescription(
            "Таблица с песни. "
            "Колони: номер, песен, изпълнител и време. "
            "Използвайте стрелките за навигация."
        )

    # =========================================================
    # ПРОГРЕС НА ОСНОВНИЯ ПРОЗОРЕЦ
    # =========================================================

    def setup_progress(self):

        progress = getattr(
            self.window,
            "loading_progress",
            None,
        )

        if isinstance(
            progress,
            QProgressBar,
        ):

            self.accessibility.setup_progress(
                progress,
                "Прогрес на зареждането",
                ("Показва напредъка при " "зареждане на проект или песни."),
            )

    # =========================================================
    # ОСНОВНИ БУТОНИ
    # =========================================================

    def setup_buttons(self):

        buttons = self.window.findChildren(QPushButton)

        for button in buttons:

            text = button.text().strip()

            object_name = button.objectName().strip()

            if "Добави песни" in text:

                self.accessibility.setup_button(
                    button,
                    "Добави песни",
                    "Добавя MP3 песни към списъка.",
                )

            elif "Добави папка" in text:

                self.accessibility.setup_button(
                    button,
                    "Добави папка",
                    "Добавя MP3 песни от избрана папка.",
                )

            elif "Нагоре" in text:

                self.accessibility.setup_button(
                    button,
                    "Нагоре",
                    "Премества избраната песен нагоре.",
                )

            elif "Надолу" in text:

                self.accessibility.setup_button(
                    button,
                    "Надолу",
                    "Премества избраната песен надолу.",
                )

            elif "Премахни" in text:

                self.accessibility.setup_button(
                    button,
                    "Премахни",
                    "Премахва избраните песни от списъка.",
                )

            elif "Провери реда" in text:

                self.accessibility.setup_button(
                    button,
                    "Провери реда",
                    "Показва проверка на реда за Nero.",
                )

            elif "Автоматично разделяне" in text:

                self.accessibility.setup_button(
                    button,
                    "Автоматично разделяне",
                    ("Автоматично разделя " "информацията за изпълнител " "и песен."),
                )

            elif "Поправи ID3" in text:

                self.accessibility.setup_button(
                    button,
                    "Поправи ID3",
                    "Редактира ID3 информацията на песента.",
                )

            elif "Export за Nero" in text:

                self.accessibility.setup_button(
                    button,
                    "Export за Nero",
                    "Експортира MP3 файловете за Nero.",
                )

            elif object_name == "previousButton":

                self.accessibility.setup_button(
                    button,
                    "Предишна песен",
                    "Пуска предишната песен.",
                )

            elif object_name == "playButton":

                self.accessibility.setup_button(
                    button,
                    "Пусни песента",
                    "Започва възпроизвеждане на песента.",
                )

            elif object_name == "pauseButton":

                self.accessibility.setup_button(
                    button,
                    "Пауза или продължи",
                    ("Поставя песента на пауза " "или продължава възпроизвеждането."),
                )

            elif object_name == "stopButton":

                self.accessibility.setup_button(
                    button,
                    "Спри песента",
                    "Спира възпроизвеждането.",
                )

            elif object_name == "nextButton":

                self.accessibility.setup_button(
                    button,
                    "Следваща песен",
                    "Пуска следващата песен.",
                )

    # =========================================================
    # МЕНЮТА
    # =========================================================

    def setup_menus(self):

        menu_bar = getattr(
            self.window,
            "menu_bar",
            None,
        )

        if isinstance(
            menu_bar,
            QMenuBar,
        ):

            self.accessibility.register(
                menu_bar,
                "Главно меню",
                (
                    "Главно меню на MP3 Order. "
                    "Команди за проект, настройки "
                    "и разделяне на MP3."
                ),
            )

        menus = self.window.findChildren(QMenu)

        for menu in menus:

            title = menu.title().strip()

            if not title:
                continue

            self.accessibility.register(
                menu,
                title,
                f"Меню {title}.",
            )

    # =========================================================
    # PLAYBACK
    # =========================================================

    def setup_playback(self):

        progress_slider = getattr(
            self.window,
            "progress_slider",
            None,
        )

        if isinstance(
            progress_slider,
            QSlider,
        ):

            self.accessibility.setup_slider(
                progress_slider,
                "Позиция на песента",
                ("Плъзгач за позицията " "на текущо възпроизвежданата песен."),
            )

        current_time = getattr(
            self.window,
            "current_time_label",
            None,
        )

        if isinstance(
            current_time,
            QLabel,
        ):

            self.accessibility.setup_label(
                current_time,
                "Изминало време",
            )

        remaining_time = getattr(
            self.window,
            "remaining_time_label",
            None,
        )

        if isinstance(
            remaining_time,
            QLabel,
        ):

            self.accessibility.setup_label(
                remaining_time,
                "Оставащо време",
            )

    # =========================================================
    # LABELS
    # =========================================================

    def setup_labels(self):

        labels = {
            "now_playing_label": "Сега свири",
            "now_playing_title": "Сега свири",
            "save_status_label": "Статус на запазването",
            "loading_label": "Статус на зареждането",
        }

        for attribute_name, accessible_name in labels.items():

            label = getattr(
                self.window,
                attribute_name,
                None,
            )

            if isinstance(
                label,
                QLabel,
            ):

                self.accessibility.setup_label(
                    label,
                    accessible_name,
                )

    # =========================================================
    # ДРУГИ КОНТРОЛИ
    # =========================================================

    def setup_other_controls(self):

        checkboxes = self.window.findChildren(QCheckBox)

        for checkbox in checkboxes:

            text = checkbox.text().strip()

            if text:

                self.accessibility.setup_checkbox(
                    checkbox,
                    text,
                    f"Настройка: {text}.",
                )

        combos = self.window.findChildren(QComboBox)

        for combo in combos:

            text = combo.currentText().strip()

            self.accessibility.setup_combobox(
                combo,
                text or "Избор",
                "Избор на настройка.",
            )

    # =========================================================
    # КЛАВИШНИ КОМАНДИ
    # =========================================================

    def setup_keyboard_commands(self):

        self.window.setAccessibleDescription(
            (
                "Клавишни команди: "
                "Ctrl+F търсене. "
                "Enter възпроизвеждане. "
                "F3 избор на песен. "
                "F5 обновяване. "
                "Ctrl+S записване. "
                "Ctrl+Z отмяна. "
                "Delete изтриване. "
                "Ctrl+Нагоре и Ctrl+Надолу "
                "за подреждане. "
                "Стрелки наляво и надясно "
                "за превъртане."
            )
        )

    # =========================================================
    # AUDIO SPLITTER
    # =========================================================

    def setup_audio_splitter(self):

        splitter = getattr(
            self.window,
            "audio_splitter",
            None,
        )

        if splitter is None:
            return

        if not hasattr(
            splitter,
            "findChildren",
        ):

            return

        # -----------------------------------------------------
        # ОСНОВЕН ПРОЗОРЕЦ
        # -----------------------------------------------------

        splitter.setAccessibleName("Разделяне на MP3")

        splitter.setAccessibleDescription(
            ("Прозорец за анализ и разделяне " "на MP3 файл на отделни песни.")
        )

        # -----------------------------------------------------
        # БУТОНИ
        # -----------------------------------------------------

        for button in splitter.findChildren(QPushButton):

            text = button.text().strip()

            if not text:
                continue

            if "Анализирай" in text:

                self.accessibility.setup_button(
                    button,
                    "Анализирай и намери песните",
                    ("Анализира MP3 файла и " "намира границите между песните."),
                )

            elif "Раздели" in text:

                self.accessibility.setup_button(
                    button,
                    "Раздели",
                    ("Разделя MP3 файла " "на отделни песни."),
                )

            else:

                self.accessibility.setup_button(
                    button,
                    text,
                    f"Бутон: {text}.",
                )

        # -----------------------------------------------------
        # PROGRESS
        # -----------------------------------------------------

        for progress in splitter.findChildren(QProgressBar):

            self.accessibility.setup_progress(
                progress,
                "Прогрес на разделянето",
                ("Показва напредъка на " "операцията по разделяне."),
            )

        # -----------------------------------------------------
        # ТАБЛИЦИ
        # -----------------------------------------------------

        for table in splitter.findChildren(QTableWidget):

            self.accessibility.setup_table(table)

            table.setAccessibleName("Резултати от анализа")

            table.setAccessibleDescription(
                ("Таблица с намерените " "песни и техните граници.")
            )

        # -----------------------------------------------------
        # INPUT ПОЛЕТА
        # -----------------------------------------------------

        for edit in splitter.findChildren(QLineEdit):

            if not edit.accessibleName():

                self.accessibility.setup_search(
                    edit,
                    "Поле в разделянето на MP3",
                    "Поле за въвеждане на информация.",
                )

        self._splitter_configured = True

    # =========================================================
    # ДИНАМИЧНО СЪСТОЯНИЕ
    # =========================================================

    def update_dynamic_state(self):

        # -----------------------------------------------------
        # AUDIO SPLITTER
        # -----------------------------------------------------

        splitter = getattr(
            self.window,
            "audio_splitter",
            None,
        )

        if splitter is not None:

            if not self._splitter_configured:

                self.setup_audio_splitter()

        # -----------------------------------------------------
        # СЕГА СВИРИ
        # -----------------------------------------------------

        now_playing = getattr(
            self.window,
            "now_playing_label",
            None,
        )

        if isinstance(
            now_playing,
            QLabel,
        ):

            text = now_playing.text().strip()

            if text:

                now_playing.setAccessibleDescription(f"Сега свири: {text}")

        # -----------------------------------------------------
        # SAVE STATUS
        # -----------------------------------------------------

        save_status = getattr(
            self.window,
            "save_status_label",
            None,
        )

        if isinstance(
            save_status,
            QLabel,
        ):

            text = save_status.text().strip()

            if text:

                save_status.setAccessibleDescription(f"Статус: {text}")

        # -----------------------------------------------------
        # LOADING STATUS
        # -----------------------------------------------------

        loading_label = getattr(
            self.window,
            "loading_label",
            None,
        )

        if isinstance(
            loading_label,
            QLabel,
        ):

            text = loading_label.text().strip()

            if text:

                loading_label.setAccessibleDescription(text)

        # -----------------------------------------------------
        # ВРЕМЕ
        # -----------------------------------------------------

        current_time = getattr(
            self.window,
            "current_time_label",
            None,
        )

        if isinstance(
            current_time,
            QLabel,
        ):

            text = current_time.text().strip()

            if text:

                current_time.setAccessibleDescription(f"Изминало време: {text}")

        remaining_time = getattr(
            self.window,
            "remaining_time_label",
            None,
        )

        if isinstance(
            remaining_time,
            QLabel,
        ):

            text = remaining_time.text().strip()

            if text:

                remaining_time.setAccessibleDescription(f"Оставащо време: {text}")

        # -----------------------------------------------------
        # ОСНОВЕН ПРОГРЕС
        # -----------------------------------------------------

        progress = getattr(
            self.window,
            "loading_progress",
            None,
        )

        if isinstance(
            progress,
            QProgressBar,
        ):

            maximum = progress.maximum()

            if maximum > 0:

                value = progress.value()

                percent = int((value / maximum) * 100)

                progress.setAccessibleDescription(f"Прогрес: {percent} процента.")

        # -----------------------------------------------------
        # ТЕКУЩ РЕД
        # -----------------------------------------------------

        table = getattr(
            self.window,
            "table",
            None,
        )

        if isinstance(
            table,
            QTableWidget,
        ):

            row = table.currentRow()

            if 0 <= row < table.rowCount():

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

                duration = (
                    duration_item.text().strip() if duration_item is not None else ""
                )

                parts = [f"Ред {row + 1}"]

                if title:

                    parts.append(f"Песен: {title}")

                if artist:

                    parts.append(f"Изпълнител: {artist}")

                if duration:

                    parts.append(f"Време: {duration}")

                table.setAccessibleDescription(", ".join(parts))

        # -----------------------------------------------------
        # AUDIO SPLITTER СТАТУСИ
        # -----------------------------------------------------

        splitter = getattr(
            self.window,
            "audio_splitter",
            None,
        )

        if splitter is not None:

            for progress in splitter.findChildren(QProgressBar):

                maximum = progress.maximum()

                if maximum > 0:

                    value = progress.value()

                    percent = int((value / maximum) * 100)

                    progress.setAccessibleDescription(
                        f"Прогрес на разделянето: " f"{percent} процента."
                    )

            for label in splitter.findChildren(QLabel):

                text = label.text().strip()

                if text and (
                    "Оставащо" in text
                    or "Зареждане" in text
                    or "Анализ" in text
                    or "готов" in text.lower()
                    or "успешно" in text.lower()
                ):

                    label.setAccessibleDescription(text)

    # =========================================================
    # ДИАЛОЗИ
    # =========================================================

    def setup_dialog(
        self,
        dialog,
    ):

        if not isinstance(
            dialog,
            QDialog,
        ):

            return

        title = dialog.windowTitle().strip()

        if title:

            self.accessibility.register(
                dialog,
                title,
                f"Диалогов прозорец: {title}.",
            )

        buttons = dialog.findChildren(QPushButton)

        for button in buttons:

            text = button.text().strip()

            if text:

                self.accessibility.setup_button(
                    button,
                    text,
                    f"Бутон: {text}.",
                )

    # =========================================================
    # ОБЯВЯВАНЕ НА СЪОБЩЕНИЕ
    # =========================================================

    def announce(
        self,
        text,
    ):

        self.accessibility.announce(text)
