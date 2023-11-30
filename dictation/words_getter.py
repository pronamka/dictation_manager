from random import shuffle
from typing import Callable

import pandas
import numpy

from core import SheetsSchemes, PATH_TO_VOCABULARY, \
    DictWithDefaultReturn, SheetScheme, process_range


class StringConstants:
    sheet_name_request = "What words do you want to learn?({})\n"
    no_such_sheet_message = "No such sheet!"
    sheet_name_second_request = "Please, choose one of those: {}. \n"
    use_preset_request = "Use preset?(y/n)"
    use_range_request = "Get only the words within a certain range?((start, stop)/n)"
    words_status_request = "Which words do you want to learn?(a/n/r)"


class SheetSchemeGetter:
    """Class to get the scheme of the sheet, words from which user wants to learn."""
    sheet_schemes = SheetsSchemes()
    available_schemes_message = StringConstants.sheet_name_request.format(
            {'/'.join(sheet_schemes.available_sheets)})

    def __init__(self) -> None:
        self.sheet_scheme = self.get_sheet_scheme()

    def get_sheet_scheme(self) -> SheetScheme:
        sheet_name = self.get_input()
        while sheet_name not in self.sheet_schemes.available_sheets:
            print(StringConstants.no_such_sheet_message)
            sheet_name = self.get_input()

        return self.sheet_schemes.get(sheet_name)

    @classmethod
    def get_input(cls):
        return input(cls.available_schemes_message)

    @property
    def scheme(self):
        return self.sheet_scheme


class WordsGetter:
    """Class to get words that need to be learned from an Excel file."""

    # possible statuses of words. User can specify words with which status he wants to learn
    targets = {
        "a": lambda x: True,
        "r": lambda x: x == "NEEDS_REVISION",
        "n": lambda x: x == "NEW"
    }

    # calculates the range of words that are to be learned
    range_use: DictWithDefaultReturn = DictWithDefaultReturn(
        {"n": lambda words, rng: slice(words.shape[0])},
        lambda words, rng: slice(*process_range(rng))
    )

    # a preset for quick settings initialization
    settings_preset = {
        "use_range": range_use.__getitem__("n"),
        "target": targets.get("n")
    }

    def __init__(self, sheet_scheme: SheetScheme) -> None:
        self.sheet_scheme = sheet_scheme

        self.all_words = self.get_all_words()
        self.words_range, self.target_checker = self.get_dictation_settings()
        self.requested_words: dict[int, str] = self.get_requested_words()

    def get_all_words(self) -> numpy.ndarray[str]:
        """Read the specified sheet and extract all content from it."""
        words = pandas.read_excel(PATH_TO_VOCABULARY, sheet_name=self.sheet_scheme.sheet_name)
        words = numpy.array(words, dtype=str)
        return words

    def get_dictation_settings(self) -> tuple[slice, Callable]:
        """Initialize dictation settings: the status of the words that need to be learned
        and the range from which to take them."""

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
        """Filters words: leaves only those with the right status and in right range."""
        a = {}
        c = s if (s := self.words_range.start) else 0
        for num, val in enumerate(self.all_words[self.words_range]):
            if self.target_checker(val[self.sheet_scheme.status].split("*")[0]):
                a[num + c] = val
        a = list(a.items())
        shuffle(a)
        return dict(a)

    @property
    def words(self):
        return self.requested_words


class GettersManager:
    """Class to get words to learn and sheet scheme."""
    def __init__(self):
        self.scheme = SheetSchemeGetter().scheme
        self.words = WordsGetter(self.scheme).words

    def get_learning_data(self) -> tuple[SheetScheme, numpy.ndarray[str]]:
        """:returns: scheme of the list from which the words were taken
        and the words themselves."""
        return self.scheme, self.words
