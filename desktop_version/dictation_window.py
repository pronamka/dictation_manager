from typing import Callable, Union
from enum import Enum

import pandas as pd
import flet as ft

from user_settings import SETTINGS
from exceptions import BaseExceptionWithUIMessage, InvalidRangeOfWordsError, \
    ExcelAppOpenedError, NarrationError
from core import SheetScheme, ExcelParser, SheetToSchemeCompatibilityChecker, \
    WordsGetter, Dictation, DictationContent, Choice, AnswerCheckedResponse, Narrator


class AnswerCorrectness(Enum):
    CORRECT = 1
    INCORRECT = 2
    WITH_HINT = 3


class DictationRunControls(ft.Column):
    translation_label_text = "translation-label-text"
    dictation_completed_message = "dictation-completed-message"
    dictation_stopped_message = "dictation-stopped-message"
    answer_shown_instructions = "answer-shown-instructions"
    translation_text_template = "translation-text-template"
    instructions_text_template = "instructions-text-template"
    information_about_the_word_template = "information-about-the-word-template"
    no_information_message = "no-information-message"
    previous_word_label_first_message = "previous-word-label-first-message"
    additional_information_label_first_message = "additional-information-label-first-message"
    stop_dictation_button = "stop-dictation"
    show_answer_button = "show-answer"
    previous_word_information = "previous-word-information"
    current_word_information = "current-word-information"
    right_prompt = "right-prompt"
    wrong_prompt = "wrong-prompt"
    answer_shown_prompt = "answer-shown-prompt"

    def __init__(self, page: ft.Page, exit_dictation: Callable, block_width: int):
        SETTINGS.translate_widget(self.__class__)
        self.answer_correctness_relations = {
            AnswerCorrectness.CORRECT: [self.right_prompt, "green"],
            AnswerCorrectness.INCORRECT: [self.wrong_prompt, "red"],
            AnswerCorrectness.WITH_HINT: [self.answer_shown_prompt, "yellow"]
        }

        self.page = page
        self.exit_dictation = exit_dictation
        self.block_width = block_width

        self.page.on_keyboard_event = self.get_hint_through_keyboard

        self.synonyms_label = ft.Text(color=ft.colors.DEEP_PURPLE, size=15)
        self.variations_left_label = ft.Text(color="red", size=15)
        self.previous_word_label = ft.Text(
            self.previous_word_label_first_message,
            size=18
        )
        self.additional_information_label = ft.Text(
            self.additional_information_label_first_message,
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

        self.stop_dictation_button = ft.ElevatedButton(self.stop_dictation_button, on_click=self.stop_dictation_request)
        self.show_answer_button = ft.ElevatedButton(self.show_answer_button, on_click=self.show_answer)

        self.errors_label = ft.Text(color="red")

        self.previous_word_block_title = ft.Text(
            self.previous_word_information,
            style=ft.TextThemeStyle.TITLE_LARGE,
            text_align=ft.TextAlign.CENTER
        )

        self.current_word_block_title = ft.Text(
            self.current_word_information,
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
                              self.stop_dictation_button, self.errors_label]

        self.current_word_block_annotations = [self.translation_label, self.instructions_label,
                                               self.synonyms_label, self.variations_left_label,
                                               self.answer_correctness_indicator, self.hints_label,
                                               self.errors_label]

        self.inputs = [self.user_input, self.show_answer_button, self.stop_dictation_button]

        self.dictation, self.narrator = None, None
        self.awaiting_hint_typed, self.with_narration = False, False

        super().__init__(self.controls_list)
        self.set_width()

    def reload(self):
        self.previous_word_label.value = self.previous_word_label_first_message
        self.additional_information_label.value = self.additional_information_label_first_message
        for i in self.current_word_block_annotations:
            i.value = ""
        for i in self.inputs:
            i.disabled = False
        self.dictation = None,
        self.awaiting_hint_typed = False

    def set_width(self):
        for i in self.controls:
            i.width = self.block_width

    def get_hint_through_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "H" and e.ctrl is True:
            self.show_answer(e)

    def stop_dictation_request(self, e: ft.ControlEvent):
        self.dictation.stop()
        self.stop_dictation(self.dictation_stopped_message)

    def run_dictation(self, dictation_settings: tuple[bool, DictationContent]):
        self.disabled = False

        dictation_content = dictation_settings[1]
        self.with_narration = dictation_settings[0] and dictation_content.narration_possible
        if self.with_narration:
            self.narrator = Narrator(dictation_content.narration_language)
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
        initial_input = self.user_input.value
        answer_right = False
        if self.awaiting_hint_typed:
            self.awaiting_hint_typed = False
            self.hints_label.value = ""
            self.display_correctness_indicator(AnswerCorrectness.WITH_HINT)
        elif not res.is_right:
            self.display_correctness_indicator(AnswerCorrectness.INCORRECT, initial_input)
            self.user_input.focus()
            self.page.update()
            return
        else:
            answer_right = True
            self.display_correctness_indicator(AnswerCorrectness.CORRECT)

        self.display_previous_word(res)
        self.user_input.value = ""
        self.display_current_word()
        self.user_input.focus()
        self.page.update()
        if answer_right and self.with_narration:
            try:
                self.narrator.narrate(initial_input)
            except NarrationError as e:
                self.errors_label.value = e.message()

    def display_previous_word(self, word: AnswerCheckedResponse):
        self.variations_left_label.value = word.synonyms_left

        self.previous_word_label.value = word.other_variations
        information = self.no_information_message if word.info_to_given_word in ["nan", "n-", ""] else \
            self.information_about_the_word_template.format(word.info_to_given_word)
        self.additional_information_label.value = information

    def display_correctness_indicator(self, state: AnswerCorrectness, content: Union[str, bool] = False):
        scheme = self.answer_correctness_relations.get(state)
        s = scheme[0].format(content) if content else scheme[0]
        self.answer_correctness_indicator.value = s
        self.answer_correctness_indicator.color = scheme[1]

    def clear_labels(self):
        self.translation_label.value = ""
        self.instructions_label.value = ""

    def handle_excel_errors(self, e: ExcelAppOpenedError):
        self.errors_label.value = e.message()
        self.user_input.disabled = True
        self.show_answer_button.disabled = True
        self.stop_dictation_button.disabled = False

    def stop_dictation(self, message: str):
        try:
            self.dictation.stop()
        except ExcelAppOpenedError as e:
            self.handle_excel_errors(e)
            return
        self.clear_labels()
        self.disabled = True
        self.reload()
        self.exit_dictation()


class SchemeChoiceControls(ft.Column):
    schemes_key = "schemes"
    no_schemes_message = "no-schemes-message"
    scheme_choice_label = "scheme-choice-label"
    scheme_choice_hint_text = "scheme-choice-hint-text"

    def __init__(self, scheme_chosen_function: Callable):
        SETTINGS.translate_widget(self.__class__)
        self.schemes = SETTINGS.get(self.schemes_key)
        self.schemes_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(i) for i in self.schemes.keys()],
            on_change=lambda x: scheme_chosen_function(x.control.value),
            autofocus=True,

            label=self.scheme_choice_label,
            hint_text=self.scheme_choice_hint_text
        )

        self.no_schemes_label = ft.Text(color="red")
        self.no_schemes_label.visible = False

        self._check_for_schemes()
        self.controls_list = [self.schemes_dropdown, self.no_schemes_label]
        super().__init__(self.controls_list)

    def reload(self):
        self.schemes = SETTINGS.get(self.schemes_key)
        self.schemes_dropdown.value = ""
        self.schemes_dropdown.options = [ft.dropdown.Option(i) for i in self.schemes.keys()]
        self._check_for_schemes()
        self.update()

    def _check_for_schemes(self) -> bool:
        if self.schemes:
            self.schemes_dropdown.disabled = False
            self.no_schemes_label.visible = False
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
    range_choice_label = "range-choice-label"
    range_start_label = "range-start-label"
    range_end_label = "range-end-label"
    target_choice_label = "target-choice-label"
    target_choice_hint_text = "target-choice-hint-text"
    with_narration_label = "with-narration-label"
    shuffle_words_label = "shuffle-words-label"
    start_dictation_label = "start-dictation-label"

    def __init__(self, page: ft.Page, start_dictation_function: Callable):
        SETTINGS.translate_widget(self.__class__)
        self.page = page
        self.start_dictation_function = start_dictation_function

        self.sheet_processing_error_label = ft.Text(color="red")

        self.range_label = ft.Text(self.range_choice_label)
        self.range_start = ft.TextField(label=self.range_start_label, width=page.width // 8, keyboard_type=ft.KeyboardType.NUMBER)
        self.range_end = ft.TextField(label=self.range_end_label, width=page.width // 8, keyboard_type=ft.KeyboardType.NUMBER)

        self.range_controls = ft.Row(
            [self.range_label, self.range_start, self.range_end],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        )

        self.target_choice = ft.Dropdown(
            options=[ft.dropdown.Option(i) for i in self.target_states],
            label=self.target_choice_label,
            hint_text=self.target_choice_hint_text
        )
        self.target_choice.value = "NEW"

        self.with_narrator_checkbox = ft.Checkbox(label=self.with_narration_label)
        self.with_narrator_checkbox.value = True

        self.with_shuffle_checkbox = ft.Checkbox(label=self.shuffle_words_label)
        self.with_shuffle_checkbox.value = True

        self.start_dictation_button = ft.ElevatedButton(self.start_dictation_label, on_click=self.send_dictation_settings)

        self.error_with_chosen_settings_label = ft.Text(color="red")

        self.controls_list = [self.sheet_processing_error_label, self.range_controls, self.target_choice,
                              self.with_narrator_checkbox, self.with_shuffle_checkbox,
                              self.start_dictation_button,
                              self.error_with_chosen_settings_label]

        self.user_inputs = [self.range_start, self.range_end, self.target_choice]
        self.text_messages = [self.sheet_processing_error_label, self.error_with_chosen_settings_label]

        self.allowed_range: range = range(2, 2)
        self.sheet, self.scheme = None, None

        super().__init__(self.controls_list)

    def reload(self):
        for i in self.user_inputs:
            i.value = ""
            i.disabled = False
        self.target_choice.value = "NEW"
        self.with_narrator_checkbox.value = True
        self.with_shuffle_checkbox.value = True
        self.start_dictation_button.disabled = False
        for i in self.text_messages:
            i.value = ""
        self.sheet, self.scheme = None, None
        self.allowed_range = range(2, 2)

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
        self.sheet_processing_error_label.value = ""
        self.page.update()

    def fill_range(self, sheet: pd.DataFrame):
        self.allowed_range = range(2, sheet.shape[0] + 1)
        self.range_start.value = self.allowed_range.start
        self.range_end.value = self.allowed_range.stop

    def check_sheet_validity(self, sheet: pd.DataFrame, scheme: SheetScheme) -> bool:
        try:
            SheetToSchemeCompatibilityChecker(sheet, scheme).check_compatibility()
            return True
        except Exception as e:
            self.sheet_processing_error_label.value = e.message()
            self.disabled = True
            return False

    def process_inputs(self) -> tuple[range, str, bool, bool]:
        start, stop = int(self.range_start.value), int(self.range_end.value)
        input_range = range(start, stop)
        if start > stop or start < self.allowed_range.start or stop > self.allowed_range.stop:
            raise InvalidRangeOfWordsError(self.allowed_range.start, self.allowed_range.stop)
        return input_range, self.target_choice.value, \
               self.with_narrator_checkbox.value, self.with_shuffle_checkbox.value

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
            return self.start_dictation_function((with_narration, words))
        except BaseExceptionWithUIMessage as e:
            self.error_with_chosen_settings_label.value = e.message()
            self.page.update()


class DictationSettingsControls(ft.Column):
    no_vocabulary_path_set_message = "no-vocabulary-path-set-message"
    statuses_updated_message = "statuses-updated-message"
    dictation_settings_label = "dictation-settings-label"

    def __init__(self, page: ft.Page, send_words_function: Callable):
        SETTINGS.translate_widget(self.__class__)
        width = page.window_width // 3 - 20
        self.send_words_function = send_words_function
        self.no_vocabulary_path_set_label = ft.Text(color="red")
        self.section_label = ft.Text(self.dictation_settings_label, style=ft.TextThemeStyle.TITLE_LARGE)

        self.scheme_choice_controls = SchemeChoiceControls(self.fill_run_settings)
        if not SETTINGS.vocabulary_path_valid:
            self.scheme_choice_controls.disabled = True
            self.no_vocabulary_path_set_label.value = self.no_vocabulary_path_set_message

        self.dictation_run_settings_controls = DictationRunSettingsControls(page, self.start_dictation)
        self.dictation_run_settings_controls.disabled = True
        self.dictation_run_settings_controls.set_width(width)

        self.statues_updated_label = ft.Text(
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

    def show_statues_updated_message(self):
        self.statues_updated_label.value = self.statuses_updated_message
        self.statues_updated_label.visible = True

    def reload(self):
        self.scheme_choice_controls.reload()
        self.dictation_run_settings_controls.reload()

        if not SETTINGS.vocabulary_path_valid:
            self.scheme_choice_controls.disabled = True
            self.no_vocabulary_path_set_label.value = self.no_vocabulary_path_set_message
        else:
            self.scheme_choice_controls.disabled = False
            self.no_vocabulary_path_set_label.value = ""
        self.statues_updated_label.value = ""
        self.statues_updated_label.visible = False

        self.dictation_run_settings_controls.disabled = True
        self.sheet, self.scheme = None, None

    def fill_run_settings(self, scheme_name: str):
        self.scheme = SheetScheme(SETTINGS.schemes.get(scheme_name))
        sheet_name = self.scheme.sheet_name
        self.sheet = ExcelParser.get_sheet(sheet_name)
        self.dictation_run_settings_controls.fill_controls(self.sheet, self.scheme)
        self.update()

    def start_dictation(self, dictation_settings: tuple[bool, DictationContent]):
        self.send_words_function(dictation_settings)

    def set_width(self, width: int):
        for i in self.controls:
            i.width = width


class DictationControls(ft.Row):

    def __init__(self, page: ft.Page):
        self.page = page

        self.controls_list = [
            DictationSettingsControls(page, self.start_dictation),
            DictationRunControls(self.page, self.dictation_ended, self.page.window_width // 1.5 - 30)
        ]

        self.dictation_settings = self.controls_list[0]

        self.dictation = self.controls_list[1]
        self.dictation.disabled = True
        self.dictation.visible = False

        super().__init__(self.controls_list, alignment=ft.MainAxisAlignment.CENTER,
                         vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def start_dictation(self, dictation_settings: tuple[bool, DictationContent]):
        self.dictation_settings.disabled = True
        self.dictation_settings.visible = False

        self.dictation.visible = True
        self.dictation.disabled = False
        self.dictation.run_dictation(dictation_settings)
        self.update()

    def dictation_ended(self):
        self.reload()
        self.dictation_settings.show_statues_updated_message()
        self.update()

    def reload(self, external: bool = False):
        if external:
            self.visible = True
        if external and self.dictation.visible:
            return

        self.dictation.visible = False
        self.dictation.disabled = True

        self.dictation_settings.reload()
        self.dictation.reload()

        self.dictation_settings.disabled = False
        self.dictation_settings.visible = True