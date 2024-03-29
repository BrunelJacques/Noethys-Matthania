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
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

                
  
class Track(object):
    def __init__(self, dictValeurs):
        self.dictValeurs = dictValeurs
        self.MAJ()

    def MAJ(self):
        self.IDcontrat_tarif = self.dictValeurs["IDcontrat_tarif"]
        self.date_debut = self.dictValeurs["date_debut"]
        self.revenu = self.dictValeurs["revenu"]
        self.quotient = self.dictValeurs["quotient"]
        self.taux = self.dictValeurs["taux"]
        self.tarif_base = self.dictValeurs["tarif_base"]
        self.tarif_depassement = self.dictValeurs["tarif_depassement"]

# ----------------------------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.clsbase = kwds.pop("clsbase", None)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.donnees = []
        self.listeDonnees = []
        self.InitObjectListView()

    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        def FormateDate(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateDDEnFr(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateMontant2(montant):
            if montant == None or montant == "" : return ""
            return "%.5f %s" % (montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(_("IDcontrat_tarif"), "left", 0, "IDcontrat_tarif", typeDonnee="entier"),
            ColumnDefn(_("Date de d�but"), 'left', 100, "date_debut", typeDonnee="date", isSpaceFilling=True, stringConverter=FormateDate),
            ColumnDefn(_("Revenu"), 'center', 90, "revenu", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Quotient"), 'center', 90, "quotient", typeDonnee="entier"),
            ColumnDefn(_("Taux"), 'center', 90, "taux", typeDonnee="montant", stringConverter=FormateMontant2),
            ColumnDefn(_("Tarif de base"), 'center', 90, "tarif_base", typeDonnee="montant", stringConverter=FormateMontant2),
            ColumnDefn(_("Tarif d�pass."), 'center', 90, "tarif_depassement", typeDonnee="montant", stringConverter=FormateMontant2),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun tarif"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(1)
        
    def MAJ(self):
        self.SetObjects(self.donnees)
        self._ResizeSpaceFillingColumns() 

    def SetDonnees(self, listeDonnees=[]):
        self.donnees = []
        for dictTarif in listeDonnees :
            self.donnees.append(Track(self, dictTarif))

    def SetTracks(self, tracks=[]):
        self.donnees = tracks
        self.MAJ()

    def GetTracks(self):
        return self.GetObjects()
    
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

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()

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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des tarifs"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des tarifs"), autoriseSelections=False)

    def Ajouter(self, event):
        from Dlg import DLG_Saisie_contratpsu_tarif
        dlg = DLG_Saisie_contratpsu_tarif.Dialog(self, IDfamille=self.clsbase.GetValeur("IDfamille"))
        if self.clsbase != None and len(self.GetTracks()) == 0 :
            date_debut = self.clsbase.GetValeur("date_debut")
            dlg.ctrl_date_debut.SetDate(date_debut)
            dlg.ctrl_date_debut.Enable(False)
        if dlg.ShowModal() == wx.ID_OK:
            dictTarif = dlg.GetDonnees()
            self.AddObject(Track(dictTarif))
        dlg.Destroy()
        
    def Modifier(self, event):  
        if len(self.Selection()) == 0 :
           dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun tarif � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
           dlg.ShowModal()
           dlg.Destroy()
           return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_contratpsu_tarif
        dlg = DLG_Saisie_contratpsu_tarif.Dialog(self, IDfamille=self.clsbase.GetValeur("IDfamille"))
        dlg.SetTrack(track)
        if dlg.ShowModal() == wx.ID_OK:
            track.dictValeurs = dlg.GetDonnees()
            track.MAJ()
            self.RefreshObject(track)
        dlg.Destroy()

    def VerifieTarif(self, trackExclus=None):
        """ V�rifie si un tarif commence bien au premier jour du contrat """
        date_debut_contrat = self.clsbase.GetValeur("date_debut")
        valide = False
        for track in self.GetTracks():
            if track != trackExclus and track.date_debut <= date_debut_contrat :
                valide = True
        return valide

    def Supprimer(self, event):  
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune consommation � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]

        # if self.VerifieTarif(track) == False :
        #     dlg = wx.MessageDialog(self, _("Attention, si vous supprimez ce tarif, la p�riode du contrat ne disposera pas de tarif disponible au premier jour du contrat !\n\nSouhaitez-vous tout de m�me supprimer le tarif s�lectionn� ?"), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
        #     reponse = dlg.ShowModal()
        #     dlg.Destroy()
        #     if reponse != wx.ID_YES :
        #         return

        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer le tarif s�lectionn� ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES :
            return
        
        # Suppression
        self.RemoveObject(track)


# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_soldes
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "date" : {"mode" : "nombre", "singulier" : _("consommation"), "pluriel" : _("consommations"), "alignement" : wx.ALIGN_CENTER},
            "duree" : {"mode" : "total", "format" : "temps", "alignement" : wx.ALIGN_CENTER},
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
        self.SetSize((800, 400))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
