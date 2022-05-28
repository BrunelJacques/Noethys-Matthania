#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Liste_rappels
from Ctrl import CTRL_Rappels_options
from Utils import UTILS_Rappels


class Dialog(wx.Dialog):
    def __init__(self, parent, filtres=[],dictParametres=None):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX,
                           name="DLG_Rappels_impression")
        # Bandeau
        intro = _("Cochez les lettres de rappel à imprimer puis cliquez sur le bouton 'Aperçu' pour visualiser le ou les documents dans votre lecteur PDF.")
        titre = _("DLG_Rappels_impression lettres de rappel")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, cheminImage=Chemins.GetStaticPath("Images/32x32/Imprimante.png"))
        
        # Factures
        self.box_factures_staticbox = wx.StaticBox(self, -1, _("Liste des lettres de rappel"))
        self.CTRL_Liste_rappels = CTRL_Liste_rappels.CTRL(self, filtres=filtres)
        if dictParametres:
            self.CTRL_Liste_rappels.dictParametres = dictParametres
            self.CTRL_Liste_rappels.ctrl_rappels.lstIDfamilles = dictParametres["listeIDfamilles"]
        self.CTRL_Liste_rappels.ctrl_rappels.onlyRappels = True

        # Options
        self.box_options_staticbox = wx.StaticBox(self, -1, _("Options d'impression"))
        self.ctrl_options = CTRL_Rappels_options.CTRL(self)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aperçu"), cheminImage=Chemins.GetStaticPath("Images/32x32/Apercu.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init Contrôles
        self.CTRL_Liste_rappels.MAJ()

    def __set_properties(self):
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour afficher le PDF"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((890, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Factures
        box_factures = wx.StaticBoxSizer(self.box_factures_staticbox, wx.VERTICAL)
        box_factures.Add(self.CTRL_Liste_rappels, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_factures, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Options
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        box_options.Add(self.ctrl_options, 0, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_options, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
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
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Imprimer1")

    def OnBoutonAnnuler(self, event): 
        self.ctrl_options.MemoriserParametres() 
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonApercu(self, event): 
        """ Aperçu PDF des lettres de rappel """
        # Validation des données saisies
        tracks = self.CTRL_Liste_rappels.GetTracksCoches() 
        if len(tracks) == 0 : 
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune lettre de rappel à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        listeIDrappel = []
        lstIDfamilles = []
        for track in tracks :
            listeIDrappel.append(track.IDrappel)
            lstIDfamilles.append(track.IDfamille)
        
        # Récupération des options
        dictOptions = self.ctrl_options.GetOptions()
        if dictOptions == False :
            return False

        # Impression des factures sélectionnées
        facturation = UTILS_Rappels.Facturation(lstIDfamilles=lstIDfamilles)
        facturation.Impression(afficherDoc=True, dictOptions=dictOptions, repertoire=dictOptions["repertoire"])

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
