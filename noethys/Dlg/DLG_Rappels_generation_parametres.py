#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania approche des paramétres par sélection des dûs clients globaux
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques BRUNEL
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import datetime
import wx.lib.agw.hyperlink as Hyperlink
import GestionDB

from Ctrl import CTRL_Liste_rappels

# ---------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Lot_rappels(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.MAJ()
        self.Select(0)

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else :
            self.Enable(True)
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDlot, nom
        FROM lots_rappels
        ORDER BY IDlot;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = [_("Aucun lot"),]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : _("Inconnue")}
        index = 1
        for IDlot, nom in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDlot, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout" :
            self.parent.ctrl_rappels.CocheTout()
        if self.URL == "rien" :
            self.parent.ctrl_rappels.CocheRien()
        self.UpdateLink()

class Panel_rappels(wx.Panel):
    def __init__(self, parent, filtres=[], IDcompte_payeur=None, checkColonne = True, triColonne = "solde"):
        wx.Panel.__init__(self, parent, id=-1, name="DLG_Rappels_generation_selection.panel_rappel", style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Liste des rappels
        self.ctrl_rappels = CTRL_Liste_rappels.CTRL(self, filtres=filtres)
        self.ctrl_rappels.MAJ()
        self.ctrl_rappels.bouton_apercu.Enable(False)
        self.ctrl_rappels.bouton_email.Enable(False)
        self.ctrl_rappels.bouton_supprimer.Enable(False)
        #self.ctrl_recherche = OL_Rappels.CTRL_Outils(self, listview=self.ctrl_rappels)

        # Options de liste
        #self.ctrl_recherche = OL_Rappels.BarreRecherche(self, listview=self.ctrl_rappels)

        self.__do_layout()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)

        grid_sizer_liste = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_liste.Add(self.ctrl_rappels, 1, wx.EXPAND, 0)

        grid_sizer_liste.AddGrowableRow(0)
        grid_sizer_liste.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_liste, 1, wx.EXPAND, 0)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def GetTracksCoches(self):
        return self.ctrl_rappels.GetTracksCoches()

    def MAJ(self):
        self.ctrl_rappels.MAJ()

    def SetFiltres(self, filtres=[]):
        self.ctrl_rappels.SetFiltres(filtres)

    def SetParametres(self, dictParametres={}):
        self.dictParametres = dictParametres
        self.MAJ()

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, size=(700,500), name="DLG_Rappels_generation_selection", style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Textes
        self.box_rappels_staticbox = wx.StaticBox(self, -1, _("Page 1 - Liste des impayés : clients avec dû"))

        # Rappels disponibles
        #self.ctrl_rappels = CTRL_Liste_rappels.CTRL(self)
        self.panel_rappels = Panel_rappels(self)
        self.__do_layout()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=10, hgap=10)


        box_rappels = wx.StaticBoxSizer(self.box_rappels_staticbox, wx.VERTICAL)
        grid_sizer_rappels = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_rappels.Add(self.panel_rappels, 1, wx.EXPAND, 0)
        #grid_sizer_rappels.Add((200,100), 1, wx.EXPAND, 0)

        grid_sizer_rappels.AddGrowableRow(0)
        grid_sizer_rappels.AddGrowableCol(0)

        box_rappels.Add(grid_sizer_rappels, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_rappels, 1, wx.EXPAND, 0)
        
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def MAJ(self):
        self.panel_rappels.SetParametres(self.parent.dictParametres)
        
    def Validation(self):
        # Validation de la saisie
        nbreCoches = len(self.panel_rappels.GetTracksCoches())
        if nbreCoches == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune famille à relancer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Envoi des rappels générées (selectionnés seulement pas encore générés)
        date_emission = datetime.date.today()
        listeIDfamilles = []
        tracks = self.panel_rappels.ctrl_rappels.ctrl_rappels.GetTracksCoches()
        for track in tracks :
            listeIDfamilles.append(track.IDfamille)

        self.parent.dictParametres = {
            "date_reference" : date_emission,
            "date_edition" : date_emission,
            "listeActivites" : [],
            "listeIDfamilles" : listeIDfamilles
            }
        return True


    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetMinSize((900, 700))
        self.SetSizer(sizer_1)

        panel.dictParametres = {
            "date_reference" : datetime.date(2017, 1, 1),
            "IDlot" : None,
            "date_edition" : datetime.date.today(),
            "prestations" : ["consommation", "cotisation", "autre"],
            "IDcompte_payeur" : None,
            "listeActivites" : [396, 397, 394, 425, 426],
            "listeExceptionsComptes" : [],
            }

        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        self.boutonTest = wx.Button(panel, -1, _("Bouton de test"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)
        
    def OnBoutonTest(self, event):
        """ Bouton Test """
        self.ctrl.SauvegardeRappels()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()



