#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Gestion de l'ajout d'articles apparaissant dans la tarification d'une inscription
# Gestion de la recherche d'une famille puis incorporation
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import Chemins
import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn,Filter, CTRL_Outils

# ----Choix d'une famille -------------------------------------------------------------------
class TrackFamille(object):
    def __init__(self, track):
        if track == None:
            self.IDfamille = None
            self.designation = None
            self.ville = None
        else:
            self.IDfamille = track["IDfamille"]
            self.designation = track["designation"]
            self.ville = track["ville"]

class OLVchoixFamille(FastObjectListView):
    def __init__(self,parent,*args, **kwds):
        self.parent = parent
        FastObjectListView.__init__(self, parent, *args, **kwds)
        self.listeChampsTrack = ["IDfamille", "designation", "ville"]
        self.InitObjectListView()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        #fin __init__

    def OnItemActivated(self,event):
        self.parent.OnBoutonOk(None)

    def AppelDonnees(self):
            donnees= []
            DB = GestionDB.DB()
            req =  """SELECT rattachements.IDfamille, individus.nom, individus.prenom, individus.ville_resid
                    FROM rattachements INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
                    WHERE (rattachements.titulaire=1)
                    GROUP BY rattachements.IDfamille, individus.nom, individus.prenom, individus.ville_resid;
                    """
            retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" : DB.AfficheErr(self,retour)
            recordset = DB.ResultatReq()
            DB.Close()
            self.dicFamille = {}
            for IDfamille, nomInd, prenomInd, villeInd in recordset:
                if not nomInd : nomInd=''
                if not prenomInd : prenomInd=''
                if not villeInd : villeInd=''
                if IDfamille not in list(self.dicFamille.keys()):
                    self.dicFamille[IDfamille] = {}
                    self.dicFamille[IDfamille]['nom']= nomInd
                    self.dicFamille[IDfamille]['prenom']= prenomInd
                    self.dicFamille[IDfamille]['ville']= villeInd
                    self.dicFamille[IDfamille]['designation'] = nomInd + " " +prenomInd
                else:
                    if not nomInd in self.dicFamille[IDfamille]["nom"]:
                        self.dicFamille[IDfamille]['designation'] += " & "+ nomInd + " " + prenomInd
                        self.dicFamille[IDfamille]['nom'] += nomInd
                        self.dicFamille[IDfamille]['prenom'] += prenomInd
                    else:
                        self.dicFamille[IDfamille]['designation'] += " & "+ prenomInd
                        self.dicFamille[IDfamille]['prenom'] += " & "+ prenomInd

                    if villeInd != self.dicFamille[IDfamille]["ville"]:
                        if len(self.dicFamille[IDfamille]["ville"])>1 and len(villeInd)>1:
                            et = ' & '
                        else: et = ''
                        self.dicFamille[IDfamille]['ville'] += (et + villeInd)

            # Transposition des données SQL avec les noms de champs utilisés en track
            for key in list(self.dicFamille.keys()):
                i = 0
                record = {}
                item = [key, self.dicFamille[key]['designation'], self.dicFamille[key]['ville']]
                for champ in self.listeChampsTrack :
                    record[champ] = item[i]
                    i= i +1
                donnees.append(record)
            #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
            listeOLV = []
            for item in donnees:
                track = TrackFamille(item)
                listeOLV.append(track)
            listeOLV.append(TrackFamille(None))
            return listeOLV
        #fin AppelDonnees

    def InitObjectListView(self):
        self.listeOLV = self.AppelDonnees()
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn("Code", "center", 50, "IDfamille",typeDonnee="texte"),
            ColumnDefn("Designation", "left", 150, "designation", typeDonnee="texte",isSpaceFilling = True ),
            ColumnDefn("Ville", "left", 150, "ville",typeDonnee="texte",isSpaceFilling = True),
            ]
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune famille définie"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.listeOLV)
        #fin InitObjectListView
        
    def GetParrain(self,IDparrain):
            self.nomChoix = self.dicFamille[IDparrain]['designation'] + " / "+self.dicFamille[IDparrain]['ville']
            #fin GetParrain


