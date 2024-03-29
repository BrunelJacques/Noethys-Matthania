#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Utils import UTILS_Dates
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import GestionDB
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Dlg.DLG_Ouvertures import Track_evenement



class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.grid = kwds.pop("grid", None)
        self.liste_colonnes = kwds.pop("liste_colonnes", None)
        self.IDactivite = kwds.pop("IDactivite", None)
        self.date = kwds.pop("date", None)
        self.IDunite = kwds.pop("IDunite", None)
        self.IDgroupe = kwds.pop("IDgroupe", None)
        self.donnees = kwds.pop("liste_evenements", [])
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        pass

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateEngFr(str(dateDD))

        def FormateHeure(heure):
            if heure == "00:00" or heure == None : return ""
            return heure.replace(":", "h")

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        if self.liste_colonnes == None :
            self.liste_colonnes = ["ID", "date", "nom", "heure_debut", "heure_fin", "montant", "capacite_max"]

        dict_colonnes = {
            "ID": ColumnDefn(_("ID"), "left", 0, "IDvenement", typeDonnee="entier"),
            "date": ColumnDefn(_("Date"), 'left', 80, "date", typeDonnee="date", stringConverter=FormateDateCourt),
            "nom": ColumnDefn(_("Nom"), "left", 200, "nom", typeDonnee="texte"),
            "heure_debut": ColumnDefn(_("D�but"), 'center', 60, "heure_debut", typeDonnee="texte", stringConverter=FormateHeure),
            "heure_fin": ColumnDefn(_("Fin"), 'center', 60, "heure_fin", typeDonnee="texte", stringConverter=FormateHeure),
            "montant": ColumnDefn(_("Montant"), 'center', 80, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "capacite_max": ColumnDefn(_("Capacit� max."), 'center', 100, "capacite_max", typeDonnee="entier"),
            }

        liste_temp = []
        for code in self.liste_colonnes :
            liste_temp.append(dict_colonnes[code])
        self.SetColumns(liste_temp)
        self.SetEmptyListMsg(_("Aucun �v�nement"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, track=None):
        self.InitModel()
        self.InitObjectListView()
        # S�lection d'un item
        if track != None :
            self.SelectObject(track, deselectOthers=True, ensureVisible=True)
        else :
            self.DefileDernier()

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

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
            
        menuPop.AppendSeparator()

        # Item Modifier
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

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donn�e � imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des �v�nements"), format="A", orientation=wx.PORTRAIT)
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
        UTILS_Export.ExportTexte(self, titre=_("Liste des �v�nements"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des �v�nements"))

    def Ajouter(self, event):
        from Dlg import DLG_Saisie_evenement
        track_evenement = Track_evenement({"IDactivite":self.IDactivite, "IDunite":self.IDunite, "IDgroupe":self.IDgroupe, "date":self.date, "tarifs" : []})
        dlg = DLG_Saisie_evenement.Dialog(self, mode="ajout", track_evenement=track_evenement)
        if dlg.ShowModal() == wx.ID_OK:
            track_evenement = dlg.GetTrackEvenement()
            self.donnees.append(track_evenement)
            self.MAJ(track_evenement)
        dlg.Destroy()

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun �v�nement � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track_evenement = self.Selection()[0]

        nbre_conso = self.GetNbreConsoAssociees(track_evenement)
        if nbre_conso > 0 :
            dlg = wx.MessageDialog(self, _("Cet �v�nement est d�j� associ� � %d consommations.\n\nSouhaitez-vous tout de m�me le modifier ?") % nbre_conso, _("Modification"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES:
                return False

        from Dlg import DLG_Saisie_evenement
        dlg = DLG_Saisie_evenement.Dialog(self, mode="modification", track_evenement=track_evenement)
        if dlg.ShowModal() == wx.ID_OK:
            track_evenement = dlg.GetTrackEvenement()
            self.RefreshObject(track_evenement)
        dlg.Destroy() 

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun �v�nement � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track_evenement = self.Selection()[0]

        # V�rifie qu'une conso n'est pas d�j� associ�e � cet �v�nement
        nbre_conso = self.GetNbreConsoAssociees(track_evenement)
        if nbre_conso > 0 :
            dlg = wx.MessageDialog(self, _("Suppression interdite.\n\nVous ne pouvez pas supprimer cet �v�nement car %d consommations y sont d�j� associ�es !") % nbre_conso, _("Suppression"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cet �v�nement ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            self.donnees.remove(track_evenement)
            self.MAJ()
        dlg.Destroy()

    def GetNbreConsoAssociees(self, track_evenement=None):
        if track_evenement.IDevenement != None :
            DB = GestionDB.DB()
            req = """SELECT IDconso, IDevenement
            FROM consommations 
            WHERE IDevenement=%d
            ;""" % track_evenement.IDevenement
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeConso = DB.ResultatReq()
            DB.Close()
            return len(listeConso)
        return 0

    def GetListeEvenements(self):
        return self.GetObjects()



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
        self.SetSize((800, 200))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
