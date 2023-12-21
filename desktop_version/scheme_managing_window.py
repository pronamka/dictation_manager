from typing import Union, Callable
from copy import deepcopy

import pandas as pd
import flet as ft

from desktop_version.exceptions import SchemeExistsError, InvalidIndexesError
from desktop_version.core import SETTINGS


def event_with_page_update(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        res = func(args[0], args[1])
        args[0].update()
        return res

    return wrapper


def schemes_as_options():
    return [ft.dropdown.Option(i) for i in SETTINGS.schemes]


class WordToCheckSchemeControls(ft.Column):
    def __init__(self):
        self._instructions_input = ft.TextField(label="instructions for the input")
        self._word_to_check_column_index_input = ft.Dropdown()
        self._special_information_column_index_input = ft.Dropdown()
        self._controls_list = [self._instructions_input, self._word_to_check_column_index_input,
                               self._special_information_column_index_input]
        super().__init__(self._controls_list)
        self.disabled = True

    def add_options(self, options: list[ft.dropdown.Option]):
        self._word_to_check_column_index_input.options = deepcopy(options)
        self._special_information_column_index_input.options = deepcopy(options)
        self.disabled = False

    def get_values(self) -> tuple[str, int, int]:
        return self._instructions_input.value, int(self._word_to_check_column_index_input.
                                                   value.split(" - ", maxsplit=1)[0]) - 1, \
               int(self._special_information_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1

    def clean(self):
        self._instructions_input.clean()
        self._word_to_check_column_index_input.clean()
        self._special_information_column_index_input.clean()


class SchemeDeletionControls(ft.Column):
    _scheme_deleted_message_template = "Scheme `{}` was successfully deleted."

    def __init__(self):

        self._schemes = ft.Dropdown()
        self._delete_scheme_button = ft.ElevatedButton("Delete", on_click=self.delete_scheme)
        self._error_label = ft.Text(color="red")
        self._error_label.visible = False
        self._scheme_deleted_label = ft.Text(color="green")

        super().__init__([
            ft.Row([self._schemes, self._delete_scheme_button]),
            self._error_label,
            self._scheme_deleted_label
        ])

        self._fill_dropdown()

    def _fill_dropdown(self):
        schemes = schemes_as_options()
        if SETTINGS.vocabulary_path_valid:
            self._schemes.options = schemes
        if not schemes:
            self._delete_scheme_button.disabled = True
            self._error_label.visible = True
            self._error_label.value = "You do not have any schemes configured. Please go to schemes " \
                                      "creation panel and create a scheme to proceed."

    def reload(self):
        self._error_label.value = ""
        self._error_label.visible = False
        self._scheme_deleted_label.value = ""
        self._fill_dropdown()

    @event_with_page_update
    def delete_scheme(self, e: ft.ControlEvent):
        scheme_name = self._schemes.value
        scheme = SETTINGS.schemes.get(scheme_name, False)
        if not scheme:
            self._error_label.value = "Choose the scheme to delete."
            return

        SETTINGS.schemes.pop(scheme_name)
        SETTINGS.change_settings("schemes", SETTINGS.schemes)

        self._scheme_deleted(scheme_name)

    def _scheme_deleted(self, scheme_name: str):
        self.reload()
        self._scheme_deleted_label.value = self._scheme_deleted_message_template.format(scheme_name)


class SchemeCreationControls(ft.Column):
    _scheme_created_message_template = "Scheme `{}` was successfully created."

    def __init__(self):
        self._title = ft.Text(value="Scheme Creation", style=ft.TextThemeStyle.TITLE_LARGE)

        self._sheet_choice = ft.Dropdown(
            on_change=self._fill_dropdowns,

        )
        self._sheet_choice.disabled = True

        self._file, self._sheets = None, None

        self._scheme_name = ft.TextField(label="name of the scheme")

        self._translation_column_index_input = ft.Dropdown()
        self._word_status_column_index_input = ft.Dropdown()

        self._test_blocks = [WordToCheckSchemeControls()]
        self._test_blocks_column = ft.Column([i for i in self._test_blocks])

        self._errors_label = ft.Text(color="red")
        self._scheme_created_label = ft.Text(color="green")

        self._add_test_block_button = ft.ElevatedButton("Add a test block", on_click=self._add_test_block)
        self._remove_test_block_button = ft.ElevatedButton("Remove the last test block",
                                                           on_click=self._remove_test_block)

        self._create_scheme_button = ft.ElevatedButton("Create Scheme", on_click=self._create_scheme)

        controls = [self._title, self._sheet_choice, self._scheme_name,
                    self._translation_column_index_input, self._word_status_column_index_input,
                    self._test_blocks_column, self._errors_label,
                    self._add_test_block_button, self._remove_test_block_button, self._create_scheme_button,
                    self._scheme_created_label]

        self._inputs = [self._sheet_choice, self._scheme_name,
                        self._translation_column_index_input, self._word_status_column_index_input]

        super().__init__(controls)

        if SETTINGS.vocabulary_path_valid:
            self._fill_sheet_choice_options()

    def reload(self):
        if SETTINGS.vocabulary_path_valid:
            self._fill_sheet_choice_options()

        for i in self._inputs:
            i.value = ""

        self._translation_column_index_input.options.clear()
        self._word_status_column_index_input.options.clear()

        self._test_blocks.clear()
        self._test_blocks.append(WordToCheckSchemeControls())
        self._update_test_block_column()

        self._errors_label.value = ""
        self._scheme_created_label = ""

    def _scheme_created(self, scheme_name: str) -> None:
        self.reload()
        self._scheme_created_label = self._scheme_created_message_template.format(scheme_name)

    def _create_scheme(self, e):
        try:
            scheme_name = self._scheme_name.value
            if not scheme_name:
                raise TypeError
            scheme = self._build_scheme()
            self._write_scheme(scheme_name, scheme)
            self._scheme_created(scheme_name)
        except (InvalidIndexesError, SchemeExistsError) as e:
            self._errors_label.value = e.message()
        except (TypeError, AttributeError) as e:
            self._errors_label.value = "Fill in all the fields."
        self.update()

    def _build_scheme(self) -> tuple[str, int, int, list[dict[str, Union[str, int]]]]:
        sheet_name = self._sheet_choice.value
        if not sheet_name:
            raise TypeError
        translation_column_index = int(self._translation_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1
        word_status_column_index = int(self._word_status_column_index_input.value.split(" - ", maxsplit=1)[0]) - 1

        test_blocks = []
        for i in self._test_blocks:
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
    def _write_scheme(name: str, scheme: tuple[str, int, int, list[dict[str, Union[str, int]]]]):
        schemes: dict = SETTINGS.get("schemes")
        if schemes.get(name, None):
            raise SchemeExistsError(name)
        schemes[name] = scheme
        SETTINGS.change_settings("schemes", schemes)

    @event_with_page_update
    def _add_test_block(self, e: ft.ControlEvent):
        self._errors_label.value = ""
        block = WordToCheckSchemeControls()
        block.add_options(self._get_columns())
        self._test_blocks.append(block)
        self._update_test_block_column()

    @event_with_page_update
    def _remove_test_block(self, e: ft.ControlEvent):
        if len(self._test_blocks) == 1:
            self._errors_label.value = "A scheme must have at least one test block."
            return
        self._test_blocks.pop()
        self._update_test_block_column()

    def _fill_dropdowns(self, e) -> None:
        column = self._get_columns()
        self._translation_column_index_input.options = deepcopy(column)
        self._word_status_column_index_input.options = deepcopy(column)
        for i in self._test_blocks:
            i.add_options(column)
        self.update()

    def _update_test_block_column(self):
        self._test_blocks_column.controls = self._test_blocks

    def _get_columns(self) -> list[ft.dropdown.Option]:
        sheet_name = self._sheet_choice.value
        sheet: pd.DataFrame = self._file.parse(sheet_name)
        return [ft.dropdown.Option(f"{index} - {name}") for index, name in enumerate(sheet.columns, start=1)]

    def _fill_sheet_choice_options(self):
        self._file, self._sheets = self._parse_excel(SETTINGS.path)
        self._sheet_choice.options = [ft.dropdown.Option(i) for i in self._sheets]
        self._sheet_choice.disabled = False

    @staticmethod
    def _parse_excel(path: str) -> tuple[pd.ExcelFile, list]:
        file = pd.ExcelFile(path)
        sheets = file.sheet_names
        return file, sheets


class SchemeManagingControls(ft.Row):
    def __init__(self, reload: Callable, page: ft.Page):
        self.page = page
        self.reload = reload

        self.no_vocabulary_file_label = ft.Text(color="red")

        self.scheme_creation = SchemeCreationControls()

        self.scheme_deletion = SchemeDeletionControls()
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
        self.update()
