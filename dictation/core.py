from abc import ABC, abstractmethod


class WordNotCompleted(Exception):
    ...


class SheetsSchemes:
    nouns = {"translation": 5,
             "to_check": [
                 {"comment_spelling": "Type singular noun with definite article",
                  "comment_pronunciation": "Pronounce singular noun without an article",
                  "spelling": 0,
                  "pronunciation": 1},

                 {"comment_spelling": "Type plural noun without an article",
                  "comment_pronunciation": "Pronounce plural noun without an article",
                  "spelling": 2,
                  "pronunciation": 3}
             ]}

    verbs = {"translation": 3,
             "to_check": [
                 {"comment_spelling": "Type the verb in the infinitive form",
                  "comment_pronunciation": "Pronounce the verb in the infinitive form",
                  "spelling": 0,
                  "pronunciation": 1}
             ]}

    irregular_verbs_present = {"translation": 10,
                               "to_check": [
                                   {"comment_spelling": "Type the verb in the infinitive form",
                                    "spelling": 0,
                                    "pronunciation": 1},
                                   {"comment_spelling": "Type the verb in the present 1st person singular form",
                                    "spelling": 2,
                                    "pronunciation": 3},
                                   {"comment_spelling": "Type the verb in the present 2nd person singular form",
                                    "spelling": 4,
                                    "pronunciation": 5},
                                   {"comment_spelling": "Type the verb in the present 3rd person singular form",
                                    "spelling": 6,
                                    "pronunciation": 7},
                                   {"comment_spelling": "Type the verb in the present 2nd person plural form",
                                    "spelling": 8,
                                    "pronunciation": 9},
                               ]}

    irregular_verbs_past = {"translation": 10,
                               "to_check": [
                                   {"comment_spelling": "Type the verb in the infinitive form",
                                    "spelling": 0,
                                    "pronunciation": 1},
                                   {"comment_spelling": "Type the verb in the past 1st/3rd person singular form",
                                    "spelling": 2,
                                    "pronunciation": 3},
                                   {"comment_spelling": "Type the verb in the past 2nd person singular form",
                                    "spelling": 4,
                                    "pronunciation": 5},
                                   {"comment_spelling": "Type the verb in the past 1st/3rd person plural form",
                                    "spelling": 6,
                                    "pronunciation": 7},
                                   {"comment_spelling": "Type the verb in the past 2nd person plural form",
                                    "spelling": 8,
                                    "pronunciation": 9},
                               ]}

    adjectives = {"translation": 3,
                  "to_check": [
                      {"comment_spelling": "Type the adjective: ",
                       "comment_pronunciation": "Pronounce the adjective: ",
                       "spelling": 0,
                       "pronunciation": 1}
                  ]}

    other = {"translation": 3,
             "to_check": [
                 {"comment_spelling": "Type the word(s): ",
                  "comment_pronunciation": "Pronounce the word(s): ",
                  "spelling": 0,
                  "pronunciation": 1}
             ]}

    pronouns = {"translation": 3,
                "to_check": [
                    {"comment_spelling": "Type the word: ",
                     "spelling": 0,
                     "pronunciation": 1}
                ]}


class BaseChecker(ABC):
    def __init__(self, comment: str, word: str):
        self.comment = comment
        self.original_word = word
        self.words = word.strip().lstrip().split("/")

    @abstractmethod
    def check(self):
        """Check"""


PATH_TO_VOCABULARY = "../vocabulary.xlsx"
