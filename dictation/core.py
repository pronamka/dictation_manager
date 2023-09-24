from typing import Any, Iterable, Mapping, Union
from abc import ABC, abstractmethod

from ast import literal_eval


class WordNotCompleted(Exception):
    ...


class DictWithDefaultReturn(dict):
    def __init__(self, data: Union[None, Iterable, Mapping], default_return: Any) -> None:
        super(DictWithDefaultReturn, self).__init__(data)
        self.default_return = default_return

    def __missing__(self, key: Any) -> Any:
        return self.default_return


class SheetScheme:
    def __init__(self,
                 translation_index: int,
                 status_index: int,
                 to_check: list[dict[str, Union[str, int]]]
                 ) -> None:
        self.translation = translation_index
        self.status = status_index
        self.to_check = to_check


class SheetsSchemes:
    path_to_schemes = "sheets_schemes.txt"

    def __init__(self):
        self.all_schemes = {key: SheetScheme(*val) for key, val in self.read_schemes().items()}
        self.available_sheets = list(self.all_schemes.keys())

    def read_schemes(self) -> dict:
        with open(self.path_to_schemes, mode="r") as file:
            return literal_eval(file.read())

    def get(self, key: str) -> SheetScheme:
        return self.all_schemes.get(key, self.all_schemes.get("other"))


class BaseChecker(ABC):
    def __init__(self, comment: str, word: str):
        self.comment = comment
        self.original_word = word
        self.diff_words = word.strip().lstrip().split("|")
        self.words_variations = [i.split("/") for i in self.diff_words]

    @abstractmethod
    def check(self):
        """Check"""


PATH_TO_VOCABULARY = "C:/Users/Yuriy/Desktop/dictation_manager/vocabulary.xlsx"
