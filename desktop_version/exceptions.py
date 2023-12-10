from abc import ABC, abstractmethod


class BaseExceptionWithUIMessage(Exception, ABC):
    @abstractmethod
    def message(self) -> str:
        """Should return a string that will be displayed to the user in a label."""


class SchemeExistsError(BaseExceptionWithUIMessage):
    error_message = "Scheme with the name `{scheme_name}` already exists. " \
                    "Give your scheme a different name."

    def __init__(self, scheme_name: str) -> None:
        self.scheme_name = scheme_name

    def message(self):
        return self.error_message.format(self.scheme_name)


class InvalidIndexesError(BaseExceptionWithUIMessage):
    error_messages = ["Indexes of translation and status columns must be unique.",
                      "Indexes of word and information columns must not be the same."]

    def __init__(self, indexes: list[int, int, int, int]) -> None:
        self.translation_index, self.status_index, self.word_index, self.info_index = indexes

    def message(self) -> str:
        if self.translation_index == self.status_index or self.translation_index == self.word_index \
                or self.translation_index == self.info_index or self.status_index == self.word_index or \
                self.status_index == self.word_index:
            return self.error_messages[0]
        return self.error_messages[1]


class SheetNotFoundError(BaseExceptionWithUIMessage):
    error_message = "The sheet name configured for that scheme is `{sheet_name}`, " \
                    "but that sheet is not present in the file `{file_path}`."

    def __init__(self, sheet_name: str, file_path: str) -> None:
        self.sheet_name = sheet_name
        self.file_path = file_path

    def message(self) -> str:
        return self.error_message.format(sheet_name=self.sheet_name, file_path=self.file_path)


class VocabularyFileNotFoundError(BaseExceptionWithUIMessage):
    error_message = "File with vocabulary at the path: `{file_path}` was not found."

    def __init__(self, file_path: str):
        self.file_path = file_path

    def message(self) -> str:
        return self.error_message.format(file_path=self.file_path)


class InvalidSchemeError(Exception):
    error_message = "The selected scheme does not fit the sheet. Sheet name: `{sheet_name}`. \n" \
                    "Please check that the sheet has all the columns specified in the scheme."

    def __init__(self, sheet_name: str) -> None:
        self.sheet_name = sheet_name

    def message(self) -> str:
        return self.error_message.format(sheet_name=self.sheet_name)


class InvalidStatusError(BaseExceptionWithUIMessage):
    error_message = "An error occurred while processing the statuses in the status " \
                    "column of the sheet: `{sheet_name}`. \n" \
                    "Status column index was `{status_column_index}`; \n" \
                    "Status that caused the error was `{status}` (on line `{line_index}`); \n" \
                    "Check that the status name is allowed and that it has the index of power(must be greater than 0)."

    def __init__(self, sheet_name: str, status_column_index: int, status: str, error_line_index: int):
        self.formatted_message = self.error_message.format(
            sheet_name=sheet_name,
            status_column_index=status_column_index,
            status=status,
            line_index=error_line_index
        )

    def message(self) -> str:
        return self.formatted_message


class InvalidRangeOfWordsError(BaseExceptionWithUIMessage):
    error_message = "The range you specified is invalid.\n" \
                    "Your range must be a subrange of range [{start}, {end}] to be valid."

    def __init__(self, start: int, end: int):
        self.formatted_message = self.error_message.format(start=start, end=end)

    def message(self) -> str:
        return self.formatted_message
