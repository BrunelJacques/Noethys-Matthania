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

class Dialog(wx.Dialog):
    def __init__(self, parent, IDactivite=None, IDcategorie_tarif=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDactivite = IDactivite
        self.IDcategorie_tarif = IDcategorie_tarif
        
        # Nom
        self.staticbox_nom_staticbox = wx.StaticBox(self, -1, _("Catégorie de tarif"))
        self.label_nom = wx.StaticText(self, -1, _("Nom :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")
        self.label_campeur = wx.StaticText(self, -1, _("Suivi remplissage :"))
        self.ctrl_campeur = wx.RadioBox(self, -1, choices= ["Animateurs","Campeurs","Staff & Autres"],
                                        label="Type de campeur", style=wx.RA_SPECIFY_COLS)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        if self.IDcategorie_tarif != None :
            self.Importation()

    def __set_properties(self):
        self.SetTitle(_("Saisie d'une catégorie de tarif"))
        self.ctrl_nom.SetToolTip(_("Saisissez un nom pour cette catégorie"))
        mess = "Seuls les campeurs sont dans le tableau d'accueil des effectifs,"
        mess += "ce type d'effectif sera utilisé dans les tableaux de suivi du remplissage par groupe"
        self.ctrl_campeur.SetToolTip(mess)
        self.label_campeur.SetToolTip(mess)
        """
        self.bouton_villes_ajouter.SetToolTip(_(u"Cliquez ici pour ajouter une ville dans la liste"))
        self.bouton_villes_supprimer.SetToolTip(_(u"Cliquez ici pour enlever la ville sélectionnée de la liste"))
        """
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))

        self.SetMinSize((420, 250))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        staticbox_nom = wx.StaticBoxSizer(self.staticbox_nom_staticbox, wx.VERTICAL)
        grid_sizer_nom = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_nom.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_nom.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_eff = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_eff.Add(self.label_campeur, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_eff.Add(self.ctrl_campeur, 0, wx.EXPAND, 0)
        grid_sizer_nom.AddGrowableCol(1)
        staticbox_nom.Add(grid_sizer_nom, 1, wx.ALL|wx.EXPAND, 5)
        staticbox_nom.Add(grid_sizer_eff, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_nom, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        grid_sizer_base.Add((10,10), 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)

        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Tarification")
    
    def GetIDcategorieTarif(self):
        return self.IDcategorie_tarif

    def OnBoutonOk(self, event):
        # Vérification des données
        if self.ctrl_nom.GetValue() == "" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom pour cette catégorie !"), "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return
        estAnim = False
        for radical in (u"anim",u"equip",u"perso", u"bénévol",u"cadre"):
            if radical in self.ctrl_nom.GetValue().lower():
                estAnim = True

        if self.ctrl_campeur.GetSelection() != 1 and not estAnim:
            mess = u"Tarif pour non campeur\n\n"
            mess += u"Il n'entrera pas dans l'effectifs campeur du suivi du nombre d'inscrits\n"
            mess += u"Il ne contient pas un radical 'anim', 'perso', 'bénévol', 'cadre' ou 'equip'"
            mess += u"\nSeul le personnel accompagnant n'est pas 'campeur', quelle que soit l'activité."
            mess += u"\nConfirmez-vous votre choix d'assimiler ce tarif à celui du personnel ?"
            dlg = wx.MessageDialog(self, mess, "A confirmer", wx.YES_NO | wx.ICON_EXCLAMATION)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                self.ctrl_campeur.SetFocus()
                return
        if self.ctrl_campeur.GetSelection() == wx.CHK_CHECKED and estAnim:
            mess = u"Tarif pour le personnel dans les campeurs\n\n"
            mess += u"Contient un radical 'anim', 'perso', 'bénévol', 'cadre' ou 'equip'"
            mess += u"\nle personnel n'est pas censé entrer dans le suivi des effectifs des campeurs."
            mess += u"\nConfirmez-vous votre choix d'assimiler ce tarif à celui des campeurs ?"
            dlg = wx.MessageDialog(self, mess, "A confirmer", wx.YES_NO | wx.ICON_EXCLAMATION)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                #self.ctrl_campeur.SetSelection()
                return

        # Sauvegarde
        DB = GestionDB.DB()
        listeDonnees = [("IDactivite", self.IDactivite),
                        ("nom", self.ctrl_nom.GetValue()),
                        ("campeur", self.ctrl_campeur.GetSelection())
                        ]
        if self.IDcategorie_tarif == None :
            self.IDcategorie_tarif = DB.ReqInsert("categories_tarifs", listeDonnees)
        else:
            DB.ReqMAJ("categories_tarifs", listeDonnees, "IDcategorie_tarif", self.IDcategorie_tarif)
        DB.Close()
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)
    
    def Importation(self):
        db = GestionDB.DB()
        req = """SELECT nom,campeur
        FROM categories_tarifs 
        WHERE IDcategorie_tarif=%d; """ % self.IDcategorie_tarif
        db.ExecuterReq(req, MsgBox="DLG_Saisie_categorie_tarif.Importation")
        listeDonnees = db.ResultatReq()
        db.Close()
        if len(listeDonnees) == 0 : return
        # Nom
        nom = listeDonnees[0][0]
        campeur = listeDonnees[0][1]
        self.ctrl_nom.SetValue(nom)
        if campeur:
            self.ctrl_campeur.SetSelection(campeur)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDactivite=1, IDcategorie_tarif=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
