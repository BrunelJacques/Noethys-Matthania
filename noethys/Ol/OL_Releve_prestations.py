#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import datetime
import operator
from Dlg import DLG_Releve_prestations_saisie


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
        
LISTE_MOIS = (_("Janvier"), _("F�vrier"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Ao�t"), _("Septembre"), _("Octobre"), _("Novembre"), _("D�cembre"))

def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
        
def PeriodeComplete(mois, annee):
    periodeComplete = "%s %d" % (LISTE_MOIS[mois-1], annee)
    return periodeComplete




class Track(object):
    def __init__(self, periode={}, index=None):
        self.periode = periode
        self.index = index
        self.selection = periode["selection"]
        self.typeDonnees = periode["type"]
        self.dictPeriode = periode["periode"]
        self.dictOptions = periode["options"]
        
        # Type
        if self.typeDonnees == "prestations" : 
            self.label_type = _("Prestations")
        if self.typeDonnees == "factures" : 
            self.label_type = _("Factures")
        
        # P�riode
        self.date_debut = self.dictPeriode["date_debut"]
        self.date_fin = self.dictPeriode["date_fin"]
        self.code_periode = self.dictPeriode["code"]
        self.label_periode = self.dictPeriode["label"]

        # Options
        self.listeOptions = []
                
        if "impayes" in self.dictOptions and self.dictOptions["impayes"] == True :
            self.listeOptions.append(_("Uniquement les impay�s"))
        
        if "regroupement" in self.dictOptions :
            if self.dictOptions["regroupement"] == "date" :
                self.listeOptions.append(_("Regroupement par date"))
            if self.dictOptions["regroupement"] == "mois" :
                self.listeOptions.append(_("Regroupement par mois"))
            if self.dictOptions["regroupement"] == "annee" :
                self.listeOptions.append(_("Regroupement par ann�e"))
                
        if "conso" in self.dictOptions and self.dictOptions["conso"] == True :
            self.listeOptions.append(_("D�tail des consommations"))
        
        self.label_options = ", ".join(self.listeOptions)



class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.IDfamille = kwds.pop("IDfamille", None)
        self.listePeriodes = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)

    def InitModel(self):
        # Cr�ation des tracks
        self.donnees = []
        index = 0
        for item in self.listePeriodes :
            track = Track(item, index)
            self.donnees.append(track)
            index += 1

    def InitObjectListView(self):        
        
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        liste_Colonnes = [
            ColumnDefn(_("P�riode"), 'left', 180, "label_periode", typeDonnee="entier"),
            ColumnDefn(_("Type"), "left", 100, "label_type", typeDonnee="texte"),
            ColumnDefn(_("Options"), "left", 230, "label_options", typeDonnee="texte"),
            ColumnDefn(_("Date de d�but"), "left", 0, "date_debut", typeDonnee="date"),
            ColumnDefn(_("Date de fin"), "left", 0, "date_fin", typeDonnee="date"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucune p�riode"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[4])
        self.SetObjects(self.donnees)
        
        # Coche
        for track in self.donnees :
            if track.selection == True :
                self.Check(track)
                self.RefreshObject(track)
       
    def MAJ(self, listePeriodes=None):
        if listePeriodes != None :
            self.listePeriodes = listePeriodes
        self.InitModel()
        self.InitObjectListView()
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def CocheTout(self, event=None):
        for track in self.donnees :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def GetInfosCoches(self):
        listeDonnees = []
        for track in self.GetTracksCoches() :
            listeDonnees.append(track)
        return listeDonnees
            
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """            
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        item = wx.MenuItem(menuPop, 70, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=70)
        
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, 60, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=60)
        if len(self.Selection()) == 0 : item.Enable(False)

        item = wx.MenuItem(menuPop, 80, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=80)
        if len(self.Selection()) == 0 : item.Enable(False)

        menuPop.AppendSeparator()
        
        # Tout s�lectionner
        item = wx.MenuItem(menuPop, 20, _("Tout s�lectionner"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=20)

        # Tout d�-s�lectionner
        item = wx.MenuItem(menuPop, 30, _("Tout d�-s�lectionner"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=30)
        
        menuPop.AppendSeparator()
        
        # Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donn�e � imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des p�riodes"), intro="", total="", format="A", orientation=wx.LANDSCAPE)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()
        
    def Apercu(self, event):
        self.Impression("preview")

    def Imprimer(self, event):
        self.Impression("print")

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des p�riodes"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des p�riodes"))

    def Ajouter(self, event=None):
        self.MemoriseCoches() 
        dlg = DLG_Releve_prestations_saisie.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            dictDonnees = dlg.GetDonnees()
            self.listePeriodes.append(dictDonnees)
            self.MAJ() 
        dlg.Destroy()
        
    def Modifier(self, event=None):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune p�riode � modifier dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.MemoriseCoches() 
        track = self.Selection()[0]
        periode = track.periode
        
        dlg = DLG_Releve_prestations_saisie.Dialog(self)
        dlg.SetTitle(_("Modification d'une p�riode"))
        dlg.SetDonnees(track.periode)
        if dlg.ShowModal() == wx.ID_OK:
            dictDonnees = dlg.GetDonnees()
            self.listePeriodes[track.index] = dictDonnees
            self.MAJ() 
        dlg.Destroy()
        
    def Supprimer(self, event=None):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune p�riode � supprimer dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.MemoriseCoches() 
        track = self.Selection()[0]
        
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cette p�riode ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            self.listePeriodes.pop(track.index)
            self.MAJ() 
        dlg.Destroy()
        
    def MemoriseCoches(self):
        for track in self.donnees :
            etat = self.IsChecked(track)
            track.selection = etat
            self.listePeriodes[track.index]["selection"] = etat
    
    def GetListePeriodes(self):
        self.MemoriseCoches() 
        listePeriodesTemp = sorted(self.listePeriodes, key=operator.itemgetter("date_debut"), reverse=False)
        return listePeriodesTemp


# -------------------------------------------------------------------------------------------------------------------------------------


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
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

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
