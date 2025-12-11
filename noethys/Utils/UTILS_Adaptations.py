#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS, JB
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import sys
from importlib import import_module


def Import(nom_module=""):
    # Essaye d'importer
    try :
        module = import_module(nom_module)
        return module
    except ImportError:
        pass

    # Recherche si le module est déjà chargé
    if nom_module in sys.modules:
        module = sys.modules[nom_module]
        return module

    # Essaye d'importer sans le module_path
    module_path, class_name = nom_module.rsplit('.', 1)
    try :
        module = import_module(class_name)
        return module
    except ImportError:
        pass

    return None

import wx
import warnings

class Menu(wx.Menu):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def AppendItem(self, item):
        super().Append(item)

    def AppendMenu(self, *args, **kwds):
        # Old style: (id, text, submenu)
        if len(args) >= 3 and isinstance(args[0], int) and isinstance(args[2], wx.Menu):
            _id, text, submenu = args[:3]
            warnings.warn(
                "\nLa forme AppendMenu(id, text, submenu) est obsolète\n"
                f"Modifier en: AppendMenu(submenu, text) dans module Parent",
                DeprecationWarning,
                stacklevel=2
            )
            return super().AppendSubMenu(submenu, text, **kwds)

        # New style: (submenu, text)
        elif len(args) >= 2 and isinstance(args[0], wx.Menu):
            submenu, text = args[:2]
            return super().AppendSubMenu(submenu, text, **kwds)

        else:
            raise TypeError("Unsupported arguments for AppendMenu")

class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        wx.ToolBar.__init__(self, *args, **kwds)

    def AddLabelTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            super(ToolBar, self).AddTool(*args, **kw)
        else :
            super(ToolBar, self).AddLabelTool(*args, **kw)

    def AddSimpleTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            super(ToolBar, self).AddTool(*args, **kw)
        else :
            super(ToolBar, self).AddSimpleTool(*args, **kw)


if __name__ == "__main__":
    pass