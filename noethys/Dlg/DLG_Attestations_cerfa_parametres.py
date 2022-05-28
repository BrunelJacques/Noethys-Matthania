#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
from Ctrl import CTRL_Saisie_date
from Ol import OL_Attestations_cerfa_prestations
from Utils import UTILS_Utilisateurs
import wx.lib.agw.pybusyinfo as PBI


class CTRL_Modes_reglements(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.listeModes, self.dictModes = self.Importation()
        self.SetListeChoix()
        self.SetMinSize((-1, 80))
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self)

    def OnCheck(self,evt):
        self.parent.OnBoutonActualiser(None)

    def Importation(self):
        listeModes = []
        dictModes = {}
        DB = GestionDB.DB()
        req = """SELECT IDmode, label FROM modes_reglements ORDER BY label;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()   
        DB.Close() 
        for IDmode, label in listeDonnees :
            dictModes[IDmode] = label
            listeModes.append((label, IDmode))
        return listeModes, dictModes

    def SetListeChoix(self):
        self.Clear()
        listeItems = []
        index = 0
        for label, IDmode in self.listeModes :
            self.Append(label)
            index += 1
        self.CocheSome()
        
    def GetIDcoches(self, modeTexte=False):
        listeIDcoches = []
        NbreItems = len(self.listeModes)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                if modeTexte == False :
                    ID = self.listeModes[index][1]
                else:
                    ID = str(self.listeModes[index][1])
                listeIDcoches.append(ID)
        return listeIDcoches
    
    def CocheSome(self):
        index = 0
        for index in range(0, len(self.listeModes)):
            if self.listeModes[index][0][:3].lower() in ("chè","che","che","vir","esp"):
                self.Check(index)
            index += 1

    def zzzCocheTout(self):
        index = 0
        for index in range(0, len(self.listeModes)):
            self.Check(index)
            index += 1

    def SetIDcoches(self, listeIDcoches=[]):
        index = 0
        for index in range(0, len(self.listeModes)):
            ID = self.listeModes[index][1]
            if ID in listeIDcoches or str(ID) in listeIDcoches :
                self.Check(index)
            index += 1
    
# ----------------------------------------------------------------------------------------------------------------------------------

class Parametres(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_parametres", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Période
        self.staticbox_periode_staticbox = wx.StaticBox(self, -1, _("Période de référence"))
        self.label_date_debut = wx.StaticText(self, -1, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_date_fin = wx.StaticText(self, -1, _("Au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)
        self.btn_plus = wx.Button(self,label="+1an",size=(40,25))
        self.btn_moins = wx.Button(self,label="-1an",size=(40,25))

        # Séparation
        self.staticbox_saisie = wx.StaticBox(self, -1, _("Sélection des dons :"))
        self.check_prestations = wx.CheckBox(self, -1, _(" saisis en prestations de type Don"))
        self.check_factures = wx.CheckBox(self, -1, _(" saisis en lignes Don sur pièces"))
        self.check_prestations.SetValue(True)
        self.check_factures.SetValue(True)

        # Modes de règlements
        self.staticbox_modes_staticbox = wx.StaticBox(self, -1, _("Modes de règlement"))
        self.ctrl_modes = CTRL_Modes_reglements(self)

        # Actualiser
        self.bouton_actualiser = CTRL_Bouton_image.CTRL(self, texte=_("Rafraîchir la liste"), cheminImage=Chemins.GetStaticPath("Images/32x32/Actualiser.png"))

        self.__set_properties()
        self.__do_layout()
        

        # Init Contrôles

    def __set_properties(self):
        self.ctrl_date_debut.SetToolTip(_("Saisissez la date de début de période"))
        self.ctrl_date_fin.SetToolTip(_("Saisissez la date de fin de période"))
        self.bouton_actualiser.SetToolTip(_("Cliquez ici pour actualiser la liste"))
        self.btn_plus.SetToolTip("Cliquez pour avancer d'un an les dates")
        self.btn_moins.SetToolTip("Cliquez pour reculer d'un an les dates")
        self.btn_plus.Name = 'plus'
        self.btn_moins.Name = 'moins'
        self.Bind(wx.EVT_BUTTON, self.OnBoutonActualiser, self.bouton_actualiser)
        self.Bind(wx.EVT_BUTTON, self.OnBtnPlusMoins, self.btn_plus)
        self.Bind(wx.EVT_BUTTON, self.OnBtnPlusMoins, self.btn_moins)


    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        
        # Date de référence
        staticbox_periode = wx.StaticBoxSizer(self.staticbox_periode_staticbox, wx.VERTICAL)
        grid_sizer_periode = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)
        grid_sizer_periode.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.btn_plus, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.btn_moins, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox_periode.Add(grid_sizer_periode, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_periode, 1, wx.RIGHT|wx.EXPAND, 5)
        
        # Saisie
        staticbox_saisie = wx.StaticBoxSizer(self.staticbox_saisie, wx.VERTICAL)
        grid_sizer_saisie = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_saisie.Add(self.check_prestations, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_saisie.Add(self.check_factures, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox_saisie.Add(grid_sizer_saisie, 0, wx.EXPAND|wx.ALL, 5)
        grid_sizer_base.Add(staticbox_saisie, 1, wx.RIGHT|wx.EXPAND, 5)

        # Modes de règlements
        staticbox_modes = wx.StaticBoxSizer(self.staticbox_modes_staticbox, wx.VERTICAL)
        staticbox_modes.Add(self.ctrl_modes, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_modes, 1, wx.RIGHT|wx.EXPAND, 5)

        grid_sizer_base.Add(self.bouton_actualiser, 0, wx.EXPAND|wx.RIGHT, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)

    def OnBtnPlusMoins(self,event):
        if event.EventObject.Name == "plus":
            sens = 1
        else: sens = -1
        dte = self.ctrl_date_debut.GetDate()
        self.ctrl_date_debut.SetDate(dte.replace(year=dte.year + sens))
        dte = self.ctrl_date_fin.GetDate()
        self.ctrl_date_fin.SetDate(dte.replace(year=dte.year + sens))
        self.OnBoutonActualiser(None)

    def OnBoutonActualiser(self, event): 
        # Validation de la période
        date_debut = self.ctrl_date_debut.GetDate() 
        if self.ctrl_date_debut.FonctionValiderDate() == False or date_debut == None :
            dlg = wx.MessageDialog(self, _("La date de début de période semble incorrecte !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        date_fin = self.ctrl_date_fin.GetDate() 
        if self.ctrl_date_fin.FonctionValiderDate() == False or date_fin == None :
            dlg = wx.MessageDialog(self, _("La date de fin de période semble incorrecte !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        if date_fin < date_debut :
            dlg = wx.MessageDialog(self, _("La date de début de période est supérieure à la date de fin !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Validation des modes de règlement
        listeModes = self.GetModes()
        if len(listeModes) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez sélectionner au moins un mode de règlement !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Vérification droits utilisateurs
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_attestations", "creer", afficheMessage=False) == False :
            dlg = wx.MessageDialog(self, _("Vous n'avez pas l'autorisation de générer des attestations !"), _("Action non autorisée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # MAJ de la liste des prestations
        dlgAttente = PBI.PyBusyInfo(_("Recherche des données..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield() 
        try :
            self.MAJprestations() 
            del dlgAttente
        except Exception as err :
            print(err)
            del dlgAttente

    def MAJprestations(self):
        date_debut = self.ctrl_date_debut.GetDate()
        date_fin = self.ctrl_date_fin.GetDate()
        listeModes = self.GetModes()
        typesDons = self.GetTypesDons()
        self.parent.ctrl_listview.MAJ(date_debut, date_fin, listeModes,typesDons)

    def GetModes(self):
        return self.ctrl_modes.GetIDcoches() 
    
    def GetTypesDons(self):
        return self.check_prestations.Value,self.check_factures.Value,


# --------------------------------------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Panel Paramètres
        self.ctrl_parametres = Parametres(self)
        
        # CTRL Prestations
        self.staticbox_prestations = wx.StaticBox(self, -1, _("Liste des dons à attester"))
        self.label_commentaires = wx.StaticText(self, -1, _("C'est la part don réglée qui sera retenue. (Don - réglé hors période)"))

        self.listviewAvecFooter = OL_Attestations_cerfa_prestations.ListviewAvecFooter(self,  kwargs={})
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Attestations_cerfa_prestations.CTRL_Outils(self, listview=self.ctrl_listview, afficherCocher=True)


        self.__do_layout()
        
        # Données par défaut
        anneeActuelle = datetime.date.today().year
        self.ctrl_parametres.ctrl_date_debut.SetDate(datetime.date(anneeActuelle-1, 1, 1))
        self.ctrl_parametres.ctrl_date_fin.SetDate(datetime.date(anneeActuelle-1, 12, 31))

        # Init contrôles
        self.ctrl_parametres.MAJprestations()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        # Panel des paramètres
        grid_sizer_contenu.Add(self.ctrl_parametres, 1, wx.EXPAND, 0)
        
        # Ctrl des prestations
        staticbox_prestations = wx.StaticBoxSizer(self.staticbox_prestations, wx.VERTICAL)
        staticbox_prestations.Add(self.label_commentaires, 0, wx.ALL|wx.EXPAND, 5)
        staticbox_prestations.Add(self.listviewAvecFooter, 1, wx.EXPAND, 5)
        staticbox_prestations.Add(self.ctrl_recherche, 0, wx.EXPAND, 5)

        grid_sizer_contenu.Add(staticbox_prestations, 1, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout() 

    def Validation(self):
        # Validation des prestations
        listePrestations = self.ctrl_listview.GetTracksCoches() 
        if len(listePrestations) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez cocher au moins une prestation !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True
    
    def GetPeriode(self):
        return self.ctrl_parametres.ctrl_date_debut.GetDate(), self.ctrl_parametres.ctrl_date_fin.GetDate() 
    
    def GetPrestations(self):
        return self.ctrl_listview.GetTracksCoches()

    def MAJ(self):
        self.ctrl_listview.MAJ

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.boutonTest = wx.Button(panel, -1, _("Bouton de test"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.panel = panel
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)
        
    def OnBoutonTest(self, event):
        """ Bouton Test """
        # Test d'affichage des résultats
        listePrestations = self.ctrl.GetPrestations()
        from Ol import OL_Attestations_cerfa_selection
        frm = OL_Attestations_cerfa_selection.MyFrame(self, listePrestations)
        frm.SetSize((900, 500))
        frm.Show()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None)
    frame_1.SetSize((980, 650))
    frame_1.CenterOnScreen() 
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
