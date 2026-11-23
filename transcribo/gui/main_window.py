"""Главное окно приложения: Асинхронность, Файлы, Drag & Drop."""

from __future__ import annotations

import sys
import re
from pathlib import Path

from PySide6.QtCore import Qt, QStandardPaths
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QSplitter,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QFileDialog
)

from transcribo.core.engine import TranscriptionEngine
from transcribo.core.database import DatabaseStore
from transcribo.core.worker import TranscriptionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Transcribo — English → Russian")
        self.resize(1000, 650)
        self.setAcceptDrops(True)  # Включаем Drag & Drop для главного окна

        # 1. Инициализируем хранилище (SQLite)
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        self.db_path = Path(app_data) / "vocabulary.db"
        self.dict_store = DatabaseStore(self.db_path)

        # 2. Импортируем базовый словарь
        self._import_base_vocabulary()

        # 3. Инициализируем движок
        self.engine = TranscriptionEngine(custom_vocabulary=self.dict_store.as_vocabulary())

        self._is_refreshing_table = False
        self.worker = None  # Ссылка на фоновый поток

        # 4. Строим интерфейс
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_transcribe_tab(), "Транскрипция")
        self.tabs.addTab(self._build_dictionary_tab(), "Словарь")
        main_layout.addWidget(self.tabs)

        self.statusBar().showMessage("Готово. Перетащите .txt файл в окно для загрузки.")
        self.refresh_dictionary_table()

    def _import_base_vocabulary(self) -> None:
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.parent
            
        base_db_file = base_path / "resources" / "base_vocabulary.db"
        
        if base_db_file.exists():
            base_store = DatabaseStore(base_db_file)
            existing_words = {e.word for e in self.dict_store.get_all()}
            for entry in base_store.get_all():
                if entry.word not in existing_words:
                    self.dict_store.add(entry.word, entry.transcription, source="auto")

    # ---------- Вкладка 1: Транскрипция ----------
    def _build_transcribe_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Панель инструментов (Кнопки)
        button_row = QHBoxLayout()
        
        self.transcribe_button = QPushButton("Транскрибировать →")
        self.transcribe_button.clicked.connect(self.on_transcribe_clicked)
        
        self.open_button = QPushButton("📂 Открыть .txt")
        self.open_button.clicked.connect(self.on_open_file_clicked)
        
        self.save_button = QPushButton("💾 Сохранить результат")
        self.save_button.clicked.connect(self.on_save_file_clicked)

        button_row.addWidget(self.transcribe_button)
        button_row.addWidget(self.open_button)
        button_row.addWidget(self.save_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        # Текстовые поля
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Английский текст (или перетащите файл сюда):"))
        
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Введите или вставьте текст на английском...")
        # ОТКЛЮЧАЕМ перехват файлов, чтобы работал Drag & Drop главного окна
        self.input_edit.setAcceptDrops(False) 
        
        left_layout.addWidget(self.input_edit)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Транскрипция:"))
        
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Здесь появится результат...")
        # ОТКЛЮЧАЕМ перехват файлов и для поля вывода
        self.output_edit.setAcceptDrops(False)
        
        right_layout.addWidget(self.output_edit)
        splitter.addWidget(right)

        splitter.setSizes([500, 500])
        layout.addWidget(splitter, stretch=1)
        return tab

    # ---------- Вкладка 2: Словарь ----------
    def _build_dictionary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Форма добавления
        form_layout = QHBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Слово (на англ.)")
        self.transcription_input = QLineEdit()
        self.transcription_input.setPlaceholderText("Транскрипция (на рус.)")
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.on_add_word_clicked)
        self.delete_button = QPushButton("Удалить выбранное")
        self.delete_button.clicked.connect(self.on_delete_word_clicked)

        form_layout.addWidget(QLabel("Слово:"))
        form_layout.addWidget(self.word_input, stretch=1)
        form_layout.addWidget(QLabel("Транскрипция:"))
        form_layout.addWidget(self.transcription_input, stretch=1)
        form_layout.addWidget(self.add_button)
        form_layout.addWidget(self.delete_button)
        layout.addLayout(form_layout)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по словарю...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Слово", "Транскрипция", "Источник"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
        return tab

    # ---------- Асинхронная транскрипция ----------
    def on_transcribe_clicked(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите текст для транскрипции.")
            return

        self.transcribe_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.transcribe_button.setText("Обработка...")
        self.statusBar().showMessage("Идет транскрипция в фоновом режиме...")

        self.worker = TranscriptionWorker(self.engine, text)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_transcription_error)
        self.worker.start()

    def on_transcription_finished(self, result: str):
        self.output_edit.setPlainText(result)
        self.transcribe_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.transcribe_button.setText("Транскрибировать →")
        self.statusBar().showMessage("Транскрипция завершена!", 3000)

    def on_transcription_error(self, error_msg: str):
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {error_msg}")
        self.transcribe_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.transcribe_button.setText("Транскрибировать →")
        self.statusBar().showMessage("Ошибка при обработке", 3000)

    # ---------- Работа с файлами ----------
    def on_open_file_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self._load_file_to_input(file_path)

    def on_save_file_clicked(self) -> None:
        text = self.output_edit.toPlainText()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Нет текста для сохранения.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                Path(file_path).write_text(text, encoding="utf-8")
                self.statusBar().showMessage(f"Сохранено в {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    # ---------- Drag & Drop ----------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".txt"):
                self._load_file_to_input(file_path)
                break
            else:
                QMessageBox.warning(self, "Ошибка", "Поддерживаются только .txt файлы.")

    def _load_file_to_input(self, file_path: str):
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            self.input_edit.setPlainText(content)
            self.statusBar().showMessage(f"Загружен файл: {Path(file_path).name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{e}")

    # ---------- Логика словаря ----------
    def refresh_dictionary_table(self, filter_text: str = ""):
        self._is_refreshing_table = True
        entries = self.dict_store.get_all()
        if filter_text:
            entries = [e for e in entries if filter_text.lower() in e.word.lower()]

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.word))
            self.table.setItem(row, 1, QTableWidgetItem(entry.transcription))
            
            source_text = "Вы" if entry.source == "user" else "Авто"
            source_item = QTableWidgetItem(source_text)
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, source_item)
            
        self._is_refreshing_table = False

    def update_engine_vocabulary(self):
        self.engine.update_vocabulary(self.dict_store.as_vocabulary())

    def on_search_changed(self, text: str):
        self.refresh_dictionary_table(text)

    def on_item_changed(self, item: QTableWidgetItem):
        if self._is_refreshing_table or item.column() != 1:
            return
            
        row = item.row()
        word = self.table.item(row, 0).text()
        new_transcription = item.text().strip()

        if not new_transcription:
            QMessageBox.warning(self, "Ошибка", "Транскрипция не может быть пустой!")
            self.refresh_dictionary_table(self.search_input.text())
            return

        self.dict_store.add(word, new_transcription, source="user")
        self.update_engine_vocabulary()
        
        self._is_refreshing_table = True
        self.table.setItem(row, 2, QTableWidgetItem("Вы"))
        self._is_refreshing_table = False
        
        self.statusBar().showMessage(f"Обновлено: {word} -> {new_transcription}", 3000)

    def on_add_word_clicked(self) -> None:
        word = self.word_input.text().strip()
        transcription = self.transcription_input.text().strip()

        if not word or not transcription:
            QMessageBox.warning(self, "Ошибка", "Заполните оба поля!")
            return
            
        if re.search(r'[а-яА-ЯёЁ]', word):
            QMessageBox.warning(self, "Ошибка", "Слово должно быть на английском (без кириллицы)")
            return

        self.dict_store.add(word, transcription, source="user")
        self.refresh_dictionary_table(self.search_input.text())
        self.update_engine_vocabulary()

        self.word_input.clear()
        self.transcription_input.clear()
        self.word_input.setFocus()
        self.statusBar().showMessage(f"Слово '{word}' добавлено", 3000)

    def on_delete_word_clicked(self) -> None:
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите слово в таблице для удаления.")
            return

        word = self.table.item(selected_row, 0).text()
        self.dict_store.remove(word)
        self.refresh_dictionary_table(self.search_input.text())
        self.update_engine_vocabulary()
        self.statusBar().showMessage(f"Слово '{word}' удалено", 3000)