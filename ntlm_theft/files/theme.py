#!/usr/bin/env python
# -*- coding: utf-8 -*-


def create_theme(generate, server, filename):
    with open(filename, "w") as file:
        file.write(
            """[Theme]
; Windows - IDS_THEME_DISPLAYNAME_AERO_LIGHT
DisplayName=\\"""
            + server
            + """ Theme
SetLogonBackground=0
; Computer - SHIDI_SERVER
[CLSID\\{20D04FE0-3AEA-1069-A2D8-08002B30309D}\\DefaultIcon]
DefaultValue=\\\\"""
            + server
            + """\\setup.exe,-109

; UsersFiles - SHIDI_USERFILES
[CLSID\\{59031A47-3F72-44A7-89C5-5595FE6B30EE}\\DefaultIcon]
DefaultValue=\\\\"""
            + server
            + """\\setup.exe,-123

; Network - SHIDI_MYNETWORK
[CLSID\\{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}\\DefaultIcon]
DefaultValue=\\\\"""
            + server
            + """\\setup.exe,-25

; Recycle Bin - SHIDI_RECYCLERFULL SHIDI_RECYCLER
[CLSID\\{645FF040-5081-101B-9F08-00AA002F954E}\\DefaultIcon]
Full=\\\\"""
            + server
            + """\\setup.exe,-54
Empty=\\\\"""
            + server
            + """\\setup.exe,-55

[Control Panel\\Cursors]
AppStarting=\\\\"""
            + server
            + """\\setup.exe
Arrow=\\\\"""
            + server
            + """\\aero_arrow.cur
Crosshair=
Hand=\\\\"""
            + server
            + """\\aero_link.cur
Help=\\\\"""
            + server
            + """\\aero_helpsel.cur
IBeam=
No=\\\\"""
            + server
            + """\\aero_unavail.cur
NWPen=\\\\"""
            + server
            + """\\aero_pen.cur
SizeAll=\\\\"""
            + server
            + """\\aero_move.cur
SizeNESW=\\\\"""
            + server
            + """\\aero_nesw.cur
SizeNS=\\\\"""
            + server
            + """\\aero_ns.cur
SizeNWSE=\\\\"""
            + server
            + """\\aero_nwse.cur
SizeWE=\\\\"""
            + server
            + """\\aero_ew.cur
UpArrow=\\\\"""
            + server
            + """\\aero_up.cur
Wait=\\\\"""
            + server
            + """\\aero_busy.ani
DefaultValue=Windows Default
DefaultValue.MUI=@main.cpl,-1020

[Control Panel\\Desktop]
Wallpaper=\\\\"""
            + server
            + """\\setup.exe
TileWallpaper=0
WallpaperStyle=10
Pattern=
MultimonBackgrounds=0

[VisualStyles]
Path=\\\\"""
            + server
            + """\\Themes\\Aero\\Aero.msstyles
ColorStyle=NormalColor
Size=NormalSize
AutoColorization=0
ColorizationColor=0XC40078D4
SystemMode=Light
AppMode=Light

[boot]
SCRNSAVE.EXE=

[MasterThemeSelector]
MTSM=RJSPBS

[Sounds]
; IDS_SCHEME_DEFAULT
SchemeName=@\\\\"""
            + server
            + """\\setup.dll,-800
		"""
        )
    print("Created: " + filename + " (THEME TO INSTALL")
