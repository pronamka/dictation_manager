import os

from typing import Any, Iterable, Mapping, Union
from abc import ABC, abstractmethod

from ast import literal_eval


def process_range(rng: str) -> list[int, int]:
    r = list(map(int, rng.split(" ")))
    r[0] -= 1
    return r


class WordNotCompleted(Exception):
    ...


class DictWithDefaultReturn(dict):
    """Acts entirely like a `dict`, only always returns a
    default object(preassigned when initializing) when `get` method is called but
    the specified key is missing."""

    def __init__(self, data: Union[None, Iterable, Mapping], default_return: Any) -> None:
        """
        :param data: any data that `dict` can be initialized with
        :param default_return: any object to be returned when specified key
            was not found during the use of `get` method
        """
        super(DictWithDefaultReturn, self).__init__(data)
        self.default_return = default_return

    def __missing__(self, key: Any) -> Any:
        return self.default_return


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


class SheetsSchemes:
    """Class to get specified schemes of Excel sheets."""

    path_to_schemes = "sheets_schemes.txt"

    def __init__(self):
        self.all_schemes = {key: SheetScheme(*val) for key, val in self._read_schemes().items()}
        self.available_sheets = list(self.all_schemes.keys())

    def _read_schemes(self) -> dict:
        with open(self.path_to_schemes, mode="r") as file:
            return literal_eval(file.read())

    def get(self, key: str) -> SheetScheme:
        return self.all_schemes.get(key, self.all_schemes.get("other"))


class BaseChecker(ABC):
    """Abstract class used to set a universal word processing rule."""
    def __init__(self, comment: str, word: str):
        self.comment = comment
        self.original_word = word
        self.diff_words = word.strip().lstrip().split("|")
        self.words_variations = [i.split("/") for i in self.diff_words]

    @abstractmethod
    def check(self):
        """Check"""


USERNAME = os.getcwd().split("\\")[2]
VOCABULARY_RELATIVE_LOCATION = "../vocabulary.xlsx"
PATH_TO_VOCABULARY = os.path.abspath(VOCABULARY_RELATIVE_LOCATION)
