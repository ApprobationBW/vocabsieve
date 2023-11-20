from .GenericImporter import GenericImporter
from datetime import datetime as dt, timezone as tz
import sqlite3
import os
import re
from PyQt5.QtWidgets import QCheckBox, QLabel
from ..tools import grouper
from ..lemmatizer import lem_word
from .models import ReadingNote
from ..models import LookupRecord

def remove_author(titleauthor):
    "Remove author, which is in the last parentheses"
    return re.sub(r'\s*\([^)]*\)$', "", titleauthor)


class KindleVocabImporter(GenericImporter):
    def __init__(self, parent, path):
        super().__init__(parent, "Kindle lookups", path, "kindle")

    def toggleNotesFiltering(self, enable: bool):
        if enable:
            self.notes = self.clippings_items
        else:
            self.notes = None
        self.updateHighlightCount()

    def getNotes(self):
        if self.path is None:
            return []
        vocab_db_path = os.path.join(self.path, "system", "vocabulary", "vocab.db")
        clippings_path = os.path.join(self.path, "documents", "My Clippings.txt")

        con = sqlite3.connect(vocab_db_path)
        cur = con.cursor()

        try:
            with open(clippings_path) as file:
                clippings_titleauthors, _, _, clippings_words, _ = zip(*list(grouper(file.read().splitlines(), 5)))
                clippings_words = [re.sub('[\\?\\.!«»…,()\\[\\]]*', "", str(word)).lower() for word in clippings_words]
                clippings_titles = [remove_author(titleauthor.strip("\ufeff")) for titleauthor in clippings_titleauthors]
                self.clippings_items = set(zip(clippings_words, clippings_titles))
                clippings_only = QCheckBox(f"Only select highlighted words ({str(len(clippings_words))} entries found)")
                clippings_only.clicked.connect(self.toggleNotesFiltering)
                self._layout.addRow(clippings_only)
        except Exception as e:
            print(e)
            self.clippings_items = set()
            self._layout.addRow(QLabel("Cannot read highlights. Make sure that your clippings file is in the right place, and its length is a multiple of 5."))


        bookdata = list(cur.execute("SELECT * FROM book_info"))
        bookid2name = dict(zip(list(zip(*bookdata))[2],list(zip(*bookdata))[4]))
        reading_notes = []
        langcode = self.parent.settings.value("target_language", 'en')
        count = 0
        lookups_count_before = self.parent.rec.countLookups(langcode)
        for _, lword, bookid, _, _, sentence, timestamp in cur.execute("SELECT * FROM lookups"):
            if lword.startswith(langcode):
                word = lword.removeprefix(langcode+":")
                count += 1
                self.parent.rec.recordLookup(
                    LookupRecord(
                        word=word, 
                        lemma=lem_word(word, langcode),
                        language=langcode, 
                        source="kindle", 
                        lemmatization=False,
                        success=True,
                    ), 
                    timestamp/1000, 
                    commit=False
                )
                reading_notes.append(
                    ReadingNote(
                        lookup_term=word,
                        sentence=sentence,
                        book_name=bookid2name[bookid],
                        date=str(dt.fromtimestamp(timestamp/1000).astimezone())[:19]
                    
                    )
                )
        lookups_count_after = self.parent.rec.countLookups(langcode)
        self._layout.addRow(QLabel("Vocabulary database: " + vocab_db_path))
        self._layout.addRow(QLabel(f"Found {count} lookups in {langcode}, added { lookups_count_after - lookups_count_before } to lookup database."))
        self.parent.rec.conn.commit()
        return reading_notes