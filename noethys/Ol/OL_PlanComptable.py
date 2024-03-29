#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Gestion de la table Plan comptable d�finissant le regroupement compta
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import copy
import GestionDB
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Utilisateurs

class ListView(FastObjectListView):
    def __init__(self, parent, *args, **kwds):
        self.parent = parent
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.parent.choix = self.GetSelectedObject()
        self.parent.EndModal(wx.ID_OK)
                
    def InitModel(self):
        """ R�cup�ration des donn�es """
        DB = GestionDB.DB()
        req = """SELECT pctCodeComptable,pctLibelle,pctCompte
        FROM matPlanComptable ORDER BY pctCodeComptable; """
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        self.donnees = copy.deepcopy(DB.ResultatReq())
        DB.Close()
        return

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn(_("Code"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_("Code"), "left", 80, 0, typeDonnee="texte"),
            ColumnDefn(_("Libelle"), 'left', 250, 1, typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_("Compta"), 'left', 80, 2, typeDonnee="texte"),
            ]
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun bloc d�fini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)

    def MAJ(self, ID=None):
        self.InitModel()
        self.InitObjectListView()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].Code
        # Cr�ation du menu contextuel
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
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des blocs lignes facture"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des blocs lignes facture"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def PrepareEnreg(self, listeDonnees, mode):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits de param�trage activit�")
        else :
            from Dlg import DLG_SaisiePlanComptable
            dlg = DLG_SaisiePlanComptable.Dialog(self,mode)
            if listeDonnees != None :
                dlg.SetBloc(listeDonnees)
            listeDonnees = []
            if dlg.ShowModal() == wx.ID_OK:
                code = dlg.ctrl_code.GetValue()
                libelle = dlg.ctrl_libelle.GetValue()
                compta = dlg.ctrl_compta.GetValue()
                listeDonnees = [("pctCodeComptable", code ), ("pctLibelle", libelle),("pctCompte", compta),]
            dlg.Destroy()
        return listeDonnees

    def Ajouter(self, event):
        listeDonnees = self.PrepareEnreg(None,"ajout")
        if len(listeDonnees)== 0 :return
        DB = GestionDB.DB()
        retour = DB.ReqInsert("matPlanComptable", listeDonnees,retourID=False)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            GestionDB.MessageBox(self, "Vous n'avez s�lectionn� aucun bloc dans la liste")
            return
        listeDonnees = self.PrepareEnreg(self.Selection()[0],"modif")
        if len(listeDonnees)== 0 :return
        DB = GestionDB.DB()
        code = str(listeDonnees[0][1])
        retour = DB.ReqMAJ("matPlanComptable", listeDonnees, "pctCodeComptable",code)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            GestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun bloc dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        bloc = self.Selection()[0]
        # V�rifie que ce compte de bloc n'a pas d�j� �t� utilis�
        DB = GestionDB.DB()
        req = """SELECT COUNT (artCodeArticle)
        FROM matArticles
        WHERE artCodeComptable=%s
        ;""" % bloc[0]
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        resultat = DB.ResultatReq()
        if resultat != [] :
            nbreBlocs = len(resultat)
            dlg = wx.MessageDialog(self, _("Ce compte a d�j� �t� attribu� %d fois.\n\nVous ne pouvez donc pas le supprimer !") % nbreBlocs, _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce compte ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            retour = DB.ReqDEL("matPlanComptable", "pctCodeComptable",bloc[0])
            DB.Close()
            if retour == "ok" :
                self.MAJ()
            else :
                dlgErr = wx.MessageDialog(self,retour)
                dlgErr.ShowModal()
                dlgErr.Destroy()
            self.MAJ()
        dlg.Destroy()

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
