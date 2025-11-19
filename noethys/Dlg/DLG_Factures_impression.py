#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Liste_factures



class Dialog(wx.Dialog):
    def __init__(self, parent, filtres=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        # Bandeau
        intro = _("Cochez les factures à imprimer puis cliquez sur le bouton 'Aperçu' pour visualiser le ou les documents dans votre lecteur PDF.")
        titre = "Impression de factures"

        self.SetTitle("DLG_Factures_impression")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Imprimante.png")
        
        # Factures
        self.box_factures_staticbox = wx.StaticBox(self, -1, _("Liste des factures"))
        self.panel_factures = CTRL_Liste_factures.CTRL(self, filtres=filtres)
        
        # Options
        #self.ctrl_options = CTRL_Factures_options.CTRL(self)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_imprime = CTRL_Bouton_image.CTRL(self, texte=_("Génération PDF"), cheminImage="Images/32x32/Imprimante.png")
        self.bouton_visu = CTRL_Bouton_image.CTRL(self, texte=_("Aperçu-Impression"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        # Schedule __calledAfter to run once the dialog is idle (i.e., shown)
        wx.CallAfter(self.__calledAfter)

    def __calledAfter(self):
        self.panel_factures.MAJ()
        self.panel_factures.ctrl_filtres.OnBoutonParametres(None)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_imprime.SetToolTip(wx.ToolTip(
            "Cliquez ici pour imprimer les factures cochées dans la liste"))
        self.bouton_visu.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher le PDF")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((900, 850))
        #self.ctrl_options.SetMinSize((400,300))

        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprime, self.bouton_imprime)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_visu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Factures
        box_factures = wx.StaticBoxSizer(self.box_factures_staticbox, wx.VERTICAL)
        box_factures.Add(self.panel_factures, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(box_factures, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Options
        #grid_sizer_base.Add(self.ctrl_options, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_imprime, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_visu, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(3)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def GetTracksCoches(self):
        tracks = self.panel_factures.GetTracksCoches()
        if not tracks:
            self.panel_factures.ctrl_factures.CocheTout()
            tracks = self.panel_factures.GetTracksCoches()
        if not tracks :
            dlg = wx.MessageDialog(self, _("Vous devez avoir au moins une facture dans la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        return tracks

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Imprimer")

    def OnBoutonAnnuler(self, event): 
        #self.ctrl_options.MemoriserParametres()
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonImprime(self, event):
        self.panel_factures.ctrl_factures.ImprimerItems(afficherDoc = False)

    def OnBoutonApercu(self, event):
        self.panel_factures.ctrl_factures.ImprimerItems(afficherDoc = True)


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
