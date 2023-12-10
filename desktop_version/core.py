import os

from typing import Union, Callable
from ast import literal_eval
from random import shuffle

import numpy as np
import pandas as pd

from desktop_version.exceptions import VocabularyFileNotFoundError, SheetNotFoundError, InvalidStatusError, \
    InvalidSchemeError


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

        self.columns_range = range(1, self.sheet.shape[0])

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
        column = self.sheet[:, status_index-1]
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

    def get_words(self) -> dict[int, np.ndarray]:
        """Filters words: leaves only those with the right status and in right range."""
        a = {}
        c = s if (s := self.words_range.start) else 0
        for num, val in enumerate(self.sheet[self.words_range]):
            if self.target_checker(val[self.scheme.status].split("*")[0]):
                a[num + c] = val
        a = list(a.items())
        if self.with_shuffle:
            shuffle(a)
        return dict(a)


SETTINGS = Settings()
