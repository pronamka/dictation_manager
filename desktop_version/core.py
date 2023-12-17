import os

from typing import Union, Callable, Generator
from collections import deque
from ast import literal_eval
from random import shuffle

import numpy as np
import pandas as pd

from desktop_version.exceptions import VocabularyFileNotFoundError, SheetNotFoundError, InvalidStatusError, \
    InvalidSchemeError, NoWordsMatchingSettings


class Settings(dict):
    settings_filename = "settings.txt"
    vocabulary_key = "PATH_TO_VOCABULARY"
    schemes_key = "schemes"

    def __init__(self):
        with open(self.settings_filename, mode="r") as file:
            settings_dict = literal_eval(file.read())
        super().__init__(settings_dict)

    def change_settings(self, key, value) -> None:
        self[key] = value
        with open(self.settings_filename, mode="w") as file:
            file.write(str(self))

    @property
    def schemes(self) -> dict:
        return self.get(self.schemes_key, {})

    """@property
    def schemes_as_options(self) -> list[ft.dropdown.Option]:
        return [ft.dropdown.Option(i) for i in self.get(self.schemes_key, {}).keys()]"""

    @property
    def path(self) -> str:
        return self.get(self.vocabulary_key, "")

    @property
    def vocabulary_path_valid(self) -> bool:
        path = self.get(self.vocabulary_key, "")
        if os.path.exists(path) and path.rsplit(".", maxsplit=1)[-1] == "xlsx":
            return True
        return False


class SheetScheme:
    """Represents a scheme of an Excel sheet.
    provides information on how the data is stored on the sheet."""
    def __init__(self,
                 sheet_name: str,
                 translation_index: int,
                 status_index: int,
                 to_check: list[dict[str, Union[str, int]]]
                 ) -> None:
        self.sheet_name = sheet_name
        self.translation = translation_index
        self.status = status_index
        self.to_check = to_check

    @property
    def get_sheet_name(self):
        return self.sheet_name


class ExcelParser:
    @staticmethod
    def get_sheet(sheet_name: str) -> pd.DataFrame:
        if not SETTINGS.vocabulary_path_valid:
            raise VocabularyFileNotFoundError(SETTINGS.path)
        file = pd.ExcelFile(SETTINGS.path)
        sheets = file.sheet_names
        if sheet_name not in sheets:
            raise SheetNotFoundError(sheet_name, SETTINGS.path)
        return file.parse(sheet_name=sheet_name)


class StaticSettings:
    available_statuses = ["NEW", "NORMAL", "NEEDS_REVISION", "DELAYED"]


class SheetToSchemeCompatibilityChecker:
    def __init__(self, sheet: pd.DataFrame, scheme: SheetScheme):
        self.sheet = np.array(sheet)
        self.scheme = scheme

        self.columns_range = range(0, self.sheet.shape[0])

    def check_compatibility(self) -> None:
        self.check_indexes()
        self.check_status_column()

    def check_indexes(self) -> None:
        translation_index, status_index = self.scheme.translation, self.scheme.status
        self.check_indexes_in_range(translation_index, status_index)

        for i in self.scheme.to_check:
            spelling_index, info_index = i.get("spelling", -1), i.get("info", -1)
            self.check_indexes_in_range(spelling_index, info_index)

    def check_status_column(self) -> None:
        status_index = self.scheme.status
        column = self.sheet[:, status_index]
        for num, content in enumerate(column):
            self.process_status(content, num + 1)

    def process_status(self, status_string: str, line_index: int) -> None:
        data_package = (self.scheme.sheet_name, self.scheme.status, status_string, line_index)
        try:
            status_name, status_power = status_string.split("*")
        except ValueError:
            raise InvalidStatusError(*data_package)
        if status_name not in StaticSettings.available_statuses or (not (1 <= int(status_power) <= 50)):
            raise InvalidStatusError(*data_package)

    def check_indexes_in_range(self, first_index: int, second_index: int) -> bool:
        if first_index not in self.columns_range or second_index not in self.columns_range:
            raise InvalidSchemeError(self.scheme.sheet_name)
        return True


class WordToCheck:

    def __init__(self, word: str, info: str = ""):
        self.word_variations = word.split("/")
        self.info_variations = info.split("/")
        """max_length = max(len(self.word_variations), len(self.info_variations))
        self.word_variations += [""] * (max_length - len(self.word_variations))
        self.info_variations += [""] * (max_length - len(self.info_variations))
        
        self.pairs = [(w, i) for w, i in zip(self.word_variations, self.info_variations)]"""
        l = len(self.word_variations) - len(self.info_variations)
        l = 0 if l < 0 else l
        self.info_variations += [""] * l
        self.pairs = {w: i for w, i in zip(self.word_variations, self.info_variations)}

    def check_answer(self, answer: str) -> tuple[bool, str, str]:
        info = self.pairs.get(answer, False)
        return (False, "", "") if info is False else (True, info, self.give_other_variations(answer))

    def give_other_variations(self, answer: str) -> str:
        s = f"Right, the word was: {answer}."
        if len(self.pairs) > 1:
            s += "Other variations you could have given: "
        for k, i in self.pairs.items():
            if k == answer:
                continue
            s += k + f"({i}), "
        return s.removesuffix(", ") + "."

    def return_as_options(self) -> str:
        s = ""
        for k, i in self.pairs.items():
            s += k + f"({i})/"
        return s.removesuffix("/")


