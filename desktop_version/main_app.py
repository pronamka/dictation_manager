import os

from typing import Union, Callable
from ast import literal_eval

import flet as ft
import pandas as pd

from desktop_version.exceptions import SchemeExistsError, InvalidIndexesError
from desktop_version.core import SheetScheme


class ExcelParser:
    @staticmethod
    def get_sheet(sheet_name: str) -> pd.DataFrame:
        if not SETTINGS.vocabulary_path_valid:
            ...

        sheet = pd.read_excel(SETTINGS.path, sheet_name, dtype=str)
        return sheet


class Block:
    def __init__(self, block_representation: Union[ft.Row, ft.Column]):
        self.block_representation = block_representation

    def disable_controls(self):
        self.block_representation.disabled = True

    def enable_controls(self):
        self.block_representation.disabled = False

    @property
    def as_block(self) -> Union[ft.Row, ft.Column]:
        return self.block_representation


class DictationControls(ft.Column):
    def __init__(self):

        self.translation_label = ft.Text("Translation of the current word: ")
        self.instructions_label = ft.Text("Type ...")
        self.additional_information = ft.Text("Some additional information")

        self.user_input = ft.TextField(on_submit=...)
        self.input_information = ft.Text()
        self.controls_list = [self.translation_label,self.instructions_label,self.additional_information,
                         self.user_input,self.input_information]
        super().__init__(self.controls_list)


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

    @property
    def schemes_as_options(self) -> list[ft.dropdown.Option]:
        return [ft.dropdown.Option(i) for i in self.get(self.schemes_key, {}).keys()]

    @property
    def path(self) -> str:
        return self.get(self.vocabulary_key, "")

    @property
    def vocabulary_path_valid(self) -> bool:
        path = self.get(self.vocabulary_key, "")
        if os.path.exists(path) and path.rsplit(".", maxsplit=1)[-1] == "xlsx":
            return True
        return False


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


class SchemeChoiceControls(ft.Column):
    schemes_key = "schemes"
    no_schemes_message = "You do not have any schemes configured. Please go to schemes " \
                         "creation panel and create a scheme to proceed."

    def __init__(self, scheme_chosen_function: Callable):
        self.schemes = SETTINGS.get(self.schemes_key)
        self.schemes_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(i) for i in self.schemes.keys()],
            on_change=lambda x: scheme_chosen_function(x.control.value)
        )

        self.no_schemes_label = ft.Text(color="red")
        self._check_for_schemes()
        self.controls_list= [self.schemes_dropdown, self.no_schemes_label]
        super().__init__(self.controls_list)

    def _check_for_schemes(self) -> bool:
        if self.schemes:
            return True
        self.schemes_dropdown.disabled = True
        self.no_schemes_label.value = self.no_schemes_message
        return False

    @property
    def valid_schemes_present(self) -> bool:
        return bool(self.schemes)

    @property
    def chosen_scheme(self) -> str:
        return self.schemes_dropdown.value


