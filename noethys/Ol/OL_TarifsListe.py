#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Gestion de la table TarifsNoms définissant les noms des différents tarifs
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
from Dlg import DLG_TarifsLignes
from Data import DATA_Tables
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

class Track(object):
    def __init__(self, donnees):
        self.code = donnees["code"]
        self.libelle = donnees["libelle"]
        self.nbLignes = donnees["nbLignes"]
        self.nbActivites = donnees["nbActivites"]
        self.len = len(donnees)

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        FastObjectListView.__init__(self, *args, **kwds)
        self.listeOLV = []
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.nomTable = "matTarifsNoms"
        self.champCle = "trnCodeTarif"
        self.listeChampsSQL = [str((a)) for a, b, c in DATA_Tables.DB_DATA[self.nomTable]]
        self.listeChampsTrack = ["code", "libelle","nbLignes"]
        if len(self.listeChampsSQL) != len(self.listeChampsSQL) :
            GestionDB.MessageBox(self, "Problème programmation des champs : " + self.nomTable)
            self.Destroy()

    def GetDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        champsSQL = ""
        for item in self.listeChampsSQL :
            champsSQL = champsSQL  + item + ", "
        champsSQL = champsSQL + ""
        self.champsSQL = champsSQL[:-2]
        DB = GestionDB.DB()
        req =   """
                SELECT matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle, Count(matTarifsLignes.trlNoLigne) AS CompteDetrlNoLigne
                FROM matTarifsNoms LEFT JOIN matTarifsLignes ON matTarifsNoms.trnCodeTarif = matTarifsLignes.trlCodeTarif
                GROUP BY matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle;
                """
        retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()
        req =   """
                SELECT matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle, Count(matTarifs.trfIDcategorie_tarif) AS CompteDetrfIDcategorie_tarif
                FROM matTarifsNoms LEFT JOIN matTarifs ON matTarifsNoms.trnCodeTarif = matTarifs.trfCodeTarif
                GROUP BY matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle;
                """
        retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" : DB.AfficheErr(self,retour)
        recordset2 = DB.ResultatReq()
        DB.Close()
        # Transposition des données SQL avec les noms de champs utilisés en track
        for item in recordset :
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            for item2 in recordset2 :
                if item2[0] == item[0]:
                    record["nbActivites"] = item2[2]
            donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item["code"]:
                self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        self.listeOLV = self.GetDonnees()
        def FormateEntier(entier):
            if entier == None or entier == "": return ""
            return "%.2f" % (entier)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(_("Null"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_("Code"), "left", 80, "code", typeDonnee="texte"),
            ColumnDefn(_("Libelle"), 'left', 350,"libelle", typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_("NbActivites"), 'right', 70, "nbActivites", typeDonnee="entier", stringConverter=FormateEntier),
            ColumnDefn(_("NbLignes"), 'right', 70, "nbLignes", typeDonnee="entier", stringConverter=FormateEntier),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_("Aucun nom défini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.listeOLV)

    def OnItemActivated(self,event):
        self.Modifier(None)

    def MAJ(self, ID=None):
         self.InitObjectListView()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].Code
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des noms de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des noms de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def SaisieNom(self, selection, mode):
        nomNomsSQL = []
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits de paramétrage des  activités")
        else :
            dlg = DLG_TarifsLignes.Dialog(self,mode)
            if mode == "modif" :
                dlg.SetNomTarif(selection[0])
            if dlg.ShowModal() == wx.ID_OK:
                nomTrack = dlg.GetNomTarif()
                for i in range(len(nomTrack)) :
                    nomNomsSQL.append((self.listeChampsSQL[self.listeChampsTrack.index(nomTrack[i][0])],nomTrack[i][1]))
            dlg.Destroy()
        return nomNomsSQL

    def Ajouter(self, event):
        nom = self.SaisieNom(None,"ajout")
        if len(nom) == 0 :return
        DB = GestionDB.DB()
        retour = DB.ReqInsert(self.nomTable, nom,retourID=False)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            GestionDB.MessageBox(self, "Vous n'avez sélectionné aucun tarif dans la liste")
            return
        index = self.SelectedItemCount
        nom = self.SaisieNom(self.Selection(),"modif")
        if len(nom) == 0 :return
        DB = GestionDB.DB()
        retour = DB.ReqMAJ( self.nomTable, nom, self.champCle, nom[0][1],True)
        DB.Close()
        #self.SetSelection(index)
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun tarif dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Vérifie que ce type de nom de tarif n'a pas déjà été utilisé
        DB = GestionDB.DB()
        req ="""SELECT COUNT (trlCodeTarif)
                FROM matTarifsLignes
                WHERE trlCodeTarif = '%s'
              """  %track.code
        DB.ExecuterReq(req,MsgBox = "Supprimer")
        resultat = DB.ResultatReq()

        if resultat != [] :
            nbreNoms = resultat[0][0]
            dlg = wx.MessageDialog(self, _("Ce Tarif a %d ligne(s) attribuée(s).\n\nIl faut d'abord supprimer les lignes associées !") % nbreNoms, _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce Tarif ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            retour = DB.ReqDEL(self.nomTable, self.champCle, track.code )
            DB.Close()
            if retour == "ok" :
                self.MAJ()
            else :
                dlgErr = wx.MessageDialog(self,retour)
                dlgErr.ShowModal()
                dlgErr.Destroy()
            self.MAJ()
        dlg.Destroy()
#fin listview

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un Bloc..."))
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
        txtSearch = self.GetValue().replace("'","\\'")
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
