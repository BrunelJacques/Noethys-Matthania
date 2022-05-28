#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys? Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques BRUNEL
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ol import OL_Individus
from Utils import UTILS_Config

ID_CREER_FAMILLE = wx.Window.NewControlId()
ID_MODIFIER_FAMILLE = wx.Window.NewControlId()
ID_SUPPRIMER_FAMILLE = wx.Window.NewControlId()
ID_OUVRIR_GRILLE = 60
ID_OUVRIR_FICHE_IND = 70
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
            {"ID" : ID_CREER_FAMILLE, "label" : _("Ajouter"), "image" : "Images/32x32/Famille_ajouter.png", "tooltip" : _("Créer une nouvelle famille")},
            None,
            {"ID": ID_MODIFIER_FAMILLE, "label": _("Modifier"), "image": "Images/32x32/Famille_modifier.png", "tooltip": _("Modifier la fiche famille de l'individu sélectionné")},
            {"ID": ID_SUPPRIMER_FAMILLE, "label": _("Supprimer"), "image": "Images/32x32/Famille_supprimer.png", "tooltip": _("Supprimer ou détacher l'individu sélectionné")},
            None,
            {"ID": ID_OUVRIR_GRILLE, "label": _("Calendrier"), "image": "Images/32x32/Calendrier.png", "tooltip": _("Ouvrir la grille des consommations de l'individu sélectionné\n(ou double-clic sur la ligne + touche CTRL enfoncée)")},
            {"ID": ID_OUVRIR_FICHE_IND, "label": _("Fiche ind."), "image": "Images/32x32/Personnes.png", "tooltip": _("Ouvrir la fiche individuelle de l'individu sélectionné\n(ou double-clic sur la ligne + touche SHIFT enfoncée)")},
            None,
            {"ID": ID_PARAMETRES, "label": _("Paramètres"), "image": "Images/32x32/Configuration2.png", "type": wx.ITEM_NORMAL, "tooltip": _("Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _("Outils"), "image": "Images/32x32/Configuration.png", "tooltip": _("Outils")},
            ]
        for bouton in liste_boutons :
            if bouton == None :
                self.AddSeparator()
            else :
                try :
                    self.AddTool(bouton["ID"], bouton["label"], wx.Bitmap(Chemins.GetStaticPath(bouton["image"]), wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")
                except :
                    self.AddLabelTool(bouton["ID"], bouton["label"], wx.Bitmap(Chemins.GetStaticPath(bouton["image"]), wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")

        # Binds
        self.Bind(wx.EVT_TOOL, self.Ajouter_famille, id=ID_CREER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Modifier_famille, id=ID_MODIFIER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Supprimer_famille, id=ID_SUPPRIMER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_grille, id=ID_OUVRIR_GRILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_fiche_ind, id=ID_OUVRIR_FICHE_IND)
        self.Bind(wx.EVT_TOOL, self.Parametres, id=ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.MenuOutils, id=ID_OUTILS)
        
        self.SetToolBitmapSize((32, 32))
        self.Realize()
    
    def Ajouter_famille(self, event):
        self.GetParent().ctrl_listview.Ajouter(None)

    def Modifier_famille(self, event):
        self.GetParent().ctrl_listview.Modifier(None)

    def Supprimer_famille(self, event):
        self.GetParent().ctrl_listview.Supprimer(None)

    def Ouvrir_grille(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Ouvrir_fiche_ind(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Parametres(self, event):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        from Dlg import DLG_Selection_individus
        dlg = DLG_Selection_individus.Dialog(self)
        dlg.SetParametres(parametres)
        if dlg.ShowModal() == wx.ID_OK:
            UTILS_Config.SetParametre("liste_individus_parametres", dlg.GetParametres())
        dlg.Destroy()

        # Actualise la liste d'individus
        self.GetParent().ActualiseParametresAffichage() 
        self.GetParent().ctrl_listview.MAJ(forceActualisation=True)
        
    def MenuOutils(self, event):
        # Création du menu Outils
        menuPop = wx.Menu()
            
        item = wx.MenuItem(menuPop, ID_APERCU, _("Aperçu avant impression"), _("Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)
        
        item = wx.MenuItem(menuPop, ID_IMPRIMER, _("Imprimer"), _("Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)
        
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _("Exporter au format Texte"), _("Exporter au format Texte"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportTexte, id=ID_EXPORT_TEXTE)
        
        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _("Exporter au format Excel"), _("Exporter au format Excel"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportExcel, id=ID_EXPORT_EXCEL)
        
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_ACTUALISER, _("Actualiser"), _("Actualiser l'affichage"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()
        
        item = wx.MenuItem(menuPop, ID_AIDE, _("Aide"), _("Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.GetParent().ctrl_listview.Apercu(None)

    def Imprimer(self, event):
        self.GetParent().ctrl_listview.Imprimer(None)

    def Actualiser(self, event):
        self.GetParent().MAJ()

    def Aide(self, event):
        self.GetParent().Aide()


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="recherche_individus", id=-1, style=wx.TAB_TRAVERSAL)
        
        self.toolBar = ToolBar(self)
        self.ctrl_listview = OL_Individus.ListView(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_recherche = OL_Individus.CTRL_Outils(self, listview=self.ctrl_listview, historique=True)
        self.coche_inPayeurs = wx.CheckBox(self,-1,"Recherche sur payeurs")
        self.__set_properties()
        self.__do_layout()
        
        # Recherche paramètres d'affichage de la liste des individus
        self.ActualiseParametresAffichage()

    def __set_properties(self):
        mess = "Permet de chercher ausi dans les payeurs ou les noms d'épouse"
        self.coche_inPayeurs.SetToolTip(mess)
        self.coche_inPayeurs.SetValue(wx.CHK_UNCHECKED)
        self.coche_inPayeurs.Bind(wx.EVT_CHECKBOX, self.MAJ)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.toolBar, 1, wx.EXPAND|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_listview, 1, wx.EXPAND|wx.ALL, 0)
        sizerbase = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        sizerbase.Add(self.ctrl_recherche, 1, wx.ALL|wx.EXPAND, 0)
        sizerbase.Add(self.coche_inPayeurs, 1, wx.ALL|wx.EXPAND, 0)
        sizerbase.AddGrowableCol(0)
        grid_sizer_base.Add(sizerbase, 1, wx.EXPAND|wx.ALL, 0)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        self.Layout()
        
    def MAJ(self,*arg,**kwd):
        kwd["inPayeurs"] = self.coche_inPayeurs.GetValue()
        self.ctrl_listview.MAJ(*arg,**kwd)
        
    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lalistedesindividus")
    
    def ActualiseParametresAffichage(self):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        self.ctrl_listview.SetParametres(parametres)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= Panel(panel)
        self.ctrl.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