class DlgChoixFamille(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent=None,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        """Constructor"""
        self.SetTitle("DLG_ChoixLigne :Choix d'une famille")
        self.parent = parent
        self.choix = None
        self.label_famille = wx.StaticText(self, -1, _("Famille choisie :"))
        self.olv_famille = OLVchoixFamille(self)
        self.olv_famille.Select(0)
        self.olv_famille.SetToolTip(_("Sélectionnez lafamille parmi la liste"))
        self.ctrl_recherche = CTRL_Outils(self, listview=self.olv_famille)
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Choisir"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Annuler_L72.png"), wx.BITMAP_TYPE_ANY))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.__do_layout()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)

        grid_sizer_haut = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_haut.Add(self.label_famille, 1, wx.LEFT | wx.TOP, 5)
        grid_sizer_haut.Add(self.olv_famille, 1, wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        grid_sizer_haut.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_haut.AddGrowableRow(1)
        grid_sizer_haut.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.EXPAND, 0)

        grid_sizer_bas = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_bas.Add((10,10), 0, wx.ALIGN_LEFT, 0)
        grid_sizer_bas.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.SetMinSize((550, 450))
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonOk(self, event):
        self.IDchoix = self.olv_famille.GetSelectedObjects()[0].IDfamille
        if self.IDchoix == None: self.nomChoix = " "
        else : self.nomChoix = self.olv_famille.GetSelectedObjects()[0].designation + " / "+str(self.olv_famille.GetSelectedObjects()[0].ville)
        self.EndModal(wx.ID_OK)


# ----Choix d'un article -------------------------------------------------------------------
class Track(object):
    def __init__(self, track):
        self.codeArticle = track["codeArticle"]
        self.libelle = track["libelle"]
        if track["prix"] == None: self.prixUnit = 0
        else : self.prixUnit = track["prix"]
        self.qte = 1
        self.montant = 0
        self.montantCalcul = self.prixUnit * self.qte
        self.len = len(track)+3

class OLVchoixArticles(FastObjectListView):
    def __init__(self,parent,niveau= 'Famille',*args, **kwds):
        self.parent = parent
        self.niveau = niveau
        FastObjectListView.__init__(self, parent, *args, **kwds)
        self.listeChampsTrack = ["codeArticle", "libelle", "prix"]
        self.InitObjectListView()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.parent.OnBoutonOk)
        #fin __init__

    def AppelDonnees(self,niveau = "Famille"):
            donnees= []
            DB = GestionDB.DB()
            if niveau == "Famille":
                req =  """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1
                        FROM matArticles
                        WHERE artNiveauFamille = 1 OR artNiveauFamille Is Null;
                        """
            else:
                req =  """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1
                        FROM matArticles
                        WHERE artNiveauActivite = 1 OR artNiveauActivite Is Null;
                        """
            retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" : DB.AfficheErr(self,retour)
            recordset = DB.ResultatReq()
            DB.Close()
            # Transposition des données SQL avec les noms de champs utilisés en track
            for item in recordset:
                i = 0
                record = {}
                for champ in self.listeChampsTrack :
                    record[champ] = item[i]
                    i= i +1
                donnees.append(record)
            #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
            listeOLV = []
            for item in donnees:
                track = Track(item)
                listeOLV.append(track)
            return listeOLV
        #fin AppelDonnees

    def InitObjectListView(self):
        self.listeOLV = self.AppelDonnees(self.niveau)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn("Code", "center", 100, "codeArticle",typeDonnee="texte"),
            ColumnDefn("Libelle (libelles modifiables)", "left", 300, "libelle", typeDonnee="texte",isSpaceFilling = True ),
            ColumnDefn("Prix1", "right", 100, "prixUnit",typeDonnee="montant",stringConverter="%.2f"),
            ]
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun article défini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.CreateCheckStateColumn()
        self.SetObjects(self.listeOLV)
        #fin InitObjectListView

