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
