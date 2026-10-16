"""MetaDel desktop window (PySide6) — Ukrainian / English UI.

Workflow: add files -> Clean (stages verified-clean temp copies, originals untouched)
-> Save selected / Save all (commits the staged copies to disk). A file is shown
green only after a re-read confirmed it is empty.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from ..core.logger import get_logger
from ..core.models import Status, WipeResult
from ..core.pipeline import Pipeline
from ..engine.tools import exiftool_available, ffmpeg_available
from .theme import ACCENTS, build_qss

try:
    from PySide6.QtCore import QSettings, Qt, QThread, Signal
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - environment guard
    PYSIDE_OK = False
else:
    PYSIDE_OK = True


# --------------------------------------------------------------------------- i18n

TR = {
    "uk": {
        "title": "MetaDel — повне очищення метаданих",
        "add_files": "Додати файли…",
        "add_folder": "Додати теку…",
        "clear": "Очистити список",
        "save_label": "Зберігати як:",
        "mode_copy": "Копію (*_clean)",
        "mode_replace": "Замінювати оригінал",
        "keep_icc": "Зберігати кольоровий профіль ICC",
        "lang_label": "Мова:",
        "col_file": "Файл",
        "col_type": "Тип",
        "col_status": "Статус",
        "col_details": "Деталі",
        "btn_clean": "Очистити",
        "btn_save_sel": "Зберегти вибране",
        "btn_save_all": "Зберегти все",
        "btn_report": "Зберегти звіт…",
        "save_as": "Зберегти як",
        "choose_folder": "Оберіть теку для збереження",
        "btn_settings": "Налаштування",
        "set_title": "Налаштування",
        "set_theme": "Тема:",
        "set_light": "Світла",
        "set_dark": "Темна",
        "set_accent": "Акцент:",
        "set_lang": "Мова:",
        "set_keep_icc": "Зберігати профіль ICC за замовчуванням",
        "set_open_after": "Відкривати теку після збереження",
        "acc_blue": "Синій", "acc_teal": "Бірюзовий", "acc_green": "Зелений",
        "acc_purple": "Фіолетовий", "acc_orange": "Помаранчевий", "acc_red": "Червоний",
        "st_queued": "у черзі",
        "st_cleaned": "✓ Очищено",
        "st_unsupported": "— Не вмію",
        "st_failed": "✗ Залишились дані",
        "st_error": "⚠ Помилка",
        "d_removed": "Видалено: ",
        "d_residual": "Залишилось {n} — подвійний клік для списку",
        "m_add_first": "Спочатку додайте файли.",
        "m_nothing_clean": "Немає файлів для очищення.",
        "m_nothing_save": "Немає очищених файлів для збереження.",
        "m_select_rows": "Виділіть рядки для збереження.",
        "m_replace_title": "Замінити оригінали?",
        "m_replace_text": "Оригінали буде замінено очищеними файлами. Продовжити?",
        "m_nothing_report": "Поки нема чого зберігати.",
        "dlg_title": "Деталі",
        "dlg_file": "Файл: ",
        "dlg_type": "Тип: ",
        "dlg_status": "Статус: ",
        "dlg_targets": "Цільові контейнери:",
        "dlg_residual": "Залишкові метадані ({n}):",
        "dlg_ok": "Перевірку пройдено: метаданих не залишилось.",
        "dlg_msg": "Повідомлення: ",
        "eng_missing": "⚠ Не знайдено: {tools}. Покладіть файл(и) у теку «tools» поряд із програмою.",
        "eng_exiftool": "exiftool.exe (потрібен для фото/RAW/відео)",
        "eng_ffmpeg": "ffmpeg.exe (потрібен для відео)",
        "report_dialog": "Зберегти звіт",
    },
    "en": {
        "title": "MetaDel — complete metadata removal",
        "add_files": "Add files…",
        "add_folder": "Add folder…",
        "clear": "Clear list",
        "save_label": "Save as:",
        "mode_copy": "Copy (*_clean)",
        "mode_replace": "Replace original",
        "keep_icc": "Keep ICC colour profile",
        "lang_label": "Language:",
        "col_file": "File",
        "col_type": "Type",
        "col_status": "Status",
        "col_details": "Details",
        "btn_clean": "Clean",
        "btn_save_sel": "Save selected",
        "btn_save_all": "Save all",
        "btn_report": "Save report…",
        "save_as": "Save as",
        "choose_folder": "Choose a folder to save into",
        "btn_settings": "Settings",
        "set_title": "Settings",
        "set_theme": "Theme:",
        "set_light": "Light",
        "set_dark": "Dark",
        "set_accent": "Accent:",
        "set_lang": "Language:",
        "set_keep_icc": "Keep ICC profile by default",
        "set_open_after": "Open folder after saving",
        "acc_blue": "Blue", "acc_teal": "Teal", "acc_green": "Green",
        "acc_purple": "Purple", "acc_orange": "Orange", "acc_red": "Red",
        "st_queued": "queued",
        "st_cleaned": "✓ Cleaned",
        "st_unsupported": "— Unsupported",
        "st_failed": "✗ Residual data",
        "st_error": "⚠ Error",
        "d_removed": "Removed: ",
        "d_residual": "{n} left — double-click for the list",
        "m_add_first": "Add files first.",
        "m_nothing_clean": "Nothing to clean.",
        "m_nothing_save": "No cleaned files to save.",
        "m_select_rows": "Select rows to save.",
        "m_replace_title": "Replace originals?",
        "m_replace_text": "Originals will be replaced with the cleaned files. Continue?",
        "m_nothing_report": "Nothing to save yet.",
        "dlg_title": "Details",
        "dlg_file": "File: ",
        "dlg_type": "Type: ",
        "dlg_status": "Status: ",
        "dlg_targets": "Targeted containers:",
        "dlg_residual": "Residual metadata ({n}):",
        "dlg_ok": "Verification passed: no metadata left.",
        "dlg_msg": "Message: ",
        "eng_missing": "⚠ Not found: {tools}. Put the file(s) into the 'tools' folder next to the app.",
        "eng_exiftool": "exiftool.exe (needed for photo/RAW/video)",
        "eng_ffmpeg": "ffmpeg.exe (needed for video)",
        "report_dialog": "Save report",
    },
}

_COL_FILE, _COL_TYPE, _COL_STATUS, _COL_DETAILS = range(4)


if PYSIDE_OK:

    _COLOR_SAVED = QColor(46, 125, 50)
    _COLOR_CLEANED = QColor(2, 119, 189)
    _COLOR_BAD = QColor(198, 40, 40)
    _COLOR_GREY = QColor(120, 120, 120)

    class Worker(QThread):
        progress = Signal(int, int)
        file_done = Signal(str, object)  # path, WipeResult
        finished_all = Signal()

        def __init__(self, files: list[str], pipeline: Pipeline) -> None:
            super().__init__()
            self._files = files
            self._pipeline = pipeline

        def run(self) -> None:
            total = len(self._files)
            for i, f in enumerate(self._files, 1):
                try:
                    res = self._pipeline.prepare(Path(f))
                except Exception as exc:  # never let the thread die silently
                    res = WipeResult(Path(f), Status.ERROR, error=str(exc))
                self.file_done.emit(f, res)
                self.progress.emit(i, total)
            self.finished_all.emit()

    class DetectWorker(QThread):
        """Detects file types off the UI thread so the Type column fills in at once."""

        detected = Signal(str, str)  # path, type label

        def __init__(self, paths: list[str]) -> None:
            super().__init__()
            self._paths = paths

        def run(self) -> None:
            from ..core.detector import detect
            for p in self._paths:
                try:
                    label = detect(Path(p)).label
                except Exception:
                    label = "?"
                self.detected.emit(p, label)

    class SettingsDialog(QDialog):
        """Themes, accent colour, language and a couple of defaults."""

        def __init__(self, parent: "MainWindow", current: dict) -> None:
            super().__init__(parent)
            self.setWindowTitle(current["t_title"])
            self.setMinimumWidth(380)
            form = QFormLayout(self)
            form.setSpacing(12)

            self.cmb_theme = QComboBox()
            self.cmb_theme.addItem(current["t_light"], "light")
            self.cmb_theme.addItem(current["t_dark"], "dark")
            self.cmb_theme.setCurrentIndex(1 if current["theme"] == "dark" else 0)

            self.cmb_accent = QComboBox()
            for key, label in current["accent_items"]:
                self.cmb_accent.addItem(label, key)
            keys = list(ACCENTS)
            self.cmb_accent.setCurrentIndex(keys.index(current["accent"]) if current["accent"] in keys else 0)

            self.cmb_lang = QComboBox()
            self.cmb_lang.addItem("Українська", "uk")
            self.cmb_lang.addItem("English", "en")
            self.cmb_lang.setCurrentIndex(1 if current["lang"] == "en" else 0)

            self.chk_icc = QCheckBox(current["l_keep_icc"])
            self.chk_icc.setChecked(current["keep_icc"])
            self.chk_open = QCheckBox(current["l_open_after"])
            self.chk_open.setChecked(current["open_after"])

            form.addRow(current["l_theme"], self.cmb_theme)
            form.addRow(current["l_accent"], self.cmb_accent)
            form.addRow(current["l_lang"], self.cmb_lang)
            form.addRow("", self.chk_icc)
            form.addRow("", self.chk_open)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def values(self) -> dict:
            return {
                "theme": self.cmb_theme.currentData(),
                "accent": self.cmb_accent.currentData(),
                "lang": self.cmb_lang.currentData(),
                "keep_icc": self.chk_icc.isChecked(),
                "open_after": self.chk_open.isChecked(),
            }

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self._settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "MetaDel", "MetaDel")
            self.lang = self._settings.value("lang", "uk") or "uk"
            self._theme = self._settings.value("theme", "light") or "light"
            self._accent = self._settings.value("accent", "blue") or "blue"
            self._open_after = self._settings.value("open_after", False, type=bool)
            self._keep_icc_default = self._settings.value("keep_icc", True, type=bool)

            self._files: list[str] = []
            self._row_of: dict[str, int] = {}
            self._results: dict[str, WipeResult] = {}
            self._pretype: dict[str, str] = {}
            self._detect_workers: list = []
            self._check_cache: dict = {}
            self._worker: Optional[Worker] = None
            self._logger = get_logger()
            self.pipeline = Pipeline(logger=self._logger)

            self.resize(960, 600)
            self.setMinimumSize(720, 460)
            self.setAcceptDrops(True)
            self._build_ui()
            self._apply_theme()
            self._retranslate()
            self._refresh_engine_banner()

        def tr(self, key: str, **kw) -> str:
            text = TR[self.lang].get(key, key)
            return text.format(**kw) if kw else text

        # -- UI construction -------------------------------------------------

        def _build_ui(self) -> None:
            central = QWidget()
            root = QVBoxLayout(central)

            self.banner = QLabel()
            self.banner.setWordWrap(True)
            root.addWidget(self.banner)

            top = QHBoxLayout()
            self.btn_add = QPushButton()
            self.btn_add_dir = QPushButton()
            self.btn_clear = QPushButton()
            self.btn_settings = QPushButton()
            self.btn_add.clicked.connect(self._pick_files)
            self.btn_add_dir.clicked.connect(self._pick_folder)
            self.btn_clear.clicked.connect(self._clear)
            self.btn_settings.clicked.connect(self._open_settings)
            top.addWidget(self.btn_add)
            top.addWidget(self.btn_add_dir)
            top.addWidget(self.btn_clear)
            top.addStretch(1)
            top.addWidget(self.btn_settings)
            root.addLayout(top)

            opts = QHBoxLayout()
            self.chk_icc = QCheckBox()
            self.chk_icc.setChecked(self._keep_icc_default)
            opts.addWidget(self.chk_icc)
            opts.addStretch(1)
            root.addLayout(opts)

            self.table = QTableWidget(0, 4)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.verticalHeader().setVisible(False)
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(_COL_FILE, QHeaderView.Stretch)
            header.setSectionResizeMode(_COL_TYPE, QHeaderView.Interactive)
            header.setSectionResizeMode(_COL_STATUS, QHeaderView.Interactive)
            header.setSectionResizeMode(_COL_DETAILS, QHeaderView.Stretch)
            self.table.setColumnWidth(_COL_TYPE, 130)
            self.table.setColumnWidth(_COL_STATUS, 170)
            self.table.cellDoubleClicked.connect(self._show_details)
            root.addWidget(self.table, 1)

            self.progress = QProgressBar()
            self.progress.setValue(0)
            root.addWidget(self.progress)

            bottom = QHBoxLayout()
            self.btn_clean = QPushButton()
            self.btn_clean.setObjectName("primary")
            self.btn_save_sel = QPushButton()
            self.btn_save_all = QPushButton()
            self.btn_report = QPushButton()
            self.btn_clean.clicked.connect(self._start_clean)
            self.btn_save_sel.clicked.connect(self._save_selected)
            self.btn_save_all.clicked.connect(self._save_all)
            self.btn_report.clicked.connect(self._save_log)
            bottom.addWidget(self.btn_report)
            bottom.addStretch(1)
            bottom.addWidget(self.btn_clean)
            bottom.addWidget(self.btn_save_sel)
            bottom.addWidget(self.btn_save_all)
            root.addLayout(bottom)

            self.setCentralWidget(central)

        def _retranslate(self) -> None:
            self.setWindowTitle(self.tr("title"))
            self.btn_add.setText(self.tr("add_files"))
            self.btn_add_dir.setText(self.tr("add_folder"))
            self.btn_clear.setText(self.tr("clear"))
            self.btn_settings.setText("⚙  " + self.tr("btn_settings"))
            self.chk_icc.setText(self.tr("keep_icc"))
            self.table.setHorizontalHeaderLabels(
                [self.tr("col_file"), self.tr("col_type"), self.tr("col_status"), self.tr("col_details")]
            )
            self.btn_clean.setText(self.tr("btn_clean"))
            self.btn_save_sel.setText(self.tr("btn_save_sel"))
            self.btn_save_all.setText(self.tr("btn_save_all"))
            self.btn_report.setText(self.tr("btn_report"))
            # Make every button at least as wide as its (translated) text, so labels
            # ending in "…" are never clipped at any window size.
            for btn in (self.btn_add, self.btn_add_dir, self.btn_clear, self.btn_settings,
                        self.btn_clean, self.btn_save_sel, self.btn_save_all, self.btn_report):
                btn.setMinimumWidth(btn.sizeHint().width() + 14)
            for path in self._files:
                self._render_row(path)
            self._refresh_engine_banner()

        def _apply_theme(self) -> None:
            app = QApplication.instance()
            if app is None:
                return
            accent_hex = ACCENTS.get(self._accent, ACCENTS["blue"])
            check = self._checkmark_png(accent_hex).replace("\\", "/")
            app.setStyleSheet(build_qss(self._theme, self._accent, check))

        def _checkmark_png(self, color_hex: str) -> str:
            """Draw a small tick in the accent colour and cache it as a PNG (no SVG
            plugin needed), so a checked box shows a coloured ✓ instead of a solid fill."""
            cached = self._check_cache.get(color_hex)
            if cached and os.path.exists(cached):
                return cached
            import tempfile
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPainter, QPen, QPixmap, QPolygonF

            pm = QPixmap(16, 16)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(QColor(color_hex))
            pen.setWidthF(2.0)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPolyline(QPolygonF([QPointF(3.5, 8.5), QPointF(6.5, 11.5), QPointF(12.5, 4.5)]))
            painter.end()

            fd, path = tempfile.mkstemp(prefix="metadel_chk_", suffix=".png")
            os.close(fd)
            pm.save(path, "PNG")
            self._check_cache[color_hex] = path
            return path

        def _open_settings(self) -> None:
            current = {
                "t_title": self.tr("set_title"),
                "t_light": self.tr("set_light"),
                "t_dark": self.tr("set_dark"),
                "l_theme": self.tr("set_theme"),
                "l_accent": self.tr("set_accent"),
                "l_lang": self.tr("set_lang"),
                "l_keep_icc": self.tr("set_keep_icc"),
                "l_open_after": self.tr("set_open_after"),
                "accent_items": [(k, self.tr("acc_" + k)) for k in ACCENTS],
                "theme": self._theme,
                "accent": self._accent,
                "lang": self.lang,
                "keep_icc": self.chk_icc.isChecked(),
                "open_after": self._open_after,
            }
            dlg = SettingsDialog(self, current)
            if dlg.exec() != QDialog.Accepted:
                return
            v = dlg.values()
            self._theme = v["theme"]
            self._accent = v["accent"]
            self._open_after = v["open_after"]
            self.lang = v["lang"]
            self.chk_icc.setChecked(v["keep_icc"])
            for key in ("theme", "accent", "lang", "open_after", "keep_icc"):
                self._settings.setValue(key, v[key])
            self._apply_theme()
            self._retranslate()

        def _refresh_engine_banner(self) -> None:
            # No "works locally" notice — show a warning only if a tool is missing.
            missing = []
            if not exiftool_available():
                missing.append(self.tr("eng_exiftool"))
            if not ffmpeg_available():
                missing.append(self.tr("eng_ffmpeg"))
            if missing:
                self.banner.setText(self.tr("eng_missing", tools=", ".join(missing)))
                self.banner.setStyleSheet("color:#c62828;")
                self.banner.setVisible(True)
            else:
                self.banner.clear()
                self.banner.setVisible(False)

        # -- file list -------------------------------------------------------

        def _add_files(self, paths: list[str]) -> None:
            new_keys: list[str] = []
            for p in paths:
                path = Path(p)
                if not path.is_file():
                    continue
                key = str(path)
                if key in self._row_of:
                    continue
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col in range(4):
                    self.table.setItem(row, col, QTableWidgetItem(""))
                self.table.item(row, _COL_FILE).setText(path.name)
                self.table.item(row, _COL_FILE).setToolTip(key)
                self._files.append(key)
                self._row_of[key] = row
                self._render_row(key)
                new_keys.append(key)
            if new_keys:
                self._start_detection(new_keys)

        def _start_detection(self, keys: list[str]) -> None:
            worker = DetectWorker(keys)
            worker.detected.connect(self._on_detected)
            worker.finished.connect(self._cleanup_detect_workers)
            self._detect_workers.append(worker)
            worker.start()

        def _on_detected(self, path: str, label: str) -> None:
            self._pretype[path] = label
            if path not in self._results:  # don't overwrite a finished result
                self._render_row(path)

        def _cleanup_detect_workers(self) -> None:
            self._detect_workers = [w for w in self._detect_workers if w.isRunning()]

        def _pick_files(self) -> None:
            files, _ = QFileDialog.getOpenFileNames(self, self.tr("add_files"))
            if files:
                self._add_files(files)

        def _pick_folder(self) -> None:
            folder = QFileDialog.getExistingDirectory(self, self.tr("add_folder"))
            if folder:
                self._add_files([str(p) for p in Path(folder).rglob("*") if p.is_file()])

        def _clear(self) -> None:
            if self._worker is not None:
                return
            for res in self._results.values():
                self.pipeline.discard(res)  # drop any unsaved staged temps
            self.table.setRowCount(0)
            self._files.clear()
            self._row_of.clear()
            self._results.clear()
            self._pretype.clear()
            self.progress.setValue(0)

        # -- drag & drop -----------------------------------------------------

        def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def dropEvent(self, event) -> None:  # noqa: N802
            paths = []
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.is_dir():
                    paths += [str(x) for x in p.rglob("*") if x.is_file()]
                elif p.is_file():
                    paths.append(str(p))
            self._add_files(paths)

        # -- clean -----------------------------------------------------------

        def _start_clean(self) -> None:
            if self._worker is not None:
                return
            if not self._files:
                QMessageBox.information(self, "MetaDel", self.tr("m_add_first"))
                return
            todo = [f for f in self._files if f not in self._results]
            if not todo:
                QMessageBox.information(self, "MetaDel", self.tr("m_nothing_clean"))
                return

            self.pipeline.keep_icc = self.chk_icc.isChecked()
            self._set_busy(True)
            self.progress.setMaximum(len(todo))
            self.progress.setValue(0)

            self._worker = Worker(todo, self.pipeline)
            self._worker.file_done.connect(self._on_file_done)
            self._worker.progress.connect(lambda done, total: self.progress.setValue(done))
            self._worker.finished_all.connect(self._on_finished)
            self._worker.start()

        def _on_file_done(self, path: str, result: WipeResult) -> None:
            self._results[path] = result
            self._render_row(path)

        def _on_finished(self) -> None:
            self._worker = None
            self._set_busy(False)

        def _set_busy(self, busy: bool) -> None:
            for w in (self.btn_add, self.btn_add_dir, self.btn_clear, self.btn_settings,
                      self.btn_clean, self.btn_save_sel, self.btn_save_all, self.chk_icc):
                w.setEnabled(not busy)

        # -- save ------------------------------------------------------------

        def _save_selected(self) -> None:
            rows = sorted({idx.row() for idx in self.table.selectionModel().selectedRows()})
            if not rows:
                QMessageBox.information(self, "MetaDel", self.tr("m_select_rows"))
                return
            self._save([self._path_at(r) for r in rows])

        def _save_all(self) -> None:
            self._save(list(self._files))

        def _save(self, paths: list[str]) -> None:
            if self._worker is not None:
                return
            stageable = [
                p for p in paths
                if p and p in self._results
                and self._results[p].status is Status.CLEANED
                and self._results[p].staged_path is not None
            ]
            if not stageable:
                QMessageBox.information(self, "MetaDel", self.tr("m_nothing_save"))
                return

            # Ask where to save: a single file -> "Save as"; several -> a folder.
            opened_dir = None
            if len(stageable) == 1:
                src = Path(stageable[0])
                suggested = str(src.with_name(f"{src.stem}_clean{src.suffix}"))
                # A filter for the source extension makes the dialog append it when
                # the user types a bare name.
                ext_filter = f"*{src.suffix} (*{src.suffix})" if src.suffix else ""
                dest, _ = QFileDialog.getSaveFileName(
                    self, self.tr("save_as"), suggested, ext_filter)
                if not dest:
                    return
                self._commit_one(stageable[0], Path(dest))
                opened_dir = Path(dest).parent
            else:
                folder = QFileDialog.getExistingDirectory(self, self.tr("choose_folder"))
                if not folder:
                    return
                target = Path(folder)
                for p in stageable:
                    self._commit_one(p, self._unique_in(target, Path(p).name))
                opened_dir = target

            if self._open_after and opened_dir and opened_dir.exists() and hasattr(os, "startfile"):
                try:
                    os.startfile(str(opened_dir))  # noqa: S606 - local, user-initiated
                except OSError:
                    pass

        def _commit_one(self, path: str, dest: Path) -> None:
            res = self.pipeline.commit_to(self._results[path], dest)
            self._results[path] = res
            self._render_row(path)
            if res.error:
                QMessageBox.warning(self, "MetaDel", res.error)

        @staticmethod
        def _unique_in(folder: Path, name: str) -> Path:
            dest = folder / name
            if not dest.exists():
                return dest
            stem, suffix = Path(name).stem, Path(name).suffix
            i = 1
            while (folder / f"{stem}_{i}{suffix}").exists():
                i += 1
            return folder / f"{stem}_{i}{suffix}"

        # -- rendering -------------------------------------------------------

        def _path_at(self, row: int) -> Optional[str]:
            for key, r in self._row_of.items():
                if r == row:
                    return key
            return None

        def _render_row(self, path: str) -> None:
            row = self._row_of.get(path)
            if row is None:
                return
            result = self._results.get(path)
            type_item = self.table.item(row, _COL_TYPE)
            status_item = self.table.item(row, _COL_STATUS)
            details_item = self.table.item(row, _COL_DETAILS)

            if result is None:
                type_item.setText(self._pretype.get(path, ""))
                status_item.setText(self.tr("st_queued"))
                status_item.setForeground(_COLOR_GREY)
                details_item.setText("")
                return

            type_item.setText(result.detected_label)
            status_item.setText(self._status_text(result))
            status_item.setForeground(self._status_color(result))
            details_item.setText(self._details_line(result))

        def _status_text(self, result: WipeResult) -> str:
            if result.status is Status.UNSUPPORTED:
                return self.tr("st_unsupported")
            if result.status is Status.ERROR:
                return self.tr("st_error")
            if result.status is Status.FAILED_VERIFICATION:
                return self.tr("st_failed")
            if result.status is Status.CLEANED:
                return self.tr("st_cleaned")
            return result.status.value

        @staticmethod
        def _status_color(result: WipeResult) -> "QColor":
            if result.status is Status.CLEANED:
                return _COLOR_SAVED
            if result.status is Status.UNSUPPORTED:
                return _COLOR_GREY
            return _COLOR_BAD

        def _details_line(self, result: WipeResult) -> str:
            if result.status is Status.CLEANED:
                return self.tr("d_removed") + ", ".join(result.removed)
            if result.status is Status.FAILED_VERIFICATION and result.report:
                return self.tr("d_residual", n=result.report.residual_count)
            return result.error

        def _show_details(self, row: int, _col: int) -> None:
            key = self._path_at(row)
            if key is None or key not in self._results:
                return
            result = self._results[key]
            lines = [
                self.tr("dlg_file") + Path(key).name,
                self.tr("dlg_type") + result.detected_label,
                self.tr("dlg_status") + self._status_text(result),
                "",
            ]
            if result.removed:
                lines.append(self.tr("dlg_targets"))
                lines += [f"  • {r}" for r in result.removed]
                lines.append("")
            if result.report and result.report.residuals:
                lines.append(self.tr("dlg_residual", n=result.report.residual_count))
                lines += [f"  • {r}" for r in result.report.residuals]
            elif result.status is Status.CLEANED:
                lines.append(self.tr("dlg_ok"))
            if result.error:
                lines += ["", self.tr("dlg_msg") + result.error]
            QMessageBox.information(self, self.tr("dlg_title"), "\n".join(lines))

        def _save_log(self) -> None:
            if not self._results:
                QMessageBox.information(self, "MetaDel", self.tr("m_nothing_report"))
                return
            path, _ = QFileDialog.getSaveFileName(self, self.tr("report_dialog"),
                                                  "metadel-report.txt", "Text (*.txt)")
            if not path:
                return
            lines = []
            for key in self._files:
                res = self._results.get(key)
                if not res:
                    continue
                lines.append(f"[{res.status.value}] {key} ({res.detected_label})")
                if res.removed:
                    lines.append("    removed: " + ", ".join(res.removed))
                if res.report and res.report.residuals:
                    for r in res.report.residuals:
                        lines.append(f"    residual: {r}")
                if res.output_path:
                    lines.append(f"    saved: {res.output_path}")
                if res.error:
                    lines.append(f"    note: {res.error}")
            Path(path).write_text("\n".join(lines), encoding="utf-8")

        def closeEvent(self, event) -> None:  # noqa: N802
            for res in self._results.values():
                self.pipeline.discard(res)
            super().closeEvent(event)


def main() -> int:
    if not PYSIDE_OK:
        print("PySide6 is not installed. Run: pip install PySide6")
        return 1
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
