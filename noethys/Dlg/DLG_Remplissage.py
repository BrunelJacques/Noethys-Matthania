#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import os
from Ctrl import CTRL_Remplissage
from Ctrl import CTRL_Ticker_presents
from Utils import UTILS_Config

AFFICHE_PRESENTS = 1

ID_MODE_PLACES_INITIALES = wx.Window.NewControlId()
ID_MODE_PLACES_PRISES = wx.Window.NewControlId()
ID_MODE_PLACES_RESTANTES = wx.Window.NewControlId()
ID_MODE_PLACES_ATTENTE = wx.Window.NewControlId()
ID_LISTE_ATTENTE = wx.Window.NewControlId()
ID_PARAMETRES = wx.Window.NewControlId()
ID_OUTILS = wx.Window.NewControlId()

ID_ACTUALISER = wx.Window.NewControlId()
ID_IMPRIMER = wx.Window.NewControlId()
ID_APERCU = wx.Window.NewControlId()
ID_EXPORT_EXCEL = wx.Window.NewControlId()
ID_EXPORT_TEXTE = wx.Window.NewControlId()
ID_AIDE = wx.Window.NewControlId()


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT|wx.TB_TEXT
        wx.ToolBar.__init__(self, *args, **kwds)

        # Boutons
        liste_boutons = [
            {"ID": ID_MODE_PLACES_INITIALES, "label": _("Places max."), "image": "Images/32x32/Places_max.png", "type" : wx.ITEM_RADIO, "tooltip": _("Afficher le nombre de places maximal initial")},
            {"ID": ID_MODE_PLACES_PRISES, "label": _("Places prises"), "image": "Images/32x32/Places_prises.png", "type" : wx.ITEM_RADIO, "tooltip": _("Afficher le nombre de places prises")},
            {"ID": ID_MODE_PLACES_RESTANTES, "label": _("Places dispo."), "image": "Images/32x32/Places_dispo.png", "type" : wx.ITEM_RADIO, "tooltip": _("Afficher le nombre de places restantes")},
            {"ID": ID_MODE_PLACES_ATTENTE, "label": _("Places attente"), "image": "Images/32x32/Places_attente.png", "type" : wx.ITEM_RADIO, "tooltip": _("Afficher le nombre de places en attente")},
            None,
            {"ID": ID_LISTE_ATTENTE, "label": _("Liste d'attente"), "image": "Images/32x32/Liste_attente.png", "type" : wx.ITEM_NORMAL, "tooltip": _("Afficher la liste d'attente")},
            None,
            {"ID": ID_PARAMETRES, "label": _("Paramètres"), "image": "Images/32x32/Configuration2.png", "type" : wx.ITEM_NORMAL, "tooltip": _("Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _("Outils"), "image": "Images/32x32/Configuration.png", "type" : wx.ITEM_NORMAL, "tooltip": _("Outils")},
        ]

        for bouton in liste_boutons :
            if bouton == None :
                self.AddSeparator()
            else :
                try :
                    self.AddTool(bouton["ID"], bouton["label"], wx.Bitmap(Chemins.GetStaticPath(bouton["image"]), wx.BITMAP_TYPE_ANY), wx.NullBitmap, bouton["type"], bouton["tooltip"], "")
                except :
                    self.AddLabelTool(bouton["ID"], bouton["label"], wx.Bitmap(Chemins.GetStaticPath(bouton["image"]), wx.BITMAP_TYPE_ANY), wx.NullBitmap, bouton["type"], bouton["tooltip"], "")

        # Binds
        self.Bind(wx.EVT_TOOL, self.Mode_places_initiales, id=ID_MODE_PLACES_INITIALES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_prises, id=ID_MODE_PLACES_PRISES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_restantes, id=ID_MODE_PLACES_RESTANTES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_attente, id=ID_MODE_PLACES_ATTENTE)
        self.Bind(wx.EVT_TOOL, self.Liste_attente, id=ID_LISTE_ATTENTE)
        self.Bind(wx.EVT_TOOL, self.Parametres, id=ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.MenuOutils, id=ID_OUTILS)
        
        self.SetToolBitmapSize((32, 32))
        self.Realize()
    
    def Mode_places_initiales(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesInitial"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Mode_places_prises(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesPrises"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Mode_places_restantes(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesRestantes"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()
        
    def Mode_places_attente(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbreAttente"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Liste_attente(self, event):
        self.GetParent().OuvrirListeAttente()

    def Parametres(self, event):
        global AFFICHE_PRESENTS
        from Dlg import DLG_Parametres_remplissage
        dictDonnees = self.GetParent().dictDonnees
        if "modeAffichage" in dictDonnees :
            modeAffichage = dictDonnees["modeAffichage"]
        else:
            modeAffichage = "nbrePlacesPrises"
        largeurColonneUnites = self.GetParent().ctrl_remplissage.GetLargeurColonneUnite()
        abregeGroupes = self.GetParent().ctrl_remplissage.GetAbregeGroupes()
        affichePresents = AFFICHE_PRESENTS
        dlg = DLG_Parametres_remplissage.Dialog(None, dictDonnees, largeurColonneUnites, abregeGroupes=abregeGroupes, affichePresents=affichePresents)
        if dlg.ShowModal() == wx.ID_OK:
            # Mise à jour des paramètres du tableau
            listeActivites = dlg.GetListeActivites()
            listePeriodes = dlg.GetListePeriodes()
            dictDonnees = dlg.GetDictDonnees() 
            largeurColonnesUnites = dlg.GetLargeurColonneUnite()
            abregeGroupes = dlg.GetAbregeGroupes()
            # Mise à jour du tableau de remplissage
            self.GetParent().ctrl_remplissage.SetListeActivites(listeActivites)
            self.GetParent().ctrl_remplissage.SetListePeriodes(listePeriodes)
            self.GetParent().ctrl_remplissage.SetLargeurColonneUnite(largeurColonnesUnites)
            self.GetParent().ctrl_remplissage.SetAbregeGroupes(abregeGroupes)
            self.GetParent().ctrl_remplissage.MAJ()
            dictDonnees["modeAffichage"] = modeAffichage
            self.GetParent().SetDictDonnees(dictDonnees)
            # Affiche ticker des présents
            AFFICHE_PRESENTS = dlg.GetAffichePresents()
            UTILS_Config.SetParametre("remplissage_affiche_presents", int(AFFICHE_PRESENTS))
            # MAJ
            self.GetParent().MAJ()
        dlg.Destroy()

    def MenuOutils(self, event):
        # Création du menu Outils
        menuPop = wx.Menu()

        item = wx.MenuItem(menuPop, ID_APERCU, _("Aperçu avant impression"), _("Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)

        ID_IMPRIMER = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_IMPRIMER, _("Imprimer"), _("Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)
        
        menuPop.AppendSeparator()

        ID_EXPORT_TEXTE = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _("Exporter au format Texte"), _("Exporter au format Texte"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_remplissage.ExportTexte, id=ID_EXPORT_TEXTE)

        ID_EXPORT_EXCEL = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _("Exporter au format Excel"), _("Exporter au format Excel"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_remplissage.ExportExcel, id=ID_EXPORT_EXCEL)
        
        menuPop.AppendSeparator()

        ID_ACTUALISER = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_ACTUALISER, _("Actualiser"), _("Actualiser l'affichage"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()

        ID_AIDE = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_AIDE, _("Aide"), _("Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
        
    def Actualiser(self, event):
        self.GetParent().ctrl_remplissage.MAJ()

    def Imprimer(self, event):
        self.GetParent().Imprimer()

    def Apercu(self, event):
        self.GetParent().Apercu()

    def Aide(self, event):
        self.GetParent().Aide()


    
class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="panel_remplissage", id=-1, style=wx.TAB_TRAVERSAL)
        
        # Récupération des paramètres d'affichage
        self.dictDonnees = self.GetParametres() 

        # Création des contrôles
        self.toolBar = ToolBar(self)
        self.ctrl_remplissage = CTRL_Remplissage.CTRL(self, self.dictDonnees)
        
        self.ctrl_presents = CTRL_Ticker_presents.CTRL(self, delai=60, listeActivites=[15,])
        self.ctrl_presents.Show(False) 

        global AFFICHE_PRESENTS
        AFFICHE_PRESENTS = UTILS_Config.GetParametre("remplissage_affiche_presents", 1)

        if "modeAffichage" in self.dictDonnees :
            if self.dictDonnees["modeAffichage"] == "nbrePlacesInitial" : self.toolBar.ToggleTool(ID_MODE_PLACES_INITIALES, True)
            if self.dictDonnees["modeAffichage"] == "nbrePlacesPrises" : self.toolBar.ToggleTool(ID_MODE_PLACES_PRISES, True)
            if self.dictDonnees["modeAffichage"] == "nbrePlacesRestantes" : self.toolBar.ToggleTool(ID_MODE_PLACES_RESTANTES, True)
            if self.dictDonnees["modeAffichage"] == "nbreAttente" : self.toolBar.ToggleTool(ID_MODE_PLACES_ATTENTE, True)
            
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        pass

    def __do_layout(self):
        self.grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        self.grid_sizer_base.Add(self.toolBar, 1, wx.EXPAND|wx.ALL, 0)
        self.grid_sizer_base.Add(self.ctrl_presents, 1, wx.EXPAND|wx.ALL, 0)
        self.grid_sizer_base.Add(self.ctrl_remplissage, 1, wx.EXPAND|wx.ALL, 0)
        self.grid_sizer_base.AddGrowableRow(2)
        self.grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(self.grid_sizer_base)
        self.Layout()
    
    def GetParametres(self):
        defaut = {
            'listeActivites': [], 
            'listeSelections': (), 
            'listePeriodes': [], 
            'modeAffichage': 'nbrePlacesPrises', 
            'dateDebut': None, 
            'dateFin': None, 
            'annee': datetime.date.today().year,
            'page': 0,
            }
        dictDonnees = UTILS_Config.GetParametre("dict_selection_periodes_activites", defaut)
        return dictDonnees
    
    def SetDictDonnees(self, dictDonnees={}):
        if len(dictDonnees) != 0 :
            self.dictDonnees = dictDonnees
        # Mémorisation du dict de Données de sélection
        self.ctrl_remplissage.SetDictDonnees(self.dictDonnees)
        # Mémorisation du dict de données dans le config
        UTILS_Config.SetParametre("dict_selection_periodes_activites", self.dictDonnees)

    def MAJ(self):
        self.ctrl_remplissage.MAJ() 
        self.MAJpresents()

    def MAJpresents(self):
        """ MAJ du Ticker des présents """
        listeActivites = self.dictDonnees["listeActivites"]
        self.ctrl_presents.SetActivites(listeActivites)
        self.ctrl_presents.MAJ() 
    
    def AffichePresents(self, etat=True):
        """ Affiche ou cache le Ticker des présents """
        if AFFICHE_PRESENTS == 0 :
            etat = 0
        self.ctrl_presents.Show(etat)
        self.grid_sizer_base.Layout()

    def Imprimer(self):
        self.ctrl_remplissage.Imprimer() 

    def Apercu(self):
        self.ctrl_remplissage.Apercu() 

    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Leseffectifs")

    def OuvrirListeAttente(self):
        self.ctrl_remplissage.MAJ()
        dictEtatPlaces = self.ctrl_remplissage.GetEtatPlaces()
        dictUnitesRemplissage = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Attente
        dlg = DLG_Attente.Dialog(self, dictDonnees=self.dictDonnees, dictEtatPlaces=dictEtatPlaces, dictUnitesRemplissage=dictUnitesRemplissage)
        dlg.ShowModal()
        dlg.Destroy() 

    def OuvrirListeRefus(self):
        self.ctrl_remplissage.MAJ()
        dictEtatPlaces = self.ctrl_remplissage.GetEtatPlaces()
        dictUnitesRemplissage = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Refus
        dlg = DLG_Refus.Dialog(self, dictDonnees=self.dictDonnees, dictEtatPlaces=dictEtatPlaces, dictUnitesRemplissage=dictUnitesRemplissage)
        dlg.ShowModal()
        dlg.Destroy() 


class Dialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        wx.Dialog.__init__(self, *args, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX,
                           size=(700, 800))
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = Dialog(None, -1, "TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
