# ============================================================
# MP3_Order PRO - Language Manager
# Български 🇧🇬 / English 🇬🇧
# ============================================================

from PySide6.QtCore import QSettings


class LanguageManager:
    """
    Централна езикова система на MP3_Order PRO.

    Поддържани езици:
        bg - Български
        en - English

    Езикът се запазва чрез QSettings.
    При първо стартиране: Български.
    """

    def __init__(self):

        self.settings = QSettings("MP3_Order", "MP3_Order_PRO")

        self.languages: dict[str, str] = {
            "bg": "🇧🇬 Български",
            "en": "🇬🇧 English",
        }

        saved_language = self.settings.value("language", "bg")

        self.current_language: str = str(saved_language)

        if self.current_language not in self.languages:
            self.current_language = "bg"

        self.translations: dict[str, dict[str, str]] = {
            # ==================================================
            # ОСНОВЕН ПРОЗОРЕЦ
            # ==================================================
            "app_title": {
                "bg": "MP3 Order PRO - Nero Disc Creator",
                "en": "MP3 Order PRO - Nero Disc Creator",
            },
            "file_menu": {
                "bg": "Файл",
                "en": "File",
            },
            "new_project": {
                "bg": "Нов проект",
                "en": "New Project",
            },
            "open_project": {
                "bg": "Отвори проект...",
                "en": "Open Project...",
            },
            "save_project": {
                "bg": "Запази проект",
                "en": "Save Project",
            },
            "save_project_as": {
                "bg": "Запази проект като...",
                "en": "Save Project As...",
            },
            "exit": {
                "bg": "Изход",
                "en": "Exit",
            },
            "settings": {
                "bg": "⚙️ Настройки",
                "en": "⚙️ Settings",
            },
            "split_mp3": {
                "bg": "🎵 Разделяне на MP3",
                "en": "🎵 Split MP3",
            },
            "check_for_updates": {
                "bg": "Проверка за нови обновления",
                "en": "Check for Updates",
            },
            "no_updates": {
                "bg": "В момента няма нови обновления.",
                "en": "There are currently no new updates.",
            },
            "loading": {
                "bg": "Зареждане...",
                "en": "Loading...",
            },
            # ==================================================
            # ТАБЛИЦА
            # ==================================================
            "table_number": {
                "bg": "№",
                "en": "No.",
            },
            "table_song": {
                "bg": "Песен",
                "en": "Song",
            },
            "table_artist": {
                "bg": "Изпълнител",
                "en": "Artist",
            },
            "table_time": {
                "bg": "Време",
                "en": "Time",
            },
            "drop_mp3": {
                "bg": "🎵 Пуснете MP3 файловете тук",
                "en": "🎵 Drop MP3 files here",
            },
            "search_placeholder": {
                "bg": "Търси по №, песен или изпълнител...",
                "en": "Search by #, song or artist...",
            },
            "search": {
                "bg": "Търси",
                "en": "Search",
            },
            # ==================================================
            # ОСНОВНИ БУТОНИ
            # ==================================================
            "add_songs": {
                "bg": "➕ Добави песни",
                "en": "➕ Add Songs",
            },
            "add_folder": {
                "bg": "📁 Добави папка",
                "en": "📁 Add Folder",
            },
            "move_up": {
                "bg": "⬆ Нагоре",
                "en": "⬆ Move Up",
            },
            "move_down": {
                "bg": "⬇ Надолу",
                "en": "⬇ Move Down",
            },
            "remove": {
                "bg": "❌ Премахни",
                "en": "❌ Remove",
            },
            "check_order": {
                "bg": "🔍 Провери реда",
                "en": "🔍 Check Order",
            },
            "automatic_split": {
                "bg": "🪄 Автоматично разделяне",
                "en": "🪄 Automatic Split",
            },
            "edit_id3": {
                "bg": "🏷️ Поправи ID3",
                "en": "🏷️ Edit ID3",
            },
            "edit_id3_title": {
                "bg": "🏷️ Поправи ID3",
                "en": "🏷️ Edit ID3",
            },
            "export_nero": {
                "bg": "💾 Export за Nero",
                "en": "💾 Export for Nero",
            },
            # ==================================================
            # ID3
            # ==================================================
            "artist": {
                "bg": "Изпълнител:",
                "en": "Artist:",
            },
            "song": {
                "bg": "Песен:",
                "en": "Song:",
            },
            "done": {
                "bg": "Готово",
                "en": "Done",
            },
            "ok": {
                "bg": "OK",
                "en": "OK",
            },
            "cancel": {
                "bg": "Отказ",
                "en": "Cancel",
            },
            "id3_saved": {
                "bg": "✅ ID3 таговете са записани успешно!",
                "en": "✅ ID3 tags were saved successfully!",
            },
            "id3_save_error": {
                "bg": "Неуспешен запис на ID3 тагове.",
                "en": "Failed to save ID3 tags.",
            },
            # ==================================================
            # СЪОБЩЕНИЯ
            # ==================================================
            "no_selected_song_title": {
                "bg": "Няма избрана песен",
                "en": "No Song Selected",
            },
            "no_selected_song_text": {
                "bg": "Избери песен от таблицата.",
                "en": "Select a song from the table.",
            },
            "now_playing": {
                "bg": "СЕГА СВИРИ",
                "en": "NOW PLAYING",
            },
            "no_song": {
                "bg": "Няма песен",
                "en": "No Song",
            },
            "no_songs_title": {
                "bg": "Няма песни",
                "en": "No Songs",
            },
            "add_songs_first": {
                "bg": "Добави песни първо!",
                "en": "Add songs first!",
            },
            "error": {
                "bg": "Грешка",
                "en": "Error",
            },
            "success": {
                "bg": "Готово",
                "en": "Done",
            },
            "delete_success": {
                "bg": "Записите са изтрити успешно от списъка.",
                "en": "The entries were deleted successfully from the list.",
            },
            "new_list_title": {
                "bg": "Нов списък",
                "en": "New List",
            },
            "save_success_title": {
                "bg": "Запазено успешно",
                "en": "Saved Successfully",
            },
            "save_success": {
                "bg": "Списъкът е запазен успешно.",
                "en": "The list was saved successfully.",
            },
            "save_error": {
                "bg": "Списъкът не можа да бъде запазен.",
                "en": "The list could not be saved.",
            },
            "open_list_error": {
                "bg": "Списъкът не може да бъде отворен.",
                "en": "The list could not be opened.",
            },
            "invalid_mp3_list": {
                "bg": "В избрания списък няма валидни MP3 файлове.",
                "en": "The selected list contains no valid MP3 files.",
            },
            "no_songs_to_save": {
                "bg": "Няма заредени песни за записване.",
                "en": "There are no loaded songs to save.",
            },
            "play_error_title": {
                "bg": "Грешка при пускане",
                "en": "Playback Error",
            },
            "play_error": {
                "bg": "Песента не можа да бъде пусната.",
                "en": "The song could not be played.",
            },
            "vlc_init_error": {
                "bg": "VLC не успя да се инициализира.",
                "en": "VLC failed to initialize.",
            },
            "song_file_missing": {
                "bg": "Файлът на песента не съществува.",
                "en": "The song file does not exist.",
            },
            "open_list": {
                "bg": "Отвори списък",
                "en": "Open List",
            },
            "save_list_as_title": {
                "bg": "Запази списък като...",
                "en": "Save List As...",
            },
            "select_mp3_files": {
                "bg": "Избери MP3 песни",
                "en": "Select MP3 Songs",
            },
            "mp3_files_filter": {
                "bg": "MP3 Files (*.mp3)",
                "en": "MP3 Files (*.mp3)",
            },
            "mp3_list_filter": {
                "bg": "MP3 Order списък (*.m3plist)",
                "en": "MP3 Order List (*.m3plist)",
            },
            "choose_folder": {
                "bg": "Избери папка",
                "en": "Choose Folder",
            },
            "new_list_question": {
                "bg": (
                    "Искате ли да започнете нов списък?\n\n"
                    "Текущо заредените песни ще бъдат премахнати "
                    "само от програмата.\n"
                    "MP3 файловете няма да бъдат изтрити от компютъра."
                ),
                "en": (
                    "Do you want to start a new list?\n\n"
                    "The currently loaded songs will be removed "
                    "only from the program.\n"
                    "The MP3 files will not be deleted from the computer."
                ),
            },
            "duplicate_title": {
                "bg": "Дублиране",
                "en": "Duplicate",
            },
            "song_already_loaded": {
                "bg": "Песента вече е заредена.",
                "en": "The song is already loaded.",
            },
            "replace_song_question": {
                "bg": "Искате ли да я замените?",
                "en": "Do you want to replace it?",
            },
            "folder_already_loaded": {
                "bg": "Папката вече е заредена.",
                "en": "The folder is already loaded.",
            },
            "replace_folder_question": {
                "bg": "Искате ли да я замените?",
                "en": "Do you want to replace the folder?",
            },
            "delete_selected_song_question": {
                "bg": "Искате ли да изтриете избраната песен от списъка?",
                "en": "Do you want to delete the selected song from the list?",
            },
            "delete_all_songs_question": {
                "bg": "Искате ли да изтриете всички песни от този списък?",
                "en": "Do you want to delete all songs from this list?",
            },
            "delete_selected_songs_question": {
                "bg": "Искате ли да изтриете избраните песни от списъка?",
                "en": "Do you want to delete the selected songs from the list?",
            },
            # ==================================================
            # EXPORT
            # ==================================================
            "choose_export_folder": {
                "bg": "Избери папка за Export",
                "en": "Choose Export Folder",
            },
            "nero_ready": {
                "bg": "MP3 файловете са готови за Nero!",
                "en": "The MP3 files are ready for Nero!",
            },
            "nero_check_title": {
                "bg": "Проверка за Nero",
                "en": "Nero Check",
            },
            "nero_queue": {
                "bg": "🎵 Ред за Nero",
                "en": "🎵 Nero Queue",
            },
            "nero_total_songs": {
                "bg": "🎵 Общо песни: {count}",
                "en": "🎵 Total songs: {count}",
            },
            "nero_total_time": {
                "bg": "⏱️ Общо време: {minutes:02d}:{seconds:02d}",
                "en": "⏱️ Total time: {minutes:02d}:{seconds:02d}",
            },
            "nero_within_limit": {
                "bg": "✅ Дискът влиза в 80 минути CD",
                "en": "✅ The disc fits within the 80-minute CD limit",
            },
            "nero_over_limit": {
                "bg": "❌ Дискът е над 80 минути",
                "en": "❌ The disc exceeds 80 minutes",
            },
            "automatic_split_title": {
                "bg": "Автоматично разделяне",
                "en": "Automatic Split",
            },
            "auto_split_success_summary": {
                "bg": "✔ Разделени успешно: {count} песни\n\n",
                "en": "✔ Successfully split: {count} songs\n\n",
            },
            "auto_split_warning_header": {
                "bg": "⚠ Нуждаят се от проверка:\n",
                "en": "⚠ Need to be checked:\n",
            },
            "auto_split_complete": {
                "bg": "Всички песни са разделени успешно.",
                "en": "All songs were split successfully.",
            },
            # ==================================================
            # НАСТРОЙКИ
            # ==================================================
            "settings_title": {
                "bg": "⚙️ Настройки",
                "en": "⚙️ Settings",
            },
            "language": {
                "bg": "Език:",
                "en": "Language:",
            },
            "bulgarian": {
                "bg": "🇧🇬 Български",
                "en": "🇬🇧 Bulgarian",
            },
            "english": {
                "bg": "🇬🇧 English",
                "en": "🇬🇧 English",
            },
            "language_saved": {
                "bg": "Езикът е запазен.",
                "en": "Language saved.",
            },
            "fade_title": {
                "bg": "🎧 Плавен преход между песни",
                "en": "🎧 Smooth transition between songs",
            },
            "fade_description": {
                "bg": "Постепенно намалява звука на текущата песен "
                "и плавно увеличава звука на следващата.",
                "en": "Gradually lowers the volume of the current song "
                "and smoothly increases the volume of the next one.",
            },
            "fade_enabled": {
                "bg": "Включи плавен преход",
                "en": "Enable smooth transition",
            },
            "enabled": {
                "bg": "Включено",
                "en": "Enabled",
            },
            "disabled": {
                "bg": "Изключено",
                "en": "Disabled",
            },
            "fade_on_message": {
                "bg": "Плавният преход е включен.",
                "en": "Smooth transition is enabled.",
            },
            "fade_off_message": {
                "bg": "Плавният преход е изключен.",
                "en": "Smooth transition is disabled.",
            },
            "fade": {
                "bg": "🎧 Плавен преход",
                "en": "🎧 Smooth Transition",
            },
            "fade_time_title": {
                "bg": "⏱️ Продължителност на fade",
                "en": "⏱️ Fade Duration",
            },
            "fade_time_description": {
                "bg": "Определя колко секунди да продължава "
                "плавният преход между две песни.",
                "en": "Determines how many seconds the "
                "smooth transition between two songs lasts.",
            },
            "fade_duration": {
                "bg": "Продължителност:",
                "en": "Duration:",
            },
            "seconds": {
                "bg": " сек.",
                "en": " sec.",
            },
            "autosave_description": {
                "bg": "Програмата може автоматично да запазва "
                "текущия проект през избран интервал. "
                "Използва същото съобщение за успешно "
                "запазване, което вече използваме при Ctrl+S.",
                "en": "The program can automatically save "
                "the current project at the selected interval. "
                "It uses the same successful save message "
                "that we already use for Ctrl+S.",
            },
            "autosave_title": {
                "bg": "💾 Автоматично запазване",
                "en": "💾 Auto Save",
            },
            "autosave_button": {
                "bg": "Настрой интервала...",
                "en": "Set interval...",
            },
            "autosave_interval": {
                "bg": "Интервал: {minutes} минути.",
                "en": "Interval: {minutes} minutes.",
            },
            "autosave_saved": {
                "bg": "Настройката за автоматично запазване е запазена успешно.",
                "en": "The auto save setting has been saved successfully.",
            },
            "autosave_interval_short": {
                "bg": "Интервал: {minutes} мин.",
                "en": "Interval: {minutes} min.",
            },
            "autosave_interval_description": {
                "bg": "Избери през колко минути програмата "
                "автоматично да запазва текущия проект.",
                "en": "Choose how many minutes the program "
                "should automatically save the current project.",
            },
            "autosave_on_message": {
                "bg": "✅ Автоматичното запазване е включено.",
                "en": "✅ Auto Save is enabled.",
            },
            "autosave_off_message": {
                "bg": "☐ Автоматичното запазване е изключено.",
                "en": "☐ Auto Save is disabled.",
            },
            "autosave_next": {
                "bg": "След",
                "en": "Next",
            },
            "autosave_suffix": {
                "bg": "да се запазва автоматично.",
                "en": "to be saved automatically.",
            },
            "autosave_minutes": {
                "bg": " мин.",
                "en": " min.",
            },
            "autosave_restart_message": {
                "bg": (
                    "Моля, рестартирайте програмата, "
                    "за да се запази настройката за "
                    "автоматичното запазване на проекта."
                ),
                "en": ("Please restart the program " "to apply the auto save setting."),
            },
            "restart": {
                "bg": "Рестартирай",
                "en": "Restart",
            },
            "end_title": {
                "bg": "💿 След края на списъка",
                "en": "💿 After the End of the List",
            },
            "end_description": {
                "bg": "Избира какво да направи програмата, "
                "когато последната песен от списъка приключи.",
                "en": "Choose what the program should do "
                "when the last song in the list finishes.",
            },
            "end_stop": {
                "bg": "Спира възпроизвеждането",
                "en": "Stop playback",
            },
            "end_repeat": {
                "bg": "Повтаря списъка",
                "en": "Repeat the list",
            },
            "end_list_title": {
                "bg": "💿 Край на списъка",
                "en": "💿 End of List",
            },
            "theme_title": {
                "bg": "🎨 Цветова тема",
                "en": "🎨 Color Theme",
            },
            "theme_description": {
                "bg": "Избери цветова тема за интерфейса на MP3_Order.",
                "en": "Choose a color theme for the MP3_Order interface.",
            },
            "theme_purple_blue": {
                "bg": "Лилаво-синя",
                "en": "Purple-Blue",
            },
            "theme_blue": {
                "bg": "Синя",
                "en": "Blue",
            },
            "theme_green": {
                "bg": "Зелена",
                "en": "Green",
            },
            "theme_red": {
                "bg": "Червена",
                "en": "Red",
            },
            "theme_orange": {
                "bg": "Оранжева",
                "en": "Orange",
            },
            "theme_classic": {
                "bg": "Класическа",
                "en": "Classic",
            },
            "theme_list_title": {
                "bg": "🎨 Цветова тема",
                "en": "🎨 Color Theme",
            },
            "language_title": {
                "bg": "🌐 Език",
                "en": "🌐 Language",
            },
            "language_description": {
                "bg": "Избери езика на програмата.",
                "en": "Choose the language of the program.",
            },
            "language_list_title": {
                "bg": "🌐 Език",
                "en": "🌐 Language",
            },
            "settings_main_description": {
                "bg": "Главен прозорец за настройките.",
                "en": "Main settings window.",
            },
            # ==================================================
            # ОБНОВЯВАНЕ
            # ==================================================
            "update_available_title": {
                "bg": "🔄 Налична е нова версия",
                "en": "🔄 A new version is available",
            },
            "update_available_text": {
                "bg": (
                    "Налична е нова версия на MP3_Order PRO.\n\n"
                    "Текуща версия: {current_version}\n"
                    "Нова версия: {latest_version}\n\n"
                    "Искате ли да обновите програмата?"
                ),
                "en": (
                    "A new version of MP3_Order PRO is available.\n\n"
                    "Current version: {current_version}\n"
                    "New version: {latest_version}\n\n"
                    "Would you like to update the program?"
                ),
            },
            "update_button": {
                "bg": "Обнови",
                "en": "Update",
            },
            "update_later": {
                "bg": "По-късно",
                "en": "Later",
            },
            # ==================================================
            # СТАТУСИ
            # ==================================================
            "project_saved": {
                "bg": "✓ Проектът е запазен",
                "en": "✓ Project saved",
            },
            "changes_saved": {
                "bg": "✓ Промените са запазени",
                "en": "✓ Changes saved",
            },
            "changes_save_error": {
                "bg": "Промените не можаха да бъдат запазени.",
                "en": "The changes could not be saved.",
            },
            "no_playlist_loaded": {
                "bg": "Няма зареден списък с песни",
                "en": "No song list loaded",
            },
            "loading_songs": {
                "bg": "🎵 Зареждане на песни...",
                "en": "🎵 Loading songs...",
            },
            "loading_song_progress": {
                "bg": "🎵 Зареждане... {current} / {total}",
                "en": "🎵 Loading... {current} / {total}",
            },
            "loading_folder_progress": {
                "bg": "🎵 Зареждане на папка... {current} / {total}",
                "en": "🎵 Loading folder... {current} / {total}",
            },
            "loading_folder_complete": {
                "bg": "✅ Зареждането завърши — {total} / {total}",
                "en": "✅ Loading completed — {total} / {total}",
            },
            "loading_song_complete": {
                "bg": "✅ Зареждането завърши — {total} / {total}",
                "en": "✅ Loading completed — {total} / {total}",
            },
            "loading_project": {
                "bg": "⏳ Зареждане на проекта: {file_name}",
                "en": "⏳ Loading project: {file_name}",
            },
            "loading_mp3": {
                "bg": "🎵 Зареждане на MP3 файла...",
                "en": "🎵 Loading MP3 file...",
            },
            "previous_song": {
                "bg": "Предишна песен",
                "en": "Previous Song",
            },
            "play_song": {
                "bg": "Пусни песента",
                "en": "Play Song",
            },
            "pause_song": {
                "bg": "Пауза / Продължи",
                "en": "Pause / Resume",
            },
            "stop_song": {
                "bg": "Спри песента",
                "en": "Stop Song",
            },
            "next_song": {
                "bg": "Следваща песен",
                "en": "Next Song",
            },
            "paused": {
                "bg": "⏸ ПАУЗА",
                "en": "⏸ PAUSED",
            },
            "now_playing_status": {
                "bg": "▶ СЕГА СВИРИ",
                "en": "▶ NOW PLAYING",
            },
            "stopped": {
                "bg": "⏹ ПЕСЕНТА Е СПРЯНА",
                "en": "⏹ SONG STOPPED",
            },
            "refresh_title": {
                "bg": "Обновяване",
                "en": "Refresh",
            },
            "refresh_success": {
                "bg": "✅ Таблицата е обновена.",
                "en": "✅ The table has been refreshed.",
            },
            # ==================================================
            # РАЗДЕЛЯНЕ НА MP3
            # ==================================================
            "split_title": {
                "bg": "Разделяне на MP3",
                "en": "Split MP3",
            },
            "split_title_header": {
                "bg": "🎵 РАЗДЕЛЯНЕ НА MP3",
                "en": "🎵 SPLIT MP3",
            },
            "section_file": {
                "bg": "ФАЙЛ",
                "en": "FILE",
            },
            "load_mp3": {
                "bg": "📂  Зареди MP3",
                "en": "📂  Load MP3",
            },
            "open_mp3": {
                "bg": "Зареди MP3 файл",
                "en": "Load MP3 File",
            },
            "play_tooltip": {
                "bg": "Пусни",
                "en": "Play",
            },
            "pause_tooltip": {
                "bg": "Пауза",
                "en": "Pause",
            },
            "stop_tooltip": {
                "bg": "Стоп",
                "en": "Stop",
            },
            "no_loaded_mp3": {
                "bg": "Няма зареден MP3 файл",
                "en": "No MP3 file loaded",
            },
            "elapsed": {
                "bg": "Изминало: {time}",
                "en": "Elapsed: {time}",
            },
            "remaining": {
                "bg": "Оставащо: {time}",
                "en": "Remaining: {time}",
            },
            "audio_waveform": {
                "bg": "🎵 Аудио вълнова форма",
                "en": "🎵 Audio Waveform",
            },
            "fast_mode": {
                "bg": "🟢  БЪРЗ РЕЖИМ",
                "en": "🟢  FAST MODE",
            },
            "precision_mode": {
                "bg": "🔵  ТОЧЕН РЕЖИМ",
                "en": "🔵  PRECISION MODE",
            },
            "analyze_find_songs": {
                "bg": "🔍 Анализирай и намери песните",
                "en": "🔍 Analyze and Find Songs",
            },
            "table_start": {
                "bg": "Начало",
                "en": "Start",
            },
            "table_end": {
                "bg": "Край",
                "en": "End",
            },
            "table_duration": {
                "bg": "Продължителност",
                "en": "Duration",
            },
            "split_button": {
                "bg": "✂️ Раздели",
                "en": "✂️ Split",
            },
            "close": {
                "bg": "Затвори",
                "en": "Close",
            },
            "analysis": {
                "bg": "Анализ",
                "en": "Analysis",
            },
            "analyzing": {
                "bg": "Анализиране...",
                "en": "Analyzing...",
            },
            "analysis_complete": {
                "bg": "Анализът приключи успешно.",
                "en": "Analysis completed successfully.",
            },
            "analysis_error": {
                "bg": "Възникна грешка при анализа.",
                "en": "An error occurred during analysis.",
            },
            "split_wait": {
                "bg": "Моля, изчакайте, процесът да започне.",
                "en": "Please wait for the process to start.",
            },
            "splitting": {
                "bg": "Разделяне...",
                "en": "Splitting...",
            },
            "split_complete": {
                "bg": "Разделянето на песните завърши успешно!",
                "en": "The songs were split successfully!",
            },
            "split_error": {
                "bg": "Възникна грешка при разделянето.",
                "en": "An error occurred while splitting.",
            },
            "current_time": {
                "bg": "Изминало време",
                "en": "Elapsed Time",
            },
            "remaining_time": {
                "bg": "Оставащо време",
                "en": "Remaining Time",
            },
            "progress": {
                "bg": "Прогрес",
                "en": "Progress",
            },
            "songs_found": {
                "bg": "Намерени песни",
                "en": "Songs Found",
            },
            "no_songs_found": {
                "bg": "Не бяха намерени песни.",
                "en": "No songs were found.",
            },
            "select_mp3_first": {
                "bg": "Първо зареди MP3 файл.",
                "en": "Load an MP3 file first.",
            },
            "analyze_first": {
                "bg": "Първо трябва да анализираш файла.",
                "en": "You must analyze the file first.",
            },
            # ==================================================
            # КОНВЕРТОР
            # ==================================================
            "converter": {
                "bg": "🎵 Конвертор",
                "en": "🎵 Converter",
            },
            "converter_title": {
                "bg": "MP3_Order PRO - Конвертор",
                "en": "MP3_Order PRO - Converter",
            },
            "converter_header": {
                "bg": "🎵 Аудио Конвертор",
                "en": "🎵 Audio Converter",
            },
            "converter_url_placeholder": {
                "bg": "🔗 Постави линк към аудио...",
                "en": "🔗 Paste audio link...",
            },
            "converter_add_url": {
                "bg": "🔗 Добави линк",
                "en": "🔗 Add Link",
            },
            "converter_add_files": {
                "bg": "📁 Добави файлове",
                "en": "📁 Add Files",
            },
            "converter_remove": {
                "bg": "➖ Премахни линк",
                "en": "➖ Remove Link",
            },
            "converter_clear": {
                "bg": "🗑 Изчисти",
                "en": "🗑 Clear",
            },
            "converter_format": {
                "bg": "Формат:",
                "en": "Format:",
            },
            "converter_quality": {
                "bg": "Качество:",
                "en": "Quality:",
            },
            "converter_output_placeholder": {
                "bg": "Избери папка за запис...",
                "en": "Choose output folder...",
            },
            "converter_folder": {
                "bg": "📁 Папка",
                "en": "📁 Folder",
            },
            "converter_ready": {
                "bg": "Готово.",
                "en": "Ready.",
            },
            "converter_convert": {
                "bg": "🔄 Конвертирай",
                "en": "🔄 Convert",
            },
            "converter_stop": {
                "bg": "⛔ Спри",
                "en": "⛔ Stop",
            },
            "converter_missing_link_title": {
                "bg": "Липсва линк",
                "en": "Missing Link",
            },
            "converter_missing_link": {
                "bg": "Моля, добавете линк.",
                "en": "Please add a link.",
            },
            "converter_invalid_link_title": {
                "bg": "Невалиден линк",
                "en": "Invalid Link",
            },
            "converter_invalid_link": {
                "bg": "Моля, поставете валиден http или https линк.",
                "en": "Please enter a valid http or https link.",
            },
            "converter_duplicate_link_title": {
                "bg": "Линкът вече е добавен",
                "en": "Link Already Added",
            },
            "converter_duplicate_link": {
                "bg": "Този линк вече е поставен в списъка.",
                "en": "This link has already been added to the list.",
            },
            "converter_delete_selected_link": {
                "bg": "Искате ли да изтриете избрания линк?",
                "en": "Do you want to delete the selected link?",
            },
            "converter_delete_selected_file": {
                "bg": "Искате ли да изтриете избрания файл?",
                "en": "Do you want to delete the selected file?",
            },
            "converter_delete_selected_links": {
                "bg": "Искате ли да изтриете избраните {count} линка?",
                "en": "Do you want to delete the selected {count} links?",
            },
            "converter_delete_all_links": {
                "bg": "Искате ли да изтриете всички линкове?",
                "en": "Do you want to delete all links?",
            },
            "converter_delete_selected_items": {
                "bg": "Искате ли да изтриете избраните {count} елемента?",
                "en": "Do you want to delete the selected {count} items?",
            },
            "converter_clear_message": {
                "bg": "Искате ли да изтриете всички добавени линкове и файлове?",
                "en": "Do you want to delete all added links and files?",
            },
            "converter_output_folder_title": {
                "bg": "Избери папка за запис",
                "en": "Choose Output Folder",
            },
            "converter_audio_filter": {
                "bg": "Аудио файлове (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma)",
                "en": "Audio Files (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma)",
            },
            "converter_all_files": {
                "bg": "Всички файлове (*.*)",
                "en": "All Files (*.*)",
            },
            "converter_prepare": {
                "bg": "Подготовка...",
                "en": "Preparing...",
            },
            "converter_processing": {
                "bg": "Обработва се {current} от {total}: {name}",
                "en": "Processing {current} of {total}: {name}",
            },
            "converter_downloading": {
                "bg": "Изтегляне:\n{url}",
                "en": "Downloading:\n{url}",
            },
            "converter_converting": {
                "bg": "Конвертиране:\n{name}",
                "en": "Converting:\n{name}",
            },
            "converter_no_downloaded_file": {
                "bg": "Не беше намерен изтеглен аудио файл.",
                "en": "No downloaded audio file was found.",
            },
            "converter_missing_yt_dlp": {
                "bg": (
                    "Липсва библиотеката yt-dlp.\n\n"
                    "Инсталирай я с:\n"
                    "python -m pip install yt-dlp"
                ),
                "en": (
                    "The yt-dlp library is missing.\n\n"
                    "Install it with:\n"
                    "python -m pip install yt-dlp"
                ),
            },
            "converter_ffmpeg_output_error": {
                "bg": "FFmpeg не предостави изходен поток.",
                "en": "FFmpeg did not provide an output stream.",
            },
            "converter_ffmpeg_failed": {
                "bg": "FFmpeg не успя да конвертира файла.",
                "en": "FFmpeg failed to convert the file.",
            },
            "converter_stopped": {
                "bg": "Операцията беше спряна.",
                "en": "The operation was stopped.",
            },
            "converter_status_stopping": {
                "bg": "Спиране...",
                "en": "Stopping...",
            },
            "converter_stop_confirmation": {
                "bg": "Искате ли да спрете изтеглянето?",
                "en": "Do you want to stop the download?",
            },
            "converter_operation_error": {
                "bg": "Възникна грешка:\n{error}",
                "en": "An error occurred:\n{error}",
            },
            "converter_no_ffmpeg_title": {
                "bg": "Липсва FFmpeg",
                "en": "FFmpeg Missing",
            },
            "converter_no_ffmpeg": {
                "bg": "Не е намерен FFmpeg.",
                "en": "FFmpeg was not found.",
            },
            "converter_no_sources_title": {
                "bg": "Няма файлове",
                "en": "No Files",
            },
            "converter_no_sources": {
                "bg": "Добави файл или линк.",
                "en": "Add a file or link.",
            },
            "converter_no_output_title": {
                "bg": "Липсва папка",
                "en": "Output Folder Missing",
            },
            "converter_no_output": {
                "bg": "Избери папка за запис.",
                "en": "Choose an output folder.",
            },
            "converter_invalid_output_title": {
                "bg": "Невалидна папка",
                "en": "Invalid Folder",
            },
            "converter_invalid_output": {
                "bg": "Избраната папка не съществува.",
                "en": "The selected folder does not exist.",
            },
            "converter_success_title": {
                "bg": "MP3_Order PRO",
                "en": "MP3_Order PRO",
            },
            "converter_success": {
                "bg": "Конвертирането на файловете завърши успешно!",
                "en": "File conversion completed successfully!",
            },
            "converter_success_status": {
                "bg": "✅ Конвертирането завърши успешно.",
                "en": "✅ Conversion completed successfully.",
            },
            # ==================================================
            # ОБЩИ
            # ==================================================
            "yes": {
                "bg": "Да",
                "en": "Yes",
            },
            "no": {
                "bg": "Не",
                "en": "No",
            },
            "warning": {
                "bg": "Предупреждение",
                "en": "Warning",
            },
            "information": {
                "bg": "Информация",
                "en": "Information",
            },
            "question": {
                "bg": "Въпрос",
                "en": "Question",
            },
        }

    # ========================================================
    # ВРЪЩА ТЕКСТ СПОРЕД ТЕКУЩИЯ ЕЗИК
    # ========================================================

    def get(self, key: str, **kwargs: str) -> str:

        translation = self.translations.get(key)

        if translation is None:
            return key

        text = translation.get(
            self.current_language,
            translation.get("bg", key),
        )

        if kwargs:

            try:

                text = text.format(**kwargs)

            except Exception:

                pass

        return text

    # ========================================================
    # СМЯНА НА ЕЗИКА
    # ========================================================

    def set_language(self, language_code: str):

        if language_code not in self.languages:

            language_code = "bg"

        self.current_language = language_code

        self.settings.setValue(
            "language",
            self.current_language,
        )

        self.settings.sync()

    # ========================================================
    # ТЕКУЩ ЕЗИК
    # ========================================================

    def get_language(self) -> str:

        return self.current_language

    # ========================================================
    # ПРОВЕРКА
    # ========================================================

    def is_bulgarian(self) -> bool:

        return self.current_language == "bg"

    def is_english(self) -> bool:

        return self.current_language == "en"

    # ========================================================
    # ИМЕ НА ТЕКУЩИЯ ЕЗИК
    # ========================================================

    def get_language_name(self) -> str:

        return self.languages.get(
            self.current_language,
            self.languages["bg"],
        )

    # ========================================================
    # ВСИЧКИ ЕЗИЦИ
    # ========================================================

    def get_languages(self) -> dict[str, str]:

        return self.languages.copy()


# ============================================================
# ГЛОБАЛЕН ЕЗИКОВ МЕНИДЖЪР
# ============================================================

language_manager = LanguageManager()
