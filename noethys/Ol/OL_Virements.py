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
import GestionDB
from Dlg import DLG_Saisie_operation_tresorerie
from Dlg import DLG_Saisie_virement
import datetime

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Utilisateurs
from Utils import UTILS_Dates


class Track(object):
    def __init__(self, donnees):
        self.IDvirement = donnees["IDvirement"]
        self.IDoperation_debit = donnees["IDoperation_debit"]
        self.IDoperation_credit = donnees["IDoperation_credit"]
        self.date = donnees["date"]
        self.libelle = donnees["libelle"]
        self.montant = donnees["montant"]
        self.observations = donnees["observations"]
        self.IDreleve_debit = donnees["IDreleve_debit"]
        self.IDreleve_credit = donnees["IDreleve_credit"]
        

    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.IDcompte_bancaire = kwds.pop("IDcompte_bancaire", None)
        self.ctrl_soldes = None
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
    
    def SetCompteBancaire(self, IDcompte_bancaire=None):
        self.IDcompte_bancaire = IDcompte_bancaire
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        DB = GestionDB.DB()
        
        req = """SELECT IDvirement, IDoperation_debit, IDoperation_credit
        FROM compta_virements;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeVirements = DB.ResultatReq()

        req = """SELECT IDoperation, date, libelle, montant, IDreleve, IDvirement, observations
        FROM compta_operations
        WHERE IDvirement IS NOT NULL;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeOperations = DB.ResultatReq()

        DB.Close()
        
        dictOperations = {}
        for IDoperation, date, libelle, montant, IDreleve, IDvirement, observations in listeOperations :
            date = UTILS_Dates.DateEngEnDateDD(date)
            dictOperations[IDoperation] = {
                "IDoperation" : IDoperation, "date" : date, "libelle" : libelle, 
                "montant" : montant, "IDreleve" : IDreleve, "IDvirement" : IDvirement, "observations" : observations, 
                }
            
        listeListeView = []
        for IDvirement, IDoperation_debit, IDoperation_credit in listeVirements :
            dictOperationDebit = dictOperations[IDoperation_debit]
            dictOperationCredit = dictOperations[IDoperation_credit]
            
            dictTemp = {
                "IDvirement" : IDvirement, "IDoperation_debit" : IDoperation_debit, "IDoperation_credit" : IDoperation_credit, 
                "date" : dictOperationDebit["date"], "libelle" : dictOperationDebit["libelle"], "montant" : dictOperationDebit["montant"], 
                "observations" : dictOperationDebit["observations"], "IDreleve_debit" : dictOperationDebit["IDreleve"],
                "IDreleve_credit" : dictOperationCredit["IDreleve"],
                }
            track = Track(dictTemp)
            listeListeView.append(track)
        
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def rowFormatter(listItem, track):
            if track.date > datetime.date.today() :
                listItem.SetTextColour((180, 180, 180))

        def FormateDate(date):
            return UTILS_Dates.DateDDEnFr(date)

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(u"", "left", 0, "IDvirement", typeDonnee="entier"),
            ColumnDefn(_("Date"), 'left', 80, "date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Libell�"), 'left', 200, "libelle", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Montant"), "right", 80, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            ]

        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun virement"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, track=None, IDoperation=None, IDvirement=None):
        self.Freeze()
        self.InitModel()
        self.InitObjectListView()
        # S�lection d'un item
        if track != None :
            self.SelectObject(track, deselectOthers=True, ensureVisible=True)
        if IDoperation != None :
            for trackTemp in self.donnees :
                if trackTemp.IDoperation == IDoperation :
                    self.SelectObject(trackTemp, deselectOthers=True, ensureVisible=True)
                    break
        if IDvirement != None :
            for trackTemp in self.donnees :
                if trackTemp.IDvirement == IDvirement :
                    self.SelectObject(trackTemp, deselectOthers=True, ensureVisible=True)
                    break
        # MAJ listctrl
        self._ResizeSpaceFillingColumns() 
        self.Thaw() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDvirement
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _("Ajouter un virement"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.AjouterVirement, id=10)

        menuPop.AppendSeparator()

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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des virements"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des virements"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des virements"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des virements"))

    def AjouterVirement(self, event):
        dlg = DLG_Saisie_virement.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDvirement=dlg.GetIDvirement())
        dlg.Destroy()
        
    def Modifier(self, event):
##        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_categories_comptables", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun virement � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        dlg = DLG_Saisie_virement.Dialog(self, track.IDvirement)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(track=track)
        dlg.Destroy()

    def Supprimer(self, event):
##        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_categories_comptables", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun virement � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.IDreleve_debit != None or track.IDreleve_debit != None :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer un virement point� sur un relev� bancaire !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce virement ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("compta_operations", "IDvirement", track.IDvirement)
            DB.ReqDEL("compta_virements", "IDvirement", track.IDvirement)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()
    
    
# -------------------------------------------------------------------------------------------------------------------------------------------

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



### -------------------------------------------------------------------------------------------------------------------------------------------
##
##class ListviewAvecFooter(PanelAvecFooter):
##    def __init__(self, parent, kwargs={}):
##        dictColonnes = {
##            "nomTiers" : {"mode" : "nombre", "singulier" : _("op�ration"), "pluriel" : _("op�rations"), "alignement" : wx.ALIGN_CENTER},
##            "libelle" : {"mode" : "texte", "texte" : _("Solde du jour : 10000.00 �"), "alignement" : wx.ALIGN_CENTER},
##            "solde" : {"mode" : "total"},
##            }
##        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)
##
### -------------------------------------------------------------------------------------------------------------------------------------------


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        self.ctrl_virements = ListView(panel, id=-1, IDcompte_bancaire=1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_virements.MAJ() 
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl_virements, 1, wx.ALL|wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()



if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
