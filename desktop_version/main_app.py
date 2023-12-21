import os

from typing import Union, Callable
from enum import Enum
from copy import deepcopy

import flet as ft
import pandas as pd

from desktop_version.exceptions import SchemeExistsError, InvalidIndexesError
from desktop_version.core import SETTINGS
from desktop_version.dictation_window import DictationControls


def schemes_as_options():
    return [ft.dropdown.Option(i) for i in SETTINGS.schemes]


class AnswerCorrectness(Enum):
    CORRECT = 1
    INCORRECT = 2
    WITH_HINT = 3


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


class WordToCheckSchemeControls(ft.Column):
    def __init__(self):
        self.instructions_input = ft.TextField(label="instructions for the input")
        self.word_to_check_column_index_input = ft.Dropdown()
        self.special_information_column_index_input = ft.Dropdown()
        self.controls_list = [self.instructions_input, self.word_to_check_column_index_input,
                              self.special_information_column_index_input]
        super().__init__(self.controls_list)
        self.disabled = True

    def add_options(self, options: list[ft.dropdown.Option]):
        self.word_to_check_column_index_input.options = deepcopy(options)
        self.special_information_column_index_input.options = deepcopy(options)
        self.disabled = False

    def get_values(self) -> tuple[str, int, int]:
        return self.instructions_input.value, int(self.word_to_check_column_index_input.
                                                  value.split(" - ", maxsplit=1)[0]) - 1, \
               int(self.special_information_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1

    def clean(self):
        self.instructions_input.clean()
        self.word_to_check_column_index_input.clean()
        self.special_information_column_index_input.clean()


class SchemeDeletionControls(ft.Column):
    def __init__(self, reload_function: Callable, page: ft.Page):
        self._page = page

        self.schemes = ft.Dropdown()
        self.reload = reload_function
        self.delete_scheme_button = ft.ElevatedButton("Delete", on_click=self.delete_scheme)
        self.error_label = ft.Text(color="red")

        self._fill_dropdown()

        super().__init__([ft.Row([self.schemes, self.delete_scheme_button]), self.error_label])

    def _fill_dropdown(self):
        schemes = schemes_as_options()
        if SETTINGS.vocabulary_path_valid:
            self.schemes.options = schemes
        if not schemes:
            self.delete_scheme_button.disabled = True
            self.error_label.value = "You do not have any schemes configured. Please go to schemes " \
                                     "creation panel and create a scheme to proceed."
        self._page.update()

    def delete_scheme(self, e):
        self.error_label.value = ""
        schemes: dict = SETTINGS.get("schemes")
        scheme_name = self.schemes.value
        if not scheme_name or scheme_name is None:
            self.error_label.value = "Choose the scheme you want to delete."
        del schemes[scheme_name]
        SETTINGS.change_settings("schemes", schemes)
        return self.reload()


def event_with_page_update(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        res = func(args[0], args[1])
        args[0].page.update()
        return res

    return wrapper


class SchemeCreationControls(ft.Column):
    def __init__(self, reload_function: Callable, page: ft.Page, init_message: str):
        self.reload = reload_function

        self.title = ft.Text(value="Scheme Creation")

        self.sheet_choice = ft.Dropdown(on_change=self.fill_dropdowns)
        self.sheet_choice.disabled = True

        self.file, self.sheets = None, None

        self.scheme_name = ft.TextField(label="name of the scheme")

        self.translation_column_index_input = ft.Dropdown()
        self.word_status_column_index_input = ft.Dropdown()

        self.test_blocks = [WordToCheckSchemeControls()]
        self.test_blocks_column = ft.Column([i for i in self.test_blocks])

        self.errors_label = ft.Text(init_message, color="red")
        if init_message:
            self.errors_label.color = "green"

        self.add_test_block_button = ft.ElevatedButton("Add a test block", on_click=self.add_test_block)
        self.remove_test_block_button = ft.ElevatedButton("Remove the last test block", on_click=self.remove_test_block)

        self.create_scheme_button = ft.ElevatedButton("Create Scheme", on_click=self.create_scheme)

        controls = [self.title, self.sheet_choice, self.scheme_name,
                    self.translation_column_index_input, self.word_status_column_index_input,
                    self.test_blocks_column, self.errors_label,
                    self.add_test_block_button, self.remove_test_block_button, self.create_scheme_button]

        super().__init__(controls)

        if SETTINGS.vocabulary_path_valid:
            self.fill_sheet_choice_options()

    def create_scheme(self, e):
        try:
            scheme_name = self.scheme_name.value
            if not scheme_name:
                raise TypeError
            scheme = self.build_scheme()
            self.write_scheme(scheme_name, scheme)

            return self.reload(scheme_name)
        except (InvalidIndexesError, SchemeExistsError) as e:
            self.errors_label.value = e.message()
        except (TypeError, AttributeError) as e:
            self.errors_label.value = "Fill in all the fields."
        self.update()

    def build_scheme(self) -> tuple[str, int, int, list[dict[str, Union[str, int]]]]:
        sheet_name = self.sheet_choice.value
        if not sheet_name:
            raise TypeError
        translation_column_index = int(self.translation_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1
        word_status_column_index = int(self.word_status_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1

        test_blocks = []
        for i in self.test_blocks:
            label, word_index, info_index = i.get_values()
            if not label:
                raise TypeError
            indexes = [translation_column_index, word_status_column_index, word_index, info_index]
            if len(set(indexes)) != 4:
                raise InvalidIndexesError(indexes)
            block = {"comment": label, "spelling": word_index, "info": info_index}
            test_blocks.append(block)

        scheme = (sheet_name, translation_column_index, word_status_column_index, test_blocks)
        return scheme

    @staticmethod
    def write_scheme(name: str, scheme: tuple[str, int, int, list[dict[str, Union[str, int]]]]):
        schemes: dict = SETTINGS.get("schemes")
        if schemes.get(name, None):
            raise SchemeExistsError(name)
        schemes[name] = scheme
        SETTINGS.change_settings("schemes", schemes)

    @event_with_page_update
    def add_test_block(self, e: ft.ControlEvent):
        self.errors_label.value = ""
        block = WordToCheckSchemeControls()
        block.add_options(self.get_columns())
        self.test_blocks.append(block)
        self.change_test_block_column()

    @event_with_page_update
    def remove_test_block(self, e: ft.ControlEvent):
        if len(self.test_blocks) == 1:
            self.errors_label.value = "A scheme must have at least one test block."
            return
        self.test_blocks.pop()
        self.change_test_block_column()

    def fill_dropdowns(self, e) -> None:
        column = self.get_columns()
        self.translation_column_index_input.options = deepcopy(column)
        self.word_status_column_index_input.options = deepcopy(column)
        for i in self.test_blocks:
            i.add_options(column)
        self.update()

    def change_test_block_column(self):
        self.test_blocks_column.controls = [i for i in self.test_blocks]
        self.update()

    def get_columns(self) -> list[ft.dropdown.Option]:
        sheet_name = self.sheet_choice.value
        sheet: pd.DataFrame = self.file.parse(sheet_name)
        return [ft.dropdown.Option(f"{index} - {name}") for index, name in enumerate(sheet.columns, start=1)]

    def fill_sheet_choice_options(self):
        self.file, self.sheets = self.parse_excel(SETTINGS.path)
        self.sheet_choice.options = [ft.dropdown.Option(i) for i in self.sheets]
        self.sheet_choice.disabled = False

    @staticmethod
    def parse_excel(path: str) -> tuple[pd.ExcelFile, list]:
        file = pd.ExcelFile(path)
        sheets = file.sheet_names
        return file, sheets

    def vocabulary_path_set(self):
        self.fill_sheet_choice_options()
        self.update()


class SchemeManagingNavigationBar(ft.Column):
    def __init__(self, navigation_function: Callable):
        self.to_creation_button = ft.ElevatedButton("Scheme Creation",
                                                    on_click=lambda e: navigation_function("creation"))
        self.to_deletion_button = ft.ElevatedButton("Scheme Deletion",
                                                    on_click=lambda e: navigation_function("deletion"))

        super().__init__([self.to_creation_button, self.to_deletion_button])


class SchemeManagingControls(ft.Row):
    def __init__(self, reload: Callable, page: ft.Page):
        self.page = page
        self.reload = reload

        self.no_vocabulary_file_label = ft.Text(color="red")

        self.scheme_creation = SchemeCreationControls(self.scheme_created_reload, self.page, "")

        self.scheme_deletion = SchemeDeletionControls(self.scheme_deleted_reload, self.page)
        self.scheme_deletion.visible = False

        self.navigation_routes = {
            "creation": self.scheme_creation,
            "alteration": ft.Row(),
            "deletion": self.scheme_deletion,
        }
        if not SETTINGS.vocabulary_path_valid:
            self.no_vocabulary_file_label.value = "You have no vocabulary file configured. \n" \
                                                  "Please go to `File`."
        self.controls_list = [self.no_vocabulary_file_label, self.scheme_creation, self.scheme_deletion]
        super().__init__(self.controls_list)

    def go_to(self, destination: str):
        destination = destination.rsplit("_")[-1]
        self.visible = True
        for i in self.navigation_routes.values():
            i.visible = False
        destination_object = self.navigation_routes.get(destination)
        destination_object.reload()
        destination_object.visible = True
        self.page.update()

    def scheme_deleted_reload(self):
        self.scheme_deletion.controls = SchemeDeletionControls(self.scheme_deleted_reload, self.page).controls
        self.update()

    def scheme_created_reload(self, scheme_name: str = ""):
        self.scheme_creation.controls = SchemeCreationControls(self.scheme_deleted_reload,
                                                               self.page, scheme_name).controls
        self.page.update()


class MenuBar(ft.Row):
    def __init__(self, navigation_function: Callable):
        self.dictation_window_button = ft.Text(
            disabled=False,
            spans=[
                ft.TextSpan(
                    "D",
                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    on_click=lambda x: navigation_function("dictation")
                ),
                ft.TextSpan(
                    "ictation",
                    on_click=lambda x: navigation_function("dictation")
                ),
            ],
            size=18,
            data="dictation"
        )

        self.scheme_managing_popup = ft.PopupMenuButton(
            content=ft.Text(
                disabled=False,
                spans=[
                    ft.TextSpan(
                        "S",
                        ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    ),
                    ft.TextSpan(
                        "cheme Managing"
                    )
                ],
                size=18),
            items=[
                ft.PopupMenuItem(
                    text="Scheme Creation",
                    on_click=lambda x: navigation_function("scheme_creation")
                ),
                ft.PopupMenuItem(
                    text="Scheme Alteration",
                    on_click=lambda x: navigation_function("scheme_alteration")
                ),
                ft.PopupMenuItem(
                    text="Scheme Deletion",
                    on_click=lambda x: navigation_function("scheme_deletion")
                ),
            ],
        )
        self.vocabulary_path_window_button = ft.Text(
            disabled=False,
            spans=[
                ft.TextSpan(
                    "F",
                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    on_click=lambda x: navigation_function("file")
                ),
                ft.TextSpan(
                    "ile",
                    on_click=lambda x: navigation_function("file")
                ),
            ],
            size=18,
        )

        self.controls_list = [self.vocabulary_path_window_button, self.dictation_window_button,
                              self.scheme_managing_popup]

        super().__init__(self.controls_list)
        self.alignment = ft.alignment.center_left


class MainPage:
    def process_window_event(self, e: ft.ControlEvent):
        if e.data == "enterFullScreen" or e.data == "leaveFullScreen" \
                or e.data == "resize" or e.data == "resized" \
                or e.data == "maximize" or e.data == "unmaximize":
            self.page.window_center()

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.scroll = "always"
        self.page.window_resizable = False
        self.page.window_max_width = self.page.width
        self.page.window_max_height = self.page.height
        self.page.window_center()
        self.page.on_window_event = self.process_window_event

        self.page_menu = MenuBar(self.window_changed)

        self.dictation_controls = DictationControls(self.dictation_reload, self.page)
        self.schemes = SchemeManagingControls(self.scheme_managing_reload, self.page)
        self.vocabulary_path_controls = PathToVocabularyControls(self.vocabulary_path_reload)
        self.dictation_controls.visible = True
        self.schemes.visible = False
        self.vocabulary_path_controls.visible = False

        self.navigation_routes = {
            "file": (self.vocabulary_path_controls, lambda x: (self.vocabulary_path_controls.__setattr__("visible", True))),
            "dictation": (self.dictation_controls, lambda x: (self.dictation_controls.__setattr__("visible", True))),
            "scheme": (self.schemes, lambda x: (self.schemes.go_to(x))),
        }

        self.current_page_name = ft.Text("Dictation", size=30)
        self.bar = ft.Container(
            ft.Row(
                controls=[ft.Icon(ft.icons.WORK), self.page_menu],
                spacing=20
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=10,
        )

        self.controls_list = ft.Column([
            self.bar,
            self.dictation_controls,
            self.schemes,
            self.vocabulary_path_controls
        ])

        page.add(self.controls_list)
        self.page.update()

    def vocabulary_path_reload(self):
        self.vocabulary_path_controls.controls = PathToVocabularyControls(self.vocabulary_path_reload).controls
        self.page.update()

    def scheme_managing_reload(self):
        self.schemes.controls = SchemeManagingControls(self.scheme_managing_reload, self.page).controls
        self.page.update()

    def dictation_reload(self):
        self.dictation_controls.controls = DictationControls(self.dictation_reload, self.page).controls
        self.page.update()

    def window_changed(self, destination: str):
        general_destination = destination.split("_")[0]
        for i in self.navigation_routes.values():
            i[0].visible = False
        destination_object = self.navigation_routes.get(general_destination)
        destination_object[1](destination)
        self.page.update()


def main(page: ft.Page):
    MainPage(page)


if __name__ == "__main__":
    ft.app(target=main)
