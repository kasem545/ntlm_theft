#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from ntlm_theft.files.scf import create_scf
from ntlm_theft.files.bat import create_bat
from ntlm_theft.files.url import create_url_url, create_url_icon
from ntlm_theft.files.lnk import create_lnk
from ntlm_theft.files.rtf import create_rtf
from ntlm_theft.files.xml import create_xml, create_xml_includepicture
from ntlm_theft.files.htm import create_htm, create_htm_handler
from ntlm_theft.files.docx import (
    create_docx_includepicture,
    create_docx_remote_template,
    create_docx_frameset,
)
from ntlm_theft.files.xlsx import create_xlsx_externalcell
from ntlm_theft.files.wax import create_wax
from ntlm_theft.files.m3u import create_m3u
from ntlm_theft.files.asx import create_asx
from ntlm_theft.files.jnlp import create_jnlp
from ntlm_theft.files.application import create_application
from ntlm_theft.files.pdf import create_pdf
from ntlm_theft.files.zoom import create_zoom
from ntlm_theft.files.theme import create_theme
from ntlm_theft.files.autorun import create_autoruninf
from ntlm_theft.files.desktop import create_desktopini
from ntlm_theft.files.libraryms import create_new_libraryms, create_legacy_libraryms
from ntlm_theft.files.odt import create_odt_ntlm_leak

__all__ = [
    "script_directory",
    "create_scf",
    "create_bat",
    "create_url_url",
    "create_url_icon",
    "create_lnk",
    "create_rtf",
    "create_xml",
    "create_xml_includepicture",
    "create_htm",
    "create_htm_handler",
    "create_docx_includepicture",
    "create_docx_remote_template",
    "create_docx_frameset",
    "create_xlsx_externalcell",
    "create_wax",
    "create_m3u",
    "create_asx",
    "create_jnlp",
    "create_application",
    "create_pdf",
    "create_zoom",
    "create_theme",
    "create_autoruninf",
    "create_desktopini",
    "create_new_libraryms",
    "create_legacy_libraryms",
    "create_odt_ntlm_leak",
]
