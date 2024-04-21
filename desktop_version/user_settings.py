import os

from ast import literal_eval
from json import loads


class Settings(dict):
    settings_filename = "settings.txt"
    vocabulary_key = "PATH_TO_VOCABULARY"
    schemes_key = "schemes"
    app_language_key = "APP_LANGUAGE"
    path_to_languages = "languages/"

    def __init__(self):
        with open(self.settings_filename, mode="r", encoding="utf-8") as file:
            settings_dict = literal_eval(file.read())
        super().__init__(settings_dict)
        self.app_language = self.get(self.app_language_key, "english")
        self.app_text = self.get_app_text(self.app_language)

    def get_app_text(self, app_language: str) -> dict:
        filename = os.path.join(self.path_to_languages, app_language+".json")
        if not os.path.exists(filename):
            raise

        with open(filename, mode="r", encoding="utf-8") as file:
            return loads(file.read())

    def change_settings(self, key, value) -> None:
        self[key] = value
        with open(self.settings_filename, mode="w", encoding="utf-8") as file:
            file.write(str(self))

    @property
    def schemes(self) -> dict:
        return self.get(self.schemes_key, {})

    @property
    def path(self) -> str:
        return self.get(self.vocabulary_key, "")

    @property
    def vocabulary_path_valid(self) -> bool:
        path = self.get(self.vocabulary_key, "")
        if os.path.exists(path) and path.rsplit(".", maxsplit=1)[-1] == "xlsx":
            return True
        return False

    def get_text(self, class_key: str, message_key: str) -> str:
        return self.app_text.get(class_key, {message_key: message_key}).get(message_key, message_key)

    def translate_widget(self, widget) -> None:
        for i in dir(widget):
            t = getattr(widget, i)
            if isinstance(t, str) and i != "__module__":
                setattr(widget, i, self.get_text(widget.__name__, t))


SETTINGS = Settings()
