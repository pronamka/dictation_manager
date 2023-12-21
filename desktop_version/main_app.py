from typing import Callable

import flet as ft

from desktop_version.dictation_window import DictationControls
from desktop_version.file_window import PathToVocabularyControls
from desktop_version.scheme_managing_window import SchemeManagingControls


class MenuBar(ft.Row):
    def __init__(self, navigation_function: Callable):
        self.dictation_window_button = ft.Text(
            disabled=False,
            spans=[
                ft.TextSpan(
                    "D",
                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    on_click=lambda x: navigation_function("dictation")
                ),
                ft.TextSpan(
                    "ictation",
                    on_click=lambda x: navigation_function("dictation")
                ),
            ],
            size=18,
            data="dictation"
        )

        self.scheme_managing_popup = ft.PopupMenuButton(
            content=ft.Text(
                disabled=False,
                spans=[
                    ft.TextSpan(
                        "S",
                        ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    ),
                    ft.TextSpan(
                        "chemes"
                    )
                ],
                size=18),
            items=[
                ft.PopupMenuItem(
                    text="Scheme Creation",
                    on_click=lambda x: navigation_function("scheme_creation")
                ),
                ft.PopupMenuItem(
                    text="Scheme Alteration",
                    on_click=lambda x: navigation_function("scheme_alteration")
                ),
                ft.PopupMenuItem(
                    text="Scheme Deletion",
                    on_click=lambda x: navigation_function("scheme_deletion")
                ),
            ],
        )
        self.vocabulary_path_window_button = ft.Text(
            disabled=False,
            spans=[
                ft.TextSpan(
                    "F",
                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    on_click=lambda x: navigation_function("file")
                ),
                ft.TextSpan(
                    "ile",
                    on_click=lambda x: navigation_function("file")
                ),
            ],
            size=18,
        )

        self.controls_list = [self.vocabulary_path_window_button, self.dictation_window_button,
                              self.scheme_managing_popup]

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

        self.dictation_controls = DictationControls(self.dictation_reload, self.page)
        self.schemes = SchemeManagingControls(self.scheme_managing_reload, self.page)
        self.vocabulary_path_controls = PathToVocabularyControls(self.vocabulary_path_reload)
        self.dictation_controls.visible = True
        self.schemes.visible = False
        self.vocabulary_path_controls.visible = False

        self.navigation_routes = {
            "file": (self.vocabulary_path_controls, lambda x: (self.vocabulary_path_controls.__setattr__("visible", True))),
            "dictation": (self.dictation_controls, lambda x: (self.dictation_controls.__setattr__("visible", True))),
            "scheme": (self.schemes, lambda x: (self.schemes.go_to(x))),
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

    def window_changed(self, destination: str):
        general_destination = destination.split("_")[0]
        for i in self.navigation_routes.values():
            i[0].visible = False
        destination_object = self.navigation_routes.get(general_destination)
        destination_object[1](destination)
        self.page.update()


def main(page: ft.Page):
    MainPage(page)


if __name__ == "__main__":
    ft.app(target=main)
