#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_desktopini(generate, server, filename):
    if generate == "modern":
        print("Skipping desktop.ini as it does not work on modern Windows")
        return
    file = open(filename, "w")
    file.write(
        """[.ShellClassInfo]
IconResource=\\\\"""
        + server
        + """\\aa"""
    )
    file.close()
    print("Created: " + filename + " (BROWSE TO FOLDER)")
