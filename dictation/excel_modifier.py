from typing import Literal, Iterable

import win32com.client as win32

from dictation.core import PATH_TO_VOCABULARY


class ExcelModifier:
    def __init__(self, worksheet_name: str, status_column_index: int) -> None:
        self.worksheet_name = worksheet_name
        self.status_column_index = status_column_index + 1
        self.excel = win32.gencache.EnsureDispatch("Excel.Application")
        self.workbook = self.excel.Workbooks.open(PATH_TO_VOCABULARY)
        self.worksheet = self.workbook.Worksheets(self.worksheet_name)

    def modify(self, status_to_give: Literal["NEEDS_REVISION", ], row_indexes: Iterable[int]) -> None:
        for i in row_indexes:
            self.worksheet.Cell(i+1, self.status_column_index).Value = status_to_give

    def commit(self) -> None:
        self.excel.Application.Quit()
