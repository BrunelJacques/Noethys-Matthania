#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Gestion de la table matTarifs définissant les affectation des tarifs aux camps
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
from Utils import UTILS_Utilisateurs

class Track(object):
    def __init__(self, donnees):
        # "IDactivite", "IDgroupe", "IDcategorie_tarif","activite", "groupe", "categorie", "abregeGrp","dateFin"
        self.IDactivite = donnees["IDactivite"]
        self.IDgroupe = donnees["IDgroupe"]
        self.IDcategorie_tarif = donnees["IDcategorie_tarif"]
        self.activite = donnees["activite"]
        self.groupe = donnees["groupe"]
        self.categorie = donnees["categorie"]
        self.abregeGrp = donnees["abregeGrp"]
        self.dateFin = donnees["dateFin"]
        self.code = (self.IDactivite,self.IDgroupe,self.IDcategorie_tarif)
        self.tarif = donnees["tarif"]
        if donnees["campeur"] != None:
            self.effectif = ["Encadr.","Campeur","Autre"][donnees["campeur"]]
        else: self.effectif = "Campeur"
        self.len = len(donnees)

class ListView(FastObjectListView):
    def __init__(self,parent,*args, **kwds):
        self.parent = parent
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        FastObjectListView.__init__(self,parent, *args, **kwds)
        self.listeOLV = []
        # Binds perso
        #self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.nomTable = "matTarifs"
        self.listeChampsTrack = ["IDactivite", "IDgroupe", "IDcategorie_tarif","activite", "groupe", "categorie",
                                 "abregeGrp","dateFin","tarif","campeurGrp","campeur"]
        self.InitObjectListView()
        #fin _init

    def InitObjectListView(self):
        self.listeOLV = self.AppelDonnees()
        def FormateMontant(montant):
            if montant == None or montant == "": return ""
            return "%.2f " % (montant)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(_("Effectif"), "left", 70, "effectif", typeDonnee="texte"),
            ColumnDefn(_("Activité"), "left", 200, "activite", typeDonnee="texte"),
            ColumnDefn(_("Groupe"), 'left', 150,"groupe", typeDonnee="texte"),
            ColumnDefn(_("Catégorie"), 'left', 100,"categorie", typeDonnee="texte"),
            ColumnDefn(_("AbregeGrp"), 'left', 80,"abregeGrp", typeDonnee="texte"),
            ColumnDefn(_("DateFinCamp"), 'left', 80,"dateFin", typeDonnee="texte"),
            ColumnDefn(_("TarifAffecté"), 'left', 100, "tarif", typeDonnee="texte",isSpaceFilling = True),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_("Aucune affectation à définir"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.CreateCheckStateColumn()
        #coche les camps dans Tarifs
        objects = self.listeOLV
        for track in objects :
            self.SetCheckState(track, False)
            if track.tarif == self.parent.ctrl_code.GetValue():
                    self.SetCheckState(track, True)
        self.SetObjects(self.listeOLV)
        self.SortBy(0, ascending=False)
        #fin InitObjectListView

    def AppelDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        DB = GestionDB.DB()
        if hasattr(self.parent,"ctrl_annee"):
            debut = self.parent.ctrl_annee.GetValue()+"-01-01"
        else: debut = "2022-01-01"
        # constitution de toutes les lignes:  activités-groupes-catTarif dans un dictionnaire
        req = """
                SELECT activites.IDactivite, groupes.IDgroupe, categories_tarifs.IDcategorie_tarif, 
                        activites.nom, groupes.nom, categories_tarifs.nom, groupes.abrege, activites.date_fin, "-",
                        groupes.campeur, categories_tarifs.campeur
                FROM (activites 
                        INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite) 
                        INNER JOIN categories_tarifs ON activites.IDactivite = categories_tarifs.IDactivite
                WHERE (activites.date_fin > '%s')
                HAVING groupes.campeur = categories_tarifs.campeur
                ;"""%str(debut)
        retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()
        ddDonnees = {}
        # Transposition des données SQL dans le dict avec les noms de champs utilisés en track
        for item in recordset :
            dDonnees = {}
            i = 0
            for champ in self.listeChampsTrack :
                dDonnees[champ] = item[i]
                i += 1
            cle = item[:3]
            ddDonnees[cle] = dDonnees

        # préalimenter les tarifs déjà affectés
        req = """
                SELECT activites.IDactivite, groupes.IDgroupe, categories_tarifs.IDcategorie_tarif, 
                        matTarifs.trfCodeTarif, groupes.campeur, categories_tarifs.campeur
                FROM ((activites 
                        INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite) 
                        INNER JOIN categories_tarifs ON activites.IDactivite = categories_tarifs.IDactivite) 
                        INNER JOIN matTarifs ON (activites.IDactivite = matTarifs.trfIDactivite) 
                                                AND (groupes.IDgroupe = matTarifs.trfIDgroupe) 
                                                AND (categories_tarifs.IDcategorie_tarif = matTarifs.trfIDcategorie_tarif)
                WHERE (activites.date_fin > '%s')
                HAVING groupes.campeur = categories_tarifs.campeur
                ;"""%str(debut)
        retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()
        for item in recordset :
            cle = item[:3]
            ddDonnees[cle]["tarif"] = item[3]

        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeListeView = []
        for cle, dDonnees in list(ddDonnees.items()):
            track = Track(dDonnees)
            listeListeView.append(track)
        DB.Close()
        return listeListeView
        #fin AppelDonnees
    
    def SauveDonnees(self,listeCoches):
        tarif = str(self.parent.ctrl_code.GetValue())
        if len(tarif) > 0 :
            DB = GestionDB.DB()
            req =  "DELETE FROM matTarifs WHERE (matTarifs.trfCodeTarif= '"+ tarif +"');"
            retour = DB.ExecuterReq(req,MsgBox= "OL_TarifsLignesAffectations.SauveDonnees")
            if len(listeCoches) != 0 :
                i=0
                for activite, groupe, categorie in listeCoches :
                    i=i+1
                    listeDonnees=[("trfIDactivite",activite),("trfIDgroupe",groupe),("trfIDcategorie_tarif",categorie),
                                  ("trfCodeTarif", tarif) ]
                    retour = DB.ReqInsert("matTarifs",listeDonnees, retourID=False)
                    if retour != "ok" :
                        retour = DB.ReqMAJcles("matTarifs",listeDonnees[3:],listeDonnees[:3],
                                               MsgBox="OL_TarifsLignesAffectations.SauveDonnees Modif")
            DB.Close()

    def MAJ(self, ID=None):
         self.InitObjectListView()

    #Menu contextuel
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            #ID = self.Selection()[0].Code
        # Création du menu contextuel
        menuPop = wx.Menu()

        """
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
        """
                
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
    #fin ListView

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
        panel.ctrl_code = wx.TextCtrl(self, -1, "Param Main",size=(200,20))
        panel.ctrl_code.SetValue("P1;11-13")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(panel.ctrl_code, 0, wx.ALL,4)
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
