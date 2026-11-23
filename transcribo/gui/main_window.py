"""Главное окно приложения."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QSplitter,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from transcribo.core.engine import TranscriptionEngine


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Transcribo — English → Russian")
        self.resize(1000, 650)

        self.engine = TranscriptionEngine()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_transcribe_tab(), "Транскрипция")
        self.tabs.addTab(self._build_dictionary_tab(), "Словарь")
        main_layout.addWidget(self.tabs)

        self.statusBar().showMessage("Готово")

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

    def _build_dictionary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        placeholder = QLabel("Здесь появится редактор пользовательского словаря.\nЭтап 4.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)
        return tab

    def on_transcribe_clicked(self) -> None:
        text = self.input_edit.toPlainText()
        result = self.engine.transcribe(text)
        self.output_edit.setPlainText(result)
        self.statusBar().showMessage("Транскрипция выполнена", 3000)