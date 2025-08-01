#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Utils import UTILS_Gestion
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, PanelAvecFooter, CTRL_Outils
import Olv.Filter as Filter
from Utils import UTILS_Utilisateurs


DICT_DETAILS_DEPOTS = {}


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

        
class Track(object):
    def __init__(self, donnees):
        self.IDdepot = donnees[0]
        self.date = donnees[1]
        if self.date != None :
            self.date = DateEngEnDateDD(self.date)
        else:
            self.date = datetime.date(1977, 1, 1)
        self.nom = donnees[2]
        self.verrouillage = donnees[3]
        self.IDcompte = donnees[4]
        self.nom_compte = donnees[5]
        self.numero_compte = donnees[6]
        self.observations = donnees[7]
        
        # D�tails
        if self.IDdepot in DICT_DETAILS_DEPOTS :
            dictDetails = DICT_DETAILS_DEPOTS[self.IDdepot]
            # Totaux du d�p�t
            self.nbre = dictDetails["nbre"]
            self.total = dictDetails["montant"]
            # Cr�ation du texte du d�tail
            texte = ""
            for IDmode, dictDetail in dictDetails.items() :
                if IDmode != "nbre" and IDmode != "montant" :
                    texteDetail = "%d %s (%.2f %s), " % (dictDetail["nbre"], dictDetail["nom"], dictDetail["montant"], SYMBOLE)
                    texte += texteDetail
            if len(dictDetails) > 2 :
                texte = texte[:-2]
            self.detail = texte
        else:
            self.nbre = 0
            self.total = 0.0
            self.detail = _("Aucun r�glement")

    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.limit = ""
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.GetDetailsDepots()
        self.donnees = self.GetTracks()
    
    def GetDetailsDepots(self):
        global DICT_DETAILS_DEPOTS
        DICT_DETAILS_DEPOTS = {}
        DB = GestionDB.DB()
        try:
            i = int(self.limit)
            limit = "LIMIT %s"%self.limit
        except: limit = "LIMIT 100"
        req = """SELECT 
        depots.IDdepot, reglements.IDmode, modes_reglements.label,
        SUM(reglements.montant), COUNT(reglements.IDreglement)
        FROM depots
        LEFT JOIN reglements ON reglements.IDdepot = depots.IDdepot
        LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements.IDmode
        GROUP BY depots.IDdepot, reglements.IDmode
        ORDER BY  depots.IDdepot DESC
        %s;
        """%limit
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        
        for IDdepot, IDmode, nom_mode, montant, nbre in listeDonnees :
            if IDmode != None :
                if (IDdepot in DICT_DETAILS_DEPOTS) == False :
                    DICT_DETAILS_DEPOTS[IDdepot] = {"nbre" : 0, "montant" : 0.0} 
                if (IDmode in DICT_DETAILS_DEPOTS[IDdepot]) == False :
                    DICT_DETAILS_DEPOTS[IDdepot][IDmode] = {"nom" : nom_mode, "nbre" : 0, "montant" : 0.0} 
                DICT_DETAILS_DEPOTS[IDdepot][IDmode]["nbre"] += nbre
                DICT_DETAILS_DEPOTS[IDdepot][IDmode]["montant"] += montant
                DICT_DETAILS_DEPOTS[IDdepot]["nbre"] += nbre
                DICT_DETAILS_DEPOTS[IDdepot]["montant"] += montant
                
    def GetTracks(self):
        """ R�cup�ration des donn�es """
        listeID = None
        db = GestionDB.DB()
        try:
            i = int(self.limit)
            limit = "LIMIT %s"%self.limit
        except: limit = "LIMIT 100"

        req = """SELECT 
        IDdepot, depots.date, depots.nom, verrouillage, 
        depots.IDcompte, comptes_bancaires.nom, comptes_bancaires.numero, 
        observations
        FROM depots
        LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
        ORDER BY IDdepot DESC
        %s;
        """%limit
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        
        listeListeView = []
        for item in listeDonnees :
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(item)
                listeListeView.append(track)
                if self.selectionID == item[0] :
                    self.selectionTrack = track
        return listeListeView
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        # Image list
        self.imgVerrouillage = self.AddNamedImages("verrouillage", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas_ferme.png"), wx.BITMAP_TYPE_PNG))
        
        def GetImageVerrouillage(track):
            if track.verrouillage == 1 :
                return self.imgVerrouillage
            else:
                return None
                    
        def FormateDateLong(dateDD):
            if dateDD == datetime.date(1977, 1, 1) :
                return ""
            else:
                return DateComplete(dateDD)

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 55, "IDdepot", typeDonnee="entier", imageGetter=GetImageVerrouillage),
            ColumnDefn(_("Date"), 'left', 80, "date", typeDonnee="date", stringConverter=FormateDateCourt),
            ColumnDefn(_("Nom"), 'left', 170, "nom", typeDonnee="texte"),
            ColumnDefn(_("Compte"), 'left', 120, "nom_compte", typeDonnee="texte"),
            ColumnDefn(_("Observations"), 'left', 100, "observations", typeDonnee="texte"),
            ColumnDefn(_("Nbre"), 'centre', 40, "nbre", typeDonnee="entier"),
            ColumnDefn(_("Total"), 'right', 75, "total", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("D�tail"), 'left', 210, "detail", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun d�p�t"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[0],ascending=False)
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        # S�lection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None :
            self.DefilePremier()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDdepot
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des d�p�ts"), format="A", orientation=wx.LANDSCAPE)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des d�p�ts"), format="A", orientation=wx.LANDSCAPE)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des d�p�ts"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des d�p�ts"))

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("reglements_depots", "creer") == False : return
        from Dlg import DLG_Saisie_depot
        dlg = DLG_Saisie_depot.Dialog(self, IDdepot=None) 
        dlg.ShowModal()
        IDdepot = dlg.GetIDdepot()
        self.MAJ(IDdepot)
        self.GetGrandParent().MAJreglements()
        dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("reglements_depots", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun d�p�t � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDdepot = self.Selection()[0].IDdepot
        from Dlg import DLG_Saisie_depot
        dlg = DLG_Saisie_depot.Dialog(self, IDdepot=IDdepot)      
        dlg.ShowModal()
        self.MAJ(IDdepot)
        self.GetGrandParent().MAJreglements()
        dlg.Destroy() 

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("reglements_depots", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun d�p�t � supprimer dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        IDdepot = self.Selection()[0].IDdepot
        nbre_reglements = self.Selection()[0].nbre
        if nbre_reglements > 0 :
            dlg = wx.MessageDialog(self, _("Des r�glements sont d�j� associ�s � ce d�p�t. Vous ne pouvez donc pas le supprimer !"), _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # P�riodes de gestion
        gestion = UTILS_Gestion.Gestion(None)
        if gestion.Verification("depots", track.date) == False: return False

        # Confirmation
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce d�p�t ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("depots", "IDdepot", IDdepot)
            DB.Close() 
            self.MAJ()
            self.GetGrandParent().MAJreglements()
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un d�p�t..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_depots
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
        self.listView.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nom" : {"mode" : "nombre", "singulier" : _("d�p�t"), "pluriel" : _("d�p�ts"), "alignement" : wx.ALIGN_CENTER},
            "nbre" : {"mode" : "total"},
            "total" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

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
        self.SetSize((890, 200))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
