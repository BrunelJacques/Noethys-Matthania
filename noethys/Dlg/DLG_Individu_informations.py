#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Utilisateurs
from Ctrl import CTRL_Informations
from Ol import OL_Contrats

class Panel(wx.Panel):
    def __init__(self, parent, IDindividu=None, dictFamillesRattachees={}):
        wx.Panel.__init__(self, parent, id=-1, name="panel_Contrats",
                          style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.module = "DLG_Individu_informations.Panel"
        self.IDindividu = IDindividu
        self.dictFamillesRattachees = dictFamillesRattachees

        # Contrats
        self.staticbox_contrats = wx.StaticBox(self, -1, _("Contrats"))
        self.ctrl_contrats = OL_Contrats.ListView(self, IDindividu=IDindividu,
                                                  dictFamillesRattachees=self.dictFamillesRattachees,
                                                  id=-1, name="OL_contrats",
                                                  style=wx.LC_HRULES | wx.LC_VRULES | wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL)
        self.ctrl_contrats.SetMinSize((150, 90))

        self.bouton_ajouter_contrat = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_contrat = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_contrat = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Ajouter, self.bouton_ajouter_contrat)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Modifier, self.bouton_modifier_contrat)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Supprimer, self.bouton_supprimer_contrat)

        # Propriétés
        self.bouton_ajouter_contrat.SetToolTip(wx.ToolTip(_("Cliquez ici pour créer un contrat pour cet individu")))
        self.bouton_modifier_contrat.SetToolTip(wx.ToolTip(_("Cliquez ici pour modifier le contrat sélectionné")))
        self.bouton_supprimer_contrat.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer le contrat sélectionné")))


        # Contrats layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        staticbox_contrats = wx.StaticBoxSizer(self.staticbox_contrats, wx.VERTICAL)
        grid_sizer_contrats = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        grid_sizer_contrats.Add(self.ctrl_contrats, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=7, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter_contrat, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier_contrat, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer_contrat, 0, wx.ALL, 0)
        grid_sizer_contrats.Add(grid_sizer_boutons, 1, wx.ALL, 0)

        grid_sizer_contrats.AddGrowableCol(0)
        grid_sizer_contrats.AddGrowableRow(0)
        staticbox_contrats.Add(grid_sizer_contrats, 1, wx.EXPAND | wx.ALL, 5)

        grid_sizer_base.Add(staticbox_contrats, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.ctrl_contrats.MAJ()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel, IDindividu=27)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _("TEST"), size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()