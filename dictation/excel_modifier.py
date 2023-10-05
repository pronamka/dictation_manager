import shutil

from typing import Literal, Iterable

import win32com.client as win32

from dictation.core import PATH_TO_VOCABULARY


class StringConstants:
    needs_revision = "NEEDS_REVISION"
    needs_revision_status = "NEEDS_REVISION*{}"


class ST:
    nrs = "NEEDS_REVISION*{}"
    nws = "NEW*{}"
    nmo = "NORMAL*1"


class ExcelModifier:
    path_to_gen_py = "C:/Users/Yuriy/AppData/Local/Temp/gen_py"

    default_repetitions_amount = 2

    status_changes = {
        ("NEEDS_REVISION", "NEEDS_REVISION"): lambda ra: ST.nrs.format(ra + 1),
        ("NEEDS_REVISION", "NORMAL"): lambda ra: ST.nrs.format(ra - 1) if ra - 1 else ST.nmo,
        ("NORMAL", "NEEDS_REVISION"): lambda ra: ST.nrs.format(2),
        ("NEW", "NEEDS_REVISION"): lambda ra: ST.nws.format(ra) if ra > 1 else ST.nrs.format(ra + 1),
        ("NEW", "NORMAL"): lambda ra: ST.nws.format(ra - 1) if ra - 1 else ST.nmo,
        ("NORMAL", "NORMAL"): lambda ra: ST.nmo,
    }

    def __init__(self, worksheet_name: str, status_column_index: int) -> None:
        self.worksheet_name = worksheet_name
        self.status_column_index = status_column_index + 1
        self.excel = self.open_excel()
        self.workbook = self.excel.Workbooks.Open(PATH_TO_VOCABULARY)
        self.worksheet = self.workbook.Worksheets(self.worksheet_name)

    def open_excel(self):
        try:
            return win32.gencache.EnsureDispatch("Excel.Application")
        except AttributeError:
            self.handle_excel_error()
            return win32.gencache.EnsureDispatch("Excel.Application")

    def handle_excel_error(self) -> None:
        shutil.rmtree(self.path_to_gen_py)

    def modify(
            self,
            status_to_give: Literal["NEEDS_REVISION", "NORMAL"],
            row_indexes: Iterable[int]
    ) -> None:
        for i in row_indexes:
            self.worksheet.Cells(i+2, self.status_column_index).Value = self.check_current_status(status_to_give, i)

    def check_current_status(self, status_to_give, row_index) -> str:
        status = self.worksheet.Cells(row_index+2, self.status_column_index).Value.split("*")
        new_status = self.status_changes.get((status[0], status_to_give))(int(status[1]))
        return new_status

    def commit(self) -> None:
        self.workbook.Save()
        self.excel.Application.Quit()
