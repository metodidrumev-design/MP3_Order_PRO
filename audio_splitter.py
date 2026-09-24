# =====================================================
# Начало на    ИМПОРТИ
# =====================================================

import os
import sys
import ctypes

import subprocess
from typing import cast

import tempfile

import numpy as np

import pyqtgraph as pg

from mutagen.mp3 import MP3

import vlc

from language_manager import language_manager


from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QTimer,
    QEvent,
)

from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QShortcut,
)

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
    QFileDialog,
    QProgressBar,
    QSlider,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

# =====================================================
# КРАЙ НА ИМПОРТИТЕ
# =====================================================


# =====================================================
# =========================================================
# WAVEFORM С КЛИК, ZOOM И МАРКИРАНЕ
# =========================================================


class ClickablePlotWidget(pg.PlotWidget):

    clicked_x = Signal(float)
    selection_changed = Signal(float, float)
    zoom_changed = Signal(float, float)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.waveform_duration = 0.0

        self.selecting = False

        self.selection_start = 0.0

        self.selection_region = None

        self.dragging_edge = None

        self.mouse_press_x = None
        self.mouse_press_pos = None
        self.potential_mouse_drag = False

        self.last_click_x = 0.0

    def get_view_box(self):

        plot_item = self.getPlotItem()

        if plot_item is None:

            return None

        view_box = getattr(plot_item, "vb", None)

        return view_box

    def get_mouse_x(self, event):

        view_box = self.get_view_box()

        if view_box is None:

            return None

        scene_pos = self.mapToScene(event.position().toPoint())

        view_pos = view_box.mapSceneToView(scene_pos)

        x_value = float(view_pos.x())

        if self.waveform_duration > 0:

            x_value = max(0.0, min(x_value, self.waveform_duration))

        return x_value

    # =====================================================
    # ЛЯВ БУТОН
    # =====================================================

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            mouse_x = self.get_mouse_x(event)

            if mouse_x is not None:

                # =================================================
                # CTRL + ЛЯВ БУТОН
                # =================================================

                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:

                    # =================================================
                    # АКО ВЕЧЕ ИМАМЕ МАРКИРОВКА
                    # =================================================

                    region_item = self.selection_region

                    if region_item is not None:

                        region = region_item.getRegion()

                        start_value = region[0]
                        end_value = region[1]

                        if isinstance(start_value, (list, tuple)):

                            start = float(start_value[0])

                        else:

                            start = float(start_value)

                        if isinstance(end_value, (list, tuple)):

                            end = float(end_value[0])

                        else:

                            end = float(end_value)

                        edge_tolerance = max(
                            0.15,
                            self.waveform_duration * 0.003,
                        )

                        # =================================================
                        # ЛЯВ КРАЙ
                        # =================================================

                        if abs(mouse_x - start) <= edge_tolerance:

                            self.dragging_edge = "start"

                            event.accept()

                            return

                        # =================================================
                        # ДЕСЕН КРАЙ
                        # =================================================

                        if abs(mouse_x - end) <= edge_tolerance:

                            self.dragging_edge = "end"

                            event.accept()

                            return

                    # =================================================
                    # НОВО МАРКИРАНЕ
                    # =================================================

                    self.dragging_edge = None

                    self.selecting = True

                    self.selection_start = mouse_x

                    self.update_selection_region(
                        mouse_x,
                        mouse_x,
                    )

                    event.accept()

                    return

                # =================================================
                # ОБИКНОВЕН ЛЯВ БУТОН
                # =================================================

                self.mouse_press_x = mouse_x

                self.last_click_x = mouse_x

                self.mouse_press_pos = event.position().toPoint()

                self.potential_mouse_drag = True

                event.accept()

                return

        super().mousePressEvent(event)

    # =====================================================
    # ДВИЖЕНИЕ НА МИШАТА
    # =====================================================

    def mouseMoveEvent(self, event):

        mouse_x = self.get_mouse_x(event)

        if mouse_x is None:

            super().mouseMoveEvent(event)

            return

        # =====================================================
        # МЕСТИМ ЛЕВИЯ КРАЙ
        # =====================================================

        if self.dragging_edge == "start":

            region_item = self.selection_region

            if region_item is None:

                self.dragging_edge = None

                event.accept()

                return

            region = region_item.getRegion()

            end_value = region[1]

            if isinstance(end_value, (list, tuple)):

                end = float(end_value[0])

            else:

                end = float(end_value)

            mouse_x = min(mouse_x, end)

            region_item.setRegion(
                (
                    mouse_x,
                    end,
                )
            )

            self.selection_changed.emit(
                mouse_x,
                end,
            )

            event.accept()

            return

        # =====================================================
        # МЕСТИМ ДЕСНИЯ КРАЙ
        # =====================================================

        if self.dragging_edge == "end":

            region_item = self.selection_region

            if region_item is None:

                self.dragging_edge = None

                event.accept()

                return

            region = region_item.getRegion()

            start_value = region[0]

            if isinstance(start_value, (list, tuple)):

                start = float(start_value[0])

            else:

                start = float(start_value)

            mouse_x = max(
                mouse_x,
                start,
            )

            region_item.setRegion(
                (
                    start,
                    mouse_x,
                )
            )

            self.selection_changed.emit(
                start,
                mouse_x,
            )

            event.accept()

            return

        # =====================================================
        # CTRL + DRAG - НОВА МАРКИРОВКА
        # =====================================================

        if self.selecting:

            self.update_selection_region(
                self.selection_start,
                mouse_x,
            )

            event.accept()

            return

        # =====================================================
        # ОБИКНОВЕН DRAG - НОВА МАРКИРОВКА
        # =====================================================

        if self.potential_mouse_drag:

            if self.mouse_press_pos is not None:

                current_pos = event.position().toPoint()

                distance = (current_pos - self.mouse_press_pos).manhattanLength()

                if distance >= 5:

                    self.potential_mouse_drag = False

                    self.selecting = True

                    if self.mouse_press_x is not None:

                        self.selection_start = self.mouse_press_x

                        self.update_selection_region(
                            self.selection_start,
                            mouse_x,
                        )

                    event.accept()

                    return

                event.accept()

                return

        super().mouseMoveEvent(event)

    # =====================================================
    # ПУСКАНЕ НА МИШАТА
    # =====================================================

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            # =================================================
            # ОБИКНОВЕН КЛИК
            # =================================================

            if self.potential_mouse_drag:

                if self.mouse_press_x is not None:

                    self.clicked_x.emit(self.mouse_press_x)

                self.mouse_press_x = None
                self.mouse_press_pos = None
                self.potential_mouse_drag = False

                event.accept()

                return

            # =================================================
            # КРАЙ НА ДВИЖЕНИЕТО НА КРАЙ
            # =================================================

            if self.dragging_edge is not None:

                self.dragging_edge = None

                self.mouse_press_x = None
                self.mouse_press_pos = None
                self.potential_mouse_drag = False

                event.accept()

                return

            # =================================================
            # КРАЙ НА НОВАТА МАРКИРОВКА
            # =================================================

            if self.selecting:

                mouse_x = self.get_mouse_x(event)

                if mouse_x is not None:

                    self.update_selection_region(
                        self.selection_start,
                        mouse_x,
                    )

                self.selecting = False

                self.mouse_press_x = None
                self.mouse_press_pos = None
                self.potential_mouse_drag = False

                event.accept()

                return

        super().mouseReleaseEvent(event)

    # =====================================================
    # СЪЗДАВАМЕ / ОБНОВЯВАМЕ АКТИВНАТА МАРКИРОВКА
    # =====================================================

    def update_selection_region(self, start_x, end_x):

        start = min(
            start_x,
            end_x,
        )

        end = max(
            start_x,
            end_x,
        )

        if self.waveform_duration > 0:

            start = max(
                0.0,
                min(
                    start,
                    self.waveform_duration,
                ),
            )

            end = max(
                0.0,
                min(
                    end,
                    self.waveform_duration,
                ),
            )

        if abs(end - start) < 0.001:

            end = start

        # =================================================
        # СЪЗДАВАМЕ / ОБНОВЯВАМЕ САМО АКТИВНАТА МАРКИРОВКА
        # =================================================

        region_item = self.selection_region

        if region_item is None:

            current_theme = getattr(
                self.window(),
                "current_theme",
                None,
            )

            if current_theme is None:

                return

            region_item = pg.LinearRegionItem(
                values=(
                    start,
                    end,
                ),
                movable=False,
                brush=(
                    lambda c: (
                        c.setAlpha(70),
                        pg.mkBrush(c),
                    )[1]
                )(QColor(current_theme["accent"])),
                pen=pg.mkPen(
                    current_theme["main_text"],
                    width=1,
                ),
            )

            self.selection_region = region_item

            self.addItem(region_item)

        else:

            region_item.setRegion(
                (
                    start,
                    end,
                )
            )

        self.selection_changed.emit(
            start,
            end,
        )

    # =====================================================
    # СЪЗДАВАМЕ / ОБНОВЯВАМЕ ЗАПАЗЕН СЛОТ
    # =====================================================

    def set_saved_selection_region(self, slot_number, start, end):

        if slot_number < 1 or slot_number > 5:

            return

        start = float(start)

        end = float(end)

        if self.waveform_duration > 0:

            start = max(0.0, min(start, self.waveform_duration))

            end = max(0.0, min(end, self.waveform_duration))

        if end <= start:

            return

        # =================================================
        # СЪЗДАВАМЕ РЕЧНИК ЗА ВИЗУАЛНИТЕ СЛОТОВЕ
        # =================================================

        if not hasattr(self, "saved_selection_regions"):

            self.saved_selection_regions = {}

        # =================================================
        # АКО ВЕЧЕ ИМА ТАКЪВ СЛОТ - ОБНОВЯВАМЕ ГО
        # =================================================

        region_item = self.saved_selection_regions.get(slot_number)

        if region_item is None:

            region_item = pg.LinearRegionItem(
                values=(start, end),
                movable=False,
                brush=pg.mkBrush(140, 80, 220, 45),
                pen=pg.mkPen("#B388FF", width=2),
            )

            self.addItem(region_item)

            self.saved_selection_regions[slot_number] = region_item

        else:

            region_item.setRegion((start, end))

        # =================================================
        # ПАЗИМ НОМЕРА НА СЛОТА ВЪРХУ РЕГИОНА
        # =================================================

    # =====================================================
    # ПРЕМАХВАМЕ ВИЗУАЛЕН ЗАПАЗЕН СЛОТ
    # =====================================================

    def clear_saved_selection_region(self, slot_number):

        if not hasattr(self, "saved_selection_regions"):

            return

        region_item = self.saved_selection_regions.pop(slot_number, None)

        if region_item is not None:

            try:

                self.removeItem(region_item)

            except Exception:

                pass

    # =====================================================
    # ПРЕМАХВАМЕ ВСИЧКИ ЗАПАЗЕНИ СЛОТОВЕ
    # =====================================================

    def clear_all_saved_selection_regions(self):

        if not hasattr(self, "saved_selection_regions"):

            return

        for region_item in list(self.saved_selection_regions.values()):

            try:

                self.removeItem(region_item)

            except Exception:

                pass

        self.saved_selection_regions.clear()

    # =====================================================
    # ПРЕМАХВАМЕ САМО АКТИВНАТА МАРКИРОВКА
    # ЗАПАЗЕНИТЕ СЛОТОВЕ ОСТАВАТ
    # =====================================================

    def clear_selection(self):

        region_item = self.selection_region

        if region_item is not None:

            try:

                self.removeItem(region_item)

            except Exception:

                pass

        self.selection_region = None

        self.selecting = False

        self.dragging_edge = None

    # =====================================================
    # CTRL + SCROLL → ZOOM
    # =====================================================

    def wheelEvent(self, event):

        if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):

            super().wheelEvent(event)

            return

        view_box = self.get_view_box()

        if view_box is None:

            event.accept()

            return

        delta = event.angleDelta().y()

        if delta == 0:

            event.accept()

            return

        # =====================================================
        # ТЕКУЩИ ГРАНИЦИ
        # =====================================================

        x_range = view_box.viewRange()[0]

        x_min = float(x_range[0])

        x_max = float(x_range[1])

        current_width = x_max - x_min

        if current_width <= 0:

            event.accept()

            return

        # =====================================================
        # ПОЗИЦИЯ НА МИШАТА
        # =====================================================

        scene_pos = self.mapToScene(event.position().toPoint())

        mouse_view_pos = view_box.mapSceneToView(scene_pos)

        mouse_x = float(mouse_view_pos.x())

        # =====================================================
        # ЗУМ
        # =====================================================

        if delta > 0:

            zoom_factor = 0.80

        else:

            zoom_factor = 1.25

        new_width = current_width * zoom_factor

        duration = self.waveform_duration

        if duration <= 0:

            event.accept()

            return

        new_width = min(new_width, duration)

        new_width = max(1.0, new_width)

        # =====================================================
        # ПАЗИМ ТОЧКАТА ПОД МИШАТА
        # =====================================================

        ratio = (mouse_x - x_min) / current_width

        new_x_min = mouse_x - ratio * new_width

        new_x_max = new_x_min + new_width

        # =====================================================
        # НЕ ИЗЛИЗАМЕ ИЗ ФАЙЛА
        # =====================================================

        if new_x_min < 0:

            new_x_min = 0

            new_x_max = new_width

        if new_x_max > duration:

            new_x_max = duration

            new_x_min = duration - new_width

        new_x_min = max(0.0, new_x_min)

        new_x_max = min(duration, new_x_max)

        # =====================================================
        # ПРИЛАГАМЕ ZOOM
        # =====================================================

        view_box.setXRange(new_x_min, new_x_max, padding=0)

        # =====================================================
        # ИЗПРАЩАМЕ НОВИЯ ZOOM КЪМ AUDIO SPLITTER
        # =====================================================

        self.zoom_changed.emit(new_x_min, new_x_max)

        event.accept()


# =========================================================
# WORKER ЗА ИЗТРИВАНЕ НА МАРКИРАН АУДИО УЧАСТЪК
# =========================================================


class DeleteWorker(QThread):

    delete_finished = Signal(str)

    error = Signal(str)

    def __init__(
        self,
        ffmpeg_path,
        input_file,
        filter_complex,
        map_label,
        output_file,
        trim_start=None,
        parent=None,
    ):

        super().__init__(parent)

        self.ffmpeg_path = ffmpeg_path

        self.input_file = input_file

        self.filter_complex = filter_complex

        self.map_label = map_label

        self.output_file = output_file

        self.trim_start = trim_start

    def run(self):

        try:

            # =========================================================
            # FFMPEG КОМАНДА ЗА ИЗТРИВАНЕ
            # =========================================================

            command = [
                self.ffmpeg_path,
                "-y",
                "-hide_banner",
                "-nostdin",
                "-loglevel",
                "error",
                "-i",
                self.input_file,
                "-filter_complex",
                self.filter_complex,
                "-map",
                self.map_label,
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                self.output_file,
            ]

            print(
                self.filter_complex,
            )

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode != 0:

                if os.path.exists(self.output_file):

                    os.remove(self.output_file)

                self.error.emit(
                    language_manager.get(
                        "delete_worker_error",
                        error=result.stderr,
                    )
                )

                return

            self.delete_finished.emit(self.output_file)

        except Exception as e:

            if os.path.exists(self.output_file):

                try:

                    os.remove(self.output_file)

                except Exception:

                    pass

            self.error.emit(
                language_manager.get(
                    "delete_worker_exception",
                    error=str(e),
                )
            )


# =========================================================
# WORKER ЗА ЗАРЕЖДАНЕ И ДЕКОДИРАНЕ НА MP3
# =========================================================


class AudioDecodeWorker(QThread):

    progress_changed = Signal(int)
    waveform_ready = Signal(object, float)
    error = Signal(str)
    worker_finished = Signal()

    def __init__(self, file_path, parent=None):

        super().__init__(parent)
        self.waveform_duration = 0.0

        self.file_path = file_path

    def run(self):

        raw_file = None
        process = None

        try:

            # =================================================
            # НАМИРАМЕ FFMPEG В ПАПКАТА НА ПРОЕКТА
            # =================================================

            if getattr(sys, "frozen", False):

                project_dir = os.path.dirname(os.path.abspath(sys.executable))

            else:

                project_dir = os.path.dirname(os.path.abspath(__file__))

            ffmpeg_path = os.path.join(
                project_dir, "ffmpeg-n9.0-latest-win64-gpl-9.0", "bin", "ffmpeg.exe"
            )

            if not os.path.isfile(ffmpeg_path):

                self.error.emit(
                    language_manager.get("ffmpeg_expected_path", path=ffmpeg_path)
                )

                return

            # =================================================
            # ПРОВЕРКА НА MP3
            # =================================================

            if not os.path.isfile(self.file_path):

                self.error.emit(language_manager.get("selected_mp3_missing"))

                return

            # =================================================
            # ПРОДЪЛЖИТЕЛНОСТ
            # =================================================

            try:

                audio = MP3(self.file_path)

                duration = float(audio.info.length)

            except Exception as e:

                self.error.emit(
                    language_manager.get("duration_read_error", error=str(e))
                )

                return

            if duration <= 0:

                self.error.emit(language_manager.get("invalid_duration"))

                return

            # =================================================
            # ВРЕМЕНЕН RAW ФАЙЛ
            # =================================================

            temp = tempfile.NamedTemporaryFile(suffix=".raw", delete=False)

            raw_file = temp.name

            temp.close()

            # =================================================
            # FFMPEG КОМАНДА
            # =================================================

            command = [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-nostdin",
                "-loglevel",
                "error",
                "-i",
                self.file_path,
                "-vn",
                "-ac",
                "1",
                "-ar",
                "1000",
                "-f",
                "s16le",
                "-progress",
                "pipe:1",
                "-nostats",
                raw_file,
            ]

            # =================================================
            # СТАРТИРАМЕ FFMPEG
            # =================================================

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="ignore",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # =================================================
            # ПРОГРЕС
            # =================================================

            if process.stdout is not None:

                while True:

                    line = process.stdout.readline()

                    if not line:

                        break

                    line = line.strip()

                    if not line:

                        continue

                    if line.startswith("out_time_ms="):

                        try:

                            out_time_ms = int(line.split("=", 1)[1])

                            current_seconds = out_time_ms / 1_000_000

                            percent = int((current_seconds / duration) * 100)

                            percent = max(0, min(99, percent))

                            self.progress_changed.emit(percent)

                        except (ValueError, ZeroDivisionError):

                            pass

            # =================================================
            # КРАЙ НА FFMPEG
            # =================================================

            return_code = process.wait()

            if return_code != 0:

                self.error.emit(language_manager.get("ffmpeg_process_error"))

                return

            # =================================================
            # 100%
            # =================================================

            self.progress_changed.emit(100)

            # =================================================
            # ЧЕТЕМ RAW ФАЙЛА
            # =================================================

            samples = np.fromfile(raw_file, dtype=np.int16)

            if samples.size == 0:

                self.error.emit(language_manager.get("no_audio_signal"))

                return

            # =================================================
            # НОРМАЛИЗИРАНЕ
            # =================================================

            samples = samples.astype(np.float32) / 32768.0

            # =================================================
            # WAVEFORM
            # =================================================

            target_points = 5000

            if samples.size > target_points:

                chunk_size = int(np.ceil(samples.size / target_points))

                waveform = []

                for start in range(0, samples.size, chunk_size):

                    chunk = samples[start : start + chunk_size]

                    if chunk.size == 0:

                        continue

                    waveform.append(np.max(chunk))

                    waveform.append(np.min(chunk))

                waveform = np.asarray(waveform, dtype=np.float32)

            else:

                waveform = samples

            # =================================================
            # ИЗПРАЩАМЕ WAVEFORM
            # =================================================

            self.waveform_ready.emit(waveform, duration)

        except Exception as e:

            self.error.emit(language_manager.get("decode_error", error=str(e)))

        finally:

            # =================================================
            # СПИРАМЕ ПРОЦЕСА ПРИ НЕОБХОДИМОСТ
            # =================================================

            if process is not None and process.poll() is None:

                try:

                    process.kill()

                except Exception:

                    pass

            # =================================================
            # ИЗТРИВАМЕ ВРЕМЕННИЯ ФАЙЛ
            # =================================================

            if raw_file is not None:

                try:

                    if os.path.exists(raw_file):

                        os.remove(raw_file)

                except Exception:

                    pass

            # =================================================
            # WORKER ГОТОВ
            # =================================================

            self.worker_finished.emit()


