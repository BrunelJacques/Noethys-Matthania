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
import six
import os
import GestionDB
from Dlg import DLG_Saisie_emetteur
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
from Utils import UTILS_Utilisateurs

TAILLE_IMAGE = (132/2, 72/2)
IMAGE_DEFAUT = Chemins.GetStaticPath("Images/Special/Image_non_disponible.png")



class Track(object):
    def __init__(self, donnees):
        self.IDemetteur = donnees[0]
        self.IDmode = donnees[1]
        self.nom = donnees[2]
        self.bufferImage = donnees[3]
        self.label_mode = donnees[4]
        self.bmp = self.GetImage()

    def GetImage(self):
        """ R�cup�re une image """            
        # Recherche de l'image
        if self.bufferImage != None :
            io = six.BytesIO(self.bufferImage)
            if 'phoenix' in wx.PlatformInfo:
                img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
            else :
                img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
            bmp = img.Rescale(width=int(TAILLE_IMAGE[0]), height=int(TAILLE_IMAGE[1]), quality=wx.IMAGE_QUALITY_HIGH)
            bmp = bmp.ConvertToBitmap()
            return bmp
        else:
            # Si aucune image est trouv�e, on prend l'image par d�faut
            bmp = self.GetImageDefaut() 
            return bmp
    
    def GetImageDefaut(self):
        if os.path.isfile(IMAGE_DEFAUT):
            bmp = wx.Bitmap(IMAGE_DEFAUT, wx.BITMAP_TYPE_ANY)
            bmp = bmp.ConvertToImage()
            bmp = bmp.Rescale(width=int(TAILLE_IMAGE[0]), height=int(TAILLE_IMAGE[1]), quality=wx.IMAGE_QUALITY_HIGH)
            bmp = bmp.ConvertToBitmap()
            return bmp
        return None



class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.IDmode = None
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
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
        req = """SELECT IDemetteur, emetteurs.IDmode, nom, emetteurs.image, modes_reglements.label
        FROM emetteurs
        LEFT JOIN modes_reglements ON emetteurs.IDmode = modes_reglements.IDmode
        %s
        """ % self.criteres
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
            indexImg = imageList.Add(track.bmp)            
            dictImages[track.IDemetteur] = indexImg
        self.SetImageLists(imageList, imageList)
                    
        def GetImage(track):
            return dictImages[track.IDemetteur]
                    
        liste_Colonnes = [
            ColumnDefn(_("IDemetteur"), "left", 0, "IDemetteur", typeDonnee="entier"),
            ColumnDefn(_("Image"), 'left', int(TAILLE_IMAGE[0])+1, "", imageGetter=GetImage),
            ColumnDefn(_("Mode de r�glement"), 'left', 0, "label_mode", typeDonnee="texte"),
            ColumnDefn(_("Nom de l'�metteur"), 'left', 410, "nom", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun �metteur"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[2])
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None, IDmode=None):
        if IDmode != None :
            self.IDmode = IDmode
        if self.IDmode != None :
            self.criteres = "WHERE emetteurs.IDmode=%d" % self.IDmode

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
            ID = self.Selection()[0].IDemetteur
                
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des �metteurs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des �metteurs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_emetteurs", "creer") == False : return
        if self.IDmode == None :
            dlg = wx.MessageDialog(self, _("Vous devez d'abord s�lectionner un mode de r�glement !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        dlg = DLG_Saisie_emetteur.Dialog(self, IDmode=self.IDmode, IDemetteur=None)
        if dlg.ShowModal() == wx.ID_OK:
            IDemetteur = dlg.GetIDemetteur()
            self.MAJ(IDemetteur)
        dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_emetteurs", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun �metteur � modifier dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDemetteur = self.Selection()[0].IDemetteur
        dlg = DLG_Saisie_emetteur.Dialog(self, IDmode=self.IDmode, IDemetteur=IDemetteur)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDemetteur)
        dlg.Destroy()

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_emetteurs", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun �metteur � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDemetteur = self.Selection()[0].IDemetteur
        
        # V�rifie que l'�metteur n'a pas d�j� �t� attribu� � un r�glement
        DB = GestionDB.DB()
        req = """SELECT COUNT(IDreglement)
        FROM reglements 
        WHERE IDemetteur=%d
        ;""" % IDemetteur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        nbreReglements = int(DB.ResultatReq()[0][0])
        DB.Close()
        if nbreReglements > 0 :
            message = _("Attention, cet �metteur a d�j� �t� attribu� � %d r�glement(s). Si vous le supprimez, il sera �galement dissoci� des r�glements associ�s !\n\nSouhaitez-vous tout de m�me le supprimer ?") % nbreReglements
            dlg = wx.MessageDialog(self, message, _("Suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES:
                return False

        # Suppression
        dlg = wx.MessageDialog(self, _("Confirmez-vous vraiment la suppression de cet �metteur ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("emetteurs", "IDemetteur", IDemetteur)
            DB.ReqMAJ("reglements", [("IDemetteur", None),], "IDemetteur", IDemetteur)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()



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
