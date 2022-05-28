#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania ajout de champs sur les groupes conditions age, campeur etc...
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Saisie_nombre

class Saisie(wx.Dialog):
    def __init__(self, parent, nom=None, abrege=None, ageMini=None,
                 ageMaxi=None,
                 campeur=None, nbre_inscrits_max=None, observation=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent

        self.label_nom = wx.StaticText(self, -1, _("Nom :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")
        if nom != None:
            self.ctrl_nom.SetValue(nom)

        self.label_abrege = wx.StaticText(self, -1, _("Abrégé :"))
        self.ctrl_abrege = wx.TextCtrl(self, -1, "")
        if abrege != None:
            self.ctrl_abrege.SetValue(abrege)

        self.label_campeur = wx.StaticText(self, -1, _("Catégorie tarif :"))
        self.ctrl_campeur = wx.RadioBox(self, -1,
                                        choices=["Animateurs", "Campeurs",
                                                 "Staff & Autres"],
                                        label="Proposer les tarifs")
        if campeur != None:
            self.ctrl_campeur.SetSelection(campeur)

        self.label_nbre_inscrits_max = wx.StaticText(self, -1, _("Nbre Maximum :"))
        self.ctrl_nbre_inscrits_max = CTRL_Saisie_nombre.CTRL(self, "0", size=(50, 20))
        if nbre_inscrits_max != None:
            self.ctrl_nbre_inscrits_max.SetValue(str(nbre_inscrits_max))

        self.label_ageMini = wx.StaticText(self, -1, _("Age minimum :"))
        self.ctrl_ageMini = CTRL_Saisie_nombre.CTRL(self, "0", size=(50, 20))
        if ageMini != None:
            self.ctrl_ageMini.SetValue(str(ageMini))

        self.label_ageMaxi = wx.StaticText(self, -1, _("Age maximum :"))
        self.ctrl_ageMaxi = CTRL_Saisie_nombre.CTRL(self, "0", size=(50, 20))
        if ageMaxi != None:
            self.ctrl_ageMaxi.SetValue(str(ageMaxi))

        self.label_observation = wx.StaticText(self, -1, _("Observation :"))
        self.ctrl_observation = wx.TextCtrl(self, -1, "", size=(120, 80),
                                            style=wx.TE_MULTILINE)
        if observation != None:
            self.ctrl_observation.SetValue(observation)

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"),
                                                  cheminImage=Chemins.GetStaticPath(
                                                      "Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"),
                                                cheminImage=Chemins.GetStaticPath(
                                                    "Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL,
                                                     texte=_("Annuler"),
                                                     cheminImage=Chemins.GetStaticPath(
                                                         "Images/32x32/Annuler.png"))

        if nom == None:
            self.SetTitle(_("Saisie d'un groupe"))
        else:
            self.SetTitle(_("Modification d'un groupe"))
        self.SetMinSize((500, -1))

        self.ctrl_nom.SetToolTip(
            _("Saisissez ici l'intitulé du groupe (Ex : '3-6 ans', 'Grands'...)"))
        self.ctrl_abrege.SetToolTip(
            _("Saisissez ici le nom abrégé du groupe (Ex : '3-6', 'GRANDS'..."))
        mess = "Type non prioritaire, c'est la catégorie du tarif qui détermine le type d'effectif. "
        mess += "Le choix ici filtrera les tarifs de ce type d'effectif. Le type d'effectif sert pour les tableaux de suivi du remplissage par groupe"
        self.ctrl_campeur.SetToolTip(mess)
        self.ctrl_nbre_inscrits_max.SetToolTip(
            _("Saisissez le nombre maximum d'inscription pour ce groupe"))
        self.ctrl_ageMini.SetToolTip(
            _("Saisissez l'âge minimum pour la participation à ce groupe"))
        self.ctrl_ageMaxi.SetToolTip(
            _("Saisissez l'âge maximum pour la participation à ce groupe"))
        self.ctrl_observation.SetToolTip(_("Saisissez une observation libre"))

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=7, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(self.label_nom, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_abrege, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_abrege, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_ageMini, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_ageMini, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_ageMaxi, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_ageMaxi, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_campeur, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_campeur, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_nbre_inscrits_max, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_nbre_inscrits_max, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_observation, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_observation, 0, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1,
                            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

    def GetNom(self):
        return self.ctrl_nom.GetValue()

    def GetAbrege(self):
        return self.ctrl_abrege.GetValue()

    def GetAgeMini(self):
        return self.ctrl_ageMini.GetValue()

    def GetAgeMaxi(self):
        return self.ctrl_ageMaxi.GetValue()

    def GetCampeur(self):
        return self.ctrl_campeur.GetSelection()

    def GetNbrMaxi(self):
        return self.ctrl_nbre_inscrits_max.GetValue()

    def GetObservation(self):
        return self.ctrl_observation.GetValue()

    def OnBoutonOk(self, event):
        nom = self.ctrl_nom.GetValue()
        abrege = self.ctrl_abrege.GetValue()
        if nom == "":
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir un nom de groupe !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return
        if abrege == "":
            dlg = wx.MessageDialog(self,
                                   _("Etes-vous sûr de ne pas vouloir saisir de nom abrégé pour ce groupe ?"),
                                   _("Confirmation"),
                                   wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES:
                return
        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Groupes")

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Saisie(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