# =========================================================
# WORKER ЗА РАЗДЕЛЯНЕ НА MP3
# =========================================================


class SplitWorker(QThread):

    progress_changed = Signal(int)

    time_changed = Signal(int, int)

    error = Signal(str)

    worker_finished = Signal()

    def __init__(
        self,
        ffmpeg_path,
        input_file,
        detected_songs,
        export_folder,
        source_name,
        parent=None,
    ):

        super().__init__(parent)

        self.ffmpeg_path = ffmpeg_path

        self.input_file = input_file

        self.detected_songs = detected_songs

        self.export_folder = export_folder

        self.source_name = source_name

    def run(self):

        import time

        start_time = time.time()

        try:

            total_songs = len(self.detected_songs)

            if total_songs == 0:

                self.error.emit(language_manager.get("no_songs_to_split"))

                return

            total_audio_duration = sum(
                end - start for start, end in self.detected_songs
            )

            if total_audio_duration <= 0:

                self.error.emit(language_manager.get("invalid_total_duration"))

                return

            completed_audio_duration = 0.0

            last_progress = -1

            estimated_total_seconds = None

            for index, (start, end) in enumerate(self.detected_songs, start=1):

                current_song_duration = end - start

                output_file = os.path.join(
                    self.export_folder, f"{index:02d} - {self.source_name}.mp3"
                )

                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-hide_banner",
                    "-nostats",
                    "-loglevel",
                    "error",
                    "-ss",
                    str(start),
                    "-t",
                    str(current_song_duration),
                    "-i",
                    self.input_file,
                    "-vn",
                    "-c:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    "-progress",
                    "pipe:1",
                    output_file,
                ]

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                current_audio_time = 0.0

                while process.poll() is None:

                    if process.stdout is not None:

                        line = process.stdout.readline()

                        if line:

                            line = line.strip()

                            if line.startswith("out_time_ms="):

                                try:

                                    out_time_ms = int(line.split("=", 1)[1])

                                    current_audio_time = max(
                                        0.0,
                                        min(
                                            current_song_duration,
                                            out_time_ms / 1_000_000,
                                        ),
                                    )

                                except ValueError:

                                    pass

                    processed_audio_duration = (
                        completed_audio_duration + current_audio_time
                    )

                    processed_audio_duration = max(
                        0.0,
                        min(
                            total_audio_duration,
                            processed_audio_duration,
                        ),
                    )

                    progress = int(
                        (processed_audio_duration / total_audio_duration) * 100
                    )

                    progress = max(
                        0,
                        min(99, progress),
                    )

                    if progress != last_progress:

                        self.progress_changed.emit(progress)

                        last_progress = progress

                    elapsed_seconds = int(time.time() - start_time)

                    if processed_audio_duration > 0:

                        current_estimated_total = (
                            elapsed_seconds
                            * total_audio_duration
                            / processed_audio_duration
                        )

                        if estimated_total_seconds is None:

                            estimated_total_seconds = current_estimated_total

                        else:

                            estimated_total_seconds = min(
                                estimated_total_seconds,
                                current_estimated_total,
                            )

                        remaining_seconds = max(
                            0,
                            int(estimated_total_seconds - elapsed_seconds),
                        )

                    else:

                        remaining_seconds = 0

                    self.time_changed.emit(
                        elapsed_seconds,
                        remaining_seconds,
                    )

                    time.sleep(0.2)

                return_code = process.wait()

                stderr_text = ""

                if process.stderr is not None:

                    stderr_text = process.stderr.read()

                if return_code != 0:

                    self.error.emit(
                        language_manager.get(
                            "split_song_error",
                            index=str(index),
                            error=stderr_text,
                        )
                    )

                    return

                completed_audio_duration += current_song_duration

                completed_audio_duration = min(
                    completed_audio_duration,
                    total_audio_duration,
                )

                progress = int((completed_audio_duration / total_audio_duration) * 100)

                progress = max(
                    0,
                    min(99, progress),
                )

                if progress > last_progress:

                    self.progress_changed.emit(progress)

                    last_progress = progress

            elapsed_seconds = int(time.time() - start_time)

            self.progress_changed.emit(100)

            self.time_changed.emit(
                elapsed_seconds,
                0,
            )

        except Exception as e:

            self.error.emit(
                language_manager.get(
                    "split_generic_error",
                    error=str(e),
                )
            )

        finally:

            self.worker_finished.emit()


# =========================================================
# ANALYSIS WORKER
# =========================================================


