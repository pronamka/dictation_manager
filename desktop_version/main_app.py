import os

from typing import Union, Callable
from enum import Enum
from copy import deepcopy

import flet as ft
import pandas as pd

from desktop_version.exceptions import SchemeExistsError, InvalidIndexesError, BaseExceptionWithUIMessage, \
    InvalidRangeOfWordsError, ExcelAppOpenedError
from desktop_version.core import SheetScheme, SETTINGS, ExcelParser, SheetToSchemeCompatibilityChecker, \
    WordsGetter, RowToCheck, Dictation, DictationContent, Choice, AnswerCheckedResponse


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


class DictationRunControls(ft.Column):
    translation_label_text = "Translation of the current word: {}"
    answer_correctness_relations = {
        AnswerCorrectness.CORRECT: ["Right.", "green"],
        AnswerCorrectness.INCORRECT: ["Wrong.", "red"],
        AnswerCorrectness.WITH_HINT: ["Answer Shown. You will be asked to type it again afterwards.", "yellow"]
    }

    dictation_completed_message = "Congratulations! You have completed the dictation. \n" \
                                  "The statuses of the words in your sheet have been updated."
    dictation_stopped_message = "Dictation was stopped. The statuses of the words in your sheet have been updated."
    answer_shown_instructions = "The word(s) was(were): {}. Now type it(them) to remember."
    translation_text_template = "Translation: {}"
    instructions_text_template = "Instructions: {}"
    information_about_the_word_template = "Information about the word: {}"
    no_information_message = "There was no information about that word."

    def __init__(self, page: ft.Page, reload_function: Callable, block_width: int):
        self.page = page
        self.reload_function = reload_function
        self.block_width = block_width

        self.page.on_keyboard_event = self.get_hint_through_keyboard

        self.synonyms_label = ft.Text(color=ft.colors.DEEP_PURPLE, size=15)
        self.variations_left_label = ft.Text(color="red", size=15)
        self.previous_word_label = ft.Text(
            "Here will be your previous answer.",
            size=18
        )
        self.additional_information_label = ft.Text(
            "Here will be the information about the previous answer.",
            size=15
        )

        self.translation_label = ft.Text(
            self.translation_text_template.format(""),
            size=23,
        )
        self.instructions_label = ft.Text(
            self.instructions_text_template.format(""),
            size=20,
        )

        self.hints_label = ft.Text()

        self.user_input = ft.TextField(
            on_submit=self.send_answer,
        )

        self.answer_correctness_indicator = ft.Text(size=20)

        self.stop_dictation_button = ft.ElevatedButton("Stop Dictation", on_click=self.stop_dictation_request)
        self.show_answer_button = ft.ElevatedButton("Show answer", on_click=self.show_answer)

        self.dictation_ended_label = ft.Text("")

        self.previous_word_block_title = ft.Text(
            "Information about the previous word.",
            style=ft.TextThemeStyle.TITLE_LARGE,
            text_align=ft.TextAlign.CENTER
        )

        self.current_word_block_title = ft.Text(
            "Current word.",
            style=ft.TextThemeStyle.TITLE_LARGE,
            text_align=ft.TextAlign.CENTER
        )
        self.empty_separator = ft.Container(height=20)

        self.controls_list = [self.previous_word_block_title,
                              self.previous_word_label, self.additional_information_label,
                              self.empty_separator,
                              self.current_word_block_title,
                              self.translation_label, self.instructions_label,
                              self.synonyms_label, self.variations_left_label,
                              self.answer_correctness_indicator,
                              self.hints_label, self.user_input, self.show_answer_button,
                              self.stop_dictation_button, self.dictation_ended_label]

        self.dictation = None
        self.awaiting_hint_typed = False
        super().__init__(self.controls_list)
        self.set_width()

    def set_width(self):
        for i in self.controls:
            i.width = self.block_width

    def get_hint_through_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "H" and e.ctrl is True:
            self.show_answer(e)

    def stop_dictation_request(self, e: ft.ControlEvent):
        self.dictation.stop()
        self.stop_dictation(self.dictation_stopped_message)

    def run_dictation(self, dictation_content: DictationContent):
        self.disabled = False
        self.answer_correctness_indicator.value = ""

        self.dictation_ended_label.value = ""
        self.dictation = Dictation(dictation_content, SETTINGS.path)
        self.dictation.run()
        self.display_current_word()

    def display_current_word(self):
        try:
            cur_word: Union[bool, Choice] = self.dictation.get_word()
        except ExcelAppOpenedError as e:
            self.handle_excel_errors(e)
            return
        if not cur_word:
            self.stop_dictation(self.dictation_completed_message)
            return
        cur_word: Choice = cur_word
        self.translation_label.value = self.translation_text_template.format(cur_word.translation)
        self.instructions_label.value = self.instructions_text_template.format(cur_word.instructions)
        self.synonyms_label.visible = False
        if cur_word.with_synonyms:
            self.synonyms_label.value = cur_word.with_synonyms
            self.synonyms_label.visible = True
        self.variations_left_label.value = cur_word.amount_of_words_left

    def show_answer(self, e: ft.ControlEvent):
        self.awaiting_hint_typed = True
        self.clear_labels()
        word: Choice = self.dictation.show_answer()
        self.hints_label.value = self.answer_shown_instructions.format(word.show_all_translation())
        self.user_input.focus()
        self.page.update()

    def send_answer(self, e: ft.ControlEvent):
        res: AnswerCheckedResponse = self.dictation.check_answer(self.user_input.value, (not self.awaiting_hint_typed))
        if self.awaiting_hint_typed:
            self.awaiting_hint_typed = False
            self.hints_label.value = ""
            self.display_correctness_indicator(AnswerCorrectness.WITH_HINT)
        elif not res.is_right:
            self.display_correctness_indicator(AnswerCorrectness.INCORRECT)
            self.user_input.focus()
            self.page.update()
            return
        else:
            self.display_correctness_indicator(AnswerCorrectness.CORRECT)

        self.display_previous_word(res)
        self.user_input.value = ""
        self.display_current_word()
        self.user_input.focus()
        self.page.update()

    def display_previous_word(self, word: AnswerCheckedResponse):
        self.variations_left_label.value = word.synonyms_left

        self.previous_word_label.value = word.other_variations
        information = self.no_information_message if word.info_to_given_word in ["nan", "n-"] else \
            self.information_about_the_word_template.format(word.info_to_given_word)
        self.additional_information_label.value = information

    def display_correctness_indicator(self, state: AnswerCorrectness):
        scheme = self.answer_correctness_relations.get(state)
        self.answer_correctness_indicator.value = scheme[0]
        self.answer_correctness_indicator.color = scheme[1]

    def clear_labels(self):
        self.translation_label.value = ""
        self.instructions_label.value = ""

    def handle_excel_errors(self, e: ExcelAppOpenedError):
        self.dictation_ended_label.value = e.message()
        self.dictation_ended_label.color = "red"
        self.user_input.disabled = True
        self.show_answer_button.disabled = True
        self.stop_dictation_button.disabled = False

    def stop_dictation(self, message: str):
        try:
            self.dictation.stop()
        except ExcelAppOpenedError as e:
            self.handle_excel_errors(e)
            return
        self.dictation_ended_label.value = message
        self.clear_labels()
        self.previous_word_label.value = ""
        self.additional_information_label.value = ""
        self.disabled = True
        self.reload_function()


