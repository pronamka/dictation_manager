import os

from typing import Callable

import flet as ft


class QuickStartWindow(ft.Column):
    path_to_tutorial = "tutorials/quick_start/"
    text_file_name = "quick_start_text.txt"
    blocks_separator = "AAA"

    def __init__(self, page: ft.Page):
        with open(self.path_to_tutorial + self.text_file_name, mode="r") as file:
            self.text_blocks = [ft.Text(i, size=20, overflow=ft.TextOverflow.CLIP) for i in
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
            height=page.height-100
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

    def __init__(self, navigation_function: Callable, width):
        super(NavigationSideBar, self).__init__(
            [
                NavigationSideBarDestination("Quick Start", lambda x: navigation_function("quick_start"), width-20),
                NavigationSideBarDestination("Word Statuses", lambda x: navigation_function("word_statuses"),width-20),
                NavigationSideBarDestination("Synonyms and word variations",
                                             lambda x: navigation_function("synonyms_and_variations"), width-20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )


class HelpWindow(ft.Container):
    def __init__(self, page: ft.Page):
        right_container = ft.Container(
            NavigationSideBar(lambda x: ..., page.window_width),
            width=page.window_width//4
        )
        left_container = ft.Container(
            QuickStartWindow(page),
            expand=True,
            margin=0,
            padding=0,
            bgcolor=ft.colors.LIGHT_BLUE_50,
            border_radius=10,
            alignment=ft.alignment.top_center,

        )

        self.navigation_routes = {
            "quick_start": left_container,
            "word_statuses": ft.Column(),
            "synonyms_and_variations": ft.Column(),

        }

        super().__init__(
            ft.Row([right_container, left_container],expand=True,height=page.height)
        )

    def go_to(self, destination: str):
        for i in self.navigation_routes.values():
            i.visible = False
        destination_object = self.navigation_routes.get(destination)
        destination_object.visible = True

    def reload(self, external: bool = False):
        if external:
            self.visible = True
