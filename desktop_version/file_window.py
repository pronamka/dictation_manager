import os
import _thread

import flet as ft

from user_settings import SETTINGS


class PathToVocabularyControls(ft.Column):
    vocabulary_key = "PATH_TO_VOCABULARY"
    class_key = "PathToVocabularyControls"
    no_path_set_message = "no-path-set"
    invalid_path_message = "invalid-path"
    invalid_file_extension_message = "invalid-extension"
    path_to_vocabulary_message = "current-path"

    vocabulary_file_input_label = "vocabulary-file-input-label"
    set_path_label = "set-path-label"

    def __init__(self, width: int):
        SETTINGS.translate_widget(self.__class__)

        self.path_to_vocabulary = SETTINGS.get(self.vocabulary_key)
        self.is_path_correct = self.check_path_to_vocabulary(self.path_to_vocabulary)

        self.path_to_vocabulary_label = ft.Text(
            value=self.path_to_vocabulary_message.format(self.path_to_vocabulary),
            size=16,
        )

        self.vocabulary_file_input = ft.TextField(label=self.vocabulary_file_input_label)
        self.set_path_button = ft.ElevatedButton(self.set_path_label, on_click=self.set_path_to_vocabulary,
                                                 width=width // 2)

        self.incorrect_vocabulary_path = ft.Text(color="red")
        if not self.is_path_correct:
            self.incorrect_vocabulary_path.value = self.no_path_set_message

        self.controls_list = [
            self.path_to_vocabulary_label,
            self.vocabulary_file_input,
            self.set_path_button,
            self.incorrect_vocabulary_path
        ]
        super().__init__(self.controls_list,
                         alignment=ft.MainAxisAlignment.CENTER,
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                         width=width
                         )

    def reload(self, external: bool = False):
        if external:
            self.visible = True
        self.path_to_vocabulary = SETTINGS.get(self.vocabulary_key)
        self.is_path_correct = self.check_path_to_vocabulary(self.path_to_vocabulary)
        self.path_to_vocabulary_label.value = self.path_to_vocabulary_message.format(self.path_to_vocabulary)
        self.vocabulary_file_input.value = ""
        self.incorrect_vocabulary_path.value = "" if self.is_path_correct else self.no_path_set_message
        self.update()

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

        self.update()

    @staticmethod
    def check_path_to_vocabulary(path: str) -> bool:
        if not os.path.exists(path) or path.rsplit(".", maxsplit=1)[-1] != "xlsx":
            return False
        return True

    @property
    def vocabulary_path_valid(self) -> bool:
        return self.check_path_to_vocabulary(self.path_to_vocabulary)


class AppLanguageControls(ft.Column):
    path_to_languages = "languages/"
    set_language_label = "set-language-label"
    restart_information = "restart-information"

    def __init__(self):
        SETTINGS.translate_widget(self.__class__)
        self.language_choice = ft.Dropdown(options=self.get_available_languages())
        self.language_choice.value = SETTINGS.app_language
        self.set_language = ft.ElevatedButton(self.set_language_label, on_click=self.apply_change)
        self.information_label = ft.Text(self.restart_information)
        self.controls_list = [
            self.language_choice,
            self.set_language,
            self.information_label
        ]
        super(AppLanguageControls, self).__init__(self.controls_list,
                                                  alignment=ft.MainAxisAlignment.CENTER,
                                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                  )

    def get_available_languages(self) -> list[ft.dropdown.Option]:
        return [ft.dropdown.Option(i.split(".")[0]) for i in os.listdir(self.path_to_languages)]

    def apply_change(self, e: ft.ControlEvent):
        new_language = self.language_choice.value
        SETTINGS.change_settings(SETTINGS.app_language_key, new_language)


class FileWindow(ft.Column):
    def __init__(self, width: int):
        self.path_controls = PathToVocabularyControls(width)
        self.language_controls = AppLanguageControls()
        self.controls_list = [
            self.path_controls,
            self.language_controls
        ]
        super().__init__(
            [ft.Column(self.controls_list, width=width // 2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=width)

    def reload(self, external: bool = False):
        self.path_controls.reload()
        self.visible = True
        self.update()
