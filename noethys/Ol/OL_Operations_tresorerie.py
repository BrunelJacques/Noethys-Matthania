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
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, CTRL_Outils

from Utils import UTILS_Utilisateurs
from Utils import UTILS_Dates


class Track(object):
    def __init__(self, donnees):
        self.IDoperation = donnees["IDoperation"]
        self.typeOperation = donnees["typeOperation"]
        self.date = donnees["date"]
        self.libelle = donnees["libelle"]
        self.IDtiers = donnees["IDtiers"]
        self.IDmode = donnees["IDmode"]
        self.num_piece = donnees["num_piece"]
        self.ref_piece = donnees["ref_piece"]
        self.Dcompte_bancaire = donnees["IDcompte_bancaire"]
        self.IDreleve = donnees["IDreleve"]
        self.observations = donnees["observations"]
        self.nomTiers = donnees["nomTiers"]
        self.nomMode = donnees["nomMode"]
        self.nomCompte = donnees["nomCompte"]
        self.nomReleve = donnees["nomReleve"]
        self.montant = donnees["montant"]
        self.solde = donnees["solde"]
        self.IDvirement = donnees["IDvirement"]
        
        if self.typeOperation == "debit" :
            self.debit = self.montant
            self.credit = None
        else :
            self.debit = None
            self.credit = self.montant
            
    
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
        if self.IDcompte_bancaire != None :
            conditions = "WHERE compta_operations.IDcompte_bancaire=%d" % self.IDcompte_bancaire
        else :
            conditions = ""
        db = GestionDB.DB()
        req = """SELECT 
        IDoperation, type, date, libelle, compta_operations.IDtiers, compta_operations.IDmode, num_piece, ref_piece, compta_operations.IDcompte_bancaire, compta_operations.IDreleve, montant, compta_operations.observations, compta_operations.IDvirement,
        compta_tiers.nom, modes_reglements.label, comptes_bancaires.nom, compta_releves.nom
        FROM compta_operations 
        LEFT JOIN compta_tiers ON compta_tiers.IDtiers = compta_operations.IDtiers
        LEFT JOIN modes_reglements ON modes_reglements.IDmode = compta_operations.IDmode
        LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = compta_operations.IDcompte_bancaire
        LEFT JOIN compta_releves ON compta_releves.IDreleve = compta_operations.IDreleve
        %s
        ORDER BY date, IDoperation
        ;""" % conditions
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeListeView = []
        solde = 0.0
        soldePointe = 0.0
        soldeJour = 0.0
        for IDoperation, typeOperation, date, libelle, IDtiers, IDmode, num_piece, ref_piece, IDcompte_bancaire, IDreleve, montant, observations, IDvirement, nomTiers, nomMode, nomCompte, nomReleve in listeDonnees :
            date = UTILS_Dates.DateEngEnDateDD(date)
            if typeOperation == "debit" :
                montantTemp = - montant
            else :
                montantTemp = + montant
            solde += montantTemp
            if IDreleve != None :
                soldePointe += montantTemp
            if date <= datetime.date.today() :
                soldeJour += montantTemp
            dictTemp = {
                "IDoperation" : IDoperation, "typeOperation" : typeOperation, "date" : date, "libelle" : libelle, "IDtiers" : IDtiers, "IDmode" : IDmode, "num_piece" : num_piece, 
                "ref_piece" : ref_piece, "IDcompte_bancaire" : IDcompte_bancaire, "IDreleve" : IDreleve, "montant" : montant, "observations" : observations, "IDvirement" : IDvirement,
                "nomTiers" : nomTiers, "nomMode" : nomMode, "nomCompte" : nomCompte, "nomReleve" : nomReleve, "solde" : solde,
                }
            track = Track(dictTemp)
            listeListeView.append(track)
        
        self.ctrl_soldes.label_solde_jour.SetLabel(_("Solde du jour : %.2f %s") % (soldeJour, SYMBOLE))
        self.ctrl_soldes.label_solde_pointe.SetLabel(_("Solde point� : %.2f %s") % (soldePointe, SYMBOLE))
        self.ctrl_soldes.label_solde.SetLabel(_("Solde final : %.2f %s") % (solde, SYMBOLE))
        self.ctrl_soldes.Layout() 
        
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
            ColumnDefn(u"", "left", 0, "IDoperation", typeDonnee="entier"),
            ColumnDefn(_("Date"), 'left', 80, "date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Libell�"), 'left', 180, "libelle", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Tiers"), 'left', 130, "nomTiers", typeDonnee="texte"),
            ColumnDefn(_("Mode"), 'left', 90, "nomMode", typeDonnee="texte"),
            ColumnDefn(_("N� Ch�que"), 'left', 80, "num_piece", typeDonnee="texte"),
