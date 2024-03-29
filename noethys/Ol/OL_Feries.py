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
if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else :
    from wx import DatePickerCtrl, DP_DROPDOWN

from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Utilisateurs


def dateEnDateComplet(jour, mois, annee):
    """ Transforme le format "aaaa-mm-jj" en "mercredi 12 septembre 2008" """
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    listeJours = (_("lundi"), _("mardi"), _("mercredi"), _("jeudi"), _("vendredi"), _("samedi"), _("dimanche"))
    jourSemaine = int(datetime.date(annee, mois, jour).strftime("%w"))
    texte = listeJours[jourSemaine-1] + " " + str(jour) + " " + listeMois[mois-1] + " " + str(annee)
    return texte
    

class Track(object):
    def __init__(self, donnees):
        self.IDferie = donnees[0]
        self.type = donnees[1]
        self.nom = donnees[2]
        self.jour = donnees[3]
        self.mois = donnees[4]
        self.annee = donnees[5]
        
        # Formatage de la date
        if self.type == "fixe" :
            if self.mois < 10 : 
                mois = str("0") + str(self.mois)
            else : 
                mois = str(self.mois)
            self.date = "0-" + mois + "-" + str(self.jour)
        else:
            self.date = str(self.annee) + "-" + str(self.mois) + "-" + str(self.jour)
                
                
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.type = kwds.pop("type", None)
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
        req = """SELECT IDferie, type, nom, jour, mois, annee
        FROM jours_feries WHERE type='%s';""" % self.type
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
        
        def FormateDate(valeur):
            listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
            annee, mois, jour = valeur.split("-")
            if annee != "0" :
                texte = _("Le %s") % dateEnDateComplet(int(jour), int(mois), int(annee))
            else:
                texte = _("Le %s") % str(jour) +  " " + listeMois[int(mois)-1]
            return texte
            
        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDferie"),
            ColumnDefn(_("Nom"), "left", 200, "nom"),
            ColumnDefn(_("Date"), "left", 200, "date", stringConverter=FormateDate),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun jour f�ri� %s") % self.type)
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
            ID = self.Selection()[0].IDferie
                
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des jours f�ri�s"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des jours f�ri�s"), format="A", orientation=wx.PORTRAIT)
        prt.Print()


    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_feries", "creer") == False : return
        dlg = Saisie(self, type=self.type, IDferie=None)
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetNom()
            jour = dlg.GetJour()
            mois = dlg.GetMois()
            annee = dlg.GetAnnee()
            listeDonnees = [
                ("type", self.type ),
                ("nom", nom ),
                ("jour", jour ),
                ("mois", mois ),
                ("annee", annee),
                ]
            DB = GestionDB.DB()
            IDferie = DB.ReqInsert("jours_feries", listeDonnees)
            DB.Close()
            self.MAJ(IDferie)
            dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_feries", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun jour f�ri� � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDferie = self.Selection()[0].IDferie
        nom = self.Selection()[0].nom
        jour = self.Selection()[0].jour
        mois = self.Selection()[0].mois
        annee = self.Selection()[0].annee
        dlg = Saisie(self, type=self.type, IDferie=IDferie)
        dlg.SetNom(nom)
        if self.type == "variable" :
            dlg.SetDate(jour, mois, annee)
        else:
            dlg.SetJour(jour)
            dlg.SetMois(mois)
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetNom()
            jour = dlg.GetJour()
            mois = dlg.GetMois()
            annee = dlg.GetAnnee()
            listeDonnees = [
                ("type", self.type ),
                ("nom", nom ),
                ("jour", jour ),
                ("mois", mois ),
                ("annee", annee),
                ]
            DB = GestionDB.DB()
            DB.ReqMAJ("jours_feries", listeDonnees, "IDferie", IDferie)
            DB.Close()
            self.MAJ(IDferie)
        dlg.Destroy()

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_feries", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun jour f�ri� � supprimer dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce jour f�ri� ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            IDferie = self.Selection()[0].IDferie
            DB = GestionDB.DB()
            DB.ReqDEL("jours_feries", "IDferie", IDferie)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()
    

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyDatePickerCtrl(DatePickerCtrl):
    def __init__(self, parent):
        DatePickerCtrl.__init__(self, parent, -1, style=DP_DROPDOWN)
        self.parent = parent
        
    def SetDate(self, dateTxt=None):
        jour = int(dateTxt[8:10])
        mois = int(dateTxt[5:7])-1
        annee = int(dateTxt[:4])
        date = wx.DateTime()
        date.Set(jour, mois, annee)
        self.SetValue(date)
    
    def SetDateDetail(self, jour, mois, annee):
        date = wx.DateTime()
        date.Set(jour, mois-1, annee)
        self.SetValue(date)
        
    def GetDate(self):
        date = self.GetValue()
        dateDD = datetime.date(date.GetYear(), date.GetMonth()+1, date.GetDay())
        return str(dateDD)
    
    def GetDateDD(self):
        date = self.GetValue()
        dateDD = datetime.date(date.GetYear(), date.GetMonth()+1, date.GetDay())
        return dateDD
    
    
    
