#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Choix_modele
from Utils import UTILS_Config



class Dialog(wx.Dialog):
    def __init__(self, parent, provisoire=False, titre=_("Aper�u d'une lettre de rappel"), intro=_("Vous pouvez ici cr�er un aper�u PDF du document s�lectionn�.")):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent
        
        # Bandeau
        if provisoire == True :
            intro += _(" <FONT COLOR = '#FF0000'>Attention, il ne s'agit que d'un document provisoire avant g�n�ration !</FONT>")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Apercu.png")
        
        # Param�tres
        self.box_parametres_staticbox = wx.StaticBox(self, -1, _("Param�tres"))
        
        self.label_modele = wx.StaticText(self, -1, _("Mod�le :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="rappel")
        self.ctrl_modele.SetMinSize((260, -1))
        
        self.check_coupons = wx.CheckBox(self, -1, _("Ins�rer les coupons-r�ponses"))
        self.check_codesbarres = wx.CheckBox(self, -1, _("Ins�rer les codes-barres"))
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aper�u"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init contr�les
        self.check_coupons.SetValue(UTILS_Config.GetParametre("impression_rappels_coupon", defaut=1))
        self.check_codesbarres.SetValue(UTILS_Config.GetParametre("impression_rappels_codeBarre", defaut=1))


    def __set_properties(self):
        self.ctrl_modele.SetToolTip(wx.ToolTip(_("S�lectionnez ici le mod�le de document")))
        self.check_coupons.SetToolTip(wx.ToolTip(_("Cochez cette case pour ins�rer les coupons-r�ponses")))
        self.check_codesbarres.SetToolTip(wx.ToolTip(_("Cochez cette case pour ins�rer les codes-barres")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        # Param�tres
        box_parametres = wx.StaticBoxSizer(self.box_parametres_staticbox, wx.VERTICAL)
        
        grid_sizer_haut = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_haut.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut.Add(self.ctrl_modele, 0, wx.EXPAND, 0)
                
        box_parametres.Add(grid_sizer_haut, 0, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_bas = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)
        grid_sizer_bas.Add(self.check_coupons, 0, 0, 0)
        grid_sizer_bas.Add(self.check_codesbarres, 0, 0, 0)
        box_parametres.Add(grid_sizer_bas, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_base.Add(box_parametres, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Gnration1")

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)

    def GetParametres(self):
        """ Retourne les param�tres s�lectionn�s """
        dictParametres = {} 
        
        # Mod�le
        dictParametres["IDmodele"] = self.ctrl_modele.GetID() 
        if dictParametres["IDmodele"] == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un mod�le !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        dictParametres["coupon"] = self.check_coupons.GetValue()
        dictParametres["codeBarre"] = self.check_codesbarres.GetValue()
        
        return dictParametres


    def OnBoutonOk(self, event): 
        dictParametres = self.GetParametres()
        if dictParametres == False :
            return
        self.EndModal(wx.ID_OK)




if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, provisoire=True)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