class DlgChoixArticle(wx.Dialog):
    def __init__(self, parent, niveau = 'Famille'):
        wx.Dialog.__init__(self, parent=None,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        """Constructor"""
        self.SetTitle("DLG_ChoixLigne :Choix d'un article")
        self.parent = parent
        self.choix = None
        self.label_article = wx.StaticText(self, -1, _("Article à ajouter :"))
        self.olv_article = OLVchoixArticles(self,niveau)
        self.olv_article.Select(0)
        self.olv_article.SetToolTip(_("Sélectionnez l'article parmi la liste"))
        self.ctrl_recherche = CTRL_Outils(self, listview=self.olv_article)
        self.bouton_gestionTarifs = CTRL_Bouton_image.CTRL(self, texte=_("Gestion Tarifs"), cheminImage="Images/32x32/Configuration.png")
        self.bouton_gestionArticles = CTRL_Bouton_image.CTRL(self, texte=_("Gestion Articles"), cheminImage="Images/32x32/Configuration.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ajouter"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Annuler_L72.png"), wx.BITMAP_TYPE_ANY))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnGestionTarifs, self.bouton_gestionTarifs)
        self.Bind(wx.EVT_BUTTON, self.OnGestionArticles, self.bouton_gestionArticles)
        self.__do_layout()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)

        grid_sizer_haut = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_haut.Add(self.label_article, 1, wx.LEFT | wx.TOP, 5)
        grid_sizer_haut.Add(self.olv_article, 1, wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        grid_sizer_haut.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_haut.AddGrowableRow(1)
        grid_sizer_haut.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.EXPAND, 0)

        grid_sizer_bas = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=5)
        grid_sizer_bas.Add(self.bouton_gestionTarifs, 0, wx.ALIGN_LEFT, 0)
        grid_sizer_bas.Add(self.bouton_gestionArticles, 0, wx.ALIGN_LEFT, 0)
        grid_sizer_bas.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_bas.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.SetMinSize((550, 450))
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonOk(self, event):
        # Coche l'enregistrement selectionné
        for obj in self.olv_article.GetSelectedObjects():
            self.olv_article.SetCheckState(obj, True)
        # Nouvelle instance olv pour récupérer les lignes selectionnées
        olv_selection = OLVchoixArticles(self)
        olv_selection.listeOLV=[]
        for obj in self.olv_article.GetObjects():
            if self.olv_article.IsChecked(obj):
                olv_selection.listeOLV.append(obj)
        olv_selection.SetObjects(olv_selection.listeOLV)
        for obj in olv_selection:
            olv_selection.SetCheckState(obj,True)
        # met les lignes sous forme de dictionnaires
        listeLignes = self.parent.ListeDict(olv_selection)
        for ligne in listeLignes:
            self.parent.listeLignes.append(ligne)
        self.EndModal(wx.ID_OK)

    def OnGestionTarifs(self, event):
        from Dlg import DLG_TarifsListe
        DLG = DLG_TarifsListe.Dialog(None)
        DLG.ShowModal()
        DLG.Destroy()

    def OnGestionArticles(self, event):
        from Dlg import DLG_Articles
        DLG = DLG_Articles.Dialog(None)
        DLG.ShowModal()
        DLG.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText(_("Rechercher un Bloc..."))
        self.ShowSearchButton(True)

        self.listView = self.parent.olv_article
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
"""
class MyFrame(wx.Frame):
    def __init__(self,  *args, **kwds):
        wx.Frame.__init__(self,  *args,**kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        listeDonnees = [
            ("IDactivite", 376),
            ("IDgroupe" , 767),
            ("IDcategorie_tarif", 767),
            ]
        dictDonnees = {}
        for donnee in listeDonnees:
            champ = donnee[0]
            valeur = donnee[1]
            dictDonnees[champ] = valeur
        self.myOlv = ListView(panel,dictDonnees, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ()
        #self.myOlv = OLVarticles(panel,id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
"""

if __name__ == '__main__':
    app = wx.App(0)
    f = DlgChoixFamille(None)
    app.SetTopWindow(f)
    if f.ShowModal() == wx.ID_OK:
        print("OK")
    app.MainLoop()
