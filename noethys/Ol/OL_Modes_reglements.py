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
import os
import six
import GestionDB
from Dlg import DLG_Saisie_mode_reglement
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
from Utils import UTILS_Utilisateurs


TAILLE_IMAGE = (132/2, 72/2)
IMAGE_DEFAUT = Chemins.GetStaticPath("Images/Special/Image_non_disponible.png")



def GetImage(bufferImage):
    """ R�cup�re une image """ 
    # Adaptation pour wxPython >= 2.9
    qualite = wx.IMAGE_QUALITY_HIGH
        
    # Recherche de l'image
    if bufferImage != None :
        io = six.BytesIO(bufferImage)
        if 'phoenix' in wx.PlatformInfo:
            img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
        else :
            img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
        try :
            bmp = img.Rescale(width=int(TAILLE_IMAGE[0]), height=int(TAILLE_IMAGE[1]), quality=qualite)
            bmp = bmp.ConvertToBitmap()
            return bmp
        except :
            return None

    else:
        # Si aucune image est trouv�e, on prend l'image par d�faut
        bmp = GetImageDefaut() 
        return bmp

def GetImageDefaut():
    # Adaptation pour wxPython >= 2.9
    if wx.VERSION > (2, 9, 0, 0) :
        qualite = wx.IMAGE_QUALITY_BICUBIC
    else :
        qualite = 100 

    if os.path.isfile(IMAGE_DEFAUT):
        bmp = wx.Bitmap(IMAGE_DEFAUT, wx.BITMAP_TYPE_ANY)
        bmp = bmp.ConvertToImage()
        bmp = bmp.Rescale(width=int(TAILLE_IMAGE[0]), height=int(TAILLE_IMAGE[1]), quality=qualite)
        bmp = bmp.ConvertToBitmap()
        return bmp
    return None




class Track(object):
    def __init__(self, donnees):
        self.IDmode = donnees[0]
        self.label = donnees[1]
        self.bufferImage = donnees[2]
        self.bmp = GetImage(self.bufferImage)
        self.nbre_emetteurs = donnees[3] 
        self.texte_emetteurs = ""
        if self.nbre_emetteurs == 1 :
            self.texte_emetteurs = _("1 �metteur")
        elif self.nbre_emetteurs > 1 :
            self.texte_emetteurs = _("%s �metteurs") % self.nbre_emetteurs




class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.selectionID = None
        self.selectionTrack = None
        self.itemSelected = False
        self.popupIndex = -1
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
        req = """SELECT 
        modes_reglements.IDmode, label, modes_reglements.image,
        COUNT(emetteurs.IDemetteur)
        FROM modes_reglements
        LEFT JOIN emetteurs ON emetteurs.IDmode = modes_reglements.IDmode
        GROUP BY modes_reglements.IDmode
        ORDER BY label
        """
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

        # Cr�ation du imageList avec une taille personnalis�e
        dictImages = {}
        imageList = wx.ImageList(int(TAILLE_IMAGE[0]), int(TAILLE_IMAGE[1]))
        for track in self.donnees :
            if track.bmp != None :
                indexImg = imageList.Add(track.bmp)
                dictImages[track.IDmode] = indexImg
        self.SetImageLists(imageList, imageList)
                    
        def GetImage(track):
            return dictImages[track.IDmode]
                    
        liste_Colonnes = [
            ColumnDefn(_("IDmode"), "left", 0, "IDmode", typeDonnee="entier"),
            ColumnDefn(_("Image"), 'left', int(TAILLE_IMAGE[0])+1, "", imageGetter=GetImage),
            ColumnDefn(_("Nom"), 'left', 400, "label", typeDonnee="texte"),
            ColumnDefn(_("Nbre �metteurs"), 'left', 190, "texte_emetteurs", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun mode de r�glement"))
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
            ID = self.Selection()[0].IDmode
                
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des modes de r�glements"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des modes de r�glements"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_modes_reglements", "creer") == False : return
        dlg = DLG_Saisie_mode_reglement.Dialog(self, IDmode=None)
        if dlg.ShowModal() == wx.ID_OK:
            IDmode = dlg.GetIDmode()
            self.MAJ(IDmode)
        dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_modes_reglements", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun mode de r�glement � modifier dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDmode = self.Selection()[0].IDmode
        dlg = DLG_Saisie_mode_reglement.Dialog(self, IDmode=IDmode)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDmode)
        dlg.Destroy()

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_modes_reglements", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun mode de r�glement � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDmode = self.Selection()[0].IDmode
        nbre_emetteurs = self.Selection()[0].nbre_emetteurs
        
        # V�rifie que des �metteurs ne sont pas d�j� associ�s � ce mode
        if nbre_emetteurs > 0 :
            dlg = wx.MessageDialog(self, _("%d �metteurs(s) sont d�j� attribu�s � ce mode de r�glement.\n\nVous ne pouvez donc pas le supprimer !") % nbre_emetteurs, _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # V�rifie que ce mode n'a pas d�j� attribu� � des r�glements
        DB = GestionDB.DB()
        req = """SELECT COUNT(IDreglement)
        FROM reglements 
        WHERE IDmode=%d
        ;""" % IDmode
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        nbreReglements = int(DB.ResultatReq()[0][0])
        DB.Close()
        if nbreReglements > 0 :
            dlg = wx.MessageDialog(self, _("Ce mode de r�glement a d�j� �t� attribu� � %d r�glement(s).\n\nVous ne pouvez donc pas le supprimer !") % nbreReglements, _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cet �metteur ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            
            DB = GestionDB.DB()
            DB.ReqDEL("modes_reglements", "IDmode", IDmode)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()



class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un mode de r�glement..."))
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


# -----------------------------------------------------------------------------------------------------------------

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