class DictationRunSettingsControls(ft.Column):
    target_states = ["NEW", "NORMAL", "NEEDS_REVISION", "all"]

    def __init__(self, page: ft.Page, start_dictation_function: Callable):
        self.range_label = ft.Text("Range: ")
        self.range_start = ft.TextField(label="from", width=page.width//8, keyboard_type=ft.KeyboardType.NUMBER)
        self.range_end = ft.TextField(label="to", width=page.width//8, keyboard_type=ft.KeyboardType.NUMBER)

        self.range_controls = ft.Row([self.range_label, self.range_start, self.range_end])

        self.target_choice = ft.Dropdown(options=[ft.dropdown.Option(i) for i in self.target_states])
        self.target_choice.value = ft.dropdown.Option("all")

        self.with_narrator_checkbox = ft.Checkbox(label="With Narration?")
        self.with_narrator_checkbox.value = True

        self.start_dictation_button = ft.ElevatedButton("Start Dictation", on_click=...)
        self.controls_list = [self.range_controls, self.target_choice,
                                    self.with_narrator_checkbox, self.start_dictation_button]

        self.allowed_range: range = range(2, 2)
        self.sheet = None

        super().__init__(self.controls_list)

    def fill_controls(self, data: pd.ExcelFile):
        self.sheet = data
        self.allowed_range = range(2, data[0]+1+1)
        self.range_start.value = 2
        self.range_end.value = data[0]+1
        self.disabled = False

    def check_sheet_validity(self):
        ...

    def process_inputs(self) -> tuple[range, str, bool]:
        input_range = range(int(self.range_start.value), int(self.range_end.value))
        if input_range.start > input_range.stop or input_range.start < self.allowed_range.start or \
                input_range.stop > self.allowed_range.stop:
            ...
        return input_range, self.target_choice.value, self.with_narrator_checkbox.value


class DictationSettingsControls(ft.Column):

    def __init__(self, page: ft.Page):
        self.page = page
        self.no_vocabulary_path_set_label = ft.Text(color="red")

        self.scheme_choice_controls = SchemeChoiceControls(self.fill_run_settings)
        if not SETTINGS.vocabulary_path_valid:
            self.scheme_choice_controls.disabled = True
            self.no_vocabulary_path_set_label.value = "You have no vocabulary file configured. \n" \
                                            "Please go to `File`."

        self.dictation_run_settings_controls = DictationRunSettingsControls(page, self.start_dictation)
        self.dictation_run_settings_controls.disabled = True

        self.controls_list = [self.no_vocabulary_path_set_label, self.scheme_choice_controls,
                              self.dictation_run_settings_controls]

        super().__init__(self.controls_list)

    def fill_run_settings(self, scheme_name: str):
        scheme = SheetScheme(*SETTINGS.schemes.get(scheme_name))
        sheet_name = scheme.sheet_name
        sheet = ExcelParser.get_sheet(sheet_name)
        self.dictation_run_settings_controls.fill_controls(sheet)
        self.page.update()

    def start_dictation(self):
        ...


class Dictation(ft.Row):
    def __init__(self, reload: Callable, page: ft.Page):
        self.page = page
        self.reload = reload

        self.dictation_settings = DictationSettingsControls(page)
        self.dictation_settings.width = self.page.width // 3
        self.dictation = DictationControls()
        self.dictation.width = self.page.width

        self.controls_list = [self.dictation_settings, self.dictation]

        super().__init__(self.controls_list)


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
        self.word_to_check_column_index_input.options = options
        self.special_information_column_index_input.options = options
        self.disabled = False

    def get_values(self) -> tuple[str, int, int]:
        return self.instructions_input.value, int(self.word_to_check_column_index_input.value), \
               int(self.special_information_column_index_input.value)

    def clean(self):
        self.instructions_input.clean()
        self.word_to_check_column_index_input.clean()
        self.special_information_column_index_input.clean()


def with_page_update(func: Callable) -> Callable:

    def wrapper(*args, **kwargs):
        res = func(args[0])
        args[0].page.update()
        return res

    return wrapper


class SchemeDeletionControls(ft.Column):
    def __init__(self, reload_function: Callable, page: ft.Page):
        self.page = page

        self.schemes = ft.Dropdown()
        self.reload = reload_function
        self.delete_scheme_button = ft.ElevatedButton("Delete", on_click=self.delete_scheme)
        self.error_label = ft.Text(color="red")

        self._fill_dropdown()

        super().__init__([ft.Row([self.schemes, self.delete_scheme_button]), self.error_label])

    def _fill_dropdown(self):
        schemes = SETTINGS.schemes_as_options
        if SETTINGS.vocabulary_path_valid:
            self.schemes.options = schemes
        if not schemes:
            self.delete_scheme_button.disabled = True
            self.error_label.value = "You do not have any schemes configured. Please go to schemes " \
                                     "creation panel and create a scheme to proceed."
        self.page.update()

    def delete_scheme(self, e):
        self.error_label.value = ""
        schemes: dict = SETTINGS.get("schemes")
        scheme_name = self.schemes.value
        if not scheme_name or scheme_name is None:
            self.error_label.value = "Choose the scheme you want to delete."
        del schemes[scheme_name]
        SETTINGS.change_settings("schemes", schemes)
        return self.reload()


class SchemeCreationControls(ft.Column):
    def __init__(self, reload_function: Callable, page: ft.Page, init_message: str):
        self.page = page
        self.reload = reload_function

        self.title = ft.Text(value="Scheme Creation")

        self.sheet_choice = ft.Dropdown(on_change=self.fill_dropdowns)
        self.sheet_choice.disabled = True

        self.file, self.sheets = None, None
        if SETTINGS.vocabulary_path_valid:
            self.fill_sheet_choice_options()

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

    def create_scheme(self, e):
        try:
            scheme_name = self.scheme_name.value
            scheme = self.build_scheme()
            self.write_scheme(scheme_name, scheme)

            return self.reload(scheme_name)
        except (InvalidIndexesError, SchemeExistsError) as e:
            self.errors_label.value = e.message()
        except TypeError as e:
            self.errors_label.value = "Fill in all the fields."
        self.page.update()

    def build_scheme(self) -> tuple[str, int, int, list[dict[str, Union[str, int]]]]:
        sheet_name = self.sheet_choice.value
        if not sheet_name:
            raise TypeError
        translation_column_index = int(self.translation_column_index_input.value)
        word_status_column_index = int(self.word_status_column_index_input.value)

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

    @with_page_update
    def add_test_block(self):
        self.errors_label.value = ""
        block = WordToCheckSchemeControls()
        block.add_options(self.test_blocks[0].word_to_check_column_index_input.options)
        self.test_blocks.append(block)
        self.change_test_block_column()

    @with_page_update
    def remove_test_block(self):
        if len(self.test_blocks) == 1:
            self.errors_label.value = "A scheme must have at least one test block."
            return
        self.test_blocks.pop()
        self.change_test_block_column()

    def fill_dropdowns(self, e) -> None:
        columns_amount = self.get_columns_amount()
        options = [ft.dropdown.Option(i) for i in range(1, columns_amount + 1)]
        self.translation_column_index_input.options = options
        self.word_status_column_index_input.options = options
        for i in self.test_blocks:
            i.add_options(options)
        self.change_test_block_column()
        self.page.update()

    @with_page_update
    def change_test_block_column(self):
        self.test_blocks_column.controls = [i for i in self.test_blocks]

    def get_columns_amount(self) -> int:
        sheet_name = self.sheet_choice.value
        sheet: pd.DataFrame = self.file.parse(sheet_name)
        columns_amount = sheet.shape[1]
        return columns_amount

    @with_page_update
    def fill_sheet_choice_options(self):
        self.file, self.sheets = self.parse_excel(SETTINGS.path)
        self.sheet_choice.options = [ft.dropdown.Option(i) for i in self.sheets]
        self.sheet_choice.disabled = False

    @staticmethod
    def parse_excel(path: str) -> tuple[pd.ExcelFile, list]:
        file = pd.ExcelFile(path)
        sheets = file.sheet_names
        return file, sheets

    @with_page_update
    def vocabulary_path_set(self):
        self.fill_sheet_choice_options()


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

        self.navigation_bar = SchemeManagingNavigationBar(self.go_to)

        self.no_vocabulary_file_label = ft.Text(color="red")

        self.scheme_creation = SchemeCreationControls(self.scheme_created_reload, self.page, "")

        self.scheme_deletion = SchemeDeletionControls(self.scheme_deleted_reload, self.page)
        self.scheme_deletion.visible = False

        self.navigation_routes = {"creation": self.scheme_creation, "deletion": self.scheme_deletion}
        print(SETTINGS.path)
        print(SETTINGS.vocabulary_path_valid)
        if not SETTINGS.vocabulary_path_valid:
            self.no_vocabulary_file_label.value = "You have no vocabulary file configured. \n" \
                                            "Please go to `File`."
        self.controls_list = [self.navigation_bar, ft.Column([self.no_vocabulary_file_label,
                                                         self.scheme_creation, self.scheme_deletion])]
        super().__init__(self.controls_list)

    def go_to(self, destination: str):
        for i in self.navigation_routes.values():
            i.visible = False
        destination_object = self.navigation_routes.get(destination)
        destination_object.reload()
        destination_object.visible = True
        self.page.update()

    @with_page_update
    def scheme_deleted_reload(self):
        self.scheme_deletion.controls = SchemeDeletionControls(self.scheme_deleted_reload, self.page).controls

    def scheme_created_reload(self, scheme_name: str = ""):
        self.scheme_creation.controls = SchemeCreationControls(self.scheme_deleted_reload,
                                                               self.page, scheme_name).controls
        self.page.update()


class MenuBar(ft.Row):
    def __init__(self, navigation_function: Callable):
        self.dictation_window_button = ft.ElevatedButton("Dictation", data="dictation")
        self.scheme_creation_window_button = ft.ElevatedButton("Schemes", data="schemes")
        self.vocabulary_path_window_button = ft.ElevatedButton("File", data="file")
        self.controls_list = [self.dictation_window_button, self.scheme_creation_window_button,
                    self.vocabulary_path_window_button]

        for i in self.controls_list:
            i.on_click = lambda x: navigation_function(x)

        super().__init__(self.controls_list)


class MainPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.scroll = "always"

        self.page_menu = MenuBar(self.window_changed)

        self.dictation = Dictation(self.dictation_reload, self.page)
        self.schemes = SchemeManagingControls(self.scheme_managing_reload, self.page)
        self.vocabulary_path_controls = PathToVocabularyControls(self.vocabulary_path_reload)
        self.schemes.visible = False
        self.vocabulary_path_controls.visible = False

        self.navigation_routes = {"dictation": self.dictation, "schemes": self.schemes,
                             "file": self.vocabulary_path_controls}

        self.controls_list = ft.Column([self.page_menu, ft.Row([self.dictation, self.schemes,
                                                                self.vocabulary_path_controls])])

        page.add(self.controls_list)

        self.page.update()

    def vocabulary_path_reload(self):
        self.vocabulary_path_controls.controls = PathToVocabularyControls(self.vocabulary_path_reload).controls
        self.page.update()

    def scheme_managing_reload(self):
        self.schemes.controls = SchemeManagingControls(self.scheme_managing_reload, self.page).controls
        self.page.update()

    def dictation_reload(self):
        self.dictation.controls = Dictation(self.dictation_reload, self.page).controls
        self.page.update()

    def window_changed(self, e: ft.ControlEvent):
        destination = e.control.data
        for i in self.navigation_routes.values():
            i.visible = False
        destination_object = self.navigation_routes.get(destination)
        destination_object.reload()
        destination_object.visible = True
        self.page.update()


def main(page: ft.Page):
    MainPage(page)


SETTINGS = Settings()


ft.app(target=main)