#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
from Utils import UTILS_Dates


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")



def GetCondition(titre="", typeDonnee="", choix="", criteres=""):
    description = ""
    
    # TEXTE
    if typeDonnee == "texte" :
        if choix == "EGAL" : description = _("'%s' est �gal � '%s'") % (titre, criteres)
        if choix == "DIFFERENT" : description = _("'%s' est diff�rent de '%s'") % (titre, criteres)
        if choix == "CONTIENT" : description = _("'%s' contient '%s'") % (titre, criteres)
        if choix == "CONTIENTPAS" : description = _("'%s' ne contient pas '%s'") % (titre, criteres)
        if choix == "COMMENCE" : description = _("'%s' commence par '%s'") % (titre, criteres)
        if choix == "DANS" : description = _("'%s' parmi '%s'") % (titre, criteres)
        if choix == "NONDANS" : description = _("'%s' pas parmi '%s'") % (titre, criteres)
        if choix == "VIDE" : description = _("'%s' est vide") % titre
        if choix == "PASVIDE" : description = _("'%s' n'est pas vide") % titre

    # BOOL
    if typeDonnee == "bool" :
        if choix == "TRUE" : description = _("'%s' est vrai") % titre
        if choix == "FALSE" : description = _("'%s' est faux") % titre

    # ENTIER
    if typeDonnee == "entier" :
        if choix == "EGAL" : description = _("'%s' est �gal � '%s'") % (titre, criteres)
        if choix == "DIFFERENT" : description = _("'%s' est diff�rent de '%s'") % (titre, criteres)
        if choix == "SUP" : description = _("'%s' est sup�rieur � '%s'") % (titre, criteres)
        if choix == "SUPEGAL" : description = _("'%s' est sup�rieur ou �gal � '%s'") % (titre, criteres)
        if choix == "INF" : description = _("'%s' est inf�rieur � '%s'") % (titre, criteres)
        if choix == "INFEGAL" : description = _("'%s' est inf�rieur ou �gal � '%s'")  % (titre, criteres)
        if choix == "COMPRIS" : description = _("'%s' est compris entre '%s' et '%s'") % (titre, criteres.split(";")[0], criteres.split(";")[1])
        if choix == "VIDE" : description = _("'%s' est vide") % titre
        if choix == "PASVIDE" : description = _("'%s' n'est pas vide") % titre

    # MONTANT
    if typeDonnee == "montant" :
        if choix == "EGAL" : description = _("'%s' est �gal � %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "DIFFERENT" : description = _("'%s' est diff�rent de %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "SUP" : description = _("'%s' est sup�rieur � %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "SUPEGAL" : description = _("'%s' est sup�rieur ou �gal � %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "INF" : description = _("'%s' est inf�rieur � %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "INFEGAL" : description = _("'%s' est inf�rieur ou �gal � %.2f %s") % (titre, float(criteres), SYMBOLE)
        if choix == "COMPRIS" : description = _("'%s' est compris entre %.2f %s et %.2f %s") % (titre, float(criteres.split(";")[0]), SYMBOLE, float(criteres.split(";")[1]), SYMBOLE)
        if choix == "VIDE" : description = _("'%s' est vide") % titre
        if choix == "PASVIDE" : description = _("'%s' n'est pas vide") % titre

    # DATE
    if typeDonnee == "date" :
        if choix == "EGAL" : description = _("'%s' est �gal au '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "DIFFERENT" : description = _("'%s' est diff�rent du '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "SUP" : description = _("'%s' est sup�rieur au '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "SUPEGAL" : description = _("'%s' est sup�rieur ou �gal au '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "INF" : description = _("'%s' est inf�rieur au '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "INFEGAL" : description = _("'%s' est inf�rieur ou �gal au '%s'") % (titre, UTILS_Dates.DateEngFr(criteres))
        if choix == "COMPRIS" : description = _("'%s' est compris entre le '%s' et le '%s'") % (titre, UTILS_Dates.DateEngFr(criteres.split(";")[0]), UTILS_Dates.DateEngFr(criteres.split(";")[1]))
        if choix == "VIDE" : description = _("'%s' est vide") % titre
        if choix == "PASVIDE" : description = _("'%s' n'est pas vide") % titre

    # DATE ET HEURE
    if typeDonnee == "dateheure" :
        if choix == "EGAL" : description = _("'%s' est �gal au '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "DIFFERENT" : description = _("'%s' est diff�rent du '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "SUP" : description = _("'%s' est sup�rieur au '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "SUPEGAL" : description = _("'%s' est sup�rieur ou �gal au '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "INF" : description = _("'%s' est inf�rieur au '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "INFEGAL" : description = _("'%s' est inf�rieur ou �gal au '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres))
        if choix == "COMPRIS" : description = _("'%s' est compris entre le '%s' et le '%s'") % (titre, UTILS_Dates.DatetimeEnFr(criteres.split(";")[0]), UTILS_Dates.DatetimeEnFr(criteres.split(";")[1]))

    # INSCRITS
    if typeDonnee == "inscrits" :
        if choix == "INSCRITS" : description = _("L'individu est inscrit sur les activit�s s�lectionn�es")
        if choix == "PRESENTS" : description = _("L'individu est inscrit sur les activit�s s�lectionn�es et pr�sent entre le %s et le %s") % (UTILS_Dates.DateDDEnFr(criteres["date_debut"]), UTILS_Dates.DateDDEnFr(criteres["date_fin"]))

    # COTISATIONS
    if typeDonnee == "cotisations" :
        if choix == "AJOUR" : description = _("Les cotisations s�lectionn�es sont � jour")

    return description




class Track(object):
    def __init__(self, parent, donnees, index):
        self.code = donnees["code"]
        self.typeDonnee = donnees["typeDonnee"]
        self.choix = donnees["choix"]
        self.criteres = donnees["criteres"]
        if self.typeDonnee != "libre":
            self.code = donnees["code"]
            self.choix = donnees["choix"]
            self.titre = donnees["titre"]
        else:
            self.code, self.choix, self.titre = "","",""
        self.index = index
        
        # Cr�ation de la description
        self.condition = GetCondition(self.titre, self.typeDonnee, self.choix, self.criteres)


class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.ctrl_listview = kwds.pop("ctrl_listview", None)
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
        if self.ctrl_listview != None :
            self.listeFiltres = self.ctrl_listview.listeFiltresColonnes

    def SetDonnees(self, listeFiltres=[]):
        self.listeFiltres = listeFiltres
        self.MAJ() 
    
    def GetDonnees(self):
        listeFiltres = []
        for track in self.donnees :
            listeFiltres.append({"code":track.code, "choix":track.choix, "criteres":track.criteres, "typeDonnee":track.typeDonnee, "titre":track.titre})
        return listeFiltres

    def OnItemActivated(self,event):
        self.Modifier(None)
    
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        listeListeView = []
        
        # R�cup�ration des titres des colonnes
        dictColonnes = {}
        if self.ctrl_listview != None :
            for colonne in self.ctrl_listview.listeColonnes :
                if not hasattr(colonne,"typeDonnee"):
                    colonne.typeDonnee = ""
                if not hasattr(colonne,"titre"):
                    colonne.title = ""
                dictColonnes[colonne.valueGetter] = {"typeDonnee" : colonne.typeDonnee, "titre" : colonne.title}
            
        # Lecture de la liste des filtres
        self.dictTracks = {}
        index = 0
        for dictTemp in self.listeFiltres :
##            dictTemp["typeDonnee"] = dictColonnes[dictTemp["code"]]["typeDonnee"]
##            dictTemp["titre"] = dictColonnes[dictTemp["code"]]["titre"]
            track = Track(self, dictTemp, index)
            listeListeView.append(track)
            index += 1
        return listeListeView
    
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        liste_Colonnes = [
            ColumnDefn("", "left", 0, ""),
            ColumnDefn(_("Condition"), 'left', 165, "condition", isSpaceFilling=True),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun filtre"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
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
        # S�lection d'un item
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
                
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Ajouter(self, event=None):
        # Ouverture de la fen�tre de saisie
        from Dlg import DLG_Saisie_filtre_listes
        dlg = DLG_Saisie_filtre_listes.Dialog(self, ctrl_listview=self.ctrl_listview)
        if dlg.ShowModal() == wx.ID_OK:
            dictTemp = {"code":dlg.GetCode(), "typeDonnee" : dlg.GetTypeDonnee(), "choix":dlg.GetValeur()[0], "criteres":dlg.GetValeur()[1], "titre":dlg.GetTitre()}
            self.listeFiltres.append(dictTemp)
            self.MAJ()
        dlg.Destroy()

    def Modifier(self, event=None):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun filtre � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_filtre_listes
        dlg = DLG_Saisie_filtre_listes.Dialog(self, ctrl_listview=self.ctrl_listview)
        dlg.SetCode(track.code)
        dlg.SetValeur(track.choix, track.criteres)
        if dlg.ShowModal() == wx.ID_OK:
            dictTemp = {"code":dlg.GetCode(), "typeDonnee" : dlg.GetTypeDonnee(), "choix":dlg.GetValeur()[0], "criteres":dlg.GetValeur()[1], "titre":dlg.GetTitre()}
            self.listeFiltres[track.index] = dictTemp
            self.MAJ()
        dlg.Destroy()

    def Supprimer(self, event=None):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun filtre � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce filtre ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            self.listeFiltres.pop(track.index)
            self.MAJ()
        dlg.Destroy()
    
    def ToutSupprimer(self, event):
        self.listeFiltres = []
        self.MAJ() 
        
# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un filtre..."))
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

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
                
        self.myOlv = ListView(panel, ctrl_listview=None, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
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