class Choice:
    has_synonyms_message = "This word can be translated in {} different ways. You must provide all of them. \n" \
                            "(The order in which you give answer does not matter.)"
    synonyms_left_message = "You still have to provide {} possible translations."

    def __init__(self, translation: str, words_string: str, instructions: str, additional_info_string: str):
        self._translation = translation
        self._word = word
        self._instructions = instructions
        self._info = info

    @property
    def translation(self) -> str:
        return self._translation

    @property
    def word(self) -> str:
        return self._word

    @property
    def instructions(self) -> str:
        return self._instructions

    @property
    def info(self) -> str:
        return self._info


class RowToCheck:
    def __init__(self, content: np.ndarray, scheme: SheetScheme) -> None:
        self.content = content
        self.scheme = scheme

        self.row = {
            "translation": self.content[self.scheme.translation],
            "status": self.content[self.scheme.status],
            "to_check": [],
        }

        for i in self.scheme.to_check:
            self.row["to_check"].append(WordToCheck(
                self.content[self.scheme.translation],
                content[i.get("spelling", 0)],
                i.get("comment", ""),
                content[i.get("info", 0)]
            ))

    @property
    def translation(self) -> str:
        return self.row.get("translation")

    @property
    def status(self) -> str:
        return self.row.get("status")

    @property
    def to_check(self) -> list[WordToCheck]:
        return self.row.get("to_check")

    @property
    def content_row(self) -> dict[str, Union[str, list[WordToCheck]]]:
        return self.row


class WordsGetter:

    # possible statuses of words. User can specify words with which status he wants to learn
    targets = {
        "all": lambda x: True,
        "NEEDS_REVISION": lambda x: x == "NEEDS_REVISION",
        "NEW": lambda x: x == "NEW",
        "NORMAL": lambda x: x == "NORMAL"
    }

    def __init__(
            self,
            sheet: pd.DataFrame,
            scheme: SheetScheme,
            words_range: range,
            target: str = "all",
            with_shuffle: bool = True
    ) -> None:
        self.sheet: np.ndarray = np.array(sheet, dtype=str)
        self.scheme: SheetScheme = scheme
        self.words_range: slice = slice(words_range.start, words_range.stop)
        self.target_checker: Callable = self.targets.get(target, lambda x: True)
        self.with_shuffle: bool = with_shuffle

        self.target = target

    def get_words(self) -> dict[int, RowToCheck]:
        """Filters words: leaves only those with the right status and in right range."""
        a = {}
        c = s if (s := self.words_range.start) else 0
        for num, val in enumerate(self.sheet[self.words_range]):
            if self.target_checker(val[self.scheme.status].split("*")[0]):
                a[num + c] = RowToCheck(val, self.scheme)
        a = list(a.items())
        if self.with_shuffle:
            shuffle(a)
        if not a:
            raise NoWordsMatchingSettings(self.target, self.words_range.start, self.words_range.stop)
        return dict(a)


class Dictation:
    def __init__(self, words_to_check: dict[int, RowToCheck]) -> None:
        self.words_to_check = words_to_check
        self._dictation_running = False

        self.revision_required = set()
        self.completed_successfully = set()

        self.live_queue = deque(words_to_check.items())

        self.words_generator: Generator

        self._current_row: RowToCheck
        self._current_word: WordToCheck

    def run(self):
        self._dictation_running = True
        self.update_words_generator()

    def get_word(self) -> Union[tuple[str, WordToCheck], bool]:
        try:
            return self.get_word_data()
        except StopIteration:
            any_words_left = self.update_words_generator()
            if not any_words_left:
                return False
            return self.get_word_data()

    def get_word_data(self) -> tuple[str, WordToCheck]:
        r = self.words_generator.__next__()
        return self._current_row[1].translation, r

    def update_words_generator(self) -> bool:
        if self.live_queue:
            current_row: [int, RowToCheck] = self.live_queue.popleft()
            self.words_generator = self.give_row_item(*current_row)
            return True
        return False

    def give_row_item(self, row_index: int, row: RowToCheck) -> Generator:
        self._current_row = [row_index, row]
        for i in row.to_check:
            self._current_word = i
            yield i

    def stop(self):
        """Here we should call a function to update word statuses"""
        ...

    def show_answer(self) -> WordToCheck:
        """Here we should return the answer and information about it, put the presently
        questioned word in the end of the queue and add it to self.revision_required"""
        self.live_queue.append(self._current_row)
        self.revision_required.add(self._current_row[0])
        cur_word = self._current_word
        self.update_words_generator()
        return cur_word

    def check_answer(self, answer: str) -> Union[WordToCheck, bool]:
        is_right = self._current_word.word.strip().rstrip() == answer.strip().rstrip()
        if not is_right:
            return False
        return self.count_as_right()

    def count_as_right(self) -> WordToCheck:
        """Here we add the word to self.completed_successfully"""
        self.completed_successfully.add(self._current_row[0])
        return self._current_word

    @property
    def is_running(self) -> bool:
        return self._dictation_running


SETTINGS = Settings()
