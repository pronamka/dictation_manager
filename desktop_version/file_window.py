import os

from typing import Callable

import flet as ft

from desktop_version.core import SETTINGS


class PathToVocabularyControls(ft.Column):
    vocabulary_key = "PATH_TO_VOCABULARY"
    no_path_set_message = "You have no vocabulary file chosen. " \
                          "Please specify path to your vocabulary xlsx file."
    invalid_path_message = "Path `{}` does not exist."
    invalid_file_extension_message = "File with vocabulary must have `.xlsx` extension."

    path_to_vocabulary_message = "Path to the file with vocabulary: {}"

    def __init__(self, reload: Callable):
        self.path_to_vocabulary = SETTINGS.get(self.vocabulary_key)
        self.is_path_correct = self.check_path_to_vocabulary(self.path_to_vocabulary)

        self.reload = reload

        self.path_to_vocabulary_label = ft.Text(value=self.path_to_vocabulary.format(self.path_to_vocabulary))

        self.vocabulary_file_input = ft.TextField(label="path to vocabulary")
        self.set_path_button = ft.ElevatedButton("Set path", on_click=self.set_path_to_vocabulary)

        self.incorrect_vocabulary_path = ft.Text(color="red")
        if not self.is_path_correct:
            self.incorrect_vocabulary_path.value = self.no_path_set_message

        self.controls_list = [
            self.path_to_vocabulary_label,
            ft.Row([self.vocabulary_file_input, self.set_path_button]),
            self.incorrect_vocabulary_path
        ]
        super().__init__(self.controls_list)

    def set_path_to_vocabulary(self, e) -> None:
        new_path = self.vocabulary_file_input.value
        if not os.path.exists(new_path):
            self.incorrect_vocabulary_path.value = self.invalid_path_message.format(new_path)
            self.incorrect_vocabulary_path.disabled = False
        elif new_path.rsplit(".", maxsplit=1)[-1] != "xlsx":
            self.incorrect_vocabulary_path.value = self.invalid_file_extension_message
            self.incorrect_vocabulary_path.disabled = False
        else:
            self.path_to_vocabulary_label.value = self.path_to_vocabulary_message.format(new_path)
            SETTINGS.change_settings(self.vocabulary_key, new_path)
            self.incorrect_vocabulary_path.value = ""
            self.incorrect_vocabulary_path.disabled = True
        self.vocabulary_file_input.value = ""

        self.reload()

    @staticmethod
    def check_path_to_vocabulary(path: str) -> bool:
        if not os.path.exists(path) or path.rsplit(".", maxsplit=1)[-1] != "xlsx":
            return False
        return True

    @property
    def vocabulary_path_valid(self) -> bool:
        return self.check_path_to_vocabulary(self.path_to_vocabulary)