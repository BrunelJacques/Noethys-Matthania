#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, modifié pour listes plus fonctionnelles
# Site internet :  www.noethys.com old
# Auteur:           Jacques BRUNEL
# Copyright:       (c) 2019-10 Ivan LUCAS, JB - Jacques BRUNEL
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_SelectionActivites
from Utils import UTILS_Config

CHOICES_TRI_GROUPES = [
    ("Taux de remplissage", 99), # '99' sera géré en exception
    ("Nom activité","activites.nom"),
    ("Nom du groupe","groupes.nom"),
    ("Code de l'activité","activites.code_comptable"),
    ("Nombre de campeurs","nbreInscrits"), # correspond au AS nbreInscrits de la requête sql
    ("Places de campeurs","groupes.nbre_inscrits_max"),
    ("Date de début d'activité","activites.date_debut"),
    ("Date de fin d'activité",'activites_date_fin')]

CHOICES_TRI_ACTIVITES = [
    ("Taux de remplissage", 99), # '99' sera géré en exception
    ("Nom activité","activites.nom"),
    ("Code de l'activité","activites.code_comptable"),
    ("Nombre d'inscrits","nbreInscrits"), # correspond au AS nbreInscrits de la requête sql
    ("Places totales maxi","activites.nbre_inscrits_max"),
    ("Date de début d'activité","activites.date_debut"),
    ("Date de fin d'activité",'activites_date_fin')]

# ces deux classes sont quasi identiques, à factoriser dans CTRL_SelectionActivitésModal

