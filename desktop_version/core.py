import os
import sys

from io import BytesIO
from typing import Union, Callable, Generator
from collections import deque
from ast import literal_eval
from random import shuffle
import pywintypes

import numpy as np
import pandas as pd
from gtts import gTTS
from gtts.tts import gTTSError
import pygame

from desktop_version.exceptions import VocabularyFileNotFoundError, SheetNotFoundError, InvalidStatusError, \
    InvalidSchemeError, NoWordsMatchingSettings, ExcelAppOpenedError
from desktop_version.excel_modifier import ExcelModifier


class CellFillers:
    empty_cell = "nan"
    skip_cell = "n-"

    @classmethod
    def __contains__(cls, item: str) -> bool:
        return item == cls.empty_cell or item == cls.skip_cell


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
            status_power = int(status_power)
            if not status_name:
                raise InvalidStatusError(*data_package)
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
            c = "" if i in CellFillers() else f"({i})"
            s += k + c + f", "
        return s.removesuffix(", ")

    def return_as_options(self) -> str:
        s = ""
        for k, i in self.pairs.items():
            c = "" if i in CellFillers() else f"({i})"
            s += k + c + "/"

        return s.removesuffix("/")


class Choice:
    has_synonyms_message = "This word can be translated in {} different ways. You must provide all of them. \n" \
                            "(The order in which you give answers does not matter)"
    synonyms_left_message = "You still have to provide {} possible translation(s)."

    def __init__(self, translation: str, words_string: str, instructions: str, additional_info_string: str):
        self.is_empty = words_string in CellFillers()
        if self.is_empty:
            return

        self._translation = translation
        self._instructions = instructions

        self.synonyms = words_string.strip().rstrip().split("|")
        self.amount_of_synonyms = len(self.synonyms)

        self.has_synonyms = True if self.amount_of_synonyms > 1 else False

        self.additional_info = additional_info_string.strip().rstrip().split("|")
        l = len(self.synonyms) - len(self.additional_info)
        l = 0 if l < 0 else l
        self.additional_info += [""] * l

        self.with_synonyms = ""
        if self.amount_of_synonyms > 1:
            self.with_synonyms = self.has_synonyms_message.format(self.amount_of_synonyms)

        self.words = [WordToCheck(w, i) for w, i in zip(self.synonyms, self.additional_info)]

    def check_answer(self, answer: str, affect_words: bool = True) -> tuple[bool, str, str]:
        for index, word in enumerate(self.words):
            result = word.check_answer(answer)
            if result[0] and affect_words:
                self.words.pop(index)
            if result[0]:
                return result
        else:
            return False, "", ""

    def show_all_translation(self) -> str:
        translations = ""
        for i in self.words:
            translations += i.return_as_options() + ";"
        return translations

    @property
    def translation(self) -> str:
        return self._translation

    @property
    def instructions(self) -> str:
        return self._instructions

    @property
    def all_words_checked(self) -> bool:
        return True if len(self.words) <= 0 else False

    @property
    def amount_of_words_left(self) -> str:
        l = len(self.words)
        if l:
            return self.synonyms_left_message.format(len(self.words))
        return "You have given all the translations for the previous word."


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
            choice = Choice(
                self.content[self.scheme.translation],
                content[i.get("spelling", 0)],
                i.get("comment", ""),
                content[i.get("info", 0)]
            )
            if not choice.is_empty:
                self.row["to_check"].append(choice)

    @property
    def translation(self) -> str:
        return self.row.get("translation")

    @property
    def status(self) -> str:
        return self.row.get("status")

    @property
    def to_check(self) -> list[Choice]:
        return self.row.get("to_check")

    @property
    def content_row(self) -> dict[str, Union[str, list[Choice]]]:
        return self.row


class DictationContent:
    def __init__(self, words: dict[int, RowToCheck], scheme: SheetScheme):
        self.words = words
        self.scheme = scheme


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
        self.words_range: slice = slice(words_range.start-2, words_range.stop-1)
        self.target_checker: Callable = self.targets.get(target, lambda x: True)
        self.with_shuffle: bool = with_shuffle

        self.target = target

    def get_words(self) -> DictationContent:
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
            raise NoWordsMatchingSettings(self.target, self.words_range.start+2, self.words_range.stop+1)
        return DictationContent(dict(a), self.scheme)


