#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania dérivé de DLG_Saisie_utilisateur
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB



# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDgroupe_activite=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent      
        self.IDgroupe_activite = IDgroupe_activite
        
        # Identité
        self.staticbox_identite_staticbox = wx.StaticBox(self, -1, _("Type de groupe d'activités"))
        self.label_nom = wx.StaticText(self, -1, _("Nom du groupe :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")
        self.label_observations = wx.StaticText(self, -1, _("observations :"))
        self.ctrl_observations = wx.TextCtrl(self, -1, "",size=(50,50),style=wx.TE_MULTILINE)

        # Commandes
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        if self.IDgroupe_activite == None :
            self.SetTitle(_("Ajout d'un groupe_activite"))
        else:
            self.SetTitle(_("Modification d'un groupe_activite"))
            self.Importation()

    def __set_properties(self):
        self.ctrl_nom.SetToolTip(_("Saisissez le nom du groupe d'activités\nLes activités périodiques seront dans le même groupe"))
        self.ctrl_observations.SetToolTip(_("Saisissez ici des observations éventuelles concernant le groupe d'activités"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((400, 300))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_haut = wx.FlexGridSizer(rows=1, cols=1, vgap=10, hgap=10)

        # Identité
        staticbox_identite = wx.StaticBoxSizer(self.staticbox_identite_staticbox, wx.VERTICAL)
        grid_sizer_identite = wx.FlexGridSizer(rows=2, cols=2, vgap=15, hgap=10)
        grid_sizer_identite.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_identite.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_identite.Add(self.label_observations, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_identite.Add(self.ctrl_observations, 0, wx.EXPAND, 0)

        grid_sizer_identite.AddGrowableCol(1)
        grid_sizer_identite.AddGrowableRow(1)
        staticbox_identite.Add(grid_sizer_identite, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut.Add(staticbox_identite, 1, wx.EXPAND, 0)
        
        grid_sizer_haut.AddGrowableCol(0)
        grid_sizer_haut.AddGrowableRow(0)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.ALL|wx.EXPAND, 10)

        # Commandes
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((10,10), 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Utilisateurs")


    def OnBoutonOk(self, event):
        # Vérification des données
        if len(self.ctrl_nom.GetValue()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return
            return

        # Sauvegarde
        retour = self.Sauvegarde()
        
        # Fermeture de la fenêtre
        if retour == True:
            self.EndModal(wx.ID_OK)

    def GetIDgroupe_activite(self):
        return self.IDgroupe_activite

    def Importation(self):
        """ Importation des donnees de la base """
        DB = GestionDB.DB()
        req = """SELECT nom, observations
        FROM types_groupes_activites
        WHERE IDtype_groupe_activite=%d;""" % self.IDgroupe_activite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        for item in listeDonnees[0]:
            if item == None: item = ""
        nom, observations = listeDonnees[0]

        if nom == None: nom = ""
        self.ctrl_nom.SetValue(nom)
        if observations == None: observations = ""
        self.ctrl_observations.SetValue(observations)


    def Sauvegarde(self):
        """ Sauvegarde """
        nom          = self.ctrl_nom.GetValue()
        observations = self.ctrl_observations.GetValue()

        DB = GestionDB.DB()
        listeDonnees = [    
                ("nom", nom),
                ("observations", observations),
            ]
        if self.IDgroupe_activite == None :
            ret = self.IDgroupe_activite = DB.ReqInsert("types_groupes_activites", listeDonnees,retourID=False,MsgBox =  "DLG_Saisie_groupe_activite MAJ")
        else:
            ret = DB.ReqMAJ("types_groupes_activites", listeDonnees, "IDtype_groupe_activite", self.IDgroupe_activite,MsgBox = "DLG_Saisie_groupe_activite MAJ")
        DB.Close()
        if ret != "ok":
            GestionDB.MessageBox(self,ret)
            return False
        return True


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDgroupe_activite=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
