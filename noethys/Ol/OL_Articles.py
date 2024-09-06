#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Gestion de la table Articles définissant le regroupement des lignes
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
from Dlg import DLG_SaisieArticles
from Data import DATA_Tables
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

class Track(object):
    def __init__(self, donnees):
        self.code = donnees["code"]
        self.libelle = donnees["libelle"]
        self.conditions = donnees["conditions"]
        self.calcul = donnees["calcul"]
        if donnees["prix1"]== None:
            self.prix1=0
        else: self.prix1 = donnees["prix1"]
        if donnees["prix2"]== None:
            self.prix2=0
        else: self.prix2 = donnees["prix2"]
        self.facture = donnees["facture"]
        self.compta = donnees["compta"]
        if donnees["nivActivite"]== None:
            self.nivActivite = 1
        else: self.nivActivite = donnees["nivActivite"]
        if donnees["nivFamille"]== None:
            self.nivFamille = 1
        else: self.nivFamille = donnees["nivFamille"]
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
        self.nomTable = "matArticles"
        self.champCle = "artCodeArticle"
        self.listeChampsSQL = [str((a)) for a, b, c in DATA_Tables.DB_DATA[self.nomTable]]
        self.listeChampsTrack = ["code", "libelle", "conditions", "calcul", "prix1", "prix2", "facture", "compta","nivFamille","nivActivite",]
        if len(self.listeChampsSQL) != len(self.listeChampsTrack) :
            GestionDB.MessageBox(self, "Problème programmation des champs : " + self.nomTable)
            self.Destroy()

    def GetDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        champsSQL = ""
        for item in self.listeChampsSQL :
            champsSQL = champsSQL  + item + ", "
        self.champsSQL = champsSQL[:-2]
        DB = GestionDB.DB()
        req =  "SELECT " + self.champsSQL + " FROM " + self.nomTable +" ORDER BY " + self.champCle+ "; "
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        DB.Close()
        # Transposition des données SQL avec les noms de champs utilisés en track
        for item in recordset :
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            donnees.append(record)
        return donnees

    def GetTracks(self):
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        donnees = self.GetDonnees()
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item["code"]:
                self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        self.listeOLV = self.GetTracks()
        def FormateMontant(montant):
            if montant == None or montant == "": return ""
            return "%.2f" % (montant)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(_("Null"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_("Code"), "left", 80, "code", typeDonnee="texte"),
            ColumnDefn(_("Libelle"), 'left', 150,"libelle", typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_("Conditions"), 'left', 60,"conditions", typeDonnee="texte"),
            ColumnDefn(_("Calcul"), 'left', 60, "calcul", typeDonnee="texte"),
            ColumnDefn(_("Valeur1"), 'right', 60, "prix1", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Valeur2"), 'right', 60, "prix2", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Facture"), 'left',60, "facture", typeDonnee="texte"),
            ColumnDefn(_("Compta"), 'left',60, "compta", typeDonnee="texte"),
            ColumnDefn(_("Fam"), 'left',40, "nivFamille", typeDonnee="entier"),
            ColumnDefn(_("Act"), 'left',30, "nivActivite", typeDonnee="entier"),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_("Aucun article défini"))
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
            ID = self.Selection()[0].code
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des articles"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des articles"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def SaisieArticle(self, selection, mode):
        articleNomsSQL = []
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits de paramétrage des  activités")
        else :
            dlg = DLG_SaisieArticles.Dialog(self,mode)
            if mode != "ajout" :
                dlg.SetArticle(selection[0])
            else: dlg.CreeArticle()
            if dlg.ShowModal() == wx.ID_OK:
                articleTrack = dlg.GetArticle()
                for i in range(len(articleTrack)) :
                    articleNomsSQL.append((self.listeChampsSQL[self.listeChampsTrack.index(articleTrack[i][0])],articleTrack[i][1]))
            dlg.Destroy()
        return articleNomsSQL

    def Ajouter(self, event):
        article = self.SaisieArticle(None,"ajout")
        if len(article) == 0 :return
        DB = GestionDB.DB()
        retour = DB.ReqInsert(self.nomTable, article,retourID=False)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            GestionDB.MessageBox(self, "Vous n'avez sélectionné aucun article dans la liste")
            return
        index = self.SelectedItemCount
        oldCode = self.Selection()[0].code
        article = self.SaisieArticle(self.Selection(),"modif")
        if len(article) == 0 :return
        DB = GestionDB.DB()
        retour = DB.ReqDEL(self.nomTable, self.champCle, oldCode)
        if retour == "ok":
            retour = DB.ReqInsert(self.nomTable, article,retourID=False)
        if retour != "ok":
            dlg = wx.MessageDialog(self, _("Erreur lors de la MAJ"), retour, wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return
        DB.Close()
        #self.SetSelection(index)
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun article dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Vérifie que ce type de article n'a pas déjà été utilisé
        DB = GestionDB.DB()
        req ="""SELECT COUNT(ligCodeArticle)
                FROM matPiecesLignes
                WHERE ligCodeArticle = '%s'
              """  % str(track.code)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        resultat = DB.ResultatReq()
        nbreArticles = resultat[0][0]
        if nbreArticles > 0 :
            dlg = wx.MessageDialog(self, _("Cet article '%s' a déjà été attribué %d fois.\n\nVous ne pouvez donc pas le supprimer !") % (track.code,nbreArticles), _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cet article ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            retour = DB.ReqDEL(self.nomTable, self.champCle, track.code )
            ret = DB.ReqDEL("matTarifsLignes", "trlCodeArticle", track.code )
            DB.Close()
            if retour == "ok" :
                self.MAJ()
            else :
                dlgErr = wx.MessageDialog(self,retour)
                dlgErr.ShowModal()
                dlgErr.Destroy()
            self.MAJ()
        dlg.Destroy()

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
