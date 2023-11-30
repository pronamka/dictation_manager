from random import shuffle
from typing import Iterable, Literal

from core import WordNotCompleted, SheetScheme

from excel_modifier import ExcelModifier
from spelling_checker import SpellChecker
from words_getter import GettersManager


class CheckerManager:

    def __init__(self, word_row: list, to_check: dict) -> None:
        self.to_check = to_check
        self.word_row = word_row

    def check(self) -> None:
        word = self.word_row[self.to_check.get("spelling")]
        if self.to_check.get("pronunciation", None) is not None:
            pronunciation = self.word_row[self.to_check.get("pronunciation")]
        else:
            pronunciation = ""

        SpellChecker(self.to_check.get("comment_spelling"), word, pronunciation).check()
        # PronunciationChecker(self.to_check.get("comment_pronunciation"), word, pronunciation).check()


class MainChecker:

    def __init__(self, words_row: list, row_scheme: SheetScheme) -> None:
        self.current_scheme = row_scheme
        self.word_translation = words_row[row_scheme.translation]
        self.word_row = words_row

    def check(self) -> None:
        print(f"Russian: {self.word_translation}")
        for row in self.current_scheme.to_check:
            CheckerManager(self.word_row, row).check()


class StringConstants:
    congratulations_message = "Congratulations! You've done it!"
    lets_fix_mistakes_message = "Now let's fix the mistakes."


class Dictation:
    def __init__(self, sheet_scheme: SheetScheme, words: dict[int, str]):
        self.requested_words = words
        self.sheet_scheme = sheet_scheme

    def update_statuses(
            self,
            needed_updates: dict[Literal["NEEDS_REVISION", "NORMAL"], Iterable[int]]
    ) -> None:
        excel = ExcelModifier(self.sheet_scheme.sheet_name, self.sheet_scheme.status)
        for new_status, row_indexes in needed_updates.items():
            excel.modify(new_status, row_indexes)
        excel.commit()

    def start_dictation(self) -> None:
        words = self.requested_words
        need_revision = set()
        remembered = set()
        while words:
            words = []
            for key, val in self.requested_words.items():
                try:
                    MainChecker(list(val), self.sheet_scheme).check()
                    remembered.add(key)
                except WordNotCompleted:
                    words.append((key, val))
                    need_revision.add(key)
            if words:
                print(StringConstants.lets_fix_mistakes_message)
                shuffle(words)
                words = dict(words)
            self.requested_words = words
        remembered = remembered.difference(need_revision)
        self.update_statuses({"NEEDS_REVISION": need_revision, "NORMAL": remembered})
        print(StringConstants.congratulations_message)


if __name__ == "__main__":
    data = GettersManager().get_learning_data()
    Dictation(*data).start_dictation()