class SchemeChoiceControls(ft.Column):
    schemes_key = "schemes"
    no_schemes_message = "You do not have any schemes configured. Please go to schemes " \
                         "creation panel and create a scheme to proceed."

    def __init__(self, scheme_chosen_function: Callable):
        self.schemes = SETTINGS.get(self.schemes_key)
        self.schemes_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(i) for i in self.schemes.keys()],
            on_change=lambda x: scheme_chosen_function(x.control.value),
            autofocus=True,

            label="Scheme Name",
            hint_text="Which scheme do you want to practice?"
        )

        self.no_schemes_label = ft.Text(color="red")
        self.no_schemes_label.visible = False

        self._check_for_schemes()
        self.controls_list = [self.schemes_dropdown, self.no_schemes_label]
        super().__init__(self.controls_list)

    def _check_for_schemes(self) -> bool:
        if self.schemes:
            return True
        self.schemes_dropdown.disabled = True
        self.no_schemes_label.value = self.no_schemes_message
        self.no_schemes_label.visible = True
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
        self.page = page
        self.start_dictation_function = start_dictation_function

        self.sheet_processing_error_label = ft.Text(color="red")

        self.range_label = ft.Text("Range: ")
        self.range_start = ft.TextField(label="from", width=page.width // 8, keyboard_type=ft.KeyboardType.NUMBER)
        self.range_end = ft.TextField(label="to", width=page.width // 8, keyboard_type=ft.KeyboardType.NUMBER)

        self.range_controls = ft.Row(
            [self.range_label, self.range_start, self.range_end],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        )

        self.target_choice = ft.Dropdown(
            options=[ft.dropdown.Option(i) for i in self.target_states],
            label="Word Status",
            hint_text="Words with what status you want to practice?"
        )
        self.target_choice.value = "NEW"

        self.with_narrator_checkbox = ft.Checkbox(label="With Narration?")
        self.with_narrator_checkbox.value = True

        self.start_dictation_button = ft.ElevatedButton("Start Dictation", on_click=self.send_dictation_settings)

        self.error_with_chosen_settings_label = ft.Text(color="red")

        self.controls_list = [self.sheet_processing_error_label, self.range_controls, self.target_choice,
                              self.with_narrator_checkbox, self.start_dictation_button,
                              self.error_with_chosen_settings_label]

        self.allowed_range: range = range(2, 2)
        self.sheet, self.scheme = None, None

        super().__init__(self.controls_list)

    def set_width(self, width: int):
        for i in self.controls:
            i.width = width

    def send_dictation_settings(self, e):
        try:
            inputs = self.process_inputs()
            self.start_dictation(*inputs)
        except BaseExceptionWithUIMessage as e:
            self.error_with_chosen_settings_label.value = e.message()
            self.page.update()

    def fill_controls(self, sheet: pd.DataFrame, scheme: SheetScheme) -> None:
        sheet_valid = self.check_sheet_validity(sheet, scheme)
        self.sheet = sheet
        self.scheme = scheme
        if not sheet_valid:
            return
        self.fill_range(sheet)
        self.disabled = False
        self.page.update()

    def fill_range(self, sheet: pd.DataFrame):
        self.range_start.value = 2
        self.range_end.value = sheet.shape[0]
        self.allowed_range = range(2, sheet.shape[0])

    def check_sheet_validity(self, sheet: pd.DataFrame, scheme: SheetScheme) -> bool:
        try:
            SheetToSchemeCompatibilityChecker(sheet, scheme).check_compatibility()
            return True
        except BaseExceptionWithUIMessage as e:
            self.sheet_processing_error_label.value = e.message()
            self.disabled = True
            return False

    def process_inputs(self) -> tuple[range, str, bool]:
        start, stop = int(self.range_start.value), int(self.range_end.value)
        input_range = range(start, stop)
        if start > stop or start < self.allowed_range.start or stop > self.allowed_range.stop:
            raise InvalidRangeOfWordsError(self.allowed_range.start, self.allowed_range.stop)
        return input_range, self.target_choice.value, self.with_narrator_checkbox.value

    def start_dictation(
            self,
            words_range: range,
            target: str,
            with_narration: bool = True,
            with_shuffle: bool = True
    ) -> Union[None, DictationContent]:
        if not self.scheme:
            ...
        try:
            words = WordsGetter(self.sheet, self.scheme, words_range, target, with_shuffle).get_words()
            self.error_with_chosen_settings_label.value = ""
            return self.start_dictation_function(words)
        except BaseExceptionWithUIMessage as e:
            self.error_with_chosen_settings_label.value = e.message()
            self.page.update()


class DictationSettingsControls(ft.Column):

    def __init__(self, page: ft.Page, send_words_function: Callable,
                 dictation_finished_message: str = ""):
        self.page = page
        width = page.window_width // 3 - 20
        self.send_words_function = send_words_function
        self.no_vocabulary_path_set_label = ft.Text(color="red")
        self.section_label = ft.Text("Dictation Settings", style=ft.TextThemeStyle.TITLE_LARGE)

        self.scheme_choice_controls = SchemeChoiceControls(self.fill_run_settings)
        if not SETTINGS.vocabulary_path_valid:
            self.scheme_choice_controls.disabled = True
            self.no_vocabulary_path_set_label.value = "You have no vocabulary file configured. \n" \
                                                      "Please go to `File`."

        self.dictation_run_settings_controls = DictationRunSettingsControls(page, self.start_dictation)
        self.dictation_run_settings_controls.disabled = True
        self.dictation_run_settings_controls.set_width(width)

        self.statues_updated_label = ft.Text(
            dictation_finished_message,
            color="green",
            width=width,
            text_align=ft.TextAlign.CENTER
        )

        self.controls_list = [self.section_label, self.no_vocabulary_path_set_label, self.scheme_choice_controls,
                              self.dictation_run_settings_controls, self.statues_updated_label]

        self.sheet, self.scheme = None, None

        super().__init__(self.controls_list)
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.width = page.window_width // 3 - 20

    def fill_run_settings(self, scheme_name: str):
        self.scheme = SheetScheme(*SETTINGS.schemes.get(scheme_name))
        sheet_name = self.scheme.sheet_name
        self.sheet = ExcelParser.get_sheet(sheet_name)
        self.dictation_run_settings_controls.fill_controls(self.sheet, self.scheme)
        self.page.update()

    def start_dictation(self, words: dict[int, RowToCheck]):
        self.send_words_function(words)

    def set_width(self, width: int):
        for i in self.controls:
            i.width = width


class DictationControls(ft.Row):
    dictation_finished_message = "Dictation finished! \nThe statuses of the words have been updated."

    def __init__(self, reload: Callable, page: ft.Page):
        self.page = page
        self.reload = reload

        self.dictation_settings = DictationSettingsControls(page, self.start_dictation)

        self.dictation = DictationRunControls(self.page, self.dictation_ended, self.page.window_width // 1.5 - 30)
        self.dictation.disabled = True
        self.dictation.visible = False

        self.controls_list = [self.dictation_settings, self.dictation]

        super().__init__(self.controls_list, alignment=ft.MainAxisAlignment.CENTER,
                         vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def start_dictation(self, words: DictationContent):
        self.dictation_settings.disabled = True
        self.dictation_settings.visible = False

        self.dictation.visible = True
        self.dictation.disabled = False
        self.dictation.run_dictation(words)
        self.update()

    def dictation_ended(self):
        self.dictation.visible = False
        self.dictation.disabled = True

        self.dictation_settings.disabled = False
        self.dictation_settings.visible = True

        self.dictation_settings.controls = DictationSettingsControls(self.page, self.start_dictation,
                                                                     self.dictation_finished_message).controls
        self.dictation_settings.statues_updated_label.visible = True
        self.update()


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

    def scheme_deleted_reload(self):
        self.scheme_deletion.controls = SchemeDeletionControls(self.scheme_deleted_reload, self.page).controls
        self.update()

    def scheme_created_reload(self, scheme_name: str = ""):
        self.scheme_creation.controls = SchemeCreationControls(self.scheme_deleted_reload,
                                                               self.page, scheme_name).controls
        self.page.update()


class MenuBar(ft.Row):
    def __init__(self, navigation_function: Callable):
        self.dictation_window_button = ft.ElevatedButton(
            text="Dictation",
            data="dictation",
        )
        self.scheme_creation_window_button = ft.ElevatedButton("Schemes", data="schemes")
        self.vocabulary_path_window_button = ft.ElevatedButton("File", data="file")
        self.controls_list = [self.dictation_window_button, self.scheme_creation_window_button,
                              self.vocabulary_path_window_button]

        for i in self.controls_list:
            i.on_click = lambda x: navigation_function(x)

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
        # self.page.window_full_screen = True
        self.page.scroll = "always"
        self.page.window_resizable = False
        self.page.window_max_width = self.page.width
        self.page.window_max_height = self.page.height
        self.page.window_center()
        self.page.on_window_event = self.process_window_event

        """self.page.window_max_width = 1500
        self.page.window_max_height = 800
        screen_width, screen_height = GetSystemMetrics(0), GetSystemMetrics(1)
        self.page.window_width = min(self.page.window_max_width, screen_width)
        self.page.window_height = min(self.page.window_max_height, screen_height)"""

        self.page_menu = MenuBar(self.window_changed)

        self.dictation_controls = DictationControls(self.dictation_reload, self.page)
        self.schemes = SchemeManagingControls(self.scheme_managing_reload, self.page)
        self.vocabulary_path_controls = PathToVocabularyControls(self.vocabulary_path_reload)
        self.schemes.visible = False
        self.vocabulary_path_controls.visible = False

        self.navigation_routes = {"dictation": self.dictation_controls, "schemes": self.schemes,
                                  "file": self.vocabulary_path_controls}
        self.bar = ft.Container(
            ft.Row(
                controls=[ft.Icon(ft.icons.WORK), ft.Text("Dictation", size=30),
                          self.page_menu],
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=10,
        )
        """self.page.appbar = ft.AppBar(
            leading=ft.Icon(ft.icons.WORK),
            title=ft.Text("Dictation"),
            actions=[self.page_menu],
            bgcolor=ft.colors.SURFACE_VARIANT,
        )"""
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


if __name__ == "__main__":
    ft.app(target=main)
