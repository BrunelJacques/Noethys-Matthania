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
from Ctrl import CTRL_Bouton_image
import GestionDB

from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, Filter, CTRL_Outils



class Track(object):
    def __init__(self, donnees):
        self.IDcategorie_tarif = donnees[0]
        self.nom = donnees[1]
        self.campeur = donnees[2]
        if self.campeur == None:
            self.campeur = 1
        self.effectifs = ["Animateurs","Campeurs","Staff & Autres"][self.campeur]
        self.nbGroupes = donnees[3]
    
class ListView(ObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.IDactivite = kwds.pop("IDactivite", None)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        ObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        listeID = None
        DB = GestionDB.DB()
        
        # Récupération des tarifs
        req = """
            SELECT categories_tarifs.IDcategorie_tarif, categories_tarifs.nom, categories_tarifs.campeur,
      		 		SUM(groupes.campeur = categories_tarifs.campeur)
            FROM categories_tarifs 
            LEFT JOIN groupes ON categories_tarifs.IDactivite = groupes.IDactivite
            WHERE (categories_tarifs.IDactivite = %d)
            GROUP BY categories_tarifs.IDcategorie_tarif, categories_tarifs.nom, categories_tarifs.campeur
            ORDER BY categories_tarifs.nom
            ;""" % self.IDactivite
        DB.ExecuterReq(req)
        listeCategories = DB.ResultatReq()
        

        listeListeView = []
        for item in listeCategories :
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
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                    
        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDcategorie_tarif", typeDonnee="entier"),
            ColumnDefn(_("Nom"), "left", 230, "nom", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("IDcampeur"), "left", 0, "campeur", typeDonnee="entier"),
            ColumnDefn(_("Effectifs"), "right", 80, "effectifs", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Nbre de Groupes / Type campeur"), "left", 180, "nbGroupes",typeDonnee="entier",isSpaceFilling=True),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune catégorie de tarifs"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[1])
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
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        self._ResizeSpaceFillingColumns() 
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDcategorie_tarif
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        menuPop.AppendSeparator()

        # Item Ajouter
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des catégories de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des catégories de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def Ajouter(self, event):
        from Dlg import DLG_Saisie_categorie_tarif
        dlg = DLG_Saisie_categorie_tarif.Dialog(self, IDactivite=self.IDactivite, IDcategorie_tarif=None)
        if dlg.ShowModal() == wx.ID_OK:
            IDcategorie_tarif = dlg.GetIDcategorieTarif()
            dlg.Destroy()
            self.MAJ()
        else:
            dlg.Destroy()
        # MAJ du ctrl tarifs de la fenêtre parente
        if self.GetParent().GetName() == "panel_tarification" :
            self.GetParent().MAJtarifs()

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune catégorie à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDcategorie_tarif = self.Selection()[0].IDcategorie_tarif
        from Dlg import DLG_Saisie_categorie_tarif
        dlg = DLG_Saisie_categorie_tarif.Dialog(self, IDactivite=self.IDactivite, IDcategorie_tarif=IDcategorie_tarif)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()
            self.MAJ()
        else:
            dlg.Destroy()
        # MAJ du ctrl tarifs de la fenêtre parente
        if self.GetParent().GetName() == "panel_tarification" :
            self.GetParent().MAJtarifs()

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune catégorie à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB = GestionDB.DB()
        IDcategorie_tarif = self.Selection()[0].IDcategorie_tarif
        req = """
                SELECT Count(inscriptions.IDinscription), Min(inscriptions.date_inscription)
                FROM categories_tarifs 
                    INNER JOIN inscriptions ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
                WHERE (categories_tarifs.IDcategorie_tarif = %d )
            ;"""%(IDcategorie_tarif)
        DB.ExecuterReq(req,MsgBox="OL_Categories_tarifs.ListView.Supprimer")
        retour = DB.ResultatReq()
        nbInscriptions = retour[0][0]
        if nbInscriptions > 0:
            info = "Déjà utilisé\n\nIl existe %d inscriptions faites avec cette catégorie,\n"%nbInscriptions
            info += "la première a été faite le %s, \nvous pouvez toutefois modifier le nom de cette catégorie tarif"% GestionDB.DateEngEnDateFr(retour[0][1])
            wx.MessageBox(info,"Suppression impossible",wx.ICON_STOP)
            DB.Close()
            return

        info = "Les affectations de tarif seront aussi supprimées."
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cette catégorie ?\n\n%s"%info),
                               _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES :
            DB.ReqDEL("categories_tarifs", "IDcategorie_tarif", IDcategorie_tarif)
            DB.ReqDEL("matTarifs", "trfIDcategorie_tarif", IDcategorie_tarif)
            self.MAJ()
        DB.Close()
        dlg.Destroy()
        # MAJ du ctrl tarifs de la fenêtre parente
        if self.GetParent().GetName() == "panel_tarification" :
            self.GetParent().MAJtarifs()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher une catégorie de tarifs..."))
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
        self.myOlv = ListView(panel, id=-1, IDactivite=1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
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
