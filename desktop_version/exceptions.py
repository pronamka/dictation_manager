from abc import ABC, abstractmethod

from user_settings import SETTINGS


class BaseExceptionWithUIMessage(Exception, ABC):
    error_message = "error-message"

    def __init__(self):
        SETTINGS.translate_widget(self.__class__)

    @abstractmethod
    def message(self) -> str:
        """Should return a string that will be displayed to the user in a label."""


class SchemeExistsError(BaseExceptionWithUIMessage):
    def __init__(self, scheme_name: str) -> None:
        super().__init__()
        self.scheme_name = scheme_name

    def message(self):
        return self.error_message.format(scheme_name=self.scheme_name)


class InvalidIndexesError(BaseExceptionWithUIMessage):
    def __init__(self, indexes: list[int, int, int, int]) -> None:
        super().__init__()
        self.translation_index, self.status_index, self.word_index, self.info_index = indexes

    def message(self) -> str:
        if self.translation_index == self.status_index or self.translation_index == self.word_index \
                or self.translation_index == self.info_index or self.status_index == self.word_index or \
                self.status_index == self.word_index:
            return self.error_message[0]
        return self.error_message[1]


class SheetNotFoundError(BaseExceptionWithUIMessage):
    def __init__(self, sheet_name: str, file_path: str) -> None:
        super().__init__()
        self.sheet_name = sheet_name
        self.file_path = file_path

    def message(self) -> str:
        return self.error_message.format(sheet_name=self.sheet_name, file_path=self.file_path)


class VocabularyFileNotFoundError(BaseExceptionWithUIMessage):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def message(self) -> str:
        return self.error_message.format(file_path=self.file_path)


class InvalidSchemeError(BaseExceptionWithUIMessage):
    def __init__(self, sheet_name: str) -> None:
        super().__init__()
        self.sheet_name = sheet_name

    def message(self) -> str:
        return self.error_message.format(sheet_name=self.sheet_name)


class InvalidStatusError(BaseExceptionWithUIMessage):
    def __init__(self, sheet_name: str, status_column_index: int, status: str, error_line_index: int):
        super().__init__()
        self.formatted_message = self.error_message.format(
            sheet_name=sheet_name,
            status_column_index=status_column_index,
            status=status,
            line_index=error_line_index
        )

    def message(self) -> str:
        return self.formatted_message


class InvalidRangeOfWordsError(BaseExceptionWithUIMessage):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.formatted_message = self.error_message.format(start=start, end=end)

    def message(self) -> str:
        return self.formatted_message


class NoWordsMatchingSettings(BaseExceptionWithUIMessage):
    def __init__(self, status: str, range_start: int, range_stop: int) -> None:
        super().__init__()
        self.formatted_message = self.error_message.format(status=status, range_start=range_start,
                                                           range_stop=range_stop)

    def message(self) -> str:
        return self.formatted_message


class ExcelAppOpenedError(BaseExceptionWithUIMessage):
    def __init__(self):
        super().__init__()

    def message(self) -> str:
        return self.error_message


class NarrationError(BaseExceptionWithUIMessage):
    def __init__(self):
        super().__init__()

    def message(self) -> str:
        return self.error_message