class AnswerCheckedResponse:
    def __init__(
            self,
            is_right: bool,
            with_synonyms: str,
            synonyms_left: str,
            info_to_given_word: str,
            other_variations: str
    ):
        self.is_right: bool = is_right
        self.with_synonyms: str = with_synonyms
        self.synonyms_left: str = synonyms_left
        self.info_to_given_word: str = info_to_given_word
        self.other_variations: str = other_variations


class Dictation:
    def __init__(
            self,
            dictation_content: DictationContent,
            path_to_vocabulary: str,
    ) -> None:
        self.path_to_vocabulary = path_to_vocabulary
        self.scheme = dictation_content.scheme
        self.words_to_check = dictation_content.words
        self._dictation_running = False

        self.revision_required = set()
        self.completed_successfully = set()

        self.live_queue = deque(self.words_to_check.items())
        self.revision_queue = []

        self.words_generator: Generator

        self._current_row: RowToCheck
        self._current_word: WordToCheck

    def run(self):
        self._dictation_running = True
        self.update_words_generator()

    def get_word(self) -> Union[bool, Choice]:
        try:
            return self.get_word_data()
        except StopIteration:
            any_words_left = self.update_words_generator()
            if not any_words_left:
                self.stop()
                return False
            return self.get_word_data()

    def get_word_data(self) -> Choice:
        return self.words_generator.__next__()

    def update_words_generator(self) -> bool:
        if self.revision_queue and not self.live_queue:
            shuffle(self.revision_queue)
            self.live_queue.extend(self.revision_queue)
            self.revision_queue.clear()
        if self.live_queue:
            current_row: [int, RowToCheck] = self.live_queue.popleft()
            self.words_generator = self.give_row_item(*current_row)
            return True
        return False

    def give_row_item(self, row_index: int, row: RowToCheck) -> Generator:
        self._current_row = [row_index, row]
        for i in row.to_check:
            self._current_word: Choice = i
            while not self._current_word.all_words_checked:
                yield self._current_word

    def update_statuses(self):
        self.completed_successfully = self.completed_successfully.difference(self.revision_required)
        to_update = {"NEEDS_REVISION": self.revision_required, "NORMAL": self.completed_successfully}

        excel = ExcelModifier(self.scheme.sheet_name, self.scheme.status, self.path_to_vocabulary)
        for new_status, row_indexes in to_update.items():
            excel.modify(new_status, row_indexes)
        excel.commit()

    def stop(self):
        """Here we should call a function to update word statuses"""
        if not self._dictation_running:
            return
        try:
            self.update_statuses()
        except pywintypes.com_error:
            raise ExcelAppOpenedError()
        self._dictation_running = False

    def show_answer(self) -> Choice:
        """Here we should return the answer and information about it, put the presently
        questioned word in the end of the queue and add it to self.revision_required"""
        self.revision_queue.append(self._current_row)
        self.revision_required.add(self._current_row[0])
        cur_word = self._current_word
        self.update_words_generator()
        return cur_word

    def check_answer(self, answer: str, affect_choice: bool = True) -> AnswerCheckedResponse:
        is_right = self._current_word.check_answer(answer, affect_choice)
        response_data = AnswerCheckedResponse(is_right[0], self._current_word.with_synonyms,
                                              self._current_word.amount_of_words_left,
                                              is_right[1], is_right[2])
        if is_right[0] and self._current_word.all_words_checked:
            self.count_as_right()
        return response_data

    def count_as_right(self) -> None:
        """Here we add the word to self.completed_successfully."""
        self.completed_successfully.add(self._current_row[0])

    @property
    def is_running(self) -> bool:
        return self._dictation_running


class Narrator:
    sound_narrator = pygame
    sound_narrator.init()
    sound_narrator.mixer.init()
    language = "de"
    connection_error = False

    @classmethod
    def narrate(cls, text_to_narrate: str) -> None:
        try:
            if cls.connection_error:
                return
            else:
                cls.create_sound(text_to_narrate)
        except gTTSError:
            cls.connection_error = True
            print("Couldn't narrate. Narrating turned off. \n"
                  "Establish Internet connection and relaunch the dictation to turn on it back on.",
                  file=sys.stderr)

    @classmethod
    def create_sound(cls, text_to_narrate: str) -> None:
        text_to_speech = gTTS(text_to_narrate, lang=cls.language)
        sound = BytesIO()
        text_to_speech.write_to_fp(sound)
        sound.seek(0)
        cls._play_sound(sound)

    @classmethod
    def _play_sound(cls, audio: BytesIO):
        cls.sound_narrator.mixer.music.load(audio)
        cls.sound_narrator.mixer.music.play()

SETTINGS = Settings()
