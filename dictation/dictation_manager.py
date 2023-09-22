from random import shuffle

import pandas
import numpy

from core import SheetsSchemes, WordNotCompleted, PATH_TO_VOCABULARY, DictWithDefaultReturn, SheetScheme
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
    use_range_request = "Get only the words within a certain range?(y/n)"
    words_status_request = "Which words do you want to learn?(a/n/r)"
    congratulations_message = "Congratulations! You've done it!"
    lets_fix_mistakes_message = "Now let's fix the mistakes."


class Dictation:
    targets = {
        "a": True,
        "r": lambda x: x == "NEEDS_REVISION",
        "n": lambda x: x == "NEW"
    }
    range_use: DictWithDefaultReturn = DictWithDefaultReturn(
        {"n": lambda x: slice(x.shape[0])}, lambda x: slice(len(x))
    )
    settings_preset = {
        "use_range": range_use.__getitem__("non-existent-key"),
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
        words = numpy.array(words)
        return words

    def get_dictation_settings(self):
        use_preset = True if input(StringConstants.use_preset_request) == "y" else False
        if use_preset:
            return self.settings_preset.values()
        use_range = input(StringConstants.use_range_request)
        target = input(StringConstants.words_status_request)
        words_range = self.words_range.get(use_range)
        check_target_function = self.targets.get(target, True)
        return words_range, check_target_function

    def get_requested_words(self) -> list[numpy.ndarray]:
        return [i for i in self.all_words[self.words_range(self.all_words)]
                if self.target_checker(i[self.sheet_scheme.status])]

    def start_dictation(self) -> None:
        words = self.requested_words
        while words:
            words = []
            for i in self.requested_words:
                try:
                    MainChecker(list(i), self.sheet_scheme).check()
                except WordNotCompleted:
                    words.append(i)
            if words:
                print(StringConstants.lets_fix_mistakes_message)
                shuffle(words)
            self.requested_words = words
        print(StringConstants.congratulations_message)


Dictation().start_dictation()
