#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
import datetime
from Utils import UTILS_Titulaires
from Utils import UTILS_Utilisateurs

from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils


def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def GetListe(listeActivites=None, presents=None):
    if listeActivites == None : return {} 
    
    # R�cup�ration des donn�es
    dictItems = {}

    # Conditions Activites
    if listeActivites == None or listeActivites == [] :
        conditionActivites = ""
    else:
        if len(listeActivites) == 1 :
            conditionActivites = " AND inscriptions.IDactivite=%d" % listeActivites[0]
        else:
            conditionActivites = " AND inscriptions.IDactivite IN %s" % str(tuple(listeActivites))

    # Conditions Pr�sents
##    if presents == None :
##        conditionPresents = ""
##        jointurePresents = ""
##    else:
##        conditionPresents = " AND (consommations.date>='%s' AND consommations.date<='%s')" % (str(presents[0]), str(presents[1]))
##        jointurePresents = "LEFT JOIN consommations ON consommations.IDindividu = individus.IDindividu"

    DB = GestionDB.DB()

    # R�cup�ration des pr�sents
    listePresents = []
    if presents != None :
        req = """SELECT IDfamille, inscriptions.IDinscription
        FROM consommations
        LEFT JOIN inscriptions ON inscriptions.IDinscription = consommations.IDinscription
        WHERE date>='%s' AND date<='%s' %s
        GROUP BY IDfamille
        ;"""  % (str(presents[0]), str(presents[1]), conditionActivites.replace("inscriptions", "consommations"))
        DB.ExecuterReq(req,MsgBox="OL_Liste_regimes")
        listeIndividusPresents = DB.ResultatReq()
        for IDfamille, IDinscription in listeIndividusPresents :
            listePresents.append(IDfamille)

    req = """
            SELECT inscriptions.IDfamille, regimes.nom, caisses.nom, familles.num_allocataire, familles.aides_vacances
            FROM (((inscriptions 
            LEFT JOIN individus ON inscriptions.IDindividu = individus.IDindividu) 
            LEFT JOIN familles ON (inscriptions.IDfamille = familles.IDfamille) 
                                AND (inscriptions.IDfamille = familles.IDfamille)) 
            LEFT JOIN caisses ON familles.IDcaisse = caisses.IDcaisse) 
            LEFT JOIN regimes ON caisses.IDregime = regimes.IDregime
            WHERE (caisses.IDcaisse Is Not Null) 
                    %s
            GROUP BY inscriptions.IDfamille, regimes.nom, caisses.nom, familles.num_allocataire,familles.aides_vacances;
        """ % conditionActivites

    DB.ExecuterReq(req,MsgBox="OL_Liste_regimes")
    listeFamilles = DB.ResultatReq()
    DB.Close() 
    
    # Formatage des donn�es
    dictFinal = {}
    titulaires = UTILS_Titulaires.GetTitulaires() 
    for IDfamille, nomRegime, nomCaisse, numAlloc,allocataire in listeFamilles :
        
        if presents == None or (presents != None and IDfamille in listePresents) :
            
            if IDfamille != None and IDfamille in list(titulaires.keys()):
                nomTitulaires = titulaires[IDfamille]["titulairesSansCivilite"]
            else :
                nomTitulaires = _("Aucun titulaire")
            dictFinal[IDfamille] = {
                "IDfamille" : IDfamille, "titulaires" : nomTitulaires, "nomRegime" : nomRegime, 
                "nomCaisse" : nomCaisse,
                "numAlloc" : numAlloc,
                "allocataire" : allocataire
                }
    
    return dictFinal


def GetFamillesSansCaisse(listeActivites=None, date_debut=None, date_fin=None):
    """ Permet de r�cup�rer la liste des familles n'ayant pas de caisse renseign�e """
    dictDonnees = GetListe(listeActivites=listeActivites, presents=(date_debut, date_fin))
    listeFamillesSansCaisse = []
    for IDfamille, dictFamille in dictDonnees.items() :
        if dictFamille["nomCaisse"] == None :
            listeFamillesSansCaisse.append({"IDfamille" : IDfamille, "titulaires" : dictFamille["titulaires"]})
    return listeFamillesSansCaisse

# -----------------------------------------------------------------------------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.IDfamille = donnees["IDfamille"]
        self.nomTitulaires = donnees["titulaires"]
        self.nomRegime = donnees["nomRegime"]
        self.nomCaisse = donnees["nomCaisse"]
        self.numAlloc = donnees["numAlloc"]
        alloc = ""
        if donnees["allocataire"] == 1:
            alloc = "oui"
        elif donnees["allocataire"] == 0:
            alloc = "non"
        self.allocataire = alloc

    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.dateReference = None
        self.listeActivites = None
        self.presents = None
        self.concernes = False
        self.labelParametres = ""
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
                        
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        dictDonnees = GetListe(self.listeActivites, self.presents)
        listeListeView = []
        for IDfamille, dictTemp in dictDonnees.items() :
            track = Track(dictTemp)
            listeListeView.append(track)
            if self.selectionID == IDfamille :
                self.selectionTrack = track
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 50, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_("Famille"), 'left', 220, "nomTitulaires", typeDonnee="texte"),
            ColumnDefn(_("R�gime"), "left", 90, "nomRegime", typeDonnee="texte"),
            ColumnDefn(_("Caisse"), "left", 120, "nomCaisse", typeDonnee="texte"),
            ColumnDefn(_("Num�ro Alloc."), "left", 110, "numAlloc", typeDonnee="texte"),
            ColumnDefn(_("OKaides"), "left", 70, "allocataire", typeDonnee="texte"),
            ]        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune famille"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, listeActivites=None, presents=None, labelParametres=""):
        self.listeActivites = listeActivites
        self.presents = presents
        self.labelParametres = labelParametres
        attente = wx.BusyInfo(_("Recherche des donn�es..."), self)
        self.InitModel()
        self.InitObjectListView()
        del attente
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDfamille
            
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()
        
        # Item Ouvrir fiche famille
        item = wx.MenuItem(menuPop, 70, _("Ouvrir la fiche famille correspondante"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=70)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
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

        menuPop.AppendSeparator()

        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)

        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune fiche famille � ouvrir !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.InitModel()
            self.InitObjectListView()
        dlg.Destroy()

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donn�e � imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        intro = self.labelParametres
        total = _("> %d familles") % len(self.donnees)
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des r�gimes et caisses"), intro=intro, total=total, format="A", orientation=wx.PORTRAIT)
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
        UTILS_Export.ExportTexte(self, titre=_("Liste des r�gimes et caisses"))

    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des r�gimes et caisses"))


# -------------------------------------------------------------------------------------------------------------------------------------


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher une information..."))
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
        import time
        t = time.time()
        self.myOlv.MAJ(listeActivites=(1, 2, 3), presents=(datetime.date(2015, 1, 1), datetime.date(2015, 12, 31))) 
        print(len(self.myOlv.donnees))
        print("Temps d'execution =", time.time() - t)
##        print "Nbre familles sans caisse =", GetNbreSansCaisse(listeActivites=(1, 2, 3), date_debut=datetime.date(2010, 1, 5), date_fin=datetime.date(2011, 1, 5))
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