##            ColumnDefn(_("Compte bancaire"), 'left', 120, "nomCompte"),
            ColumnDefn(_("Relev�"), 'left', 90, "nomReleve", typeDonnee="texte"),
            ColumnDefn(_("D�bit"), "right", 80, "debit", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Cr�dit"), "right", 80, "credit", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Solde"), "right", 80, "solde", typeDonnee="montant", stringConverter=FormateMontant),
            ]

        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune op�ration de tr�sorerie"))
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
            ID = self.Selection()[0].IDoperation
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _("Ajouter une op�ration au d�bit"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Addition.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.AjouterDebit, id=10)

        item = wx.MenuItem(menuPop, 11, _("Ajouter une op�ration au cr�dit"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Addition.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.AjouterCredit, id=11)

        item = wx.MenuItem(menuPop, 12, _("Ajouter un virement"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Addition.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.AjouterVirement, id=12)

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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des op�rations"), format="A", orientation=wx.LANDSCAPE)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des op�rations"), format="A", orientation=wx.LANDSCAPE)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des op�rations"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des op�rations"))

    def AjouterDebit(self, event):
        self.Ajouter("debit")

    def AjouterCredit(self, event):
        self.Ajouter("credit")

    def AjouterVirement(self, event):
        dlg = DLG_Saisie_virement.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDvirement=dlg.GetIDvirement())
        dlg.Destroy()

    def Ajouter(self, typeOperation="credit"):
        dlg = DLG_Saisie_operation_tresorerie.Dialog(self, IDcompte_bancaire=self.IDcompte_bancaire, typeOperation=typeOperation, IDoperation=None)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDoperation=dlg.GetIDoperation())
        dlg.Destroy()

    def Modifier(self, event):
##        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_categories_comptables", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune op�ration � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.IDvirement != None :
            dlg = DLG_Saisie_virement.Dialog(self, track.IDvirement)
            if dlg.ShowModal() == wx.ID_OK:
                self.MAJ(IDvirement=track.IDvirement)
            dlg.Destroy()
        else :
            dlg = DLG_Saisie_operation_tresorerie.Dialog(self, IDcompte_bancaire=self.IDcompte_bancaire, typeOperation=track.typeOperation, IDoperation=track.IDoperation)
            if dlg.ShowModal() == wx.ID_OK:
                self.MAJ(IDoperation=dlg.GetIDoperation())
            dlg.Destroy()

    def Supprimer(self, event):
##        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_categories_comptables", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune op�ration � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        
        if track.IDvirement == None and track.IDreleve != None :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer une op�ration point�e sur un relev� bancaire !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        if track.IDvirement != None :
            # V�rifie que les 2 op�rations du virement ne sont pas sur un relev�
            DB = GestionDB.DB()
            req = """SELECT IDoperation, compta_operations.IDreleve, compta_releves.nom, comptes_bancaires.nom
            FROM compta_operations 
            LEFT JOIN compta_releves ON compta_releves.IDreleve = compta_releves.IDreleve
            LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = compta_releves.IDcompte_bancaire
            WHERE IDvirement=%d
            ;""" % track.IDvirement
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            for IDoperation, IDreleve, nomReleve, nomCompte in listeDonnees :
                if IDreleve != None :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer ce virement car il a d�j� �t� point� sur le relev� '%s' du compte '%s' !") % (nomReleve, nomCompte), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
            
        # Suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cette op�ration ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            if track.IDvirement == None :
                DB.ReqDEL("compta_operations", "IDoperation", track.IDoperation)
                DB.ReqDEL("compta_ventilation", "IDoperation", track.IDoperation)
            else :
                DB.ReqDEL("compta_virements", "IDvirement", track.IDvirement)
                DB.ReqDEL("compta_operations", "IDvirement", track.IDvirement)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()
    
    
# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview=None):
        wx.SearchCtrl.__init__(self, parent, size=(-1, 20), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = listview
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

class BarreSoldes(wx.Panel):
    def __init__(self, parent, listview=None):
        wx.Panel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        self.barreRecherche = CTRL_Outils(self, listview) # BarreRecherche(self, listview)
        self.barreRecherche.SetMinSize((350, -1))
        self.label_solde_jour = wx.StaticText(self, wx.ID_ANY, _("Solde du jour : 0.00 �"))
        self.label_solde_pointe = wx.StaticText(self, wx.ID_ANY, _("Solde point� : 0.00 �"))
        self.label_solde = wx.StaticText(self, wx.ID_ANY, _("Solde final : 0.00 �"))

        grid_sizer_1 = wx.FlexGridSizer(1, 5, 0, 0)
        grid_sizer_1.Add(self.barreRecherche, 0, wx.EXPAND, 0)
        grid_sizer_1.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_solde_jour, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        grid_sizer_1.Add(self.label_solde_pointe, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        grid_sizer_1.Add(self.label_solde, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 3)
        grid_sizer_1.AddGrowableRow(0)
        grid_sizer_1.AddGrowableCol(1)
        
        self.SetSizer(grid_sizer_1)
        grid_sizer_1.Fit(self)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
    def OnSize(self, event):
        self.Refresh() 
        event.Skip()



class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        self.ctrl_operations = ListView(panel, id=-1, IDcompte_bancaire=1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        
        self.ctrl_soldes = BarreSoldes(panel, listview=self.ctrl_operations)
        self.ctrl_operations.ctrl_soldes = self.ctrl_soldes
        
        self.ctrl_operations.MAJ() 
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl_operations, 1, wx.ALL|wx.EXPAND)
        sizer_2.Add(self.ctrl_soldes, 0, wx.ALL|wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 500))
        


if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
