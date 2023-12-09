class SchemeExistsError(Exception):
    def __init__(self, scheme_name):
        self.scheme_name = scheme_name

    def message(self):
        return f"Scheme with the name `{self.scheme_name}` already exists. " \
               f"Give your scheme a different name."


class InvalidIndexesError(Exception):
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


class SheetNotFoundError(Exception):
    error_message = "The sheet name configured for that scheme is `{sheet_name}`, " \
                    "but that sheet is not present in the file `{file_path}`."

    def __init__(self, sheet_name: str, file_path: str) -> None:
        self.sheet_name = sheet_name
        self.file_path = file_path

    def message(self) -> str:
        return self.error_message.format(sheet_name=self.sheet_name, file_path=self.file_path)
