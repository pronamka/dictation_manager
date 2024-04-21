import os

from typing import Callable

import flet as ft

from user_settings import SETTINGS


class TutorialWindow(ft.Column):
    path_to_tutorials = {
        "quick_start": "tutorials/quick_start/",
        "statuses": "tutorials/statuses/",
        "synonyms_and_variations": "tutorials/synonyms_and_variations/"
    }
    text_file_names = {
        "quick_start": "text.txt",
        "statuses": "text.txt",
        "synonyms_and_variations": "text.txt"
    }
    blocks_separator = "AAA"
    allowed_languages = ["english", "russian"]

    def __init__(self, page: ft.Page, tutorial_name: str) -> None:
        self.tutorial_name = tutorial_name
        self.language = "english" if SETTINGS.app_language not in self.allowed_languages else SETTINGS.app_language
        self.path_to_tutorial = self.path_to_tutorials.get(tutorial_name)+self.language+"/"
        self.text_file_name = self.text_file_names.get(tutorial_name)

        with open(self.path_to_tutorial + self.text_file_name, mode="r", encoding="utf-8") as file:
            self.text_blocks = [ft.Text(i, size=20, overflow=ft.TextOverflow.CLIP, selectable=True) for i in
                                file.read().split(self.blocks_separator)]

        self.image_blocks = []
        for i in os.listdir(self.path_to_tutorial):
            if i.rsplit(".")[-1] == "png":
                self.image_blocks.append(ft.Image(
                    self.path_to_tutorial + i,
                    width=page.width // 3 * 2,
                ))

        self.blocks = []
        for text, image in zip(self.text_blocks, self.image_blocks):
            self.blocks.append(text)
            self.blocks.append(image)

        self.blocks.append(self.text_blocks[-1])

        super().__init__(
            scroll=ft.ScrollMode.ALWAYS,
            controls=self.blocks,
            height=page.height - 100
        )
        self.width = page.width // 3 * 2 - 40


class NavigationSideBarDestination(ft.TextButton):
    def __init__(self, text: str, navigation_function: Callable, width: int) -> None:
        super().__init__(
            text=text,
            on_click=navigation_function,
            width=width,
            height=40
        )


class NavigationSideBar(ft.Column):
    """
    quick start
    word statuses
    synonyms and word variations
    """
    destination_start = "destination-start"
    destination_statuses = "destination-statuses"
    destination_synonyms = "destination-synonyms"

    def __init__(self, navigation_function: Callable, width):
        SETTINGS.translate_widget(self.__class__)
        super(NavigationSideBar, self).__init__(
            [
                NavigationSideBarDestination(self.destination_start, lambda x: navigation_function("quick_start"), width-20),
                NavigationSideBarDestination(self.destination_statuses, lambda x: navigation_function("statuses"),width-20),
                NavigationSideBarDestination(self.destination_synonyms,
                                             lambda x: navigation_function("synonyms_and_variations"), width-20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )


class HelpWindow(ft.Container):
    def __init__(self, page: ft.Page):
        self.right_container = ft.Container(
            NavigationSideBar(self.go_to, page.window_width),
            width=page.window_width//4
        )
        self.left_container = ft.Container(
            content=TutorialWindow(page, "quick_start"),
            expand=True,
            margin=0,
            padding=0,
            bgcolor=ft.colors.LIGHT_BLUE_50,
            border_radius=10,
            alignment=ft.alignment.top_center,

        )

        self.navigation_routes = {
            "quick_start": "quick_start",
            "word_statuses": "statuses",
            "synonyms_and_variations": "synonyms_and_variations",

        }

        super().__init__(
            ft.Row([self.right_container, self.left_container],expand=True,height=page.height-80)
        )

    def go_to(self, destination: str):
        self.left_container.content = TutorialWindow(self.page, destination)
        self.update()

    def reload(self, external: bool = False):
        if external:
            self.visible = True
