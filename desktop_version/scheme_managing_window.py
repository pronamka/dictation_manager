from typing import Union, Callable
from copy import deepcopy

import pandas as pd
import flet as ft
from gtts.lang import tts_langs

from user_settings import SETTINGS
from exceptions import SchemeExistsError, InvalidIndexesError
from core import SheetScheme


def event_with_page_update(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        res = func(args[0], args[1])
        args[0].update()
        return res

    return wrapper


def schemes_as_options():
    return [ft.dropdown.Option(i) for i in SETTINGS.schemes]


class AllowedNarrationLanguages:
    languages = tts_langs()

    no_narration = "no-narration"

    def __init__(self):
        SETTINGS.translate_widget(self.__class__)

    @classmethod
    def is_allowed(cls, abbreviation: str) -> bool:
        return cls.languages.get(abbreviation, False) is not False

    @classmethod
    def as_options(cls) -> list[ft.dropdown.Option]:
        options = [ft.dropdown.Option(key=False, text=cls.no_narration)]
        options += [ft.dropdown.Option(key=i[0], text=i[1] + f" ({i[0]})") for i in cls.languages.items()]
        return options


class WordToCheckSchemeControls(ft.Column):
    instructions_input_label = "instructions-input-label"
    instructions_input_hint_text = "instructions-input-hint-text"
    word_to_check_input_label = "word-to-check-input-label"
    word_to_check_input_hint_text = "word-to-check-input-hint-text"
    information_input_label = "information-input-label"
    information_input_hint_text = "information-input-hint-text"
    no_additional_information = "no-additional_information"

    def __init__(self, width: int = 300):
        SETTINGS.translate_widget(self.__class__)
        self._instructions_input = ft.TextField(
            label=self.instructions_input_label,
            hint_text=self.instructions_input_hint_text,
            multiline=True,
            min_lines=1
        )
        self._word_to_check_column_index_input = ft.Dropdown(
            label=self.word_to_check_input_label,
            hint_text=self.word_to_check_input_hint_text
        )
        self._special_information_column_index_input = ft.Dropdown(
            label=self.information_input_label,
            hint_text=self.information_input_hint_text
        )
        self._controls_list = [self._instructions_input, self._word_to_check_column_index_input,
                               self._special_information_column_index_input]
        super().__init__(self._controls_list)
        self.disabled = True
        self.width = width

    def add_options(self, options: list[ft.dropdown.Option]):
        self._word_to_check_column_index_input.options = deepcopy(options)
        self._special_information_column_index_input.options = deepcopy(options) + [
            ft.dropdown.Option(key=False, text=self.no_additional_information)
        ]
        self.disabled = False

    def get_values(self) -> tuple[str, int, int]:
        info = self._special_information_column_index_input.value
        print(info)
        info = None if info == "false" or info is None else int(info) - 1
        return self._instructions_input.value, int(self._word_to_check_column_index_input.
                                                   value) - 1, info

    def clean(self):
        self._instructions_input.clean()
        self._word_to_check_column_index_input.clean()
        self._special_information_column_index_input.clean()


class SchemeDeletionControls(ft.Column):
    _scheme_deleted_message_template = "scheme-deleted-message-template"
    scheme_deletion = "scheme-deletion"
    schemes_label = "schemes-label"
    schemes_hint_text = "schemes-hint-text"
    delete_scheme_label = "delete-scheme-label"
    no_schemes_configured = "no-schemes-configured"
    choose_scheme = "choose-scheme"

    def __init__(self, width: int):
        SETTINGS.translate_widget(self.__class__)
        self.block_title = ft.Text(
            self.scheme_deletion,
            style=ft.TextThemeStyle.TITLE_LARGE
        )

        self._schemes = ft.Dropdown(
            label=self.schemes_label,
            hint_text=self.schemes_hint_text,
            autofocus=True,
        )
        self._delete_scheme_button = ft.ElevatedButton(self.delete_scheme_label, on_click=self.delete_scheme,
                                                       width=width // 2)
        self._error_label = ft.Text(color="red")
        self._error_label.visible = False
        self._scheme_deleted_label = ft.Text(color="green")

        super().__init__(
            [ft.Column([
                self.block_title,
                self._schemes, self._delete_scheme_button,
                self._error_label,
                self._scheme_deleted_label
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=width // 2)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            width=width

        )
        self._fill_dropdown()

    def _fill_dropdown(self):
        schemes = schemes_as_options()
        if SETTINGS.vocabulary_path_valid:
            self._schemes.options = schemes
        if not schemes:
            self._delete_scheme_button.disabled = True
            self._error_label.visible = True
            self._error_label.value = self.no_schemes_configured

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
            self._error_label.value = self.choose_scheme
            return

        SETTINGS.schemes.pop(scheme_name)
        SETTINGS.change_settings("schemes", SETTINGS.schemes)

        self._scheme_deleted(scheme_name)

    def _scheme_deleted(self, scheme_name: str):
        self.reload()
        self._scheme_deleted_label.value = self._scheme_deleted_message_template.format(scheme_name)


class SchemeCreationControls(ft.Column):
    _scheme_created_message_template = "scheme-created-message-template"
    top_title_text = "top-title-text"
    general_scheme_parameters_title = "general-scheme-parameters-title"
    sheet_choice_label = "sheet-choice-label"
    sheet_choice_hint_text = "sheet-choice-hint-text"
    scheme_name_label = "scheme-name-label"
    scheme_name_hint_text = "scheme-name-hint-text"
    translation_column_input_label = "translation-column-input-label"
    translation_column_input_hint_text = "translation-column-input-hint-text"
    word_status_column_input_label = "word-status-column-input-label"
    word_status_column_input_hint_text = "word-status-column-input-hint-text"
    narration_language_input_label = "narration-language-input-label"
    narration_language_input_hint_text = "narration-language-input-hint-text"

    test_blocks_title = "test-blocks-title"
    add_test_block = "add-test-block"
    remove_test_block = "remove-test-block"
    create_scheme = "create-scheme"
    fill_fields = "fill-fields"
    last_test_block = "last-test-block"
    no_narration = "no-narration"

    def __init__(self, overall_width: int = 600):
        SETTINGS.translate_widget(self.__class__)
        self.overall_width = overall_width
        self._file, self._sheets = None, None

        self._title = ft.Text(value=self.top_title_text, style=ft.TextThemeStyle.TITLE_LARGE)

        self._general_scheme_settings_title = ft.Text(
            value=self.general_scheme_parameters_title,
            style=ft.TextThemeStyle.TITLE_MEDIUM
        )

        self._sheet_choice = ft.Dropdown(
            on_change=self._fill_dropdowns,
            autofocus=True,
            label=self.sheet_choice_label,
            hint_text=self.sheet_choice_hint_text
        )
        self._sheet_choice.disabled = True

        self._scheme_name = ft.TextField(
            label=self.scheme_name_label,
            hint_text=self.scheme_name_hint_text
        )

        self._translation_column_index_input = ft.Dropdown(
            label=self.translation_column_input_label,
            hint_text=self.translation_column_input_hint_text
        )
        self._word_status_column_index_input = ft.Dropdown(
            label=self.word_status_column_input_label,
            hint_text=self.word_status_column_input_hint_text
        )
        self._narration_language_input = ft.Dropdown(
            label=self.narration_language_input_label,
            hint_text=self.narration_language_input_hint_text
        )

        self._empty_separator = ft.Container(height=30)

        self._test_blocks_managing_title = ft.Text(
            self.test_blocks_title,
            style=ft.TextThemeStyle.TITLE_MEDIUM
        )

        self._test_blocks = [WordToCheckSchemeControls(overall_width // 4)]
        self._test_blocks_column = ft.Column([i for i in self._test_blocks])

        self._errors_label = ft.Text(color="red")
        self._scheme_created_label = ft.Text(color="green")

        self._add_test_block_button = ft.ElevatedButton(
            self.add_test_block,
            on_click=self._add_test_block,
            width=200,
        )
        self._remove_test_block_button = ft.ElevatedButton(
            text=self.remove_test_block,
            on_click=self._remove_test_block,
            width=200,
        )

        self._test_blocks_managing_buttons = ft.Column(
            controls=[self._add_test_block_button, self._remove_test_block_button],
            width=overall_width // 5,
        )
        self._test_blocks_row = ft.Row(
            controls=self._test_blocks,
            wrap=True,
            spacing=10,
            run_spacing=10,
        )

        self._test_blocks_managing = ft.Row(
            controls=[self._test_blocks_managing_buttons, self._test_blocks_row],
            disabled=True,
            alignment=ft.MainAxisAlignment.CENTER
        )

        self._create_scheme_button = ft.ElevatedButton(
            self.create_scheme,
            on_click=self._create_scheme,
            disabled=True
        )

        controls = [self._title, self._general_scheme_settings_title,
                    self._sheet_choice, self._scheme_name,
                    self._translation_column_index_input, self._word_status_column_index_input,
                    self._narration_language_input,
                    self._empty_separator,
                    self._test_blocks_managing_title,
                    self._test_blocks_managing, self._errors_label,
                    self._create_scheme_button,
                    self._scheme_created_label]

        self._inputs = [self._sheet_choice, self._scheme_name,
                        self._translation_column_index_input, self._word_status_column_index_input,
                        self._narration_language_input]

        super().__init__(controls)

        if SETTINGS.vocabulary_path_valid:
            self._fill_sheet_choice_options()
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        for i in self._inputs:
            i.width = overall_width // 2
        self._test_blocks_managing.width = overall_width - 20

    def reload(self):
        if SETTINGS.vocabulary_path_valid:
            self._fill_sheet_choice_options()

        for i in self._inputs:
            i.value = ""

        self._translation_column_index_input.options.clear()
        self._word_status_column_index_input.options.clear()

        self._test_blocks_managing.disabled = True
        self._create_scheme_button.disabled = True

        self._test_blocks.clear()
        self._test_blocks.append(WordToCheckSchemeControls())
        self._update_test_block_row()

        self._errors_label.value = ""
        self._scheme_created_label.value = ""

    def _scheme_created(self, scheme_name: str) -> None:
        self.reload()
        self._scheme_created_label.value = self._scheme_created_message_template.format(scheme_name)

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
            self._errors_label.value = self.fill_fields
        self.update()

    def _build_scheme(self) -> dict[str, Union[int, str, list[dict[str, Union[str, int]]]]]:
        sheet_name = self._sheet_choice.value
        if not sheet_name:
            raise TypeError
        translation_column_index = int(self._translation_column_index_input.value) - 1
        word_status_column_index = int(self._word_status_column_index_input.value) - 1
        narration_language = self._narration_language_input.value

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

        scheme = SheetScheme.to_scheme((sheet_name, translation_column_index, word_status_column_index,
                                        narration_language, test_blocks))
        return scheme

    @staticmethod
    def _write_scheme(name: str, scheme: dict[str, Union[int, str, list[dict[str, Union[str, int]]]]]):
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
        self._update_test_block_row()

    @event_with_page_update
    def _remove_test_block(self, e: ft.ControlEvent):
        if len(self._test_blocks) == 1:
            self._errors_label.value = self.last_test_block
            return
        self._test_blocks.pop()
        self._update_test_block_row()

    def _fill_dropdowns(self, e) -> None:
        self._test_blocks_managing.disabled = False
        self._create_scheme_button.disabled = False

        column = self._get_columns()
        self._translation_column_index_input.options = deepcopy(column)
        self._word_status_column_index_input.options = deepcopy(column)
        self._narration_language_input.options = AllowedNarrationLanguages.as_options()
        self._narration_language_input.value = self.no_narration
        for i in self._test_blocks:
            i.add_options(column)
        self.update()

    def _update_test_block_row(self):
        max_width = self.overall_width - self.overall_width // 4
        desired_width = len(self._test_blocks) * self._test_blocks[0].width + 20
        width = max_width if desired_width > max_width else desired_width
        self._test_blocks_row.width = width
        self._test_blocks_row.controls = self._test_blocks

    def _get_columns(self) -> list[ft.dropdown.Option]:
        sheet_name = self._sheet_choice.value
        sheet: pd.DataFrame = self._file.parse(sheet_name)
        return [ft.dropdown.Option(key=int(index), text=f"{index} - {name}") for index, name in
                enumerate(sheet.columns, start=1)]

    def _fill_sheet_choice_options(self):
        self._file, self._sheets = self._parse_excel(SETTINGS.path)
        self._sheet_choice.options = [ft.dropdown.Option(i) for i in self._sheets]
        self._sheet_choice.disabled = False

    @staticmethod
    def _parse_excel(path: str) -> tuple[pd.ExcelFile, list]:
        file = pd.ExcelFile(path)
        sheets = file.sheet_names
        return file, sheets


class SchemeManagingControls(ft.Column):
    no_vocabulary_file_message = "no-vocabulary-file"

    def __init__(self, page: ft.Page):
        SETTINGS.translate_widget(self.__class__)
        self.page = page

        self.no_vocabulary_file_label = ft.Text(color="red", size=20)

        self.scheme_creation = SchemeCreationControls(overall_width=self.page.window_width - 20)

        self.scheme_deletion = SchemeDeletionControls(width=self.page.window_width - 20)
        self.scheme_deletion.visible = False

        self.navigation_routes = {
            "creation": self.scheme_creation,
            "alteration": ft.Row(),
            "deletion": self.scheme_deletion,
        }
        self.controls_list = [self.no_vocabulary_file_label, self.scheme_creation, self.scheme_deletion]
        super().__init__(self.controls_list, alignment=ft.MainAxisAlignment.CENTER,
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def set_vocabulary_file_label(self):
        self.no_vocabulary_file_label.value = "" if SETTINGS.vocabulary_path_valid else self.no_vocabulary_file_message

    def reload(self, external: bool = False):
        if external:
            self.visible = True
        self.scheme_deletion.reload()
        self.scheme_creation.reload()
        self.set_vocabulary_file_label()

    def go_to(self, destination: str):
        destination = destination.rsplit("_")[-1]
        self.visible = True
        for i in self.navigation_routes.values():
            i.visible = False
        destination_object = self.navigation_routes.get(destination)
        destination_object.reload()
        destination_object.visible = True
        self.update()