class Saisie(wx.Dialog):
    def __init__(self, parent, type="variable", IDferie=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.type = type

        self.staticBox_staticbox = wx.StaticBox(self, -1, "")
        self.label_nom = wx.StaticText(self, -1, _("Nom :"))
        self.text_ctrl_nom = wx.TextCtrl(self, -1, "")
        self.label_jour_fixe = wx.StaticText(self, -1, _("Jour :"))
        choices=[]
        for x in range(1, 32) : choices.append(str(x))
        self.choice_jour_fixe = wx.Choice(self, -1, choices=choices)
        self.label_mois_fixe = wx.StaticText(self, -1, _("Mois :"))
        self.choice_mois_fixe = wx.Choice(self, -1, choices=[_("Janvier"), _("F�vrier"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Ao�t"), _("Septembre"), _("Octobre"), _("Novembre"), _("D�cembre")])
        self.label_date_variable = wx.StaticText(self, -1, _("Date :"))
        self.datepicker_date_variable = MyDatePickerCtrl(self)
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        
        # Affiche en fonction du type de de jour f�ri�
        if self.type == "fixe" :
            self.label_date_variable.Show(False)
            self.datepicker_date_variable.Show(False)
        else:
            self.label_jour_fixe.Show(False)
            self.choice_jour_fixe.Show(False)
            self.label_mois_fixe.Show(False)
            self.choice_mois_fixe.Show(False)
            
        # Propri�t�s
        self.choice_jour_fixe.SetMinSize((50, -1))
        self.choice_mois_fixe.SetMinSize((130, 21))
        self.text_ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez un nom pour ce jour f�ri� (ex: 'No�l', 'Ascension', 'Jour de l'an', etc...)")))
        self.choice_jour_fixe.SetToolTip(wx.ToolTip(_("S�lectionnez le jour")))
        self.choice_mois_fixe.SetToolTip(wx.ToolTip(_("S�lectionnez le mois")))
        self.datepicker_date_variable.SetToolTip(wx.ToolTip(_("Saisissez ou s�lectionnez une date pour ce jour f�ri�")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler la saisie")))
        if IDferie == None :
            if self.type == "fixe" :
                self.SetTitle(_("Saisie d'un jour f�ri� fixe"))
            else:
                self.SetTitle(_("Saisie d'un jour f�ri� variable"))
        else:
            if self.type == "fixe" :
                self.SetTitle(_("Modification d'un jour f�ri� fixe"))
            else:
                self.SetTitle(_("Modification d'un jour f�ri� variable"))
        self.SetMinSize((350, -1))
    
        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        staticBox = wx.StaticBoxSizer(self.staticBox_staticbox, wx.VERTICAL)
        grid_sizer_staticBox = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_variable = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_fixe = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=5)
        grid_sizer_nom = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_nom.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_nom.Add(self.text_ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_nom.AddGrowableCol(1)
        grid_sizer_staticBox.Add(grid_sizer_nom, 1, wx.EXPAND, 0)
        grid_sizer_fixe.Add(self.label_jour_fixe, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_fixe.Add(self.choice_jour_fixe, 0, wx.RIGHT, 10)
        grid_sizer_fixe.Add(self.label_mois_fixe, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_fixe.Add(self.choice_mois_fixe, 0, wx.EXPAND, 0)
        grid_sizer_fixe.AddGrowableCol(4)
        grid_sizer_staticBox.Add(grid_sizer_fixe, 1, wx.EXPAND, 0)
        grid_sizer_variable.Add(self.label_date_variable, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_variable.Add(self.datepicker_date_variable, 0, 0, 0)
        grid_sizer_staticBox.Add(grid_sizer_variable, 1, wx.EXPAND, 0)
        grid_sizer_staticBox.AddGrowableCol(0)
        staticBox.Add(grid_sizer_staticBox, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticBox, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
    
    def SetNom(self, nom=None):
        self.text_ctrl_nom.SetValue(nom)
        
    def GetNom(self):
        return self.text_ctrl_nom.GetValue()
        
    def SetJour(self, jour=None):
        self.choice_jour_fixe.SetSelection(jour-1)
        
    def GetJour(self):
        if self.type == "variable" : 
            return self.datepicker_date_variable.GetDateDD().day
        else:
            return self.choice_jour_fixe.GetSelection()+1
    
    def SetMois(self, mois=None):
        self.choice_mois_fixe.SetSelection(mois-1)
        
    def GetMois(self):
        if self.type == "variable" : 
            return self.datepicker_date_variable.GetDateDD().month
        else:
            return self.choice_mois_fixe.GetSelection()+1
    
    def GetAnnee(self):
        if self.type == "variable" : 
            return self.datepicker_date_variable.GetDateDD().year
        else:
            return 0
        
    def SetDate(self, jour, mois, annee):
        self.datepicker_date_variable.SetDateDetail(jour, mois, annee)
            
    def OnBoutonOk(self, event):
        if self.GetNom() == "" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom pour ce jour f�ri� !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.text_ctrl_nom.SetFocus()
            return
        if self.type == "fixe" :
            # Variable
            if self.GetJour() == 0 :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un jour !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.choice_jour_fixe.SetFocus()
                return
            if self.GetMois() == 0 :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un mois !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.choice_mois_fixe.SetFocus()
                return           
        
        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Joursfris")



# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un jour f�ri� %s...") % self.parent.type)
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
        self.listView.Refresh()


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, type="variable", id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
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
