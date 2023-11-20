from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from .searchable_text_edit import SearchableTextEdit 
from ..models import Definition, DictionarySourceGroup, DisplayMode
from ..format import markdown_nop
from typing import Optional

class MultiDefinitionWidget(SearchableTextEdit):
    def __init__(self, word_widget: Optional[QLineEdit] = None):
        super().__init__()
        self.sg = DictionarySourceGroup([])
        self.word_widget = word_widget
        self._layout = QVBoxLayout(self)
        self.definitions: list[Definition] = []
        self.currentIndex = 0
        self.currentDefinition: Optional[Definition] = None
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.info_label)
        self._layout.setAlignment(Qt.AlignBottom)
        buttons_box_widget = QWidget()
        self._layout.addWidget(buttons_box_widget)
        buttons_box_layout = QHBoxLayout(buttons_box_widget)


        first_button = QPushButton("<<")
        prev_button = QPushButton("<")
        self.counter = QLabel("0/0")
        self.counter.setAlignment(Qt.AlignCenter)
        next_button = QPushButton(">")
        last_button = QPushButton(">>")
        buttons_box_layout.addWidget(first_button)
        buttons_box_layout.addWidget(prev_button)
        buttons_box_layout.addWidget(self.counter)
        buttons_box_layout.addWidget(next_button)
        buttons_box_layout.addWidget(last_button)
        prev_button.clicked.connect(self.back)
        next_button.clicked.connect(self.forward)
        first_button.clicked.connect(self.first)
        last_button.clicked.connect(self.last)

    def setSourceGroup(self, sg: DictionarySourceGroup):
        self.sg = sg

    def getDefinitions(self, word: str) -> list[Definition]:
        """Can be used by other classes to get definitions from the source group
        filters out definitions with no definition"""

        return [defi for defi in self.sg.define(word) if defi.definition is not None]

    def lookup(self, word: str):
        self.reset()
        for definition in self.getDefinitions(word):
            self.appendDefinition(definition)


    def appendDefinition(self, definition: Definition):
        self.definitions.append(definition)
        self.updateIndex()

    def updateIndex(self):
        if not self.definitions:
            return
        self.counter.setText(f"{self.currentIndex+1}/{len(self.definitions)}")
        if defi:=self.definitions[self.currentIndex]:
            self.currentDefinition = defi
            if defi.definition is not None:
                self.setText(defi.definition)
                self.info_label.setText(f"<strong>{defi.headword}</strong> in <em>{defi.source}</em>")
                if self.word_widget:
                    self.word_widget.setText(defi.headword)
    def setCurrentIndex(self, index: int):
        self.currentIndex = index
        self.updateIndex()
    
    def back(self):
        if self.currentIndex > 0:
            self.setCurrentIndex(self.currentIndex - 1)
        else: #wrap around
            self.setCurrentIndex(len(self.definitions) - 1)

    def forward(self):
        if self.currentIndex < len(self.definitions) - 1:
            self.setCurrentIndex(self.currentIndex + 1)
        else: #wrap around
            self.setCurrentIndex(0)

    def first(self):
        if self.definitions:
            self.setCurrentIndex(0)

    def last(self):
        if self.definitions:
            self.setCurrentIndex(len(self.definitions) - 1)

    def reset(self):
        self.definitions = []
        self.currentDefinition = None
        self.currentIndex = 0
        self.setText("")
        self.info_label.setText("")
        self.counter.setText("0/0")

    def process_defi_anki(self) -> str:
        """Process definitions before sending to Anki"""
        # Figure out display mode of current source
        if self.currentDefinition is None:
            return ""
        
        source_name = self.currentDefinition.source
        source = self.sg.getSource(source_name)
        if source is None:
            return ""

        match source.display_mode:
            case DisplayMode.raw:
                return self.toPlainText().replace("\n", "<br>")
            case DisplayMode.plaintext:
                return self.toPlainText().replace("\n", "<br>")
            case DisplayMode.markdown:
                return markdown_nop(self.toPlainText())
            case DisplayMode.markdown_html:
                return markdown_nop(self.toMarkdown())
            case DisplayMode.html:
                return self.original
