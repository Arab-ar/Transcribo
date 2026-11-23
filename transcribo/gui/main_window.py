"""Главное окно приложения с рабочим словарем на SQLite (с поиском и редактированием)."""

from __future__ import annotations

import sys
import re
from pathlib import Path

from PySide6.QtCore import Qt, QStandardPaths
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QSplitter,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox
)

from transcribo.core.engine import TranscriptionEngine
from transcribo.core.database import DatabaseStore


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Transcribo — English → Russian")
        self.resize(1000, 650)

        # 1. Инициализируем хранилище (SQLite)
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        self.db_path = Path(app_data) / "vocabulary.db"
        self.dict_store = DatabaseStore(self.db_path)

        # 2. Импортируем базовый словарь (если он есть)
        self._import_base_vocabulary()

        # 3. Инициализируем движок с уже заполненной базой
        self.engine = TranscriptionEngine(custom_vocabulary=self.dict_store.as_vocabulary())

        # Защитный флаг, чтобы таблица не обновляла БД во время отрисовки
        self._is_refreshing_table = False

        # 4. Строим интерфейс
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_transcribe_tab(), "Транскрипция")
        self.tabs.addTab(self._build_dictionary_tab(), "Словарь")
        main_layout.addWidget(self.tabs)

        self.statusBar().showMessage("Готово")
        self.refresh_dictionary_table()

    def _import_base_vocabulary(self) -> None:
        """Импортирует слова из resources/base_vocabulary.db в пользовательскую базу."""
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
        button_row = QHBoxLayout()
        
        self.transcribe_button = QPushButton("Транскрибировать →")
        self.transcribe_button.clicked.connect(self.on_transcribe_clicked)
        button_row.addWidget(self.transcribe_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Английский текст:"))
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Введите или вставьте текст на английском...")
        left_layout.addWidget(self.input_edit)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Транскрипция:"))
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Здесь появится результат...")
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

        # Поисковая строка
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по словарю...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Слово", "Транскрипция", "Источник"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # РАЗРЕШАЕМ РЕДАКТИРОВАНИЕ ПО ДВОЙНОМУ КЛИКУ
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
        )
        # Подключаем сигнал изменения ячейки
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
        return tab

    # ---------- Логика ----------
    def refresh_dictionary_table(self, filter_text: str = ""):
        """Перерисовывает таблицу. Если передан filter_text — фильтрует."""
        self._is_refreshing_table = True  # Блокируем срабатывание itemChanged
        
        entries = self.dict_store.get_all()
        if filter_text:
            entries = [e for e in entries if filter_text.lower() in e.word.lower()]

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.word))
            self.table.setItem(row, 1, QTableWidgetItem(entry.transcription))
            
            source_text = "Вы" if entry.source == "user" else "Авто"
            source_item = QTableWidgetItem(source_text)
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Источник менять нельзя
            self.table.setItem(row, 2, source_item)
            
        self._is_refreshing_table = False

    def update_engine_vocabulary(self):
        self.engine.update_vocabulary(self.dict_store.as_vocabulary())

    def on_search_changed(self, text: str):
        """Вызывается при вводе текста в поисковую строку."""
        self.refresh_dictionary_table(text)

    def on_item_changed(self, item: QTableWidgetItem):
        """Вызывается, когда пользователь отредактировал ячейку в таблице."""
        if self._is_refreshing_table:
            return  # Игнорируем программные изменения таблицы

        row = item.row()
        col = item.column()

        # Редактировать можно только транскрипцию (колонка 1)
        if col != 1:
            return

        word = self.table.item(row, 0).text()
        new_transcription = item.text().strip()

        if not new_transcription:
            QMessageBox.warning(self, "Ошибка", "Транскрипция не может быть пустой!")
            self.refresh_dictionary_table(self.search_input.text())
            return

        # Сохраняем как "user", чтобы перезаписать авто-вариант
        self.dict_store.add(word, new_transcription, source="user")
        self.update_engine_vocabulary()
        
        # Обновляем колонку "Источник", чтобы показать, что слово стало "Вы"
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

    def on_transcribe_clicked(self) -> None:
        text = self.input_edit.toPlainText()
        result = self.engine.transcribe(text)
        self.output_edit.setPlainText(result)
        self.statusBar().showMessage("Транскрипция выполнена", 3000)