from random import shuffle
from typing import Iterable, Literal

import pandas
import numpy

from core import SheetsSchemes, WordNotCompleted, PATH_TO_VOCABULARY, \
    DictWithDefaultReturn, SheetScheme

from excel_modifier import ExcelModifier
from spelling_checker import SpellChecker


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
    sheet_name_request = "What words do you want to learn?({})\n"
    no_such_sheet_message = "No such sheet!"
    sheet_name_second_request = "Please, choose one of those: {}. \n"
    use_preset_request = "Use preset?(y/n)"
    use_range_request = "Get only the words within a certain range?((start, stop)/n)"
    words_status_request = "Which words do you want to learn?(a/n/r)"
    congratulations_message = "Congratulations! You've done it!"
    lets_fix_mistakes_message = "Now let's fix the mistakes."


def process_range(rng: str) -> list[int, int]:
    r = list(map(int, rng.split(" ")))
    r[0] -= 1
    return r


class Dictation:
    targets = {
        "a": lambda x: True,
        "r": lambda x: x == "NEEDS_REVISION",
        "n": lambda x: x == "NEW"
    }
    range_use: DictWithDefaultReturn = DictWithDefaultReturn(
        {"n": lambda words, rng: slice(words.shape[0])},
        lambda words, rng: slice(*process_range(rng))
    )
    settings_preset = {
        "use_range": range_use.__getitem__("n"),
        "target": targets.get("n")
    }

    def __init__(self) -> None:
        self.sheets_schemes = SheetsSchemes()
        self.sheet_name = self.get_sheet_name()
        self.sheet_scheme = self.sheets_schemes.get(self.sheet_name)

        self.all_words = self.get_all_words()
        self.words_range, self.target_checker = self.get_dictation_settings()
        self.requested_words = self.get_requested_words()

    def get_sheet_name(self) -> str:
        sheet_name = input(StringConstants.sheet_name_request.format(
            {'/'.join(self.sheets_schemes.available_sheets)}))

        while sheet_name not in self.sheets_schemes.available_sheets:
            print(StringConstants.no_such_sheet_message)
            sheet_name = input(StringConstants.sheet_name_second_request.format(
                {'/'.join(self.sheets_schemes.available_sheets)}))

        return sheet_name

    def get_all_words(self):
        words = pandas.read_excel(PATH_TO_VOCABULARY, sheet_name=self.sheet_name)
        words = numpy.array(words, dtype=str)
        return words

    def get_dictation_settings(self):
        use_preset = True if input(StringConstants.use_preset_request) == "y" else False
        if use_preset:
            words_range, target_checker = self.settings_preset.values()
            return words_range(self.all_words, ""), target_checker
        use_range = input(StringConstants.use_range_request)
        target = input(StringConstants.words_status_request)
        words_range = self.range_use.__getitem__(use_range)(self.all_words, use_range)
        check_target_function = self.targets.get(target, self.targets.get("a"))
        return words_range, check_target_function

    def get_requested_words(self) -> dict[int, numpy.ndarray]:
        a = {}
        c = s if (s:=self.words_range.start) else 0
        for num, val in enumerate(self.all_words[self.words_range]):
            if self.target_checker(val[self.sheet_scheme.status].split("*")[0]):
                a[num+c] = val
        a = list(a.items())
        shuffle(a)
        return dict(a)

    def update_statuses(
            self,
            needed_updates: dict[Literal["NEEDS_REVISION", "NORMAL"], Iterable[int]]
    ) -> None:
        excel = ExcelModifier(self.sheet_name, self.sheet_scheme.status)
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


Dictation().start_dictation()
