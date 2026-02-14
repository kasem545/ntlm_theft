#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_m3u(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """#EXTM3U
#EXTINF:1337, Leak
\\\\"""
        + server
        + """\\leak.mp3"""
    )
    file.close()
    print("Created: " + filename + " (OPEN IN WINDOWS MEDIA PLAYER ONLY)")