class DlgGroupes(wx.Dialog):
    def __init__(self, parent, ):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX)
        self.parent = parent

        # Activités
        self.box_activites_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Sélection des activités"))
        self.ctrl_activites = CTRL_SelectionActivites.CTRL(self)

        # Options
        self.box_options_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Options d'affichage"))
        self.label_tri = wx.StaticText(self, wx.ID_ANY, _("Critère de tri :"))
        lstChoix = [x for (x,y) in CHOICES_TRI_GROUPES]
        self.ctrl_tri = wx.Choice(self, wx.ID_ANY, choices=lstChoix)
        self.ctrl_tri.SetSelection(0)

        self.label_sens = wx.StaticText(self, wx.ID_ANY, _("Sens de tri :"))
        self.ctrl_sens = wx.Choice(self, wx.ID_ANY, choices=[_("Croissant"), _("Décroissant")])
        self.ctrl_sens.SetSelection(0)

        self.label_alerte = wx.StaticText(self, wx.ID_ANY, _("Seuil d'alerte en % :"))
        self.ctrl_alerte = wx.SpinCtrl(self, wx.ID_ANY, "", min=0, max=100)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        # Importation
        self.Importation()

    def __set_properties(self):
        self.SetTitle(_("Paramètres d'affichage des inscriptions"))
        self.ctrl_tri.SetToolTip(_("Sélectionner un critère de tri"))
        self.ctrl_sens.SetToolTip(_("Sélectionner un sens de tri"))
        self.ctrl_alerte.SetToolTip(_("Saisissez une valeur de seuil d'alerte. Noethys signale ainsi lorsque le nombre de places restantes est égal ou inférieur à cette valeur"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((300, 570))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 0, 0)

        box_activites = wx.StaticBoxSizer(self.box_activites_staticbox, wx.VERTICAL)
        box_activites.Add(self.ctrl_activites, 1, wx.TOP | wx.EXPAND, 0)
        grid_sizer_base.Add(box_activites, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(3, 2, 10, 10)
        grid_sizer_options.Add(self.label_tri, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_tri, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_sens, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_sens, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_alerte, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_alerte, 0, 0, 0)
        grid_sizer_options.AddGrowableCol(1)
        box_options.Add(grid_sizer_options, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(box_options, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def Importation(self):
        # Activités et dates
        activites = UTILS_Config.GetParametre("nbre_campeurs_parametre_activites", defaut=None)
        if activites and ("###" in activites ):
            label, activites = activites.split("###")
        if activites != None and activites != '':
            lstIDactivite = []
            for ID in activites.split(";") :
                if not int(ID) in lstIDactivite:
                    lstIDactivite.append(int(ID))
            dates = UTILS_Config.GetParametre("nbre_campeurs_parametre_dates", defaut="")
            self.ctrl_activites.SetDates(dates=dates, lstIDactivites=lstIDactivite)
            self.ctrl_activites.SetValeurs(lstIDactivite)
            self.ctrl_activites.ctrl_activites.CocheIDliste(lstIDactivite)
            self.ctrl_activites.ctrl_activites.Modified()

        # Options
        self.ctrl_tri.SetSelection(UTILS_Config.GetParametre("nbre_campeurs_parametre_tri", 3))
        self.ctrl_sens.SetSelection(UTILS_Config.GetParametre("nbre_campeurs_parametre_sens", 1))
        self.ctrl_alerte.SetValue(UTILS_Config.GetParametre("nbre_campeurs_parametre_alerte", 5))

    def OnBoutonOk(self, event):
        if self.ctrl_activites.Validation() == False :
            return
        # Mémorisation des activités
        dateDeb = self.ctrl_activites.ctrl_date_debut.Value
        dateFin = self.ctrl_activites.ctrl_date_fin.Value
        dates = str(dateDeb) + ";" + str(dateFin)
        UTILS_Config.SetParametre("nbre_campeurs_parametre_dates", dates)
        lstIDactivitetemp = self.ctrl_activites.GetActivites()
        lstIDactivite = []
        for ID in lstIDactivitetemp :
            lstIDactivite.append(str(ID))
        parametre = "%s" % ";".join(lstIDactivite)
        UTILS_Config.SetParametre("nbre_campeurs_parametre_activites", parametre)

        # Options
        UTILS_Config.SetParametre("nbre_campeurs_parametre_tri", self.ctrl_tri.GetSelection())
        UTILS_Config.SetParametre("nbre_campeurs_parametre_sens", self.ctrl_sens.GetSelection())
        UTILS_Config.SetParametre("nbre_campeurs_parametre_alerte", int(self.ctrl_alerte.GetValue()))
        self.EndModal(wx.ID_OK)

class DlgActivites(wx.Dialog):
    def __init__(self, parent, ):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX)
        self.parent = parent
        
        # Activités
        self.box_activites_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Sélection des activités"))
        self.ctrl_activites = CTRL_SelectionActivites.CTRL(self)
        
        # Options
        self.box_options_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Options d'affichage"))
        self.label_tri = wx.StaticText(self, wx.ID_ANY, _("Critère de tri :"))
        lstChoix = [x for (x,y) in CHOICES_TRI_ACTIVITES]
        self.ctrl_tri = wx.Choice(self, wx.ID_ANY, choices=lstChoix)
        self.ctrl_tri.SetSelection(0)

        self.label_sens = wx.StaticText(self, wx.ID_ANY, _("Sens de tri :"))
        self.ctrl_sens = wx.Choice(self, wx.ID_ANY, choices=[_("Croissant"), _("Décroissant")])
        self.ctrl_sens.SetSelection(0)

        self.label_alerte = wx.StaticText(self, wx.ID_ANY, _("Seuil d'alerte :"))
        self.ctrl_alerte = wx.SpinCtrl(self, wx.ID_ANY, "", min=0, max=100)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Importation
        self.Importation() 

    def __set_properties(self):
        self.SetTitle(_("Paramètres d'affichage des inscriptions"))
        self.ctrl_tri.SetToolTip(_("Sélectionner un critère de tri"))
        self.ctrl_sens.SetToolTip(_("Sélectionner un sens de tri"))
        self.ctrl_alerte.SetToolTip(_("Saisissez une valeur de seuil d'alerte. Noethys signale ainsi lorsque le nombre de places restantes est égal ou inférieur à cette valeur"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((300, 570))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 0, 0)
        
        box_activites = wx.StaticBoxSizer(self.box_activites_staticbox, wx.VERTICAL)
        box_activites.Add(self.ctrl_activites, 1, wx.TOP | wx.EXPAND, 0)
        grid_sizer_base.Add(box_activites, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(3, 2, 10, 10)
        grid_sizer_options.Add(self.label_tri, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_tri, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_sens, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_sens, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_alerte, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_alerte, 0, 0, 0)
        grid_sizer_options.AddGrowableCol(1)
        box_options.Add(grid_sizer_options, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(box_options, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event):  
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonAnnuler(self, event):  
        self.EndModal(wx.ID_CANCEL)
    
    def Importation(self):
        # Activités et dates
        activites = UTILS_Config.GetParametre("nbre_inscrits_parametre_activites", defaut=None)
        if activites and ("###" in activites ):
            label, activites = activites.split("###")
        if activites != None and activites != '':
            lstIDactivite = []
            for ID in activites.split(";") :
                if not int(ID) in lstIDactivite:
                    lstIDactivite.append(int(ID))
            dates = UTILS_Config.GetParametre("nbre_inscrits_parametre_dates", defaut="")
            self.ctrl_activites.SetDates(dates=dates, lstIDactivites=lstIDactivite)
            self.ctrl_activites.SetValeurs(lstIDactivite)
            self.ctrl_activites.ctrl_activites.CocheIDliste(lstIDactivite)
            self.ctrl_activites.ctrl_activites.Modified()

        # Options
        self.ctrl_tri.SetSelection(UTILS_Config.GetParametre("nbre_inscrits_parametre_tri", 3))
        self.ctrl_sens.SetSelection(UTILS_Config.GetParametre("nbre_inscrits_parametre_sens", 1))
        self.ctrl_alerte.SetValue(UTILS_Config.GetParametre("nbre_inscrits_parametre_alerte", 5))

    def OnBoutonOk(self, event):  
        if self.ctrl_activites.Validation() == False :
            return
        
        # Mémorisation des activités
        dateDeb = self.ctrl_activites.ctrl_date_debut.Value
        dateFin = self.ctrl_activites.ctrl_date_fin.Value
        dates = str(dateDeb) + ";" + str(dateFin)
        UTILS_Config.SetParametre("nbre_inscrits_parametre_dates", dates)
        lstIDactivitetemp = self.ctrl_activites.GetActivites()
        lstIDactivite = []
        for ID in lstIDactivitetemp :
            lstIDactivite.append(str(ID))
        parametre = "%s" % ";".join(lstIDactivite)
        UTILS_Config.SetParametre("nbre_inscrits_parametre_activites", parametre)
        
        # Options
        UTILS_Config.SetParametre("nbre_inscrits_parametre_tri", self.ctrl_tri.GetSelection())
        UTILS_Config.SetParametre("nbre_inscrits_parametre_sens", self.ctrl_sens.GetSelection())
        UTILS_Config.SetParametre("nbre_inscrits_parametre_alerte", int(self.ctrl_alerte.GetValue()))
        
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = DlgActivites(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()


