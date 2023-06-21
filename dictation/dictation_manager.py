from random import shuffle

import pandas
import numpy

from core import SheetsSchemes, WordNotCompleted, PATH_TO_VOCABULARY
from spelling_checker import SpellChecker
# from pronunciation_checker import PronunciationChecker


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
    corresponding_schemes = {"nouns": SheetsSchemes.nouns,
                             "verbs": SheetsSchemes.verbs,
                             "adjectives": SheetsSchemes.adjectives,
                             "other": SheetsSchemes.other,
                             "IrregularVerbsPresent": SheetsSchemes.irregular_verbs_present,
                             "pronouns": SheetsSchemes.pronouns}

    def __init__(self, words_row: list, word_type: str) -> None:
        self.current_scheme = self.corresponding_schemes.get(word_type, SheetsSchemes.other)
        self.word_translation = words_row[self.current_scheme.get("translation")]
        self.word_row = words_row

    def check(self) -> None:
        print(f"Russian: {self.word_translation}")
        for row in self.current_scheme.get("to_check"):
            CheckerManager(self.word_row, row).check()


class Dictation:
    def __init__(self) -> None:
        self.word_type = input("What words do you want to learn?"
                               "(nouns/verbs/adjectives/other/IrregularVerbsPresent/numerals/pronouns)\n")
        self.get_all = True if input("Get all words?(y/n)") == "y" else False
        self.with_audio = True if input("Check pronunciation?(y/n)") == "y" else False
        self.words = self.prepare_words(self.word_type)

    def prepare_words(self, word_type: str) -> numpy.array:
        # words = pandas.read_excel(f"../germany/{word_type}.xlsx")
        words = pandas.read_excel(PATH_TO_VOCABULARY, sheet_name=word_type)
        words = numpy.array(words)
        if not self.get_all:
            words = words[int(input("Range of words starts at: "))-2:int(input("Range of words ends at: "))-2]
        numpy.random.shuffle(words)
        return words.tolist()

    def start_dictation(self) -> None:
        words = self.words
        while words:
            words = []
            for i in self.words:
                try:
                    MainChecker(list(i), self.word_type).check()
                except WordNotCompleted:
                    words.append(i)
            if words:
                print("Now let's fix the mistakes.")
                shuffle(words)
            self.words = words
        print("Congratulations! You've done it!")


Dictation().start_dictation()
