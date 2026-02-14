#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_bat(generate, server, filename):
    with open(filename, "w") as file:
        file.write(f'@echo off\nstart "" "\\\\{server}\\share"\n')
    print("Created: " + filename + " (BROWSE TO FOLDER)")