class SongAnalysisWorker(QThread):

    songs_ready = Signal(object)
    error = Signal(str)
    progress_changed = Signal(int)

    def __init__(self, file_path, parent=None):

        super().__init__(parent)

        self.file_path = file_path

    def run(self):

        process = None

        try:

            # =================================================
            # НАМИРАМЕ FFMPEG
            # =================================================

            if getattr(sys, "frozen", False):

                project_dir = os.path.dirname(os.path.abspath(sys.executable))

            else:

                project_dir = os.path.dirname(os.path.abspath(__file__))

            ffmpeg_path = os.path.join(
                project_dir,
                "ffmpeg-n9.0-latest-win64-gpl-9.0",
                "bin",
                "ffmpeg.exe",
            )

            if not os.path.isfile(ffmpeg_path):

                self.error.emit(language_manager.get("ffmpeg_not_found"))

                return

            if not os.path.isfile(self.file_path):

                self.error.emit(language_manager.get("selected_mp3_missing"))

                return

            # =================================================
            # ЧЕТЕМ ПРОДЪЛЖИТЕЛНОСТТА ПРЕДИ АНАЛИЗА
            # =================================================

            try:

                audio = MP3(self.file_path)

                duration = float(audio.info.length)

            except Exception as e:

                self.error.emit(
                    language_manager.get("duration_read_error", error=str(e))
                )

                return

            if duration <= 0:

                self.error.emit(language_manager.get("invalid_duration"))

                return

            # =================================================
            # НАЧАЛЕН ПРОГРЕС
            # =================================================

            self.progress_changed.emit(0)

            # =================================================
            # FFMPEG АНАЛИЗ
            # =================================================

            command = [
                ffmpeg_path,
                "-hide_banner",
                "-nostdin",
                "-loglevel",
                "info",
                "-i",
                self.file_path,
                "-af",
                "silencedetect=noise=-30dB:d=0.5",
                "-progress",
                "pipe:2",
                "-f",
                "null",
                "-",
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            silence_start = None

            silences = []

            last_progress = -1

            if process.stderr is not None:

                for line in process.stderr:

                    line = line.strip()

                    # =================================================
                    # ПРОГРЕС НА АНАЛИЗА
                    # =================================================

                    if line.startswith("out_time_us="):

                        try:

                            processed_us = int(line.split("=", 1)[1])

                            processed_seconds = processed_us / 1_000_000.0

                            percentage = int((processed_seconds / duration) * 100)

                            percentage = max(0, min(99, percentage))

                            if percentage != last_progress:

                                last_progress = percentage

                                self.progress_changed.emit(percentage)

                        except (
                            ValueError,
                            IndexError,
                            ZeroDivisionError,
                        ):

                            pass

                    # =================================================
                    # НАЧАЛО НА ТИШИНА
                    # =================================================

                    if "silence_start:" in line:

                        try:

                            value = line.split("silence_start:", 1)[1].strip()

                            silence_start = float(value.split()[0])

                        except (
                            ValueError,
                            IndexError,
                        ):

                            silence_start = None

                    # =================================================
                    # КРАЙ НА ТИШИНА
                    # =================================================

                    if "silence_end:" in line:

                        try:

                            value = line.split("silence_end:", 1)[1].strip()

                            silence_end = float(value.split()[0])

                            if silence_start is not None:

                                silence_duration = silence_end - silence_start

                                if silence_duration >= 0.5:

                                    silences.append(
                                        (
                                            silence_start,
                                            silence_end,
                                        )
                                    )

                            silence_start = None

                        except (
                            ValueError,
                            IndexError,
                        ):

                            silence_start = None

            process.wait()

            # =================================================
            # АНАЛИЗЪТ Е ЗАВЪРШИЛ
            # =================================================

            self.progress_changed.emit(100)

            # =================================================
            # ПОДРЕЖДАМЕ ТИШИНИТЕ
            # =================================================

            silences.sort(key=lambda item: item[0])

            # =================================================
            # СЪЗДАВАМЕ ПЪРВОНАЧАЛНИТЕ СЕГМЕНТИ
            # =================================================

            segments = []

            current_start = 0.0

            for silence_begin, silence_end in silences:

                song_end = min(silence_begin, duration)

                segment_duration = song_end - current_start

                if segment_duration >= 20.0:

                    segments.append((current_start, song_end))

                current_start = max(current_start, min(silence_end, duration))

            # =================================================
            # ПОСЛЕДНИЯ СЕГМЕНТ
            # =================================================

            if duration - current_start >= 20.0:

                segments.append((current_start, duration))

            # =================================================
            # ПРЕМАХВАМЕ ФАЛШИВИ КРАТКИ СЕГМЕНТИ
            # =================================================

            MIN_SONG_DURATION = 60.0

            songs = []

            index = 0

            while index < len(segments):

                start, end = segments[index]

                segment_duration = end - start

                # =================================================
                # НОРМАЛНА ПЕСЕН
                # =================================================

                if segment_duration >= MIN_SONG_DURATION:

                    songs.append((start, end))

                    index += 1

                    continue

                # =================================================
                # КРАТЪК СЕГМЕНТ
                # СЛИВАМЕ ГО С ПРЕДИШНАТА ПЕСЕН
                # =================================================

                if songs:

                    previous_start, previous_end = songs[-1]

                    songs[-1] = (previous_start, end)

                    index += 1

                    continue

                # =================================================
                # АКО Е ПЪРВИЯТ СЕГМЕНТ
                # СЛИВАМЕ ГО СЪС СЛЕДВАЩИЯ
                # =================================================

                if index + 1 < len(segments):

                    next_start, next_end = segments[index + 1]

                    segments[index + 1] = (start, next_end)

                index += 1

            # =================================================
            # ФИНАЛНО ПОЧИСТВАНЕ
            # =================================================

            cleaned_songs = []

            for start, end in songs:

                if end - start >= MIN_SONG_DURATION:

                    cleaned_songs.append((start, end))

            songs = cleaned_songs

            # =================================================
            # РЕЗУЛТАТ
            # =================================================

            self.songs_ready.emit(songs)

        except Exception as e:

            self.error.emit(
                language_manager.get("analysis_generic_error", error=str(e))
            )

        finally:

            if process is not None and process.poll() is None:

                try:

                    process.kill()

                except Exception:

                    pass


# =========================================================
# AUDIO SPLITTER
# =========================================================


class AudioSplitter(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        # =====================================================
        # ПРОЗОРЕЦ
        # =====================================================

        self.setWindowTitle(language_manager.get("split_title"))

        # =====================================================
        # ПОЗВОЛЯВАМЕ МИНИМИЗИРАНЕ ОТ БУТОНА НА ПРОЗОРЕЦА
        # =====================================================

        self.setWindowFlag(
            Qt.WindowType.WindowMinimizeButtonHint,
            True,
        )

        from PySide6.QtCore import QSettings
        from themes import set_theme, get_theme

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        # =====================================================
        # ЗАПАМЕТЕНА ПОЗИЦИЯ НА ПРОЗОРЕЦА
        # =====================================================

        self.window_settings = settings

        # =====================================================
        # УПРАВЛЕНИЕ НА БЛОКИРАНЕТО НА ОСНОВНИЯ ПРОЗОРЕЦ
        # =====================================================

        self._block_parent_input = False

        self._event_filter_installed = False

        self.setWindowModality(
            Qt.WindowModality.NonModal,
        )

        theme_name = settings.value(
            "theme_name",
            "Лилаво-синя",
            type=str,
        )

        if not set_theme(theme_name):
            theme_name = "Лилаво-синя"

        self.current_theme = get_theme(theme_name)
        self._last_language = language_manager.get_language()

        self.setMinimumSize(1100, 700)

        self.resize(1100, 750)

        # =====================================================
        # ВЪЗСТАНОВЯВАМЕ ПОСЛЕДНАТА ПОЗИЦИЯ НА ПРОЗОРЕЦА
        # =====================================================

        saved_x = cast(
            int,
            self.window_settings.value(
                "splitter_window_x",
                -1,
                type=int,
            ),
        )

        saved_y = cast(
            int,
            self.window_settings.value(
                "splitter_window_y",
                -1,
                type=int,
            ),
        )

        if saved_x >= 0 and saved_y >= 0:

            self.move(
                saved_x,
                saved_y,
            )

        self.setStyleSheet("""
            QToolTip {
                font-size: 16px;
                font-weight: bold;
            }
        """)

        # =====================================================
        # СЪСТОЯНИЕ
        # =====================================================

        self.current_file = None

        self.current_duration = 0.0

        self.decode_worker = None

        self.is_paused = False

        self.audio_playing = False

        self.selection_region = None
        self.undo_history = []
        self.undo_slots_history = []
        self.undo_analysis_history = []

        self.playback_line = None

        self.detected_songs = []

        self.song_boundary_lines = []

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.position_timer = QTimer(self)

        self.position_timer.setInterval(60)

        self.position_timer.timeout.connect(self.update_playback_position)

        # =====================================================
        # ПРОВЕРКА ЗА ПРОМЯНА НА ЦВЕТОВАТА ТЕМА
        # =====================================================

        self.theme_timer = QTimer(self)

        self.theme_timer.setInterval(500)

        self.theme_timer.timeout.connect(self.check_theme_change)

        self.theme_timer.start()

        # ======================================================
        #              Shortcut......

        # =====================================================
        # CTRL + Z - UNDO
        # =====================================================

        self.undo_shortcut = QShortcut(
            QKeySequence(QKeySequence.StandardKey.Undo),
            self,
        )

        self.undo_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.undo_shortcut.setAutoRepeat(False)

        self.undo_shortcut.activated.connect(self.undo_last_action)

        # =====================================================
        # SPACE SHORTCUT
        # =====================================================

        self.space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space),
            self,
        )

        self.space_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.space_shortcut.setAutoRepeat(False)

        self.space_shortcut.activated.connect(self.toggle_play_pause)

        # =====================================================
        # CTRL + A - МАРКИРАМЕ ЦЕЛИЯ ФАЙЛ
        # =====================================================

        self.select_all_shortcut = QShortcut(
            QKeySequence(QKeySequence.StandardKey.SelectAll),
            self,
        )

        self.select_all_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.select_all_shortcut.setAutoRepeat(False)

        self.select_all_shortcut.activated.connect(self.select_all_waveform)

        # =====================================================
        # DELETE - ИЗТРИВАМЕ МАРКИРАНОТО
        # =====================================================

        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)

        self.delete_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.delete_shortcut.setAutoRepeat(False)

        # =====================================================
        # ESC - ОСВОБОЖДАВАМЕ МАРКИРОВКАТА
        # =====================================================

        self.clear_selection_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)

        self.clear_selection_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.clear_selection_shortcut.setAutoRepeat(False)

        self.clear_selection_shortcut.activated.connect(self.clear_waveform_selection)

        self.delete_shortcut.activated.connect(self.delete_selected_waveform)

        # =====================================================
        # CTRL + LEFT / RIGHT - ПРЕМЕСТВАМЕ МАРКИРОВКАТА
        # =====================================================

        self.selection_move_left_shortcut = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Left),
            self,
        )

        self.selection_move_left_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.selection_move_left_shortcut.setAutoRepeat(False)

        self.selection_move_left_shortcut.activated.connect(self.move_selection_left)

        self.selection_move_right_shortcut = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Right),
            self,
        )

        self.selection_move_right_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.selection_move_right_shortcut.setAutoRepeat(False)

        self.selection_move_right_shortcut.activated.connect(self.move_selection_right)

        # =====================================================
        # SHIFT + LEFT / RIGHT - ПРОМЕНЯМЕ ГРАНИЦИТЕ
        # =====================================================

        self.selection_resize_left_shortcut = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Left),
            self,
        )

        self.selection_resize_left_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.selection_resize_left_shortcut.setAutoRepeat(True)

        self.selection_resize_left_shortcut.activated.connect(
            self.resize_selection_left
        )

        self.selection_resize_right_shortcut = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Right),
            self,
        )

        self.selection_resize_right_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.selection_resize_right_shortcut.setAutoRepeat(True)

        self.selection_resize_right_shortcut.activated.connect(
            self.resize_selection_right
        )

        # =====================================================
        # LEFT / RIGHT - ФИНА ПОЗИЦИЯ НА БЯЛАТА ЛИНИЯ
        # =====================================================

        self.playback_left_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Left),
            self,
        )

        self.playback_left_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.playback_left_shortcut.setAutoRepeat(True)

        self.playback_left_shortcut.activated.connect(self.move_playback_left)

        self.playback_right_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Right),
            self,
        )

        self.playback_right_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.playback_right_shortcut.setAutoRepeat(True)

        self.playback_right_shortcut.activated.connect(self.move_playback_right)

        # =====================================================
        # NUM 0 - ПРЕВКЛЮЧВАМЕ РЕЖИМА НА ТОЧНОСТ
        # =====================================================

        self.selection_precision_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_0),
            self,
        )

        self.selection_precision_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.selection_precision_shortcut.setAutoRepeat(False)

        self.selection_precision_shortcut.activated.connect(
            self.toggle_selection_precision
        )

        # =====================================================
        # 1 - 5 - ЗАПАЗЕНИ МАРКИРОВКИ
        # =====================================================

        self.selection_slot_shortcuts = []

        for slot_number in range(1, 6):

            slot_key = getattr(Qt.Key, f"Key_{slot_number}")

            slot_shortcut = QShortcut(QKeySequence(slot_key), self)

            slot_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

            slot_shortcut.setAutoRepeat(False)

            slot_shortcut.activated.connect(
                lambda number=slot_number: self.handle_selection_slot(number)
            )

            self.selection_slot_shortcuts.append(slot_shortcut)

        # =====================================================
        # CTRL + 1 - 5 - ИЗТРИВАМЕ ЗАПАЗЕНИТЕ МАРКИРОВКИ
        # =====================================================

        self.selection_slot_delete_shortcuts = []

        for slot_number in range(1, 6):

            slot_key = getattr(Qt.Key, f"Key_{slot_number}")

            ctrl_sequence = QKeySequence(Qt.KeyboardModifier.ControlModifier | slot_key)

            delete_slot_shortcut = QShortcut(ctrl_sequence, self)

            delete_slot_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

            delete_slot_shortcut.setAutoRepeat(False)

            delete_slot_shortcut.activated.connect(
                lambda number=slot_number: self.delete_selection_slot(number)
            )

            self.selection_slot_delete_shortcuts.append(delete_slot_shortcut)

        # =====================================================
        # F6 - ИЗЛИЗАНЕ ОТ АКТИВНАТА МАРКИРОВКА
        # =====================================================

        self.exit_selection_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F6), self)

        self.exit_selection_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.exit_selection_shortcut.setAutoRepeat(False)

        self.exit_selection_shortcut.activated.connect(self.exit_active_selection)

        # =====================================================
        # F5 - ФОКУС КЪМ АНАЛИЗА
        # =====================================================

        self.analyze_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F5), self)

        self.analyze_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.analyze_shortcut.setAutoRepeat(False)

        self.analyze_shortcut.activated.connect(lambda: self.analyze_button.setFocus())

        # =====================================================
        # F4 - ФОКУС КЪМ ЗАРЕДИ MP3
        # =====================================================

        self.load_mp3_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F4), self)

        self.load_mp3_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.load_mp3_shortcut.setAutoRepeat(False)

        self.load_mp3_shortcut.activated.connect(lambda: self.load_button.setFocus())

        # =====================================================
        # F7 - ФОКУС КЪМ РАЗДЕЛИ
        # =====================================================

        self.split_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F7), self)

        self.split_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.split_shortcut.setAutoRepeat(False)

        self.split_shortcut.activated.connect(lambda: self.split_button.setFocus())

        # =====================================================
        # TAB - ОТ РАЗДЕЛИ КЪМ ЗАТВОРИ
        # =====================================================

        self.tab_to_close_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Tab),
            self,
        )

        self.tab_to_close_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)

        self.tab_to_close_shortcut.setAutoRepeat(False)

        self.tab_to_close_shortcut.activated.connect(
            lambda: (
                self.close_button.setFocus(Qt.FocusReason.TabFocusReason)
                if QApplication.focusWidget() is self.split_button
                else None
            )
        )

        # =====================================================
        # VLC PLAYER
        # =====================================================

        self.vlc_instance = vlc.Instance()

        if self.vlc_instance is None:

            raise RuntimeError(language_manager.get("vlc_init_error"))

        self.vlc_player = self.vlc_instance.media_player_new()

        # =====================================================
        # UI
        # =====================================================

        self.build_ui()
        self.refresh_language_texts()
        self.load_button.setFocus()

    # =====================================================
    # ФОКУСИРАНЕ НА AUDIO SPLITTER
    # =====================================================

    def _restore_focus(self):

        if self.isMinimized() or not self.isVisible():

            return

        self.raise_()

        self.activateWindow()

        QApplication.setActiveWindow(self)

        if hasattr(self, "load_button"):

            self.load_button.setFocus(
                Qt.FocusReason.ActiveWindowFocusReason,
            )

        else:

            self.setFocus(
                Qt.FocusReason.ActiveWindowFocusReason,
            )

    # =====================================================
    # ПОКАЗВАНЕ = АКТИВИРАМЕ AUDIO SPLITTER
    # =====================================================

    def showEvent(self, event):

        super().showEvent(event)

        QTimer.singleShot(
            0,
            self._activate_splitter,
        )

    def _activate_splitter(self):

        parent = self.parentWidget()

        # =================================================
        # ДЪРЖИМ ОСНОВНИЯ ПРОЗОРЕЦ ТЕХНИЧЕСКИ АКТИВЕН
        # А БЛОКИРАМЕ ВХОДА ЧРЕЗ EVENT FILTER
        # =================================================

        if parent is not None:

            parent.setEnabled(True)

        self._set_parent_input_blocked(True)

        self._restore_focus()

    # =====================================================
    # БЛОКИРАМЕ ВХОДА КЪМ ОСНОВНИЯ ПРОЗОРЕЦ
    # БЕЗ ДА ДЕАКТИВИРАМЕ НЕГОВИЯ ПРОЗОРЕЦ
    # =====================================================

    def _set_parent_input_blocked(self, blocked):

        self._block_parent_input = blocked

        app = QApplication.instance()

        if app is None:

            return

        if blocked and not self._event_filter_installed:

            app.installEventFilter(self)

            self._event_filter_installed = True

        elif not blocked and self._event_filter_installed:

            app.removeEventFilter(self)

            self._event_filter_installed = False

    # =====================================================
    # БЛОКИРАМЕ САМО ВХОДА КЪМ ОСНОВНИЯ ПРОЗОРЕЦ
    # =====================================================

    def eventFilter(self, watched, event):

        if not self._block_parent_input or self.isMinimized():

            return super().eventFilter(watched, event)

        parent = self.parentWidget()

        if parent is None:

            return super().eventFilter(watched, event)

        if isinstance(watched, QWidget):

            parent_window = parent.window()

            watched_window = watched.window()

            if watched_window is parent_window:

                if event.type() in (
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseButtonRelease,
                    QEvent.Type.MouseButtonDblClick,
                    QEvent.Type.Wheel,
                    QEvent.Type.KeyPress,
                    QEvent.Type.KeyRelease,
                    QEvent.Type.ShortcutOverride,
                    QEvent.Type.ContextMenu,
                    QEvent.Type.InputMethod,
                ):

                    return True

                if event.type() == QEvent.Type.FocusIn:

                    QTimer.singleShot(
                        0,
                        self._restore_focus,
                    )

                    return True

                if event.type() == QEvent.Type.WindowActivate:

                    QTimer.singleShot(
                        0,
                        self._restore_focus,
                    )

                    return True

        return super().eventFilter(watched, event)

    # =====================================================
    # ЗАПАЗВАМЕ ПОЗИЦИЯТА ПРИ ПРЕМЕСТВАНЕ НА ПРОЗОРЕЦА
    # =====================================================

    def moveEvent(self, event):

        super().moveEvent(event)

        if self.isMinimized():

            return

        normal_geometry = self.normalGeometry()

        self.window_settings.setValue(
            "splitter_window_x",
            normal_geometry.x(),
        )

        self.window_settings.setValue(
            "splitter_window_y",
            normal_geometry.y(),
        )

        self.window_settings.sync()

    # =====================================================
    # МИНИМИЗИРАНЕ = ВРЕМЕННО ОСВОБОЖДАВАМЕ ОСНОВНИЯ ПРОЗОРЕЦ
    # =====================================================

    def changeEvent(self, event):

        super().changeEvent(event)

        if event.type() != QEvent.Type.WindowStateChange:

            return

        parent = self.parentWidget()

        # =================================================
        # ПРИ МИНИМИЗИРАНЕ
        # ОСВОБОЖДАВАМЕ ОСНОВНИЯ ПРОЗОРЕЦ
        # =================================================

        if self.isMinimized():

            self._set_parent_input_blocked(False)

            normal_geometry = self.normalGeometry()

            self.window_settings.setValue(
                "splitter_window_x",
                normal_geometry.x(),
            )

            self.window_settings.setValue(
                "splitter_window_y",
                normal_geometry.y(),
            )

            self.window_settings.sync()

            if parent is not None:

                parent.setEnabled(True)

            return

        # =================================================
        # ПРИ ВЪЗСТАНОВЯВАНЕ
        # ОТНОВО БЛОКИРАМЕ ОСНОВНИЯ ПРОЗОРЕЦ
        # =================================================

        if parent is not None:

            parent.setEnabled(True)

        self._set_parent_input_blocked(True)

        QTimer.singleShot(
            150,
            self._restore_focus,
        )

    # =====================================================
    # ОСНОВЕН UI
    # =====================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(18, 18, 18, 18)

        main_layout.setSpacing(14)

        # =====================================================
        # ЗАГЛАВИЕ
        # =====================================================

        self.title_label = QLabel(language_manager.get("split_title_header"))

        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 8px;
            }
        """)

        main_layout.addWidget(self.title_label)

        # =====================================================
        # ГОРЕН ПАНЕЛ
        # =====================================================

        top_panel = QFrame()

        top_panel.setMinimumHeight(82)

        top_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 #15192F,
                    stop:0.5 #292F5A,
                    stop:1 #3B2054
                );

                border: 2px solid #6878D8;
                border-radius: 16px;
            }

            QPushButton {
                color: white;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                padding: 11px 22px;
            }

            QPushButton:hover {
                border: 2px solid white;
            }

            QPushButton:pressed {
                padding-top: 13px;
                padding-bottom: 9px;
            }

            QPushButton#loadMp3Button {
                background: #39457D;
                border: 1px solid #8795F0;
                min-width: 170px;
            }

            QPushButton#loadMp3Button:hover {
                background: #4A58A0;
                border: 2px solid #BFC8FF;
            }

            QPushButton#loadMp3Button:focus {
                border: 4px solid white;
            }

            QPushButton#playButton {
                background: #138A3D;
                border: 1px solid #63E89A;
                min-width: 70px;
            }

            QPushButton#playButton:hover {
                background: #22C55E;
                border: 2px solid #8AFFB0;
            }

            QPushButton#pauseButton {
                background: #007C91;
                border: 1px solid #8AF5FF;
                min-width: 70px;
            }

            QPushButton#pauseButton:hover {
                background: #00ACC1;
                border: 2px solid #B8FAFF;
            }

            QPushButton#stopButton {
                background: #A81916;
                border: 1px solid #FF9A97;
                min-width: 70px;
            }

            QPushButton#stopButton:hover {
                background: #E53935;
                border: 2px solid #FFC1BF;
            }

            QLabel#sectionLabel {
                color: #BFC8FF;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        top_layout = QHBoxLayout(top_panel)

        top_layout.setContentsMargins(18, 10, 18, 10)

        top_layout.setSpacing(12)

        # =====================================================
        # ЗАРЕЖДАНЕ
        # =====================================================

        load_area = QVBoxLayout()

        load_area.setSpacing(2)

        self.load_label = QLabel(language_manager.get("section_file"))

        self.load_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.load_label.setObjectName("sectionLabel")

        self.load_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.load_button = QPushButton(language_manager.get("load_mp3"))

        self.load_button.setObjectName("loadMp3Button")

        self.load_button.setMinimumHeight(44)

        self.load_button.clicked.connect(self.load_mp3)

        load_area.addWidget(self.load_label)

        load_area.addWidget(self.load_button)

        # =====================================================
        # PLAYBACK
        # =====================================================

        self.play_button = QPushButton("▶")

        self.play_button.setObjectName("playButton")

        self.play_button.setMinimumSize(62, 44)

        self.play_button.setToolTip(language_manager.get("play_tooltip"))

        self.play_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.play_button.clicked.connect(self.play_audio)

        self.pause_button = QPushButton("⏸")

        self.pause_button.setObjectName("pauseButton")

        self.pause_button.setMinimumSize(62, 44)

        self.pause_button.setToolTip(language_manager.get("pause_tooltip"))

        self.pause_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.pause_button.clicked.connect(self.pause_audio)

        self.stop_button = QPushButton("⏹")

        self.stop_button.setObjectName("stopButton")

        self.stop_button.setMinimumSize(62, 44)

        self.stop_button.setToolTip(language_manager.get("stop_tooltip"))

        self.stop_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.stop_button.clicked.connect(self.stop_audio)

        playback_buttons = QHBoxLayout()

        playback_buttons.setSpacing(8)

        playback_buttons.addWidget(self.play_button)

        playback_buttons.addWidget(self.pause_button)

        playback_buttons.addWidget(self.stop_button)

        playback_controls = QVBoxLayout()

        playback_controls.setSpacing(2)

        playback_controls.addLayout(playback_buttons)

        top_layout.addLayout(load_area)

        top_layout.addStretch(1)

        top_layout.addLayout(playback_controls)

        top_layout.addStretch(1)

        main_layout.addWidget(top_panel)

        # =====================================================
        # ИМЕ НА ФАЙЛА
        # =====================================================

        self.file_label = QLabel(language_manager.get("no_loaded_mp3"))

        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_label.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 18px;
                background: #202124;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        main_layout.addWidget(self.file_label)

        # =====================================================
        # ПРОГРЕС НА ЗАРЕЖДАНЕТО
        # =====================================================

        self.loading_frame = QFrame()

        self.loading_frame.setFixedHeight(145)

        self.loading_frame.setMaximumWidth(600)

        self.loading_frame.setStyleSheet("""
            QFrame {
                background: #202124;
                border: 2px solid #6878D8;
                border-radius: 14px;
            }

            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }

            QProgressBar {
                background: #303134;
                border: 1px solid #666;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-height: 24px;
            }

            QProgressBar::chunk {
                background: #22C55E;
                border-radius: 7px;
            }
        """)

        loading_layout = QVBoxLayout(self.loading_frame)

        loading_layout.setContentsMargins(22, 14, 22, 14)

        loading_layout.setSpacing(8)

        self.loading_label = QLabel(language_manager.get("loading_mp3"))

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_time_layout = QHBoxLayout()

        self.loading_elapsed_label = QLabel(
            language_manager.get("elapsed", time="00:00")
        )

        self.loading_elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_remaining_label = QLabel(
            language_manager.get("remaining", time="00:00")
        )

        self.loading_remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_elapsed_label.hide()

        self.loading_remaining_label.hide()

        self.loading_time_layout.addStretch()

        self.loading_time_layout.addWidget(self.loading_elapsed_label)

        self.loading_time_layout.addSpacing(30)

        self.loading_time_layout.addWidget(self.loading_remaining_label)

        self.loading_time_layout.addStretch()

        loading_layout.addLayout(self.loading_time_layout)

        loading_layout.addWidget(self.loading_label)

        # =================================================
        # ПРОГРЕС ЛЕНТА
        # =================================================

        self.loading_progress = QProgressBar()
        self.loading_progress.setMinimumWidth(500)

        self.loading_progress.setRange(0, 100)

        self.loading_progress.setValue(0)

        loading_layout.addWidget(self.loading_progress)

        self.loading_frame.hide()

        # =====================================================
        # КОНТЕЙНЕР ЗА WAVEFORM + LOADING
        # =====================================================

        waveform_container = QFrame()

        waveform_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        waveform_container_layout = QGridLayout(waveform_container)

        waveform_container_layout.setContentsMargins(0, 0, 0, 0)

        waveform_container_layout.setSpacing(0)

        # =====================================================
        # WAVEFORM
        # =====================================================

        waveform_frame = QFrame()

        waveform_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        waveform_frame.setStyleSheet("""
            QFrame {
                background: #151515;
                border: 2px solid #6878D8;
                border-radius: 14px;
            }
        """)

        waveform_layout = QVBoxLayout(waveform_frame)

        waveform_layout.setContentsMargins(10, 8, 10, 8)

        waveform_layout.setSpacing(4)

        # =====================================================
        # ЗАГЛАВИЕ НА WAVEFORM
        # =====================================================

        self.waveform_title = QLabel(language_manager.get("audio_waveform"))

        self.waveform_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.waveform_title.setStyleSheet("""
            QLabel {
                color: #BFC8FF;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 2px;
            }
        """)

        waveform_layout.addWidget(self.waveform_title)

        # =====================================================
        # WAVEFORM
        # =====================================================

        self.waveform_plot = ClickablePlotWidget()

        self.waveform_plot.setBackground("#111111")

        self.waveform_plot.showGrid(x=False, y=True, alpha=0.12)

        self.waveform_plot.hideAxis("left")

        self.waveform_plot.hideAxis("bottom")

        self.waveform_plot.setMouseEnabled(x=False, y=False)

        self.waveform_plot.setMenuEnabled(False)

        self.waveform_plot.setContentsMargins(0, 0, 0, 0)

        self.waveform_plot.clicked_x.connect(self.on_waveform_clicked)

        self.waveform_plot.selection_changed.connect(self.on_selection_changed)

        self.waveform_plot.zoom_changed.connect(self.on_waveform_zoom_changed)

        # =====================================================
        # НУЛЕВА ЛИНИЯ
        # =====================================================

        zero_line = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(self.current_theme["table_grid"], width=1)
        )

        self.waveform_plot.addItem(zero_line)

        waveform_layout.addWidget(self.waveform_plot, 1)

        # =====================================================
        # ХОРИЗОНТАЛНА НАВИГАЦИОННА ЛЕНТА
        # =====================================================

        self.waveform_scrollbar = QSlider(Qt.Orientation.Horizontal)

        self.waveform_scrollbar.setMinimum(0)

        self.waveform_scrollbar.setMaximum(100000)

        self.waveform_scrollbar.setValue(0)

        self.waveform_scrollbar.setTracking(True)

        self.waveform_scrollbar.setFixedHeight(12)

        self.waveform_scrollbar.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #2A2A2A;
                border: 1px solid #555555;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                width: 50px;
                margin: -4px 0;
                background: #6878D8;
                border: 1px solid #8795F0;
                border-radius: 6px;
            }

            QSlider::handle:horizontal:hover {
                background: #8795F0;
            }
        """)

        self.waveform_scrollbar.hide()

        waveform_layout.addWidget(self.waveform_scrollbar)

        # =====================================================
        # СВЪРЗВАМЕ SCROLLBAR С WAVEFORM
        # =====================================================

        self.waveform_scrollbar.valueChanged.connect(self.scroll_waveform)

        # =====================================================
        # ВРЕМЕВА ЛИНИЯ ПОД WAVEFORM
        # =====================================================

        waveform_time_layout = QHBoxLayout()

        waveform_time_layout.setContentsMargins(4, 0, 4, 0)

        waveform_time_layout.setSpacing(0)

        self.waveform_start_label = QLabel("00:00:00")

        self.waveform_end_label = QLabel("00:00:00")

        # =====================================================
        # ИНДИКАТОР ЗА РЕЖИМ НА МАРКИРАНЕ
        # =====================================================

        self.selection_mode_label = QLabel(
            "💡  " + language_manager.get("fast_mode").replace("🟢  ", "", 1)
        )

        self.selection_mode_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        self.waveform_start_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        self.waveform_end_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        waveform_time_layout.addWidget(self.waveform_start_label)

        waveform_time_layout.addStretch()

        waveform_time_layout.addWidget(self.selection_mode_label)

        waveform_time_layout.addStretch()

        waveform_time_layout.addWidget(self.waveform_end_label)

        waveform_layout.addLayout(waveform_time_layout)

        # =====================================================
        # WAVEFORM + LOADING В ЕДНО И СЪЩО МЯСТО
        # =====================================================

        waveform_container_layout.addWidget(waveform_frame, 0, 0)

        waveform_container_layout.addWidget(
            self.loading_frame, 0, 0, Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(waveform_container, 1)

        # =====================================================
        # АНАЛИЗ
        # =====================================================

        analysis_panel = QFrame()

        analysis_panel.setStyleSheet("""
            QFrame {
                background: #202124;
                border: 1px solid #555;
                border-radius: 12px;
            }

            QPushButton {
                background: #303F9F;
                color: white;
                border: 1px solid #7986CB;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #3949AB;
            }

            QPushButton:focus {
                border: 4px solid white;
            }
        """)

        analysis_layout = QHBoxLayout(analysis_panel)

        analysis_layout.setContentsMargins(12, 10, 12, 10)

        # =====================================================
        # СЛОТОВЕ ЗА ЗАПАЗЕНИ МАРКИРОВКИ
        # =====================================================

        self.selection_slot_buttons = []

        for slot_number in range(1, 6):

            slot_button = QPushButton(str(slot_number))

            slot_button.setFixedSize(32, 32)

            slot_button.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
            )

            slot_button.setStyleSheet("""
                QPushButton {
                    background: #303030;
                    color: #777777;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    font-size: 20px;
                    font-weight: bold;
                    padding: 0px;
                }

                QPushButton:hover {
                    background: #3F3F3F;
                    color: white;
                }

                QPushButton:pressed {
                    background: #252525;
                }
            """)

            analysis_layout.addWidget(slot_button, 0, Qt.AlignmentFlag.AlignVCenter)

            self.selection_slot_buttons.append(slot_button)

        # =====================================================
        # СВОБОДНО ПРОСТРАНСТВО ПРЕДИ БУТОНА
        # =====================================================

        analysis_layout.addStretch()

        # =====================================================
        # БУТОН АНАЛИЗ - ЦЕНТЪР НА ЦЕЛИЯ ПАНЕЛ
        # =====================================================

        self.analyze_button = QPushButton(language_manager.get("analyze_find_songs"))

        self.analyze_button.clicked.connect(self.analyze_songs)

        analysis_layout.addWidget(self.analyze_button, 0, Qt.AlignmentFlag.AlignVCenter)

        # =====================================================
        # СВОБОДНО ПРОСТРАНСТВО СЛЕД БУТОНА
        # =====================================================

        analysis_layout.addStretch()

        # =====================================================
        # ДЯСНО НЕВИДИМО ПРОСТРАНСТВО
        # РАВНО НА ШИРИНАТА НА 5-ТЕ СЛОТА
        # =====================================================

        analysis_layout.addSpacing(184)

        # =====================================================
        # ДОБАВЯМЕ ПАНЕЛА
        # =====================================================

        main_layout.addWidget(analysis_panel)

        # =====================================================
        # СПИСЪК
        # =====================================================

        self.songs_table = QTableWidget()

        self.songs_table.setStyleSheet("""
            QTableWidget {
                background: #202124;
                alternate-background-color: #2A2A2A;
                gridline-color: #555555;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }

            QTableWidget::item:hover {
                background: transparent;
            }

            QHeaderView::section {
                background: #303030;
                color: white;
                border: 1px solid #555555;
                padding: 8px;
                font-size: 18px;
                font-weight: bold;
            }

            QScrollBar:vertical {
                width: 14px;
                background: #202124;
                margin: 0px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #6878D8;
                min-height: 30px;
                border-radius: 0px;
                border: none;
            }

            QScrollBar::handle:vertical:hover {
                background: #8795F0;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: transparent;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #202124;
            }
        """)

        self.songs_table.verticalHeader().setVisible(False)

        self.songs_table.setColumnCount(5)

        self.songs_table.setHorizontalHeaderLabels(
            [
                language_manager.get("table_number"),
                language_manager.get("table_song"),
                language_manager.get("table_start"),
                language_manager.get("table_end"),
                language_manager.get("table_duration"),
            ]
        )

        self.songs_table.setMinimumHeight(160)

        self.songs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.songs_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        self.songs_table.setAlternatingRowColors(True)

        self.songs_table.horizontalHeader().setStretchLastSection(True)

        self.songs_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )

        self.songs_table.setColumnWidth(0, 60)
        self.songs_table.setColumnWidth(1, 320)
        self.songs_table.setColumnWidth(2, 150)
        self.songs_table.setColumnWidth(3, 150)
        self.songs_table.setColumnWidth(4, 170)

        main_layout.addWidget(self.songs_table)

        # ДОЛЕН ПАНЕЛ
        # =====================================================

        bottom_panel = QFrame()

        bottom_panel.setStyleSheet("""
            QFrame {
                background: #303134;
                border: 1px solid #555;
                border-radius: 12px;
            }

            QPushButton {
                background: #39457D;
                color: white;
                border: 1px solid #8795F0;
                border-radius: 10px;
                padding: 9px 20px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #505050;
            }

            QPushButton:focus {
                border: 4px solid white;
            }
        """)

        bottom_layout = QHBoxLayout(bottom_panel)

        bottom_layout.setContentsMargins(12, 10, 12, 10)

        self.split_button = QPushButton(language_manager.get("split_button"))
        self.split_button.clicked.connect(self.split_mp3)
        self.split_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.close_button = QPushButton("❌ " + language_manager.get("close"))
        self.close_button.clicked.connect(self.close)
        self.close_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # =====================================================
        # БЕЗОПАСЕН TAB ORDER ЗА БУТОНИТЕ
        # =====================================================

        if self.split_button.window() is self.close_button.window():

            self.setTabOrder(
                self.split_button,
                self.close_button,
            )

        bottom_layout.addStretch()

        bottom_layout.addWidget(self.split_button)

        bottom_layout.addStretch()

        bottom_layout.addWidget(self.close_button)

        main_layout.addWidget(bottom_panel)

    # =====================================================
    # ПРОВЕРКА И ПРИЛАГАНЕ НА ПРОМЯНА НА ЦВЕТОВАТА ТЕМА
    # =====================================================

    def check_theme_change(self):

        from PySide6.QtCore import QSettings
        from themes import set_theme, get_theme

        current_language = language_manager.get_language()

        if current_language != getattr(self, "_last_language", None):

            self._last_language = current_language
            self.refresh_language_texts()

        settings = QSettings("MP3_Order", "MP3_Order_PRO")

        theme_name = settings.value(
            "theme_name",
            "Лилаво-синя",
            type=str,
        )

        if theme_name == getattr(self, "_last_theme_name", None):

            return

        if not set_theme(theme_name):

            theme_name = "Лилаво-синя"

        self._last_theme_name = theme_name

        self.current_theme = get_theme(theme_name)

        self.refresh_theme_styles()

    # =====================================================
    # ОБНОВЯВАНЕ НА ЕЗИКА В РАЗДЕЛЯНЕ НА MP3
    # =====================================================

    def refresh_language_texts(self):

        self.setWindowTitle(language_manager.get("split_title"))

        self.title_label.setText(language_manager.get("split_title_header"))

        self.load_label.setText(language_manager.get("section_file"))

        self.waveform_title.setText(language_manager.get("audio_waveform"))

        self.load_button.setText(language_manager.get("load_mp3"))

        self.load_button.setToolTip(language_manager.get("open_mp3"))

        self.play_button.setToolTip(language_manager.get("play_tooltip"))

        self.pause_button.setToolTip(language_manager.get("pause_tooltip"))

        self.stop_button.setToolTip(language_manager.get("stop_tooltip"))

        if self.current_file is None:

            self.file_label.setText(language_manager.get("no_loaded_mp3"))

        current = self.loading_label.text()

        if current:

            self.loading_label.setText(language_manager.get("loading_mp3"))

        current = self.loading_elapsed_label.text()

        value = current.split(":", 1)[1].strip() if ":" in current else "00:00"

        self.loading_elapsed_label.setText(language_manager.get("elapsed", time=value))

        current = self.loading_remaining_label.text()

        value = current.split(":", 1)[1].strip() if ":" in current else "00:00"

        self.loading_remaining_label.setText(
            language_manager.get("remaining", time=value)
        )

        if (
            language_manager.get("precision_mode").split("  ", 1)[-1]
            in self.selection_mode_label.text()
            or "PRECISION" in self.selection_mode_label.text()
        ):

            self.selection_mode_label.setText(
                "💡  " + language_manager.get("precision_mode").replace("🔵  ", "", 1)
            )

        else:

            self.selection_mode_label.setText(
                "💡  " + language_manager.get("fast_mode").replace("🟢  ", "", 1)
            )

        self.analyze_button.setText(language_manager.get("analyze_find_songs"))

        self.split_button.setText(language_manager.get("split_button"))

        self.close_button.setText("❌ " + language_manager.get("close"))

        self.songs_table.setHorizontalHeaderLabels(
            [
                language_manager.get("table_number"),
                language_manager.get("table_song"),
                language_manager.get("table_start"),
                language_manager.get("table_end"),
                language_manager.get("table_duration"),
            ]
        )

    # =====================================================
    # ОБНОВЯВАНЕ НА ЦВЕТОВАТА ТЕМА В РАЗДЕЛЯНЕ НА MP3
    # =====================================================

    def refresh_theme_styles(self):

        theme = self.current_theme

        color_map = {
            "#202124": theme["window_bg"],
            "#15192F": theme["panel_bg"],
            "#292F5A": theme["panel_bg_2"],
            "#3B2054": theme["panel_bg_3"],
            "#FFFFFF": theme["main_text"],
            "#BDBDBD": theme["accent_light"],
            "#303134": theme["header_bg"],
            "#181818": theme["table_bg"],
            "#555555": theme["table_grid"],
            "#1E88E5": theme["table_selected"],
            "#39457D": theme["button_bg"],
            "#6878D8": theme["accent"],
            "#8795F0": theme["accent_light"],
            "#303F9F": theme["button_bg"],
            "#7986CB": theme["button_border"],
            "#3949AB": theme["accent"],
            "#2A2A2A": theme["table_bg"],
            "#303030": theme["button_bg"],
            "#444444": theme["table_grid"],
            "#AAAAAA": theme["accent_light"],
            "#111111": theme["table_bg"],
            "#151515": theme["panel_bg"],
            "#666666": theme["table_grid"],
            "#777777": theme["accent_light"],
            "#3F3F3F": theme["button_bg"],
            "#252525": theme["table_bg"],
            "#505050": theme["button_bg"],
            "#55AA55": theme["play_pressed"],
            "#5CFF5C": theme["play"],
            "#7FFF7F": theme["play"],
            "#8AFFB0": theme["play"],
            "#63E89A": theme["play"],
            "#FF9A97": theme["stop"],
            "#FFC1BF": theme["stop"],
            "#FF5555": theme["stop"],
            "#BFC8FF": theme["accent_light"],
            "#B388FF": theme["accent"],
            "#F39C12": theme["next"],
            "#B66A00": theme["next_pressed"],
            "#22C55E": theme["play"],
            "#138A3D": theme["play_pressed"],
            "#00ACC1": theme["pause"],
            "#007C91": theme["pause_pressed"],
            "#E53935": theme["stop"],
            "#A81916": theme["stop_pressed"],
        }

        widgets = [self] + self.findChildren(QWidget)

        if not hasattr(self, "_original_theme_styles"):
            self._original_theme_styles = {}

        for widget in widgets:

            if widget not in self._original_theme_styles:
                self._original_theme_styles[widget] = widget.styleSheet()

            original_style = self._original_theme_styles[widget]

            if not original_style:
                continue

            new_style = original_style

            for old_color, new_color in color_map.items():
                new_style = new_style.replace(old_color, new_color)

            widget.setStyleSheet(new_style)

        self.setStyleSheet(self.styleSheet() + f"""
            QToolTip {{
                background: {theme["tooltip_bg"]};
                color: {theme["tooltip_text"]};
                border: 2px solid {theme["tooltip_border"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }}
            """)

        self.refresh_theme_graphics()

    def refresh_theme_graphics(self):

        theme = self.current_theme

        # -----------------------------------------------------
        # WAVEFORM ОСНОВНА ЛИНИЯ
        # -----------------------------------------------------

        try:
            for item in self.waveform_plot.listDataItems():
                item.setPen(pg.mkPen(theme["accent"], width=1))
        except Exception:
            pass

        # -----------------------------------------------------
        # PYQTGRAPH ЛИНИИ
        # -----------------------------------------------------

        try:
            for item in self.waveform_plot.items():

                if isinstance(item, pg.InfiniteLine):

                    if item is getattr(self, "playback_line", None):
                        item.setPen(pg.mkPen(theme["main_text"], width=3))
                        continue

                    if item in getattr(self, "song_boundary_lines", []):
                        item.setPen(pg.mkPen(theme["stop"], width=2))
                        continue

                    item.setPen(pg.mkPen(theme["table_grid"], width=1))
        except Exception:
            pass

        # -----------------------------------------------------
        # АКТИВНА МАРКИРОВКА
        # -----------------------------------------------------

        try:
            region = getattr(self.waveform_plot, "selection_region", None)

            if region is not None:
                color = QColor(theme["accent"])
                color.setAlpha(70)
                region.setBrush(pg.mkBrush(color))
                region.setPen(pg.mkPen(theme["main_text"], width=1))
        except Exception:
            pass

        # -----------------------------------------------------
        # ЗАПАЗЕНИ СЛОТОВЕ
        # -----------------------------------------------------

        try:
            for region in getattr(
                self.waveform_plot,
                "saved_selection_regions",
                {},
            ).values():

                color = QColor(theme["accent"])
                color.setAlpha(45)
                region.setBrush(pg.mkBrush(color))
                region.setPen(pg.mkPen(theme["accent_light"], width=2))
        except Exception:
            pass

        # -----------------------------------------------------
        # БУТОНИ НА СЛОТОВЕТЕ
        # -----------------------------------------------------

        try:
            saved_slots = getattr(self, "saved_selection_slots", {})

            for slot_number in range(1, 6):
                self.update_selection_slot_button_color(
                    slot_number,
                    slot_number in saved_slots,
                )
        except Exception:
            pass

        # -----------------------------------------------------
        # ДИНАМИЧНО СЪОБЩЕНИЕ
        # -----------------------------------------------------

        message = getattr(self, "selection_slot_message", None)

        if message is not None:

            message.setStyleSheet(f"""
                QLabel {{
                    background: {theme["window_bg"]};
                    color: {theme["main_text"]};
                    border: 2px solid {theme["accent"]};
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 20px;
                    font-weight: bold;
                }}
            """)

    def load_mp3(self):

        dialog = QFileDialog(
            self,
            language_manager.get("load_dialog_title"),
        )

        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        dialog.setNameFilter("MP3 files (*.mp3)")

        dialog.setWindowTitle(language_manager.get("load_dialog_title"))

        dialog.setFocus()

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        selected_files = dialog.selectedFiles()

        if not selected_files:

            return

        file_path = selected_files[0]

        # =================================================
        # АКО ВЕЧЕ ЗАРЕЖДАМЕ
        # =================================================

        if self.decode_worker is not None and self.decode_worker.isRunning():

            return

        # =================================================
        # СПИРАМЕ ТЕКУЩОТО ВЪЗПРОИЗВЕЖДАНЕ
        # =================================================

        try:

            self.vlc_player.stop()

        except Exception:

            pass

        self.position_timer.stop()

        self.audio_playing = False

        self.is_paused = False

        # =================================================
        # ЗАПАЗВАМЕ ФАЙЛА
        # =================================================

        self.current_file = file_path
        self.analyzed_file = None

        self.current_duration = 0.0

        self.file_label.setText(os.path.basename(file_path))

        # =================================================
        # ПРОГРЕС
        # =================================================

        self.loading_label.setText("🎵 " + language_manager.get("loading_mp3"))

        self.loading_progress.setValue(0)

        self.loading_frame.show()

        self.load_button.setEnabled(False)

        # =================================================
        # ИЗЧИСТВАМЕ WAVEFORM
        # =================================================

        self.waveform_plot.clear()

        zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen("#555555", width=1),
        )

        self.waveform_plot.addItem(zero_line)

        # =================================================
        # НУЛИРАМЕ ВРЕМЕТО ВЪВ WAVEFORM
        # =================================================

        self.waveform_start_label.setText("00:00:00")

        self.waveform_end_label.setText("00:00:00")

        self.playback_line = None

        # =================================================
        # WORKER
        # =================================================

        self.decode_worker = AudioDecodeWorker(
            file_path,
            self,
        )

        self.decode_worker.progress_changed.connect(self.loading_progress.setValue)

        self.decode_worker.waveform_ready.connect(self.on_waveform_ready)

        self.decode_worker.error.connect(self.on_decode_error)

        self.decode_worker.worker_finished.connect(self.on_decode_finished)

        self.decode_worker.start()

    # =====================================================
    # PLAY AUDIO
    # =====================================================

    def play_audio(self):

        if not self.current_file:

            QMessageBox.information(
                self,
                language_manager.get("no_loaded_file_title"),
                language_manager.get("select_mp3_first"),
            )

            return

        if self.vlc_instance is None:

            QMessageBox.critical(
                self,
                language_manager.get("error"),
                language_manager.get("vlc_not_initialized"),
            )

            return

        if self.vlc_player is None:

            QMessageBox.critical(
                self,
                language_manager.get("error"),
                language_manager.get("vlc_player_not_initialized"),
            )

            return

        try:

            media = self.vlc_instance.media_new(self.current_file)

            self.vlc_player.set_media(media)

            self.vlc_player.play()

            self.is_paused = False

            self.audio_playing = True

            self.position_timer.start()

        except Exception as e:

            QMessageBox.critical(
                self,
                language_manager.get("playback_error_title"),
                language_manager.get("playback_error", error=str(e)),
            )

    # =====================================================
    # PAUSE AUDIO
    # =====================================================

    def pause_audio(self):

        if self.vlc_player is None:

            return

        try:

            self.vlc_player.pause()

            self.audio_playing = False

            self.is_paused = True

        except Exception as e:

            QMessageBox.critical(
                self,
                language_manager.get("pause_error_title"),
                language_manager.get("pause_error", error=str(e)),
            )

    # =====================================================
    # STOP AUDIO
    # =====================================================

    def stop_audio(self):

        if self.vlc_player is None:

            return

        try:

            self.vlc_player.stop()

            self.position_timer.stop()

            self.audio_playing = False

            self.is_paused = False

            if self.playback_line is not None:

                self.playback_line.setPos(0)

                self.playback_line.hide()

            self.waveform_start_label.setText("00:00:00")

        except Exception as e:

            QMessageBox.critical(
                self,
                language_manager.get("stop_error_title"),
                language_manager.get("stop_error", error=str(e)),
            )

    # =====================================================
    # ПРОМЯНА НА МАРКИРОВКАТА
    # =====================================================

    def on_selection_changed(self, start, end):

        self.selection_region = self.waveform_plot.selection_region

    # =====================================================
    # F6 - ИЗЛИЗАНЕ ОТ АКТИВНАТА МАРКИРОВКА
    # =====================================================

    def exit_active_selection(self):

        if self.current_duration <= 0:

            return

        if self.vlc_player is None:

            return

        try:

            # =================================================
            # ВЗЕМАМЕ АКТИВНАТА МАРКИРОВКА
            # =================================================

            region_item = self.waveform_plot.selection_region

            # =================================================
            # АКО НЯМА АКТИВНА МАРКИРОВКА
            # ИМАМЕ ПРЕДВИД ПОСЛЕДНИЯ ЗАПАЗЕН СЛОТ
            # =================================================

            if region_item is None:

                if (
                    not hasattr(self, "saved_selection_slots")
                    or not self.saved_selection_slots
                ):

                    return

                # =============================================
                # ВЗЕМАМЕ ПОСЛЕДНИЯ ЗАПАЗЕН СЛОТ
                # =============================================

                last_slot_number = next(reversed(self.saved_selection_slots))

                start, end = self.saved_selection_slots[last_slot_number]

                start = float(start)

                end = float(end)

            else:

                # =============================================
                # ИМАМЕ АКТИВНА МАРКИРОВКА
                # =============================================

                region = region_item.getRegion()

                start_value = region[0]
                end_value = region[1]

                if isinstance(start_value, (list, tuple)):

                    start = float(start_value[0])

                else:

                    start = float(start_value)

                if isinstance(end_value, (list, tuple)):

                    end = float(end_value[0])

                else:

                    end = float(end_value)

            # =================================================
            # ТЪРСИМ НАЙ-БЛИЗКОТО НЕМАРКИРАНО МЯСТО СЛЕД НЕГО
            # =================================================

            step = 0.01

            new_position = min(self.current_duration, end + step)

            # =================================================
            # ПРОВЕРЯВАМЕ ЗА ЗАПАЗЕНИ МАРКИРОВКИ
            # =================================================

            if hasattr(self, "saved_selection_slots"):

                saved_ranges = []

                for saved_start, saved_end in self.saved_selection_slots.values():

                    saved_start = float(saved_start)

                    saved_end = float(saved_end)

                    if saved_end > end:

                        saved_ranges.append((saved_start, saved_end))

                saved_ranges.sort(key=lambda item: item[0])

                for saved_start, saved_end in saved_ranges:

                    if new_position < saved_start:

                        break

                    if saved_start <= new_position <= saved_end:

                        new_position = min(self.current_duration, saved_end + step)

            # =================================================
            # ОСВОБОЖДАВАМЕ САМО АКТИВНАТА МАРКИРОВКА
            # ЗАПАЗЕНИТЕ СЛОТОВЕ ОСТАВАТ
            # =================================================

            self.waveform_plot.clear_selection()

            self.selection_region = None

            # =================================================
            # СПИРАМЕ МИГАНЕТО
            # =================================================

            if hasattr(self, "playback_blink_timer"):

                self.playback_blink_timer.stop()

            # =================================================
            # ПОКАЗВАМЕ БЯЛАТА ЛИНИЯ ПОСТОЯННО
            # =================================================

            if self.playback_line is not None:

                self.playback_line.setPos(new_position)

                self.playback_line.show()

            # =================================================
            # ПРЕМЕСТВАМЕ VLC
            # =================================================

            self.vlc_player.set_time(int(new_position * 1000))

            # =================================================
            # АКТУАЛИЗИРАМЕ ВРЕМЕТО
            # =================================================

            self.waveform_start_label.setText(self.format_time(new_position))

            # =================================================
            # СЪОБЩЕНИЕ - БЯЛАТА ЛИНИЯ Е СВОБОДНА
            # =================================================

            if not hasattr(self, "selection_slot_message"):

                self.selection_slot_message = QLabel(self)

                self.selection_slot_message.setStyleSheet("""
                    QLabel {
                        background: #202124;
                        color: white;
                        border: 1px solid #6878D8;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)

                self.selection_slot_message.setAlignment(Qt.AlignmentFlag.AlignCenter)

                self.selection_slot_message.hide()

            # =================================================
            # ТАЙМЕР ЗА 4 СЕКУНДИ
            # =================================================

            if not hasattr(self, "selection_slot_message_timer"):

                self.selection_slot_message_timer = QTimer(self)

                self.selection_slot_message_timer.setSingleShot(True)

                self.selection_slot_message_timer.timeout.connect(
                    self.selection_slot_message.hide
                )

            # =================================================
            # ПОКАЗВАМЕ СЪОБЩЕНИЕТО
            # =================================================

            self.selection_slot_message.setText(language_manager.get("line_free"))

            self.selection_slot_message.setStyleSheet("""
                QLabel {
                    background: #202124;
                    color: white;
                    border: 2px solid #6878D8;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 20px;
                    font-weight: bold;
                }
            """)

            self.selection_slot_message.adjustSize()

            self.selection_slot_message.raise_()

            x = 20

            y = max(10, self.height() - self.selection_slot_message.height() - 20)

            self.selection_slot_message.move(x, y)

            self.selection_slot_message.show()

            self.selection_slot_message.raise_()

            self.selection_slot_message_timer.start(4000)

            # =================================================
            # ЗВУК
            # =================================================

            QApplication.beep()

        except Exception as e:

            print("EXIT ACTIVE SELECTION ERROR:", e)

    # =====================================================
    # CTRL + 1 - 5 - ИЗТРИВАНЕ НА ЗАПАЗЕН СЛОТ
    # =====================================================

    def delete_selection_slot(self, slot_number):

        if slot_number < 1 or slot_number > 5:

            return

        # =================================================
        # ПРОВЕРЯВАМЕ ДАЛИ ИМА РЕЧНИК СЪС СЛОТОВЕ
        # =================================================

        if not hasattr(self, "saved_selection_slots"):

            self.saved_selection_slots = {}

        # =================================================
        # АКО СЛОТЪТ Е ПРАЗЕН
        # =================================================

        if slot_number not in self.saved_selection_slots:

            if hasattr(self, "selection_slot_message"):

                self.selection_slot_message.setText(
                    language_manager.get("slot_empty", slot=slot_number)
                )

                self.selection_slot_message.adjustSize()

                self.selection_slot_message.move(20, self.height() - 90)

                self.selection_slot_message.show()

                if hasattr(self, "selection_slot_message_timer"):

                    self.selection_slot_message_timer.start(4000)

            QApplication.beep()

            return

        # =================================================
        # ПРОВЕРЯВАМЕ ДАЛИ ТОЗИ СЛОТ Е АКТИВНИЯТ МАРКЕР
        # =================================================

        active_region = self.waveform_plot.selection_region

        active_slot_matches = False

        if active_region is not None:

            try:

                region = active_region.getRegion()

                active_start_value = region[0]
                active_end_value = region[1]

                if isinstance(active_start_value, (list, tuple)):

                    active_start = float(active_start_value[0])

                else:

                    active_start = float(active_start_value)

                if isinstance(active_end_value, (list, tuple)):

                    active_end = float(active_end_value[0])

                else:

                    active_end = float(active_end_value)

                saved_start_value, saved_end_value = self.saved_selection_slots[
                    slot_number
                ]

                saved_start = float(saved_start_value)

                saved_end = float(saved_end_value)

                tolerance = 0.001

                if (
                    abs(active_start - saved_start) <= tolerance
                    and abs(active_end - saved_end) <= tolerance
                ):

                    active_slot_matches = True

            except Exception as e:

                active_slot_matches = False

        # =================================================
        # ПРЕМАХВАМЕ ВИДИМИЯ ЗАПАЗЕН МАРКЕР
        # =================================================

        try:

            self.waveform_plot.clear_saved_selection_region(slot_number)

        except Exception as e:

            print("CLEAR SAVED SLOT REGION ERROR:", e)

        # =================================================
        # ПРЕМАХВАМЕ СЛОТА ОТ ПАМЕТТА
        # =================================================

        self.saved_selection_slots.pop(slot_number, None)

        # =================================================
        # АКО Е БИЛ АКТИВНИЯТ МАРКЕР
        # ПРЕМАХВАМЕ И АКТИВНАТА МАРКИРОВКА
        # =================================================

        if active_slot_matches:

            try:

                self.waveform_plot.clear_selection()

            except Exception:

                pass

            self.selection_region = None

        self.saved_selection_slots.pop(slot_number, None)

        # =================================================
        # ВРЪЩАМЕ ЦВЕТА НА СЛОТА КАТО ПРАЗЕН
        # =================================================

        self.update_selection_slot_button_color(slot_number, False)

        # =================================================
        # АКО Е БИЛ АКТИВНИЯТ МАРКЕР
        # ПРЕМАХВАМЕ И АКТИВНАТА МАРКИРОВКА
        # =================================================

        if active_slot_matches:

            try:

                self.waveform_plot.clear_selection()

            except Exception:

                pass

            self.selection_region = None

        # =================================================
        # СЪОБЩЕНИЕ
        # =================================================

        if not hasattr(self, "selection_slot_message"):

            self.selection_slot_message = QLabel(self)

            self.selection_slot_message.setStyleSheet("""
                QLabel {
                    background: #202124;
                    color: white;
                    border: 1px solid #6878D8;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

            self.selection_slot_message.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.selection_slot_message.hide()

        # =================================================
        # ТАЙМЕР ЗА 4 СЕКУНДИ
        # =================================================

        if not hasattr(self, "selection_slot_message_timer"):

            self.selection_slot_message_timer = QTimer(self)

            self.selection_slot_message_timer.setSingleShot(True)

            self.selection_slot_message_timer.timeout.connect(
                self.selection_slot_message.hide
            )

        self.selection_slot_message.setText(
            language_manager.get("slot_deleted", slot=slot_number)
        )

        self.selection_slot_message.adjustSize()

        self.selection_slot_message.move(20, self.height() - 90)

        self.selection_slot_message.show()

        self.selection_slot_message_timer.start(4000)

        # =================================================
        # ЗВУК
        # =================================================

        QApplication.beep()

    # =====================================================
    # ЦВЯТ НА СЛОТА - ЗАЕТ / ПРАЗЕН
    # =====================================================

    def update_selection_slot_button_color(self, slot_number, occupied):

        if slot_number < 1 or slot_number > 5:

            return

        if not hasattr(self, "selection_slot_buttons"):

            return

        if slot_number > len(self.selection_slot_buttons):

            return

        slot_button = self.selection_slot_buttons[slot_number - 1]

        theme = self.current_theme

        if occupied:

            slot_button.setStyleSheet(f"""
                QPushButton {{
                    background: {theme["button_bg"]};
                    color: #5CFF5C;
                    border: 2px solid #5CFF5C;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0px;
                }}

                QPushButton:hover {{
                    background: {theme["button_bg"]};
                    color: #7FFF7F;
                    border: 2px solid #7FFF7F;
                }}

                QPushButton:pressed {{
                    background: {theme["table_bg"]};
                }}
            """)

        else:

            slot_button.setStyleSheet(f"""
                QPushButton {{
                    background: {theme["button_bg"]};
                    color: {theme["accent_light"]};
                    border: 1px solid {theme["table_grid"]};
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0px;
                }}

                QPushButton:hover {{
                    background: {theme["button_bg"]};
                    color: {theme["main_text"]};
                }}

                QPushButton:pressed {{
                    background: {theme["table_bg"]};
                }}
            """)

    # =====================================================
    # СЛОТОВЕ 1 - 5 - ЗАПАЗВАНЕ / ВРЪЩАНЕ
    # =====================================================

    def handle_selection_slot(self, slot_number):

        if slot_number < 1 or slot_number > 5:

            return

        # =================================================
        # СЪЗДАВАМЕ РЕЧНИК ЗА ЗАПАЗЕНИТЕ СЛОТОВЕ
        # =================================================

        if not hasattr(self, "saved_selection_slots"):

            self.saved_selection_slots = {}

        # =================================================
        # СЪЗДАВАМЕ ЕДНО ВРЕМЕННО СЪОБЩЕНИЕ
        # =================================================

        if not hasattr(self, "selection_slot_message"):

            self.selection_slot_message = QLabel(self)

            self.selection_slot_message.setStyleSheet("""
                QLabel {
                    background: #202124;
                    color: white;
                    border: 1px solid #6878D8;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

            self.selection_slot_message.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.selection_slot_message.hide()

        # =================================================
        # ТАЙМЕР ЗА 4 СЕКУНДИ
        # =================================================

        if not hasattr(self, "selection_slot_message_timer"):

            self.selection_slot_message_timer = QTimer(self)

            self.selection_slot_message_timer.setSingleShot(True)

            self.selection_slot_message_timer.timeout.connect(
                self.selection_slot_message.hide
            )

        # =================================================
        # ВЗЕМАМЕ ТЕКУЩАТА АКТИВНА МАРКИРОВКА
        # =================================================

        region_item = self.waveform_plot.selection_region

        # =================================================
        # СЛОТЪТ Е ПРАЗЕН → ЗАПАЗВАМЕ
        # =================================================

        if slot_number not in self.saved_selection_slots:

            if region_item is None:

                self.selection_slot_message.setStyleSheet("""
                    QLabel {
                        background: #202124;
                        color: white;
                        border: 1px solid #6878D8;
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)

                self.selection_slot_message.setText(
                    language_manager.get("slot_no_selection", slot=slot_number)
                )

                self.selection_slot_message.adjustSize()

                self.selection_slot_message.move(20, self.height() - 90)

                self.selection_slot_message.show()

                self.selection_slot_message_timer.start(4000)

                QApplication.beep()

                return

            try:

                region = region_item.getRegion()

                start_value = region[0]
                end_value = region[1]

                if isinstance(start_value, (list, tuple)):

                    start = float(start_value[0])

                else:

                    start = float(start_value)

                if isinstance(end_value, (list, tuple)):

                    end = float(end_value[0])

                else:

                    end = float(end_value)

                if end <= start:

                    return

                # =============================================
                # ЗАПАЗВАМЕ ТОЧНИТЕ ГРАНИЦИ В СЛОТА
                # =============================================

                self.saved_selection_slots[slot_number] = (start, end)

                # =============================================
                # ОЦВЕТЯВАМЕ СЛОТА КАТО ЗАЕТ
                # =============================================

                self.update_selection_slot_button_color(slot_number, True)

                # =============================================
                # СЪЗДАВАМЕ ПОСТОЯННО ВИДИМАТА
                # ЗАПАЗЕНА МАРКИРОВКА
                # =============================================

                self.waveform_plot.set_saved_selection_region(slot_number, start, end)

                # =============================================
                # ОСВОБОЖДАВАМЕ САМО АКТИВНАТА МАРКИРОВКА
                # ЗАПАЗЕНИЯТ СЛОТ ОСТАВА ВИДИМ
                # =============================================

                try:

                    self.waveform_plot.clear_selection()

                except Exception:

                    pass

                self.selection_region = None

                # =============================================
                # ПОКАЗВАМЕ СЪОБЩЕНИЕ
                # =============================================

                self.selection_slot_message.setText(
                    language_manager.get("slot_saved", slot=slot_number)
                )

                self.selection_slot_message.adjustSize()

                self.selection_slot_message.move(20, self.height() - 90)

                self.selection_slot_message.show()

                self.selection_slot_message_timer.start(4000)

                QApplication.beep()

                return

            except Exception as e:

                return

        # =================================================
        # СЛОТЪТ ВЕЧЕ Е ЗАПАЗЕН → ВРЪЩАМЕ ГО
        # =================================================

        try:

            start, end = self.saved_selection_slots[slot_number]

            # =============================================
            # ВРЪЩАМЕ СИНЯТА АКТИВНА МАРКИРОВКА
            # =============================================

            self.waveform_plot.update_selection_region(start, end)

            self.selection_region = self.waveform_plot.selection_region

            # =============================================
            # ПРОВЕРЯВАМЕ ДАЛИ ВИЗУАЛНИЯТ СЛОТ
            # СЪЩЕСТВУВА
            # =============================================

            self.waveform_plot.set_saved_selection_region(slot_number, start, end)

            # =============================================
            # ВРЪЩАМЕ БЯЛАТА ЛИНИЯ ВЪТРЕ В МАРКИРОВКАТА
            # =============================================

            if self.vlc_player is not None:

                current_time_ms = self.vlc_player.get_time()

                if current_time_ms >= 0:

                    current_seconds = current_time_ms / 1000.0

                    new_position = max(start, min(current_seconds, end))

                    self.vlc_player.set_time(int(new_position * 1000))

                    if self.playback_line is not None:

                        self.playback_line.setPos(new_position)

                        self.playback_line.show()

                    self.waveform_start_label.setText(self.format_time(new_position))

            # =============================================
            # ПОКАЗВАМЕ КРАЯ НА МАРКИРОВКАТА
            # =============================================

            self.waveform_end_label.setText(self.format_time(end))

            # =============================================
            # СЪОБЩЕНИЕ
            # =============================================

            self.selection_slot_message.setText(
                language_manager.get("slot_restored", slot=slot_number)
            )

            self.selection_slot_message.adjustSize()

            self.selection_slot_message.move(20, self.height() - 90)

            self.selection_slot_message.show()

            self.selection_slot_message_timer.start(4000)

            QApplication.beep()

        except Exception as e:

            print("RESTORE SELECTION SLOT ERROR:", e)

    # =====================================================
    # ВЪЗСТАНОВЯВАМЕ ВИДИМИТЕ СЛОТОВЕ СЛЕД DELETE
    # =====================================================

    def restore_saved_selection_regions_after_delete(self):

        try:

            if not hasattr(self, "saved_selection_slots"):

                return

            # =================================================
            # ИЗЧИСТВАМЕ СТАРИТЕ ВИДИМИ СЛОТОВЕ
            # =================================================

            self.waveform_plot.clear_all_saved_selection_regions()

            # =================================================
            # ВЪЗСТАНОВЯВАМЕ ОСТАНАЛИТЕ СЛОТОВЕ
            # =================================================

            for slot_number, slot_range in self.saved_selection_slots.items():

                start_value = slot_range[0]
                end_value = slot_range[1]

                start = float(start_value)
                end = float(end_value)

                if end <= start:

                    continue

                self.waveform_plot.set_saved_selection_region(slot_number, start, end)

        except Exception as e:

            print("RESTORE SAVED SELECTION REGIONS ERROR:", e)

    # =====================================================
    # DELETE - ИЗТРИВАМЕ МАРКИРАНИЯ АУДИО УЧАСТЪК
    # =====================================================

    def delete_selected_waveform(self):

        if not self.current_file:

            return

        if self.current_duration <= 0:

            return

        try:

            # =================================================
            # ТЕКУЩА ПОЗИЦИЯ НА БЯЛАТА ЛИНИЯ
            # =================================================

            current_seconds = 0.0

            if self.vlc_player is not None:

                current_time_ms = self.vlc_player.get_time()

                if current_time_ms >= 0:

                    current_seconds = current_time_ms / 1000.0

            # =================================================
            # ОПРЕДЕЛЯМЕ ДАЛИ СМЕ В ЗАПАЗЕН СЛОТ
            # =================================================

            target_slot_number = None

            target_slot_start = 0.0

            target_slot_end = 0.0

            # =================================================
            # ПЪРВО ПРОВЕРЯВАМЕ АКТИВНАТА МАРКИРОВКА
            # АКО ИМА - DELETE ИЗТРИВА НЕЯ
            # =================================================

            active_region = getattr(
                self.waveform_plot,
                "selection_region",
                None,
            )

            if active_region is not None:

                try:

                    active_region_values = active_region.getRegion()

                    active_start_value = active_region_values[0]
                    active_end_value = active_region_values[1]

                    if isinstance(active_start_value, (list, tuple)):

                        active_start = float(active_start_value[0])

                    else:

                        active_start = float(active_start_value)

                    if isinstance(active_end_value, (list, tuple)):

                        active_end = float(active_end_value[0])

                    else:

                        active_end = float(active_end_value)

                    start = active_start
                    end = active_end

                    # Активната маркировка е с приоритет.
                    # Не я превръщаме в DELETE SLOT.
                    target_slot_number = None

                    print(
                        "ACTIVE SELECTION DELETE:",
                        start,
                        end,
                    )

                except Exception as e:

                    print(
                        "CHECK ACTIVE SELECTION ERROR:",
                        e,
                    )

                    return

            else:

                # =================================================
                # НЯМА АКТИВНА МАРКИРОВКА
                # ПРОВЕРЯВАМЕ БЯЛАТА ЛИНИЯ ЗА ЗАПАЗЕН СЛОТ
                # =================================================

                if hasattr(self, "saved_selection_slots"):

                    matching_slots = []

                    for (
                        slot_number,
                        slot_range,
                    ) in self.saved_selection_slots.items():

                        saved_start = float(slot_range[0])

                        saved_end = float(slot_range[1])

                        if saved_start <= current_seconds <= saved_end:

                            matching_slots.append(
                                (
                                    slot_number,
                                    saved_start,
                                    saved_end,
                                )
                            )

                    # =============================================
                    # АКО ИМАМЕ СЛОТ
                    # =============================================

                    if matching_slots:

                        matching_slots.sort(key=lambda item: item[2] - item[1])

                        target_slot_number, target_slot_start, target_slot_end = (
                            matching_slots[0]
                        )

                # =================================================
                # АКО СМЕ В ЗАПАЗЕН СЛОТ
                # =================================================

                if target_slot_number is not None:

                    start = float(target_slot_start)

                    end = float(target_slot_end)

                else:

                    return

            # =================================================
            # ПРОВЕРЯВАМЕ ГРАНИЦИТЕ
            # =================================================

            start = max(0.0, min(start, self.current_duration))

            end = max(0.0, min(end, self.current_duration))

            if end <= start:

                return

            # =================================================
            # ЗАПАЗВАМЕ ВИСОКА ТОЧНОСТ
            # =================================================

            start_time = f"{start:.6f}"

            end_time = f"{end:.6f}"

            # =================================================
            # ЗАПАЗВАМЕ СТАРИТЕ СЛОТОВЕ
            # =================================================

            old_saved_selection_slots = {}

            if hasattr(self, "saved_selection_slots"):

                for slot_number, slot_range in self.saved_selection_slots.items():

                    old_saved_selection_slots[slot_number] = (
                        float(slot_range[0]),
                        float(slot_range[1]),
                    )

            # =================================================
            # ИЗЧИСЛЯВАМЕ ПРОДЪЛЖИТЕЛНОСТТА НА ИЗТРИТИЯ УЧАСТЪК
            # =================================================

            deleted_duration = end - start

            # =================================================
            # ОБНОВЯВАМЕ ОСТАНАЛИТЕ СЛОТОВЕ
            # =================================================

            updated_saved_selection_slots = {}

            for slot_number, slot_range in old_saved_selection_slots.items():

                saved_start = slot_range[0]

                saved_end = slot_range[1]

                # =============================================
                # ИЗТРИВАМЕ САМО ЦЕЛЕВИЯ СЛОТ
                # =============================================

                if target_slot_number is not None and slot_number == target_slot_number:

                    continue

                # =============================================
                # СЛОТЪТ Е ПРЕД ИЗТРИТИЯ УЧАСТЪК
                # =============================================

                if saved_end <= start:

                    new_start = saved_start

                    new_end = saved_end

                # =============================================
                # СЛОТЪТ Е СЛЕД ИЗТРИТИЯ УЧАСТЪК
                # =============================================

                elif saved_start >= end:

                    new_start = saved_start - deleted_duration

                    new_end = saved_end - deleted_duration

                # =============================================
                # СЛОТЪТ СЕ ЗАСЯГА ОТ ИЗТРИВАНЕТО
                # =============================================

                else:

                    new_start = saved_start

                    if saved_start >= start:

                        new_start = start

                    if saved_end <= end:

                        new_end = new_start

                    else:

                        new_end = saved_end - deleted_duration

                # =============================================
                # ПАЗИМ САМО СМИСЛЕНИ СЛОТОВЕ
                # =============================================

                new_start = max(
                    0.0,
                    min(new_start, self.current_duration),
                )

                new_end = max(
                    0.0,
                    min(new_end, self.current_duration),
                )

                if new_end > new_start:

                    updated_saved_selection_slots[slot_number] = (
                        new_start,
                        new_end,
                    )

            # =================================================
            # ЗАПАЗВАМЕ ТЕКУЩИЯ ФАЙЛ И СТАРИТЕ СЛОТОВЕ ЗА UNDO
            # =================================================

            old_file = self.current_file

            self.undo_history.append(old_file)
            self.undo_analysis_history.append(list(self.detected_songs))

            self.undo_slots_history.append(
                {
                    slot_number: (
                        float(slot_range[0]),
                        float(slot_range[1]),
                    )
                    for slot_number, slot_range in old_saved_selection_slots.items()
                }
            )

            # =================================================
            # ПРИЛАГАМЕ НОВИТЕ ПОЗИЦИИ НА СЛОТОВЕТЕ
            # =================================================

            self.saved_selection_slots = updated_saved_selection_slots

            # =================================================
            # СПИРАМЕ ВЪЗПРОИЗВЕЖДАНЕТО
            # =================================================

            self.stop_audio()

            # =================================================
            # FFmpeg
            # =================================================

            if getattr(sys, "frozen", False):

                project_dir = os.path.dirname(os.path.abspath(sys.executable))

            else:

                project_dir = os.path.dirname(os.path.abspath(__file__))

            ffmpeg_path = os.path.join(
                project_dir,
                "ffmpeg-n9.0-latest-win64-gpl-9.0",
                "bin",
                "ffmpeg.exe",
            )

            if not os.path.isfile(ffmpeg_path):

                self.undo_history.pop()

                self.saved_selection_slots = old_saved_selection_slots

                QMessageBox.critical(
                    self,
                    language_manager.get("error"),
                    language_manager.get("ffmpeg_not_found"),
                )

                return

            # =================================================
            # ВРЕМЕНЕН ИЗХОДЕН MP3
            # =================================================

            temp_output = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)

            output_file = temp_output.name

            temp_output.close()

            # =================================================
            # ПРОВЕРЯВАМЕ КАКВО ОСТАВА
            # =================================================

            before_exists = start > 0.01

            after_exists = end < self.current_duration - 0.01

            # =================================================
            # АКО Е МАРКИРАН ЦЕЛИЯТ ФАЙЛ
            # =================================================

            if not before_exists and not after_exists:

                if os.path.exists(output_file):

                    os.remove(output_file)

                self.current_file = None

                # =================================================
                # ИЗЧИСТВАМЕ АНАЛИЗА
                # =================================================

                self.detected_songs = []

                self.songs_table.setRowCount(0)

                # =================================================
                # ИЗЧИСТВАМЕ ЧЕРВЕНИТЕ ГРАНИЦИ
                # =================================================

                if hasattr(self, "song_boundary_lines"):

                    for line in self.song_boundary_lines:

                        try:

                            self.waveform_plot.removeItem(line)

                        except Exception:

                            pass

                    self.song_boundary_lines.clear()

                # =================================================
                # ВСИЧКИ СЛОТОВ СЕ ИЗЧИСТВАТ
                # =================================================

                self.saved_selection_slots = {}

                try:

                    self.waveform_plot.clear_all_saved_selection_regions()

                except Exception:

                    pass

                self.current_duration = 0.0

                self.audio_playing = False

                self.is_paused = False

                self.position_timer.stop()

                self.waveform_plot.clear()

                self.file_label.setText(language_manager.get("no_loaded_mp3"))

                self.waveform_start_label.setText("00:00:00")

                self.waveform_end_label.setText("00:00:00")

                self.playback_line = None

                try:

                    self.waveform_plot.removeItem(self.selection_region)

                except Exception:

                    pass

                self.selection_region = None

                self.load_button.setFocus()

                return

            # =================================================
            # FFMPEG ЧАСТИ
            # =================================================

            filter_parts = []

            if before_exists:

                filter_parts.append(
                    f"[0:a]atrim=start=0:end={start_time},"
                    f"asetpts=PTS-STARTPTS[part1]"
                )

            if after_exists:

                filter_parts.append(
                    f"[0:a]atrim=start={end_time}," f"asetpts=PTS-STARTPTS[part2]"
                )

            # =================================================
            # СЪСТАВЯМЕ РЕЗУЛТАТА
            # =================================================

            if before_exists and after_exists:

                filter_complex = (
                    ";".join(filter_parts) + ";[part1][part2]"
                    "concat=n=2:v=0:a=1[outa]"
                )

                map_label = "[outa]"

            elif before_exists:

                filter_complex = ";".join(filter_parts)

                map_label = "[part1]"

            else:

                filter_complex = ";".join(filter_parts)

                map_label = "[part2]"

            # =================================================
            # СЪЗДАВАМЕ DELETE WORKER
            # =================================================

            self.delete_worker = DeleteWorker(
                ffmpeg_path,
                self.current_file,
                filter_complex,
                map_label,
                output_file,
                trim_start=end_time if not before_exists else None,
                parent=self,
            )

            # =================================================
            # ГРЕШКА ПРИ DELETE
            # =================================================

            def delete_worker_error(message):

                if self.undo_history:

                    self.undo_history.pop()

                if self.undo_slots_history:

                    self.undo_slots_history.pop()

                self.saved_selection_slots = old_saved_selection_slots

                if os.path.exists(output_file):

                    try:

                        os.remove(output_file)

                    except Exception:

                        pass

                self.loading_frame.hide()

                self.load_button.setEnabled(True)

                QMessageBox.critical(
                    self,
                    language_manager.get("delete_error_title"),
                    message,
                )

            # =================================================
            # DELETE УСПЕШНО
            # =================================================

            def delete_worker_finished(result_file):

                # =================================================
                # ЗАПАЗВАМЕ НОВИЯ РАБОТЕН ФАЙЛ
                # =================================================

                self.current_file = result_file

                # =================================================
                # ИЗЧИСТВАМЕ СТАРИЯ АНАЛИЗ
                # =================================================

                self.detected_songs = []

                self.songs_table.setRowCount(0)

                # =================================================
                # ПРЕМАХВАМЕ СТАРИТЕ ГРАНИЦИ
                # =================================================

                if hasattr(self, "song_boundary_lines"):

                    for line in self.song_boundary_lines:

                        try:

                            self.waveform_plot.removeItem(line)

                        except Exception:

                            pass

                    self.song_boundary_lines.clear()

                # =================================================
                # ПРЕМАХВАМЕ АКТИВНАТА МАРКИРОВКА
                # =================================================

                try:

                    self.waveform_plot.clear_selection()

                except Exception:

                    pass

                self.selection_region = None

                # =================================================
                # ПРЕМАХВАМЕ СТАРИТЕ ВИДИМИ СЛОТОВЕ
                # =================================================

                try:

                    self.waveform_plot.clear_all_saved_selection_regions()

                except Exception:

                    pass

                # =================================================
                # НУЛИРАМЕ СЪСТОЯНИЕТО
                # =================================================

                self.current_duration = 0.0

                self.audio_playing = False

                self.is_paused = False

                self.position_timer.stop()

                self.playback_line = None

                self.waveform_plot.clear()

                self.waveform_start_label.setText("00:00:00")

                self.waveform_end_label.setText("00:00:00")

                self.file_label.setText(os.path.basename(result_file))

                # =================================================
                # ЗАРЕЖДАМЕ НОВИЯ WAVEFORM
                # =================================================

                self.loading_label.setText(language_manager.get("update_audio"))

                self.loading_progress.setValue(0)

                self.loading_progress.setRange(0, 100)

                self.loading_frame.show()

                self.load_button.setEnabled(False)

                self.decode_worker = AudioDecodeWorker(
                    result_file,
                    self,
                )

                self.decode_worker.progress_changed.connect(
                    self.loading_progress.setValue
                )

                self.decode_worker.waveform_ready.connect(self.on_waveform_ready)

                self.decode_worker.error.connect(self.on_decode_error)

                self.decode_worker.worker_finished.connect(self.on_decode_finished)

                self.decode_worker.worker_finished.connect(
                    self.restore_saved_selection_regions_after_delete
                )

                self.decode_worker.start()

            # =================================================
            # СВЪРЗВАМЕ DELETE WORKER
            # =================================================

            self.delete_worker.error.connect(delete_worker_error)

            self.delete_worker.delete_finished.connect(delete_worker_finished)

            # =================================================
            # ПОКАЗВАМЕ, ЧЕ ИЗТРИВАНЕТО ЗАПОЧВА
            # =================================================

            self.loading_label.setText(
                language_manager.get("delete_selection_progress")
            )

            self.loading_progress.setRange(0, 0)

            self.loading_frame.show()

            self.loading_frame.raise_()

            QApplication.processEvents()

            # =================================================
            # СТАРТИРАМЕ DELETE WORKER
            # =================================================

            self.delete_worker.start()

            print(
                "DELETE WORKER STARTED:",
                start_time,
                end_time,
            )

        except Exception as e:

            if self.undo_history and self.undo_history[-1] == self.current_file:

                self.undo_history.pop()

            self.saved_selection_slots = old_saved_selection_slots

            QMessageBox.critical(
                self,
                language_manager.get("delete_error_title"),
                language_manager.get("delete_error", error=str(e)),
            )

    # =====================================================
    # ESC - ОСВОБОЖДАВАМЕ МАРКИРОВКАТА
    # =====================================================

    def clear_waveform_selection(self):

        if self.selection_region is None:

            return

        try:

            self.waveform_plot.clear_selection()

        except Exception:

            pass

        self.selection_region = None

    # =====================================================
    # АНАЛИЗИРАМЕ И НАМИРАМЕ ПЕСНИТЕ
    # =====================================================

    def analyze_songs(self):

        if not self.current_file:

            QMessageBox.information(
                self,
                language_manager.get("no_loaded_file_title"),
                language_manager.get("select_mp3_first"),
            )

            return

        # =================================================
        # ПРОВЕРЯВАМЕ ДАЛИ ТОЗИ ФАЙЛ ВЕЧЕ Е АНАЛИЗИРАН
        # =================================================

        if hasattr(self, "analyzed_file") and self.analyzed_file == self.current_file:

            QMessageBox.information(
                self,
                language_manager.get("analysis_already_done_title"),
                language_manager.get("analysis_already_done"),
            )

            return

        # =================================================
        # ПРОВЕРЯВАМЕ ДАЛИ АНАЛИЗЪТ ВЕЧЕ СЕ ИЗПЪЛНЯВА
        # =================================================

        if (
            hasattr(self, "analysis_worker")
            and self.analysis_worker is not None
            and self.analysis_worker.isRunning()
        ):

            return

        # =================================================
        # ПОКАЗВАМЕ ПРОГРЕСА НА АНАЛИЗА
        # =================================================

        self.loading_label.setText(language_manager.get("analysis_loading"))

        self.operation_in_progress = True

        self.loading_progress.setValue(0)

        self.loading_frame.show()

        # =================================================
        # ДЕАКТИВИРАМЕ БУТОНА
        # =================================================

        self.analyze_button.setEnabled(False)

        # =================================================
        # СЪЗДАВАМЕ ANALYSIS WORKER
        # =================================================

        self.analysis_worker = SongAnalysisWorker(self.current_file, self)

        # =================================================
        # ПРОГРЕС
        # =================================================

        self.analysis_worker.progress_changed.connect(self.loading_progress.setValue)

        # =================================================
        # РЕЗУЛТАТ
        # =================================================

        self.analysis_worker.songs_ready.connect(self.on_songs_analyzed)

        # =================================================
        # ГРЕШКА
        # =================================================

        self.analysis_worker.error.connect(self.on_analysis_error)

        # =================================================
        # СТАРТИРАМЕ АНАЛИЗА
        # =================================================

        self.analysis_worker.start()

    # =====================================================
    # РАЗДЕЛЯМЕ MP3 ФАЙЛА
    # =====================================================

    def split_mp3(self):

        if not self.current_file:

            QMessageBox.information(
                self,
                language_manager.get("no_loaded_file_title"),
                language_manager.get("select_mp3_first"),
            )

            return

        if not hasattr(self, "detected_songs") or not self.detected_songs:

            QMessageBox.information(
                self,
                language_manager.get("analysis"),
                language_manager.get("analyze_first"),
            )

            return

        if not os.path.isfile(self.current_file):

            QMessageBox.warning(
                self,
                language_manager.get("error"),
                language_manager.get("loaded_file_missing"),
            )

            return

        # =====================================================
        # НАМИРАМЕ ПАПКАТА НА ПРОГРАМАТА
        # =====================================================

        if getattr(sys, "frozen", False):

            project_dir = os.path.dirname(os.path.abspath(sys.executable))

        else:

            project_dir = os.path.dirname(os.path.abspath(__file__))

        # =====================================================
        # НАМИРАМЕ FFMPEG
        # =====================================================

        ffmpeg_path = os.path.join(
            project_dir,
            "ffmpeg-n9.0-latest-win64-gpl-9.0",
            "bin",
            "ffmpeg.exe",
        )

        if not os.path.isfile(ffmpeg_path):

            QMessageBox.critical(
                self,
                language_manager.get("error"),
                language_manager.get("ffmpeg_not_found"),
            )

            return

        source_folder = os.path.dirname(self.current_file)

        source_name = os.path.splitext(os.path.basename(self.current_file))[0]

        export_folder = os.path.join(source_folder, "MP3_SPLIT")

        os.makedirs(export_folder, exist_ok=True)

        # =================================================
        # ПОДГОТОВКА НА ПРОЦЕСА ЗА РАЗДЕЛЯНЕ
        # =================================================

        total_songs = len(self.detected_songs)

        self.loading_label.setText(language_manager.get("split_wait"))
        self.operation_in_progress = True

        self.loading_elapsed_label.hide()

        self.loading_remaining_label.show()

        self.loading_remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_remaining_label.setText(
            language_manager.get("remaining_plain", time="30")
        )

        self.loading_progress.setRange(0, 0)

        self.loading_frame.show()

        self.loading_frame.raise_()

        QApplication.processEvents()

        # =================================================
        # ПЛАВЕН ВИЗУАЛЕН ПРОГРЕС
        # =================================================

        self._split_target_progress = 0

        self._split_visual_progress = 0

        self._split_progress_finished = False

        if hasattr(self, "split_progress_timer"):

            self.split_progress_timer.stop()

        self.split_progress_timer = QTimer(self)

        self.split_progress_timer.setInterval(30)

        def animate_split_progress():

            if self._split_visual_progress < self._split_target_progress:

                self._split_visual_progress += 1

                self.loading_progress.setValue(self._split_visual_progress)

            if self._split_progress_finished and self._split_visual_progress >= 100:

                self.split_progress_timer.stop()

        def update_split_progress(value):

            value = max(
                0,
                min(100, int(value)),
            )

            if value > self._split_target_progress:

                self._split_target_progress = value

            if not self.split_progress_timer.isActive():

                self.split_progress_timer.start()

        self.split_progress_timer.timeout.connect(animate_split_progress)

        self.split_worker = SplitWorker(
            ffmpeg_path,
            self.current_file,
            self.detected_songs,
            export_folder,
            source_name,
            self,
        )

        self.split_worker.progress_changed.connect(update_split_progress)

        remaining_state = {
            "seconds": 0,
            "timer": None,
        }

        def update_split_time(
            elapsed_seconds,
            remaining_seconds,
        ):

            elapsed_minutes = elapsed_seconds // 60

            elapsed_seconds_part = elapsed_seconds % 60

            self.loading_elapsed_label.setText(
                language_manager.get(
                    "elapsed",
                    time=f"{elapsed_minutes:02d}:{elapsed_seconds_part:02d}",
                )
            )

            if remaining_seconds > 0:

                if remaining_state["seconds"] <= 0:

                    remaining_state["seconds"] = remaining_seconds

                    remaining_state["timer"] = QTimer(self)

                    remaining_state["timer"].setInterval(1000)

                    def decrease_remaining_time():

                        if remaining_state["seconds"] > 0:

                            remaining_state["seconds"] -= 1

                        remaining_minutes = remaining_state["seconds"] // 60

                        remaining_seconds_part = remaining_state["seconds"] % 60

                        self.loading_remaining_label.setText(
                            language_manager.get(
                                "remaining",
                                time=f"{remaining_minutes:02d}:{remaining_seconds_part:02d}",
                            )
                        )

                        if remaining_state["seconds"] <= 0:

                            remaining_state["timer"].stop()

                    remaining_state["timer"].timeout.connect(decrease_remaining_time)

                    remaining_state["timer"].start()

            if remaining_state["seconds"] > 0:

                remaining_minutes = remaining_state["seconds"] // 60

                remaining_seconds_part = remaining_state["seconds"] % 60

                self.loading_remaining_label.setText(
                    language_manager.get(
                        "remaining",
                        time=f"{remaining_minutes:02d}:{remaining_seconds_part:02d}",
                    )
                )

        self.split_worker.time_changed.connect(update_split_time)

        self.split_worker.error.connect(
            lambda message: QMessageBox.critical(
                self,
                language_manager.get("split_error"),
                message,
            )
        )

        def split_finished():

            if remaining_state["timer"] is not None:

                remaining_state["timer"].stop()

            self._split_target_progress = 100

            self._split_progress_finished = True
            self.operation_in_progress = False

            if not self.split_progress_timer.isActive():

                self.split_progress_timer.start()

            def hide_loading():

                if self._split_visual_progress >= 100:

                    self.loading_progress.setValue(100)

                    self.loading_remaining_label.setText(
                        language_manager.get("remaining", time="00:00")
                    )

                    self.loading_frame.hide()

                    QApplication.beep()

                    message_box = QMessageBox(self)

                    message_box.setIcon(QMessageBox.Icon.Information)

                    message_box.setWindowTitle(
                        language_manager.get("split_success_title")
                    )

                    message_box.setText(language_manager.get("split_success"))

                    message_box.setStyleSheet("""
                        QMessageBox {
                            font-size: 14px;
                        }

                        QLabel {
                            font-size: 14px;
                            padding: 4px;
                        }

                        QPushButton {
                            min-width: 70px;
                            min-height: 30px;
                            font-size: 14px;
                        }
                    """)

                    message_box.exec()

                else:

                    QTimer.singleShot(30, hide_loading)

            hide_loading()

        self.split_worker.worker_finished.connect(split_finished)

        def update_waiting_time():

            remaining = self.waiting_seconds

            self.loading_remaining_label.setText(
                language_manager.get("remaining_plain", time=str(remaining))
            )

            if remaining <= 0:

                self.waiting_timer.stop()

        self.waiting_seconds = 30

        self.waiting_timer = QTimer(self)

        self.waiting_timer.setInterval(1000)

        self.waiting_timer.timeout.connect(
            lambda: (
                setattr(
                    self,
                    "waiting_seconds",
                    max(
                        0,
                        self.waiting_seconds - 1,
                    ),
                ),
                update_waiting_time(),
            )
        )

        self.waiting_timer.start()

        def start_split_process():

            self.waiting_timer.stop()

            self.loading_elapsed_label.show()

            self.loading_elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.loading_elapsed_label.setText(
                language_manager.get("elapsed", time="00:00")
            )

            self.loading_remaining_label.show()

            self.loading_remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.loading_remaining_label.setText(
                language_manager.get("remaining", time="--:--")
            )

            remaining_state["seconds"] = 0

            if remaining_state["timer"] is not None:

                remaining_state["timer"].stop()

                remaining_state["timer"] = None

            self._split_target_progress = 0

            self._split_visual_progress = 0

            self._split_progress_finished = False

            self.loading_progress.setRange(0, 100)

            self.loading_progress.setValue(0)

            self.loading_label.setText(language_manager.get("splitting"))

            QApplication.processEvents()

            self.split_progress_timer.start()

            self.operation_in_progress = True

            self.split_worker.start()

        QTimer.singleShot(30000, start_split_process)

    # =====================================================
    # ПОЛУЧАВАМЕ НАМЕРЕНИТЕ ПЕСНИ
    # =====================================================

    def on_songs_analyzed(self, songs):

        self.songs_table.show()

        self.songs_table.setRowCount(0)

        for index, song in enumerate(songs, start=1):

            start = float(song[0])

            end = float(song[1])

            duration = end - start

            row = self.songs_table.rowCount()

            self.songs_table.insertRow(row)

            self.songs_table.setItem(row, 0, QTableWidgetItem(str(index)))

            self.songs_table.setItem(
                row,
                1,
                QTableWidgetItem(language_manager.get("song_number", index=str(index))),
            )

            self.songs_table.setItem(row, 2, QTableWidgetItem(self.format_time(start)))

            self.songs_table.setItem(row, 3, QTableWidgetItem(self.format_time(end)))

            self.songs_table.setItem(
                row, 4, QTableWidgetItem(self.format_time(duration))
            )

        self.songs_table.resizeColumnsToContents()

        self.detected_songs = songs
        self.operation_in_progress = False

        # =================================================
        # ЗАПОМНЯМЕ ФАЙЛА САМО ПРИ УСПЕШЕН АНАЛИЗ
        # =================================================

        self.analyzed_file = self.current_file

        self.draw_song_boundaries()

        # =================================================
        # АНАЛИЗЪТ Е ГОТОВ
        # =================================================

        self.loading_progress.setValue(100)

        self.loading_label.setText(language_manager.get("analysis_ready"))

        QApplication.beep()

        # =================================================
        # СКРИВАМЕ ПРОГРЕСА СЛЕД 1.5 СЕКУНДИ
        # =================================================

        QTimer.singleShot(1500, self.loading_frame.hide)

        self.analyze_button.setEnabled(True)

    # =====================================================
    # ГРЕШКА ПРИ АНАЛИЗ
    # =====================================================

    def on_analysis_error(self, message):

        self.analyze_button.setEnabled(True)

        self.loading_frame.hide()

        QMessageBox.critical(self, language_manager.get("analysis"), message)

    # =====================================================
    # РИСУВАМЕ ГРАНИЦИТЕ НА ПЕСНИТЕ ВЪРХУ WAVEFORM
    # =====================================================

    def draw_song_boundaries(self):

        if not hasattr(self, "detected_songs"):

            return

        if not self.detected_songs:

            return

        if self.waveform_plot is None:

            return

        # =================================================
        # ИЗЧИСТВАМЕ СТАРИТЕ ГРАНИЦИ
        # =================================================

        if not hasattr(self, "song_boundary_lines"):

            self.song_boundary_lines = []

        for line in self.song_boundary_lines:

            try:

                self.waveform_plot.removeItem(line)

            except Exception:

                pass

        self.song_boundary_lines.clear()

        # =================================================
        # СЪЗДАВАМЕ НОВИТЕ ГРАНИЦИ
        # =================================================

        for index, song in enumerate(self.detected_songs):

            start = float(song[0])

            end = float(song[1])

            # =================================================
            # НАЧАЛНА ГРАНИЦА НА СЛЕДВАЩА ПЕСЕН
            # =================================================

            if index > 0:

                line = pg.InfiniteLine(
                    pos=start,
                    angle=90,
                    movable=False,
                    pen=pg.mkPen(self.current_theme["stop"], width=2),
                )

                self.waveform_plot.addItem(line)

                self.song_boundary_lines.append(line)

            # =================================================
            # КРАЙНА ГРАНИЦА НА ПОСЛЕДНАТА ПЕСЕН
            # =================================================

            if index == len(self.detected_songs) - 1:

                line = pg.InfiniteLine(
                    pos=end,
                    angle=90,
                    movable=False,
                    pen=pg.mkPen(self.current_theme["stop"], width=2),
                )

                self.waveform_plot.addItem(line)

                self.song_boundary_lines.append(line)

    # =====================================================
    # CTRL + A - МАРКИРАМЕ ЦЕЛИЯ ФАЙЛ
    # =====================================================

    def select_all_waveform(self):

        if self.current_duration <= 0:

            return

        # =================================================
        # ПРЕМАХВАМЕ СТАРАТА МАРКИРОВКА
        # =================================================

        self.waveform_plot.clear_selection()

        self.selection_region = None

        # =================================================
        # МАРКИРАМЕ ЦЕЛИЯ ФАЙЛ
        # =================================================

        self.waveform_plot.update_selection_region(0.0, self.current_duration)

        self.selection_region = self.waveform_plot.selection_region

        # =================================================
        # ВРЕМЕ
        # =================================================

        self.waveform_start_label.setText("00:00:00")

        self.waveform_end_label.setText(self.format_time(self.current_duration))

    # =====================================================
    # CTRL + Z - ВРЪЩАМЕ ПОСЛЕДНОТО ДЕЙСТВИЕ
    # =====================================================

    def undo_last_action(self):

        if not self.undo_history:

            return

        try:

            # =================================================
            # ВЗЕМАМЕ ПРЕДИШНИЯ РАБОТЕН ФАЙЛ
            # =================================================

            previous_file = self.undo_history.pop()

            previous_slots = {}

            if self.undo_slots_history:

                previous_slots = self.undo_slots_history.pop()

            previous_analysis = []

            if self.undo_analysis_history:

                previous_analysis = self.undo_analysis_history.pop()

            if not os.path.isfile(previous_file):

                QMessageBox.warning(
                    self,
                    language_manager.get("undo_missing_title"),
                    language_manager.get("undo_missing"),
                )

                return

            # =================================================
            # СПИРАМЕ ТЕКУЩОТО ВЪЗПРОИЗВЕЖДАНЕ
            # =================================================

            self.stop_audio()

            # =================================================
            # ВРЪЩАМЕ ПРЕДИШНИЯ ФАЙЛ
            # =================================================

            self.current_file = previous_file

            # =================================================
            # ВЪЗСТАНОВЯВАМЕ ЗАПАЗЕНИТЕ СЛОТОВЕ
            # =================================================

            self.saved_selection_slots = dict(previous_slots)
            self.detected_songs = list(previous_analysis)

            self.current_duration = 0.0

            self.audio_playing = False

            self.is_paused = False

            self.position_timer.stop()

            # =================================================
            # ИЗЧИСТВАМЕ МАРКИРОВКАТА
            # =================================================

            if self.selection_region is not None:

                try:

                    self.waveform_plot.removeItem(self.selection_region)

                except Exception:

                    pass

            self.selection_region = None

            # =================================================
            # ИЗЧИСТВАМЕ WAVEFORM
            # =================================================

            self.waveform_plot.clear()

            self.playback_line = None

            self.waveform_start_label.setText("00:00:00")

            self.waveform_end_label.setText("00:00:00")

            self.file_label.setText(os.path.basename(previous_file))

            # =================================================
            # ВЪЗСТАНОВЯВАМЕ СТАРИЯ АНАЛИЗ В ТАБЛИЦАТА
            # =================================================

            self.songs_table.show()

            self.songs_table.setRowCount(0)

            for index, song in enumerate(previous_analysis, start=1):

                start = float(song[0])

                end = float(song[1])

                duration = end - start

                row = self.songs_table.rowCount()

                self.songs_table.insertRow(row)

                self.songs_table.setItem(row, 0, QTableWidgetItem(str(index)))

                self.songs_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        language_manager.get("song_number", index=str(index))
                    ),
                )

                self.songs_table.setItem(
                    row, 2, QTableWidgetItem(self.format_time(start))
                )

                self.songs_table.setItem(
                    row, 3, QTableWidgetItem(self.format_time(end))
                )

                self.songs_table.setItem(
                    row, 4, QTableWidgetItem(self.format_time(duration))
                )

            self.songs_table.resizeColumnsToContents()

            # =================================================
            # ЗАРЕЖДАМЕ ПРЕДИШНИЯ WAVEFORM
            # =================================================

            self.loading_label.setText(language_manager.get("undo_progress"))

            self.loading_progress.setValue(0)

            self.loading_frame.show()

            self.load_button.setEnabled(False)

            self.decode_worker = AudioDecodeWorker(previous_file, self)

            self.decode_worker.progress_changed.connect(self.loading_progress.setValue)

            self.decode_worker.waveform_ready.connect(self.on_waveform_ready)

            self.decode_worker.error.connect(self.on_decode_error)

            self.decode_worker.worker_finished.connect(self.on_decode_finished)

            self.decode_worker.start()

        except Exception as e:

            QMessageBox.critical(
                self,
                language_manager.get("undo_error_title"),
                language_manager.get("undo_error", error=str(e)),
            )

    def keyPressEvent(self, event): ...

    # =====================================================
    # SPACE - PLAY / PAUSE
    # =====================================================

    def toggle_play_pause(self):

        if self.vlc_player is None:

            return

        try:

            # =================================================
            # ПРОВЕРЯВАМЕ ДИРЕКТНО СЪСТОЯНИЕТО НА VLC
            # =================================================

            if self.vlc_player.is_playing():

                self.pause_button.setDown(True)

                self.pause_button.setStyleSheet("""
                    QPushButton {
                        background: #005566;
                        color: white;
                        border: 3px solid #D9FBFF;
                        border-radius: 12px;
                        padding-top: 14px;
                        padding-bottom: 8px;
                    }
                """)

                QTimer.singleShot(
                    400,
                    lambda: (
                        self.pause_button.setDown(False),
                        self.pause_button.setStyleSheet(""),
                    ),
                )

                self.vlc_player.pause()

                self.audio_playing = False

                self.is_paused = True

                return

            # =================================================
            # АКО Е НА ПАУЗА → ПРОДЪЛЖАВАМЕ
            # =================================================

            if self.is_paused:

                self.play_button.setDown(True)

                self.play_button.setStyleSheet("""
                    QPushButton {
                        background: #0B5E2A;
                        color: white;
                        border: 3px solid #D9FFE7;
                        border-radius: 12px;
                        padding-top: 14px;
                        padding-bottom: 8px;
                    }
                """)

                QTimer.singleShot(
                    400,
                    lambda: (
                        self.play_button.setDown(False),
                        self.play_button.setStyleSheet(""),
                    ),
                )

                self.vlc_player.play()

                self.audio_playing = True

                self.is_paused = False

                self.position_timer.start()

                return

            # =================================================
            # НЯМА АКТИВНО ВЪЗПРОИЗВЕЖДАНЕ → PLAY
            # =================================================

            self.play_button.setDown(True)

            self.play_button.setStyleSheet("""
                QPushButton {
                    background: #0B5E2A;
                    color: white;
                    border: 3px solid #D9FFE7;
                    border-radius: 12px;
                    padding-top: 14px;
                    padding-bottom: 8px;
                }
            """)

            QTimer.singleShot(
                400,
                lambda: (
                    self.play_button.setDown(False),
                    self.play_button.setStyleSheet(""),
                ),
            )

            self.play_audio()

        except Exception as e:

            print("SPACE ERROR:", e)

    # =====================================================
    # ПРЕМИГВАНЕ НА БЯЛАТА PLAYBACK ЛИНИЯ
    # =====================================================

    def toggle_playback_line_visibility(self):

        if self.playback_line is None:

            return

        if self.playback_line.isVisible():

            self.playback_line.hide()

        else:

            self.playback_line.show()

    # =====================================================
    # АКТУАЛИЗИРАМЕ ПОЗИЦИЯТА НА ВЪЗПРОИЗВЕЖДАНЕ
    # =====================================================

    def update_playback_position(self):

        if self.vlc_player is None:

            return

        if self.current_duration <= 0:

            return

        if self.playback_line is None:

            return

        try:

            current_time_ms = self.vlc_player.get_time()

            if current_time_ms < 0:

                return

            current_seconds = current_time_ms / 1000.0

            # =================================================
            # ПРОВЕРЯВАМЕ ДАЛИ ИМА МАРКИРАНА ЧАСТ
            # =================================================

            region_item = self.selection_region

            selection_start = None
            selection_end = None

            if region_item is not None:

                region = region_item.getRegion()

                start_value = region[0]
                end_value = region[1]

                if isinstance(start_value, (list, tuple)):

                    selection_start = float(start_value[0])

                else:

                    selection_start = float(start_value)

                if isinstance(end_value, (list, tuple)):

                    selection_end = float(end_value[0])

                else:

                    selection_end = float(end_value)

                selection_start = max(0.0, min(selection_start, self.current_duration))

                selection_end = max(0.0, min(selection_end, self.current_duration))

            # =================================================
            # LOOP НА МАРКИРАНАТА ЧАСТ
            # =================================================

            if (
                self.audio_playing
                and not self.is_paused
                and selection_start is not None
                and selection_end is not None
                and selection_end > selection_start
                and current_seconds >= selection_end - 0.05
            ):

                self.vlc_player.set_time(int(selection_start * 1000))

                self.playback_line.setPos(selection_start)

                self.waveform_start_label.setText(self.format_time(selection_start))

                self.playback_line.show()

                return

            # =================================================
            # VLC МОЖЕ ВРЕМЕННО ДА НЕ ОТЧИТА PLAY ВЕДНАГА ПРИ СТАРТ
            # НЕ ГО ПРИЕМАМЕ ЗА КРАЙ НА ПЕСЕНТА
            # =================================================

            # =================================================
            # ДОСТИГНАТ КРАЯТ ПО ВРЕМЕ
            # =================================================

            if current_seconds >= self.current_duration - 0.1:

                self.position_timer.stop()

                self.audio_playing = False

                self.is_paused = False

                self.playback_line.setPos(self.current_duration)

                self.playback_line.hide()

                self.waveform_start_label.setText("00:00:00")

                return

            # =================================================
            # ОГРАНИЧАВАМЕ ПОЗИЦИЯТА
            # =================================================

            current_seconds = max(0.0, min(current_seconds, self.current_duration))

            # =================================================
            # МЕСТИМ БЯЛАТА ЛИНИЯ
            # =================================================

            self.playback_line.setPos(current_seconds)

            # =================================================
            # ОБНОВЯВАМЕ ВРЕМЕТО
            # =================================================

            self.waveform_start_label.setText(self.format_time(current_seconds))

            self.playback_line.show()

        except Exception:

            return

    # =====================================================
    # ZOOM НА WAVEFORM - УПРАВЛЕНИЕ НА SCROLLBAR
    # =====================================================

    def on_waveform_zoom_changed(self, x_min, x_max):

        duration = float(self.current_duration)

        if duration <= 0:

            self.waveform_scrollbar.hide()

            return

        visible_width = max(0.0, float(x_max - x_min))

        # =================================================
        # ЦЕЛИЯТ ФАЙЛ СЕ ВИЖДА
        # =================================================

        if visible_width >= duration - 0.01:

            self.waveform_scrollbar.hide()

            self.waveform_scrollbar.blockSignals(True)

            self.waveform_scrollbar.setMinimum(0)
            self.waveform_scrollbar.setMaximum(0)
            self.waveform_scrollbar.setPageStep(1)
            self.waveform_scrollbar.setValue(0)

            self.waveform_scrollbar.blockSignals(False)

            return

        # =================================================
        # SCROLLBAR В МИЛИСЕКУНДИ ЗА ПЛАВНО ДВИЖЕНИЕ
        # =================================================

        scale = 1000

        maximum = max(0, int(round((duration - visible_width) * scale)))

        page_step = max(1, int(round(visible_width * scale)))

        value = max(0, min(int(round(x_min * scale)), maximum))

        self.waveform_scrollbar.blockSignals(True)

        self.waveform_scrollbar.setMinimum(0)

        self.waveform_scrollbar.setMaximum(maximum)

        self.waveform_scrollbar.setPageStep(page_step)

        self.waveform_scrollbar.setSingleStep(max(1, scale))

        self.waveform_scrollbar.setValue(value)

        self.waveform_scrollbar.blockSignals(False)

        self.waveform_scrollbar.show()

    # =====================================================
    # CTRL + LEFT - ПРЕМЕСТВАМЕ МАРКИРОВКАТА НАЛЯВО
    # =====================================================

    def move_selection_left(self):

        if self.current_duration <= 0:

            return

        region_item = self.waveform_plot.selection_region

        if region_item is None:

            return

        try:

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(start_value, (list, tuple)):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(end_value, (list, tuple)):

                end = float(end_value[0])

            else:

                end = float(end_value)

            width = end - start

            if width <= 0:

                return

            step = 1.0

            new_start = start - step

            new_end = end - step

            if new_start < 0:

                new_start = 0.0
                new_end = width

            region_item.setRegion((new_start, new_end))

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(new_start))

            self.waveform_end_label.setText(self.format_time(new_end))

        except Exception as e:

            print("MOVE SELECTION LEFT ERROR:", e)

    # =====================================================
    # CTRL + RIGHT - ПРЕМЕСТВАМЕ МАРКИРОВКАТА НАДЯСНО
    # =====================================================

    def move_selection_right(self):

        if self.current_duration <= 0:

            return

        region_item = self.waveform_plot.selection_region

        if region_item is None:

            return

        try:

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(start_value, (list, tuple)):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(end_value, (list, tuple)):

                end = float(end_value[0])

            else:

                end = float(end_value)

            width = end - start

            if width <= 0:

                return

            step = 1.0

            new_start = start + step
            new_end = end + step

            if new_end > self.current_duration:

                new_end = self.current_duration
                new_start = max(0.0, new_end - width)

            region_item.setRegion((new_start, new_end))

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(new_start))

            self.waveform_end_label.setText(self.format_time(new_end))

        except Exception as e:

            print("MOVE SELECTION RIGHT ERROR:", e)

    # =====================================================
    # SHIFT + LEFT - МАРКИРАМЕ / ВРЪЩАМЕ ЛЯВАТА ЧАСТ
    # =====================================================

    def resize_selection_left(self):

        if self.current_duration <= 0:

            return

        try:

            region_item = self.waveform_plot.selection_region

            # =================================================
            # НЯМА МАРКИРОВКА - ЗАПОЧВАМЕ НАЗАД ОТ БЯЛАТА ЛИНИЯ
            # =================================================

            if region_item is None:

                anchor = 0.0

                try:

                    if self.playback_line is not None:

                        anchor_value = self.playback_line.value()

                        if isinstance(
                            anchor_value,
                            (list, tuple),
                        ):

                            anchor = float(anchor_value[0])

                        else:

                            anchor = float(anchor_value)

                    else:

                        last_click_value = getattr(
                            self.waveform_plot,
                            "last_click_x",
                            0.0,
                        )

                        if isinstance(
                            last_click_value,
                            (list, tuple),
                        ):

                            anchor = float(last_click_value[0])

                        else:

                            anchor = float(last_click_value)

                except (
                    AttributeError,
                    TypeError,
                    ValueError,
                    IndexError,
                ):

                    anchor = 0.0

                anchor = max(
                    0.0,
                    min(
                        anchor,
                        self.current_duration,
                    ),
                )

                step = (
                    0.01
                    if getattr(
                        self,
                        "selection_precision_mode",
                        False,
                    )
                    else 5.0
                )

                new_start = max(
                    0.0,
                    anchor - step,
                )

                new_end = anchor

                if new_end <= new_start:

                    return

                self.waveform_plot.update_selection_region(
                    new_start,
                    new_end,
                )

                self.selection_region = self.waveform_plot.selection_region

                self._keyboard_selection_anchor = anchor

                self._keyboard_selection_direction = "left"

                self.waveform_start_label.setText(self.format_time(new_start))

                self.waveform_end_label.setText(self.format_time(new_end))

                return

            # =================================================
            # ИМА МАРКИРОВКА
            # =================================================

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(
                start_value,
                (list, tuple),
            ):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(
                end_value,
                (list, tuple),
            ):

                end = float(end_value[0])

            else:

                end = float(end_value)

            step = (
                0.01
                if getattr(
                    self,
                    "selection_precision_mode",
                    False,
                )
                else 5.0
            )

            # =================================================
            # АКО МАРКИРОВКАТА Е ЗАПОЧНАЛА НАЛЯВО
            # ДВИЖИМ САМО ЛЕВИЯ КРАЙ
            # =================================================

            direction = getattr(
                self,
                "_keyboard_selection_direction",
                None,
            )

            if direction == "left":

                new_start = max(
                    0.0,
                    start - step,
                )

                if new_start >= end:

                    return

                region_item.setRegion(
                    (
                        new_start,
                        end,
                    )
                )

                self.selection_region = region_item

                self.waveform_start_label.setText(self.format_time(new_start))

                self.waveform_end_label.setText(self.format_time(end))

                return

            # =================================================
            # АКО Е ДРУГАТА ПОСОКА
            # ВРЪЩАМЕ ДЕСНИЯ КРАЙ НАЗАД
            # =================================================

            new_end = max(
                start + 0.01,
                end - step,
            )

            if new_end <= start:

                return

            region_item.setRegion(
                (
                    start,
                    new_end,
                )
            )

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(start))

            self.waveform_end_label.setText(self.format_time(new_end))

        except Exception as e:

            print(
                "RESIZE SELECTION LEFT ERROR:",
                e,
            )

    # =====================================================
    # SHIFT + RIGHT - МАРКИРАМЕ / РАЗШИРЯВАМЕ НАДЯСНО
    # =====================================================

    def resize_selection_right(self):

        if self.current_duration <= 0:

            return

        try:

            region_item = self.waveform_plot.selection_region

            # =================================================
            # НЯМА МАРКИРОВКА - ЗАПОЧВАМЕ НАДЯСНО ОТ БЯЛАТА ЛИНИЯ
            # =================================================

            if region_item is None:

                anchor = 0.0

                try:

                    if self.playback_line is not None:

                        anchor_value = self.playback_line.value()

                        if isinstance(
                            anchor_value,
                            (list, tuple),
                        ):

                            anchor = float(anchor_value[0])

                        else:

                            anchor = float(anchor_value)

                    else:

                        last_click_value = getattr(
                            self.waveform_plot,
                            "last_click_x",
                            0.0,
                        )

                        if isinstance(
                            last_click_value,
                            (list, tuple),
                        ):

                            anchor = float(last_click_value[0])

                        else:

                            anchor = float(last_click_value)

                except (
                    AttributeError,
                    TypeError,
                    ValueError,
                    IndexError,
                ):

                    anchor = 0.0

                anchor = max(
                    0.0,
                    min(
                        anchor,
                        self.current_duration,
                    ),
                )

                step = (
                    0.01
                    if getattr(
                        self,
                        "selection_precision_mode",
                        False,
                    )
                    else 5.0
                )

                new_start = anchor

                new_end = min(
                    self.current_duration,
                    anchor + step,
                )

                if new_end <= new_start:

                    return

                self.waveform_plot.update_selection_region(
                    new_start,
                    new_end,
                )

                self.selection_region = self.waveform_plot.selection_region

                self._keyboard_selection_anchor = anchor

                self._keyboard_selection_direction = "right"

                self.waveform_start_label.setText(self.format_time(new_start))

                self.waveform_end_label.setText(self.format_time(new_end))

                return

            # =================================================
            # ИМА МАРКИРОВКА
            # =================================================

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(
                start_value,
                (list, tuple),
            ):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(
                end_value,
                (list, tuple),
            ):

                end = float(end_value[0])

            else:

                end = float(end_value)

            step = (
                0.01
                if getattr(
                    self,
                    "selection_precision_mode",
                    False,
                )
                else 5.0
            )

            # =================================================
            # АКО МАРКИРОВКАТА Е ЗАПОЧНАЛА НАДЯСНО
            # ДВИЖИМ САМО ДЕСНИЯ КРАЙ
            # =================================================

            direction = getattr(
                self,
                "_keyboard_selection_direction",
                None,
            )

            if direction == "right":

                new_end = min(
                    self.current_duration,
                    end + step,
                )

                if new_end <= start:

                    return

                region_item.setRegion(
                    (
                        start,
                        new_end,
                    )
                )

                self.selection_region = region_item

                self.waveform_start_label.setText(self.format_time(start))

                self.waveform_end_label.setText(self.format_time(new_end))

                return

            # =================================================
            # АКО Е ЗАПОЧНАЛО НАЛЯВО
            # ВРЪЩАМЕ ЛЕВИЯ КРАЙ НАПРЕД
            # =================================================

            new_start = min(
                end - 0.01,
                start + step,
            )

            if new_start >= end:

                return

            region_item.setRegion(
                (
                    new_start,
                    end,
                )
            )

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(new_start))

            self.waveform_end_label.setText(self.format_time(end))

        except Exception as e:

            print(
                "RESIZE SELECTION RIGHT ERROR:",
                e,
            )

    # =====================================================
    # ALT + LEFT - ДВИЖИМ САМО ДЕСНИЯ КРАЙ НАЗАД
    # =====================================================

    def move_selection_right_edge_left(self):

        if self.current_duration <= 0:

            return

        region_item = self.waveform_plot.selection_region

        if region_item is None:

            return

        try:

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(
                start_value,
                (list, tuple),
            ):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(
                end_value,
                (list, tuple),
            ):

                end = float(end_value[0])

            else:

                end = float(end_value)

            step = 0.01

            new_end = max(
                start + 0.01,
                end - step,
            )

            if new_end <= start:

                return

            region_item.setRegion(
                (
                    start,
                    new_end,
                )
            )

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(start))

            self.waveform_end_label.setText(self.format_time(new_end))

        except Exception as e:

            print(
                "MOVE RIGHT EDGE LEFT ERROR:",
                e,
            )

    # =====================================================
    # ALT + RIGHT - ДВИЖИМ САМО ДЕСНИЯ КРАЙ НАПРЕД
    # =====================================================

    def move_selection_right_edge_right(self):

        if self.current_duration <= 0:

            return

        region_item = self.waveform_plot.selection_region

        if region_item is None:

            return

        try:

            region = region_item.getRegion()

            start_value = region[0]
            end_value = region[1]

            if isinstance(
                start_value,
                (list, tuple),
            ):

                start = float(start_value[0])

            else:

                start = float(start_value)

            if isinstance(
                end_value,
                (list, tuple),
            ):

                end = float(end_value[0])

            else:

                end = float(end_value)

            step = 0.01

            new_end = min(
                self.current_duration,
                end + step,
            )

            if new_end <= start:

                return

            region_item.setRegion(
                (
                    start,
                    new_end,
                )
            )

            self.selection_region = region_item

            self.waveform_start_label.setText(self.format_time(start))

            self.waveform_end_label.setText(self.format_time(new_end))

        except Exception as e:

            print(
                "MOVE RIGHT EDGE RIGHT ERROR:",
                e,
            )

    # =====================================================
    # NUM 0 - ПРЕВКЛЮЧВАМЕ БЪРЗ / ТОЧЕН РЕЖИМ
    # =====================================================

    def toggle_selection_precision(self):

        # =================================================
        # АКО НЯМАМЕ ЗАДАДЕН РЕЖИМ - ЗАПОЧВАМЕ С БЪРЗ
        # =================================================

        if not hasattr(
            self,
            "selection_precision_mode",
        ):

            self.selection_precision_mode = False

        # =================================================
        # ПРЕВКЛЮЧВАМЕ РЕЖИМА
        # =================================================

        self.selection_precision_mode = not self.selection_precision_mode

        # =================================================
        # ЗВУК ПРИ НАТИСКАНЕ НА 0
        # =================================================

        QApplication.beep()

        # =================================================
        # ТОЧЕН РЕЖИМ
        # =================================================

        if self.selection_precision_mode:

            self.selection_mode_label.setText(
                "💡  "
                + language_manager.get("precision_mode").replace(
                    "🔵  ",
                    "",
                    1,
                )
            )

        # =================================================
        # БЪРЗ РЕЖИМ
        # =================================================

        else:

            self.selection_mode_label.setText(
                "💡  "
                + language_manager.get("fast_mode").replace(
                    "🟢  ",
                    "",
                    1,
                )
            )

    # =====================================================
    # SCROLL НА WAVEFORM
    # =====================================================

    def scroll_waveform(self, value):

        if self.waveform_plot is None:

            return

        plot_item = self.waveform_plot.getPlotItem()

        if plot_item is None:

            return

        view_box = getattr(
            plot_item,
            "vb",
            None,
        )

        if view_box is None:

            return

        duration = float(self.current_duration)

        if duration <= 0:

            return

        x_range = view_box.viewRange()[0]

        current_width = float(x_range[1] - x_range[0])

        if current_width <= 0:

            return

        # =================================================
        # SCROLLBAR Е В МИЛИСЕКУНДИ
        # =================================================

        scale = 1000.0

        new_x_min = float(value) / scale

        maximum_x_min = max(
            0.0,
            duration - current_width,
        )

        new_x_min = max(
            0.0,
            min(
                new_x_min,
                maximum_x_min,
            ),
        )

        new_x_max = min(
            duration,
            new_x_min + current_width,
        )

        view_box.setXRange(
            new_x_min,
            new_x_max,
            padding=0,
        )

        self.waveform_start_label.setText(self.format_time(new_x_min))

    # =====================================================
    # LEFT - ФИНО МЕСТЕНЕ НА БЯЛАТА ЛИНИЯ НАЗАД
    # =====================================================

    def move_playback_left(self):

        if self.current_duration <= 0:

            return

        if self.vlc_player is None:

            return

        try:

            # =================================================
            # ПРИ ДВИЖЕНИЕ СПИРАМЕ МИГАНЕТО
            # =================================================

            if hasattr(
                self,
                "playback_blink_timer",
            ):

                self.playback_blink_timer.stop()

            if self.playback_line is not None:

                self.playback_line.show()

            current_time_ms = self.vlc_player.get_time()

            if current_time_ms < 0:

                return

            current_seconds = current_time_ms / 1000.0

            step = 0.35

            # =================================================
            # ПРОВЕРЯВАМЕ ДАЛИ ИМА АКТИВНА МАРКИРОВКА
            # =================================================

            region_item = self.waveform_plot.selection_region

            if region_item is not None:

                region = region_item.getRegion()

                start_value = region[0]
                end_value = region[1]

                if isinstance(
                    start_value,
                    (list, tuple),
                ):

                    selection_start = float(start_value[0])

                else:

                    selection_start = float(start_value)

                if isinstance(
                    end_value,
                    (list, tuple),
                ):

                    selection_end = float(end_value[0])

                else:

                    selection_end = float(end_value)

                selection_start = max(
                    0.0,
                    min(
                        selection_start,
                        self.current_duration,
                    ),
                )

                selection_end = max(
                    0.0,
                    min(
                        selection_end,
                        self.current_duration,
                    ),
                )

                # =================================================
                # АКО СМЕ СЛЕД МАРКЕРА
                # =================================================

                if current_seconds > selection_end:

                    new_position = max(
                        selection_end,
                        current_seconds - step,
                    )

                else:

                    # =================================================
                    # ВЪТРЕ В МАРКЕРА
                    # =================================================

                    new_position = max(
                        selection_start,
                        current_seconds - step,
                    )

                    new_position = min(
                        new_position,
                        selection_end,
                    )

            else:

                # =================================================
                # НЯМА МАРКИРОВКА
                # ДВИЖИМ ПО ЦЯЛАТА ПЕСЕН
                # =================================================

                new_position = max(
                    0.0,
                    current_seconds - step,
                )

            # =================================================
            # ПРЕВЪРТАНЕ НА VLC БЕЗ ПРОМЯНА НА ТЕМПОТО
            # =================================================

            import time

            now = time.monotonic()

            last_seek = getattr(
                self,
                "_last_playback_seek_time",
                0.0,
            )

            if now - last_seek >= 0.08:

                was_playing = self.audio_playing and not self.is_paused

                self.vlc_player.set_time(int(new_position * 1000))

                if was_playing:

                    self.vlc_player.set_rate(1.0)

                self._last_playback_seek_time = now

            # =================================================
            # ПРЕМЕСТВАМЕ БЯЛАТА ЛИНИЯ
            # =================================================

            if self.playback_line is not None:

                self.playback_line.setPos(new_position)

                self.playback_line.show()

            self.waveform_start_label.setText(self.format_time(new_position))

            # =================================================
            # АКО ПЕСЕНТА СВИРИ
            # =================================================

            if self.audio_playing and not self.is_paused:

                self.position_timer.start()

            # =================================================
            # СЛЕД ДВИЖЕНИЕТО ЗАПОЧВАМЕ МИГАНЕ
            # =================================================

            if hasattr(
                self,
                "playback_blink_timer",
            ):

                self.playback_blink_timer.start()

        except Exception as e:

            print(
                "MOVE PLAYBACK LEFT ERROR:",
                e,
            )

    # =====================================================
    # RIGHT - ФИНО МЕСТЕНЕ НА БЯЛАТА ЛИНИЯ НАПРЕД
    # =====================================================

    def move_playback_right(self):

        if self.current_duration <= 0:

            return

        if self.vlc_player is None:

            return

        try:

            # =================================================
            # ПРИ ДВИЖЕНИЕ СПИРАМЕ МИГАНЕТО
            # =================================================

            if hasattr(
                self,
                "playback_blink_timer",
            ):

                self.playback_blink_timer.stop()

            if self.playback_line is not None:

                self.playback_line.show()

            current_time_ms = self.vlc_player.get_time()

            if current_time_ms < 0:

                return

            current_seconds = current_time_ms / 1000.0

            step = 0.35

            # =================================================
            # ПРОВЕРЯВАМЕ ДАЛИ ИМА АКТИВНА МАРКИРОВКА
            # =================================================

            region_item = self.waveform_plot.selection_region

            if region_item is not None:

                region = region_item.getRegion()

                start_value = region[0]
                end_value = region[1]

                if isinstance(
                    start_value,
                    (list, tuple),
                ):

                    selection_start = float(start_value[0])

                else:

                    selection_start = float(start_value)

                if isinstance(
                    end_value,
                    (list, tuple),
                ):

                    selection_end = float(end_value[0])

                else:

                    selection_end = float(end_value)

                selection_start = max(
                    0.0,
                    min(
                        selection_start,
                        self.current_duration,
                    ),
                )

                selection_end = max(
                    0.0,
                    min(
                        selection_end,
                        self.current_duration,
                    ),
                )

                # =================================================
                # АКО ВЕЧЕ СМЕ СЛЕД КРАЯ НА МАРКЕРА
                # =================================================

                if current_seconds >= selection_end:

                    new_position = min(
                        self.current_duration,
                        current_seconds + step,
                    )

                else:

                    # =================================================
                    # ВЪТРЕ В МАРКЕРА
                    # =================================================

                    new_position = min(
                        selection_end,
                        current_seconds + step,
                    )

                    new_position = max(
                        new_position,
                        selection_start,
                    )

            else:

                # =================================================
                # НЯМА МАРКИРОВКА
                # ДВИЖИМ ПО ЦЯЛАТА ПЕСЕН
                # =================================================

                new_position = min(
                    self.current_duration,
                    current_seconds + step,
                )

            # =================================================
            # ОГРАНИЧАВАМЕ ЧЕСТОТАТА НА SEEK КЪМ VLC
            # =================================================

            import time

            now = time.monotonic()

            last_seek = getattr(
                self,
                "_last_playback_seek_time",
                0.0,
            )

            if now - last_seek >= 0.08:

                self.vlc_player.set_time(int(new_position * 1000))

                self._last_playback_seek_time = now

            # =================================================
            # ПРЕМЕСТВАМЕ БЯЛАТА ЛИНИЯ
            # =================================================

            if self.playback_line is not None:

                self.playback_line.setPos(new_position)

                self.playback_line.show()

            self.waveform_start_label.setText(self.format_time(new_position))

            # =================================================
            # АКО ПЕСЕНТА СВИРИ
            # =================================================

            if self.audio_playing and not self.is_paused:

                self.position_timer.start()

            # =================================================
            # СЛЕД ДВИЖЕНИЕТО ЗАПОЧВАМЕ МИГАНЕ
            # =================================================

            if hasattr(
                self,
                "playback_blink_timer",
            ):

                self.playback_blink_timer.start()

        except Exception as e:

            print(
                "MOVE PLAYBACK RIGHT ERROR:",
                e,
            )

    # =====================================================
    # КЛИК ВЪРХУ WAVEFORM
    # =====================================================

    def on_waveform_clicked(self, seconds):

        if self.vlc_player is None:

            return

        if self.current_duration <= 0:

            return

        try:

            seconds = max(
                0.0,
                min(
                    float(seconds),
                    self.current_duration,
                ),
            )

            print(
                "CLICK SECONDS:",
                seconds,
            )

            self.vlc_player.set_time(int(seconds * 1000))

            self.waveform_plot.last_click_x = seconds

            if self.playback_line is not None:

                self.playback_line.setPos(seconds)

            self.waveform_start_label.setText(self.format_time(seconds))

        except Exception as e:

            print(
                "WAVEFORM CLICK ERROR:",
                e,
            )

    # =====================================================
    # WAVEFORM ГОТОВ
    # =====================================================

    def on_waveform_ready(
        self,
        waveform,
        duration,
    ):

        self.current_duration = duration

        self.waveform_plot.waveform_duration = duration

        self.waveform_data = waveform

        # =================================================
        # ОБЩО ВРЕМЕ ВЪВ WAVEFORM ПАНЕЛА
        # =================================================

        formatted_duration = self.format_time(duration)

        self.waveform_start_label.setText("00:00:00")

        self.waveform_end_label.setText(formatted_duration)

        # =================================================
        # ИЗЧИСТВАМЕ СТАРАТА WAVEFORM
        # =================================================

        self.waveform_plot.clear_selection()

        self.selection_region = None

        self.waveform_plot.clear()

        # =================================================
        # НУЛЕВА ЛИНИЯ
        # =================================================

        zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(
                self.current_theme["table_grid"],
                width=1,
            ),
        )

        self.waveform_plot.addItem(zero_line)

        # =====================================================
        # PLAYBACK POSITION LINE
        # =====================================================

        self.playback_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            movable=False,
            pen=pg.mkPen(
                self.current_theme["main_text"],
                width=3,
            ),
        )

        self.playback_line.setZValue(1000)

        # =====================================================
        # ТАЙМЕР ЗА ПРЕМИГВАНЕ НА БЯЛАТА ЛИНИЯ
        # =====================================================

        self.playback_blink_timer = QTimer(self)

        self.playback_blink_timer.setInterval(450)

        self.playback_blink_timer.timeout.connect(self.toggle_playback_line_visibility)

        self.playback_line.hide()

        self.waveform_plot.addItem(self.playback_line)

        # =================================================
        # X КООРДИНАТА
        # =================================================

        x = np.linspace(
            0,
            duration,
            len(waveform),
        )

        # =================================================
        # ГОРНА ЧАСТ
        # =================================================

        self.waveform_plot.plot(
            x,
            waveform,
            pen=pg.mkPen(
                self.current_theme["accent"],
                width=1,
            ),
        )

        # =================================================
        # ДОЛНА ЧАСТ
        # =================================================

        self.waveform_plot.plot(
            x,
            -waveform,
            pen=pg.mkPen(
                self.current_theme["accent"],
                width=1,
            ),
        )

        # =================================================
        # МАЩАБ
        # =================================================

        self.waveform_plot.setXRange(
            0,
            duration,
        )

        self.waveform_plot.setYRange(
            -1,
            1,
        )

        self.draw_song_boundaries()

    # =====================================================
    # ГРЕШКА
    # =====================================================

    def on_decode_error(self, message):

        self.loading_frame.hide()

        self.load_button.setEnabled(True)

        QMessageBox.critical(
            self,
            language_manager.get("error"),
            message,
        )

        self.waveform_plot.clear()

        self.file_label.setText(language_manager.get("no_loaded_mp3"))

        self.waveform_start_label.setText("00:00:00")

        self.waveform_end_label.setText("00:00:00")

        self.current_file = None

        self.current_duration = 0.0

        self.audio_playing = False

        self.is_paused = False

        self.playback_line = None

    # =====================================================
    # КРАЙ НА WORKER
    # =====================================================

    def on_decode_finished(self):

        self.loading_frame.hide()

        self.load_button.setEnabled(True)

        self.decode_worker = None

    # =====================================================
    # ФОРМАТ НА ВРЕМЕТО
    # =====================================================

    @staticmethod
    def format_time(seconds):

        seconds = int(
            max(
                0,
                seconds,
            )
        )

        hours = seconds // 3600

        minutes = (seconds % 3600) // 60

        secs = seconds % 60

        return f"{hours:02d}:" f"{minutes:02d}:" f"{secs:02d}"

    # =====================================================
    # БЛОКИРАМЕ X ПО ВРЕМЕ НА ОПЕРАЦИЯ
    # =====================================================

    def reject(self):

        if (
            hasattr(
                self,
                "operation_in_progress",
            )
            and self.operation_in_progress
        ):

            return

        super().reject()

    # =====================================================
    # ЗАТВАРЯНЕ
    # =====================================================

    def closeEvent(self, event):

        # =================================================
        # НЕ ПОЗВОЛЯВАМЕ ЗАТВАРЯНЕ ПО ВРЕМЕ НА ОПЕРАЦИЯ
        # =================================================

        if (
            hasattr(
                self,
                "operation_in_progress",
            )
            and self.operation_in_progress
        ):

            event.ignore()

            return

        # =================================================
        # СПИРАМЕ БЛОКИРАНЕТО НА ОСНОВНИЯ ПРОЗОРЕЦ
        # =================================================

        self._set_parent_input_blocked(False)

        # =================================================
        # ЗАПАЗВАМЕ РЕАЛНАТА ПОЗИЦИЯ НА ПРОЗОРЕЦА
        # =================================================

        normal_geometry = self.normalGeometry()

        self.window_settings.setValue(
            "splitter_window_x",
            normal_geometry.x(),
        )

        self.window_settings.setValue(
            "splitter_window_y",
            normal_geometry.y(),
        )

        self.window_settings.sync()

        # =================================================
        # ОСВОБОЖДАВАМЕ ОСНОВНИЯ ПРОЗОРЕЦ
        # =================================================

        parent = self.parentWidget()

        if parent is not None:

            parent.setEnabled(True)

            QTimer.singleShot(
                100,
                parent.activateWindow,
            )

        # =================================================
        # СПИРАМЕ ТАЙМЕРА
        # =================================================

        self.position_timer.stop()

        # =================================================
        # СПИРАМЕ VLC
        # =================================================

        try:

            if self.vlc_player is not None:

                self.vlc_player.stop()

        except Exception:

            pass

        # =================================================
        # СПИРАМЕ WORKER
        # =================================================

        if self.decode_worker is not None and self.decode_worker.isRunning():

            self.decode_worker.quit()

            self.decode_worker.wait(3000)

        event.accept()
