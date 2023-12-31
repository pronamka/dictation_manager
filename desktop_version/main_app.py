from typing import Callable, Union

import flet as ft

from desktop_version.dictation_window import DictationControls
from desktop_version.file_window import PathToVocabularyControls
from desktop_version.scheme_managing_window import SchemeManagingControls
from desktop_version.help_window import HelpWindow


class NavigationBarLabel(ft.Text):
    def __init__(self, text: str, on_click_function: Union[Callable, None] = None):
        spans = [
                ft.TextSpan(
                    text[0],
                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                ),
                ft.TextSpan(
                    text[1:],
                ),
            ]
        if on_click_function:
            for i in spans:
                i.on_click = lambda x: on_click_function()

        super(NavigationBarLabel, self).__init__(
            disabled=False,
            size=18,
            spans=spans,
        )


class MenuBar(ft.Row):
    def __init__(self, navigation_function: Callable):
        self.dictation_window_button = NavigationBarLabel(
            "Dictation",
            lambda: navigation_function("dictation")
        )

        self.scheme_managing_popup = ft.PopupMenuButton(
            content=NavigationBarLabel(
                "Schemes",
                None,
            ),
            items=[
                ft.PopupMenuItem(
                    text="Scheme Creation",
                    on_click=lambda x: navigation_function("scheme_creation")
                ),

                ft.PopupMenuItem(
                    text="Scheme Deletion",
                    on_click=lambda x: navigation_function("scheme_deletion")
                ),
            ],
        )

        """ft.PopupMenuItem(
                    text="Scheme Alteration",
                    on_click=lambda x: navigation_function("scheme_alteration")
                ),"""

        self.vocabulary_path_window_button = NavigationBarLabel(
            "File",
            lambda: navigation_function("file")
        )

        self.help_window_button=NavigationBarLabel(
            "Help",
            lambda: navigation_function("help")
        )

        self.controls_list = [self.vocabulary_path_window_button, self.dictation_window_button,
                              self.scheme_managing_popup, self.help_window_button]

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
        self.page.scroll = "always"
        self.page.window_resizable = False
        self.page.window_max_width = self.page.width
        self.page.window_max_height = self.page.height
        self.page.window_center()
        self.page.on_window_event = self.process_window_event

        self.page_menu = MenuBar(self.window_changed)

        self.dictation_controls = DictationControls(self.page)
        self.schemes = SchemeManagingControls(self.page)
        self.vocabulary_path_controls = PathToVocabularyControls(self.page.window_width)

        self.dictation_controls.visible = True
        self.schemes.visible = False
        self.vocabulary_path_controls.visible = False

        self.help = HelpWindow(self.page)
        self.help.visible = False

        self.navigation_routes = {
            "file": (self.vocabulary_path_controls, lambda x: ...),
            "dictation": (self.dictation_controls, lambda x: ...),
            "scheme": (self.schemes, lambda x: (self.schemes.go_to(x))),
            "help": (self.help, lambda x: ...)
        }

        self.current_page_name = ft.Text("Dictation", size=30)
        self.bar = ft.Container(
            ft.Row(
                controls=[ft.Icon(ft.icons.WORK), self.page_menu],
                spacing=20
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=10,
        )

        self.controls_list = ft.Column([
            self.bar,
            self.dictation_controls,
            self.schemes,
            self.vocabulary_path_controls,
            self.help
        ], )

        page.add(self.controls_list)
        self.page.update()

    def window_changed(self, destination: str):
        general_destination = destination.split("_")[0]
        for i in self.navigation_routes.values():
            i[0].visible = False
        destination_object = self.navigation_routes.get(general_destination)
        destination_object[0].reload(external=True)
        destination_object[1](destination)
        self.page.update()


def main(page: ft.Page):
    MainPage(page)


if __name__ == "__main__":
    ft.app(target=main)
