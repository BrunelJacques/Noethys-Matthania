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
import GestionDB
from Utils import UTILS_Dates
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils



class Track(object):
    def __init__(self, donnees):
        self.IDlot = donnees[0]
        self.nom = donnees[1]
        self.date = donnees[2]
        self.verrouillage = donnees[3]
        self.observations = donnees[4]
        self.typePrelevement = donnees[5]
        if self.typePrelevement == "sepa" : 
            self.typePrelevementStr = _("SEPA")
        else :
            self.typePrelevementStr = _("National")
            self.typePrelevement = "national"
        self.nbrePrelevements = donnees[6]
        
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        listeID = None
        db = GestionDB.DB()
        req = """SELECT lots_prelevements.IDlot, lots_prelevements.nom, lots_prelevements.date, lots_prelevements.verrouillage, lots_prelevements.observations, lots_prelevements.type, Count(prelevements.IDlot) AS nbrePrelevements
        FROM lots_prelevements
        LEFT JOIN prelevements ON prelevements.IDlot = lots_prelevements.IDlot
        GROUP BY lots_prelevements.IDlot;"""
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

        def FormateDate(dateDD):
            if dateDD == None : return ""
            return UTILS_Dates.DateEngFr(str(dateDD))

        def GetImageVerrouillage(track):
            if track.verrouillage == 1 :
                return self.imgVerrouillage
            else:
                return None

        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 42, "IDlot", typeDonnee="entier", imageGetter=GetImageVerrouillage),
            ColumnDefn(_("Nom"), "left", 290, "nom", typeDonnee="texte"),
            ColumnDefn(_("Date"), "left", 80, "date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Nbre Pr�l�v."), "center", 80, "nbrePrelevements", typeDonnee="entier"),
            ColumnDefn(_("Type"), "left", 70, "typePrelevementStr", typeDonnee="texte"),
            ColumnDefn(_("Observations"), "left", 200, "observations", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun lot de pr�l�vements"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[2])
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
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDlot
                
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
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des lots de pr�l�vements"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des lots de pr�l�vements"), format="A", orientation=wx.PORTRAIT)
        prt.Print()


    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_prelevements", "creer") == False : return
        typePrelevement = self.DemanderTypePrelevement() 
        if typePrelevement == False :
            return
        from Dlg import DLG_Saisie_prelevement_lot
        dlg = DLG_Saisie_prelevement_lot.Dialog(self, typePrelevement=typePrelevement)
        if dlg.ShowModal() == wx.ID_OK:
            IDlot = dlg.GetIDlot()
            self.MAJ(IDlot)
        dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_prelevements", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun lot � modifier dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_prelevement_lot
        dlg = DLG_Saisie_prelevement_lot.Dialog(self, IDlot=track.IDlot, typePrelevement=track.typePrelevement)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(track.IDlot)
        dlg.Destroy()

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_prelevements", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun lot � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        nbrePrelevements = self.Selection()[0].nbrePrelevements
        if nbrePrelevements > 0 :
            dlg = wx.MessageDialog(self, _("Il est impossible de supprimer ce lot puisqu'il est d�j� constitu� de %d pr�l�vements(s) !") % nbrePrelevements, _("Suppression impossible"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce lot de pr�l�vements ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            IDlot = self.Selection()[0].IDlot
            DB = GestionDB.DB()
            DB.ReqDEL("lots_prelevements", "IDlot", IDlot)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()

    def Assistant(self, filtres=[], nomLot=None):
        typePrelevement = self.DemanderTypePrelevement() 
        if typePrelevement == False :
            return
        from Dlg import DLG_Saisie_prelevement_lot
        dlg = DLG_Saisie_prelevement_lot.Dialog(self, typePrelevement=typePrelevement)
        dlg.Assistant(filtres=filtres, nomLot=nomLot)
        if dlg.ShowModal() == wx.ID_OK:
            IDlot = dlg.GetIDlot()
            self.MAJ(IDlot)
        dlg.Destroy()
    
    def DemanderTypePrelevement(self):
        """ Demander si SEPA ou National � cr�er """
        # from Dlg import DLG_Choix
        # listeBoutons = [
        #     (_("Pr�l�vement SEPA"), _("Nouvelle norme de pr�l�vements bancaires valables dans toute l'Europe � partir du 1er f�vrier 2014. Veuillez � saisir les mandats de vos usagers avant d'utiliser ce nouveau type de pr�l�vement.")),
        #     (_("Pr�l�vement National"), _("Type de pr�l�vement valable uniquement jusqu'au 1er f�vrier 2014 en France. Ce type de pr�l�vement sera impossible au-del� de cette date.")),
        #     ]
        # dlg = DLG_Choix.Dialog(self, listeBoutons=listeBoutons)
        # reponse = dlg.ShowModal()
        # dlg.Destroy()
        # if reponse == wx.ID_CANCEL : return False
        # if reponse == 0 : return "sepa"
        # if reponse == 1 : return "national"
        return "sepa"
        

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un lot de pr�l�vements..."))
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
