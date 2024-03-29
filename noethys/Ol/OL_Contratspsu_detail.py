#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Utils import UTILS_Dates
import datetime
import calendar
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import ObjectListView, FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

from Dlg.DLG_Saisie_contratpsu import Base

LISTE_MOIS = [_("Janvier"), _("F�vrier"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Ao�t"), _("Septembre"), _("Octobre"), _("Novembre"), _("D�cembre")]



class Track(object):
    def __init__(self, clsbase=None, date=None, dict_date={}):
        self.clsbase = clsbase
        self.dict_date = dict_date

        self.date = date
        self.duree_prevision = dict_date["prevision"]["duree_arrondie"]
        self.duree_presence = dict_date["presence"]["duree_arrondie"]
        self.heures_absences_non_deductibles = dict_date["heures_absences_non_deductibles"]
        self.heures_absences_deductibles = dict_date["heures_absences_deductibles"]
        self.depassement = dict_date["depassement"]
        self.absences_rtt = dict_date["absences_rtt"]


# ----------------------------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.donnees = []
        self.InitObjectListView()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateComplete(dateDD)

        def FormateMontant(montant):
            if montant in ("", None, FloatToDecimal(0.0)) :
                return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateMontant2(montant):
            if montant == None or montant == "" : return ""
            return "%.5f %s" % (montant, SYMBOLE)

        def FormateDuree(duree):
            if duree in (None, "", datetime.timedelta(seconds=0)):
                return ""
            else :
                if type(duree) == int :
                    duree = datetime.timedelta(hours=duree)
                return UTILS_Dates.DeltaEnStr(duree, separateur="h")

        liste_Colonnes = [
            ColumnDefn(_(""), "left", 0, "", typeDonnee="texte"),
            ColumnDefn(_("Date"), 'left', 170, "date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Pr�vision"), 'center', 90, "duree_prevision", typeDonnee="duree", stringConverter=FormateDuree),
            ColumnDefn(_("Pr�sence"), 'center', 90, "duree_presence", typeDonnee="duree", stringConverter=FormateDuree),
            ColumnDefn(_("Abs d�duc."), 'center', 90, "heures_absences_deductibles", typeDonnee="duree", stringConverter=FormateDuree),
            ColumnDefn(_("Abs non d�duc."), 'center', 90, "heures_absences_non_deductibles", typeDonnee="duree", stringConverter=FormateDuree),
            ColumnDefn(_("H.Compl."), 'center', 90, "depassement", typeDonnee="duree", stringConverter=FormateDuree),
            ColumnDefn(_(""), 'center', 5, "5", typeDonnee="texte"),
            ColumnDefn(_("Abs. RTT"), 'center', 90, "absences_rtt", typeDonnee="duree", stringConverter=FormateDuree),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune date"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(1)

    def SetDonnees(self, track_mensualite=None):
        # Recherche des dates extr�mes du mois
        self.track_mensualite = track_mensualite

        # G�n�ration des tracks
        self.donnees = []
        for date, dict_date in track_mensualite.dict_dates.items() :
            track = Track(date=date, dict_date=dict_date)
            self.donnees.append(track)

        # MAJ du listview
        self.MAJ()

    def MAJ(self):
        self.SetObjects(self.donnees)
        self._ResizeSpaceFillingColumns() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """        
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
            
    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("D�tail de la mensualit�"), intro=self.GetIntro(), format="A", orientation=wx.LANDSCAPE)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("D�tail de la mensualit�"), intro=self.GetIntro(), format="A", orientation=wx.LANDSCAPE)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("D�tail de la mensualit�"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("D�tail de la mensualit�"), autoriseSelections=False)

    def GetIntro(self):
        return "" #TODO <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "date" : {"mode" : "nombre", "singulier" : _("date"), "pluriel" : _("dates"), "alignement" : wx.ALIGN_CENTER},
            "duree_prevision" : {"mode" : "total", "alignement" : wx.ALIGN_CENTER, "format" : "temps"},
            "duree_presence" : {"mode" : "total", "alignement" : wx.ALIGN_CENTER, "format" : "temps"},
            "heures_absences_deductibles" : {"mode" : "total", "alignement" : wx.ALIGN_CENTER, "format" : "temps"},
            "heures_absences_non_deductibles" : {"mode" : "total", "alignement" : wx.ALIGN_CENTER, "format" : "temps"},
            "depassement" : {"mode" : "total", "alignement" : wx.ALIGN_CENTER, "format" : "temps"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        ctrl = ListviewAvecFooter(panel, kwargs={})
        listview = ctrl.GetListview()
        listview.MAJ()

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(ctrl, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((1200, 400))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
