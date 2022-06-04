#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Branche Matthania
# Module :         Remontée de fichiers python
# Auteur:          JB adaptation de DLG_Restauration
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import os
import sys
import wx.lib.agw.customtreectrl as CT
from Ctrl import CTRL_Bandeau
import GestionDB
from Utils import UTILS_Sauvegarde
from Utils import UTILS_Fichiers
from Utils import UTILS_Cryptage_fichier

sys.modules['UTILS_Cryptage_fichier'] = UTILS_Cryptage_fichier

from Dlg import DLG_Saisie_param_reseau

def GetNameReleaseZip():
    # Demande l'emplacement du fichier
    wildcard = "Release Noethys (*.zip; *.7z)|*.*"
    intro = "Veuillez sélectionner le fichier contenant la MISE A JOUR DE NOETHYS"
    return UTILS_Fichiers.SelectionFichier(intro,wildcard,verifZip=True)

def GetVersionsFile(releaseZip):
    if not releaseZip: return
    return UTILS_Fichiers.GetOneFileInZip(releaseZip,"versions.txt")

class CTRL_Donnees(wx.StaticBox):
    def __init__(self, parent):
        label = "Info dernières versions"
        id = wx.ID_ANY
        pos = wx.DefaultPosition
        size = wx.DefaultSize
        style = wx.SUNKEN_BORDER
        wx.StaticBox.__init__(self, parent, id, label, pos, size, style)

        self.nameRelase = GetNameReleaseZip()
        self.versionsFile = GetVersionsFile(self.nameRelase)
        if self.versionsFile:
            self.SetValue(self.versionsFile)

# ------------------------------------------------------------------------------------------------------------------------------------------------


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        intro = _("Vous pouvez ici mettre à jour votre version Noethys. Le numéro de version actif est en haut de l'écran")
        titre = _("Release")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Restaurer.png")
                
        # Données
        self.box_donnees_staticbox = wx.StaticBox(self, -1, _("Version choisie:"))
        self.ctrl_donnees = CTRL_Donnees(self)
        self.ctrl_donnees.SetMinSize((250, -1))
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer la restauration")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((420, 460))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        box_donnees = wx.StaticBoxSizer(self.box_donnees_staticbox, wx.VERTICAL)
        box_donnees.Add(self.ctrl_donnees, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_donnees, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
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
        UTILS_Aide.Aide("Restaurerunesauvegarde")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):         
        # Données à sauver

        if True:
            # Récupère les paramètres chargés
            DB = GestionDB.DB() 
            if DB.echec != 1 :
                if DB.isNetwork == True :
                    dictConnexion = DB.GetParamConnexionReseau() 
            DB.Close() 
            
            # Demande les paramètres de connexion réseau
            if dictConnexion == None :
                
                # Demande les paramètres de connexion
                intro = _("Les fichiers que vos souhaitez restaurer nécessite une connexion réseau.\nVeuillez saisir vos paramètres de connexion MySQL:")
                dlg = DLG_Saisie_param_reseau.Dialog(self, intro=intro)
                if dlg.ShowModal() == wx.ID_OK:
                    dictConnexion = dlg.GetDictValeurs()
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
                
                # Vérifie si la connexion est bonne
                resultat = DLG_Saisie_param_reseau.TestConnexion(dictConnexion)
                if resultat == False :
                    dlg = wx.MessageDialog(self, _("Echec du test de connexion.\n\nLes paramètres ne semblent pas exacts !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
         

        # Fin du processus
        dlg = wx.MessageDialog(self, _("Le processus de mise à jour est terminé."), "Release", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Fermeture
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
