#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import decimal
import GestionDB
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")
from Utils import UTILS_Dates


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

                

  
class Track(object):
    def __init__(self, dictValeurs, index):
        self.index = index
        self.dictValeurs = dictValeurs
        self.IDprestation = dictValeurs["IDprestation"]
        self.date_debut = dictValeurs["date_debut"]
        self.date_fin = dictValeurs["date_fin"]
        self.label_prestation = dictValeurs["label_prestation"]
        self.montant_prestation = dictValeurs["montant_prestation"]
        self.date_prestation = dictValeurs["date_prestation"]
        self.IDfacture = dictValeurs["IDfacture"]
        if "numFacture" in dictValeurs :
            self.numFacture = dictValeurs["numFacture"]
        else :
            self.numFacture = None
        self.listeConso = dictValeurs["listeConso"]
        self.nbreConso = len(self.listeConso)

# ----------------------------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.IDactivite = kwds.pop("IDactivite", None)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.listeDonnees = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.donnees = []
        self.InitObjectListView()
    
    def SetActivite(self, IDactivite=None):
        self.IDactivite = IDactivite
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = []
        index = 0
        for dictPeriode in self.listeDonnees :
            track = Track(dictPeriode, index)
            self.donnees.append(track)
            index += 1
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateEngFr(str(dateDD))
        
        def FormateNumFacture(numero):
            if numero == None :
                return ""
            else :
                return "n�%d"% numero
            
        liste_Colonnes = [
            ColumnDefn(_("IDprestation"), "left", 0, "IDprestation", typeDonnee="entier"),
            ColumnDefn(u"Du", 'centre', 70, "date_debut", typeDonnee="date", stringConverter=FormateDateCourt),
            ColumnDefn(_("Au"), 'centre', 70, "date_fin", typeDonnee="date", stringConverter=FormateDateCourt),
            ColumnDefn(_("Label"), "left", 150, "label_prestation", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Montant"), 'right', 80, "montant_prestation", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Date prestation"), 'centre', 100, "date_prestation", typeDonnee="date", stringConverter=FormateDateCourt),
            ColumnDefn(_("Nbre conso."), 'centre', 80, "nbreConso", typeDonnee="entier"),
            ColumnDefn(_("Facture"), 'centre', 65, "numFacture", typeDonnee="texte", stringConverter=FormateNumFacture),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucune p�riode"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(2)
        
    def MAJ(self):
        self.InitModel()
        self.SetObjects(self.donnees)
        self._ResizeSpaceFillingColumns() 

    def SetDonnees(self, listeDonnees={}):
        self.listeDonnees = listeDonnees
        self.MAJ() 
    
    def GetDonnees(self):
        return self.listeDonnees
    
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

        # Item Assistant
        item = wx.MenuItem(menuPop, 100, _("G�n�rer automatiquement des p�riodes"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Assistant, id=100)
                
        menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Ajouter
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

        # Item Supprimer les consommations de la p�riode
        item = wx.MenuItem(menuPop, 110, _("Supprimer les consommations de cette p�riode"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.SupprimerConsoPeriode, id=110)
        if noSelection == True : item.Enable(False)

        # Item Supprimer les consommations de toutes les p�riodes
        item = wx.MenuItem(menuPop, 120, _("Supprimer les consommations de toutes les p�riodes"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.SupprimerConsoToutesPeriodes, id=120)

        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout d�cocher
        item = wx.MenuItem(menuPop, 80, _("Tout d�cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des p�riodes de contrats"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des p�riodes de contrats"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des p�riodes de contrats"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des p�riodes de contrats"), autoriseSelections=False)

    def Assistant(self, event):  
        dictValeurs = {
            "date_debut" : self.GetGrandParent().ctrl_date_debut.GetDate(),
            "date_fin" : self.GetGrandParent().ctrl_date_fin.GetDate(),
            }
        from Dlg import DLG_Saisie_contrat_periode_auto
        dlg = DLG_Saisie_contrat_periode_auto.Dialog(self, IDactivite=self.IDactivite, dictValeurs=dictValeurs, listeTracks=self.donnees)
        if dlg.ShowModal() == wx.ID_OK:
            listeDonnees = self.GetDonnees() 
            listeDonnees.extend(dlg.GetResultats())
            self.SetDonnees(listeDonnees)
        dlg.Destroy()

    def Ajouter(self, event):  
        from Dlg import DLG_Saisie_contrat_periode
        dlg = DLG_Saisie_contrat_periode.Dialog(self, IDactivite=self.IDactivite, listeTracks=self.donnees)
        if dlg.ShowModal() == wx.ID_OK:
            dictDonnees = dlg.GetDonnees() 
            self.listeDonnees.append(dictDonnees)
            self.MAJ() 
        dlg.Destroy()
        
    def Modifier(self, event):  
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune p�riode � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_contrat_periode
        dlg = DLG_Saisie_contrat_periode.Dialog(self, IDactivite=self.IDactivite, track=track, listeTracks=self.donnees)
        if dlg.ShowModal() == wx.ID_OK:
            self.listeDonnees[track.index] = dlg.GetDonnees() 
            self.MAJ() 
        dlg.Destroy()

    def Supprimer(self, event):  
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune p�riode � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if len(self.GetTracksCoches()) > 0 :
            # Suppression multiple
            listeSelections = self.GetTracksCoches()
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les p�riodes coch�es ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        else :
            # Suppression unique
            listeSelections = self.Selection()        
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer la p�riode s�lectionn�e ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        # Suppression
        listeSuppressions = []
        for track in listeSelections :

            if track.IDfacture != None :
                dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la prestation '%s' car elle appara�t d�j� sur la facture n�%s !") % (track.label_prestation, track.numFacture) , _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            
            listeSuppressionConso = []
            if track.nbreConso > 0 :
                dlg = wx.MessageDialog(self, _("Souhaitez-vous �galement supprimer les %d consommations associ�es � la p�riode s�lectionn�e ?") % track.nbreConso, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
                reponse = dlg.ShowModal() 
                dlg.Destroy()
                if reponse == wx.ID_CANCEL :
                    return
                if reponse == wx.ID_YES :
                    for dictConso in track.listeConso :
                        if dictConso["etat"] in ("present", "absenti", "absentj") :
                            dlg = wx.MessageDialog(self, _("Proc�dure de suppression annul�e :\n\nVous ne pouvez pas supprimer la consommation du %s car elle est d�j� point�e !") % UTILS_Dates.DateDDEnFr(dictConso["date"]), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                            dlg.ShowModal()
                            dlg.Destroy()
                            return
                        listeSuppressionConso.append(dictConso["IDconso"])
            
            for IDconso in listeSuppressionConso :
                self.GetGrandParent().listeSuppressionConso.append(IDconso)
            
            listeSuppressions.append(track.index)
        
        nouvelleListe = []
        index = 0
        for dictPeriode in self.listeDonnees :
            if index not in listeSuppressions :
                nouvelleListe.append(dictPeriode)
            index += 1
        self.listeDonnees = nouvelleListe
        self.MAJ() 
    
    def SupprimerConsoPeriode(self, event):
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune p�riode dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if len(track.listeConso) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucun consommation � supprimer dans cette p�riode !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les %d consommations associ�es � cette p�riode ?") % len(track.listeConso), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
        reponse = dlg.ShowModal() 
        dlg.Destroy()
        if reponse != wx.ID_YES :
            return
        for dictConso in track.listeConso :
            if dictConso["IDconso"] != None :
                self.GetGrandParent().listeSuppressionConso.append(IDconso)
        self.listeDonnees[track.index]["listeConso"] = []
        self.MAJ()
        
    def SupprimerConsoToutesPeriodes(self, event):
        listeIDconso = []
        for track in self.donnees :
            for dictConso in track.listeConso :
                listeIDconso.append(dictConso["IDconso"])
            
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les %d consommations associ�es � toutes les p�riodes ?") % len(listeIDconso), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
        reponse = dlg.ShowModal() 
        dlg.Destroy()
        if reponse != wx.ID_YES :
            return
        
        for IDconso in listeIDconso :
            if IDconso != None :
                self.GetGrandParent().listeSuppressionConso.append(IDconso)
        
        index = 0
        for dictDonnees in self.listeDonnees :
            self.listeDonnees[index]["listeConso"] = []
            index += 1
        self.MAJ()
        
    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()


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
            "date_fin" : {"mode" : "nombre", "singulier" : _("p�riode"), "pluriel" : _("p�riodes"), "alignement" : wx.ALIGN_CENTER},
            "montant_prestation" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)



class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        ctrl = ListviewAvecFooter(panel) 
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
