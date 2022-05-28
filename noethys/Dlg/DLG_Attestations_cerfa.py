#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau

from Dlg.DLG_Attestations_cerfa_parametres import Panel as Page1
from Dlg.DLG_Attestations_cerfa_selection import Panel as Page2
from Dlg.DLG_Attestations_cerfa_edition import Panel as Page3

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Attestations_cerfa_generation", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        intro = _("Vous pouvez ici générer des attestations fiscales à imprimer ou envoyer par Email Page 1 : Sélectionnez des paramètres puis cliquez sur Rafraîchir pour afficher les prestations à inclure. Page 2 : Cochez les attestations à générer puis créez les Cerfas. Page3 : Consultez, Envoyez par Email ou Imprimez")
        titre = _("DLG_Attestations_cerfa")
        titreB = _("Génération des attestations fiscales 'Dons aux oeuvres' CERFA")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titreB, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")
        self.listePages = ("Page1", "Page2", "Page3")
        self.oldPage = None
        self.static_line = wx.StaticLine(self, -1)
        
        self.bouton_emis = CTRL_Bouton_image.CTRL(self, texte=_("Afficher les Cerfas émis"), tailleImage=(16, 16), margesImage=(4, 4, 0, 0), margesTexte=(-5, 1), cheminImage=Chemins.GetStaticPath("Images/16x16/Etoile.png"))
        self.bouton_retour = CTRL_Bouton_image.CTRL(self, texte=_("Retour"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fleche_gauche.png"))
        self.bouton_suite = CTRL_Bouton_image.CTRL(self, texte=_("Suite"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fleche_droite.png"), margesImage=(0, 0, 4, 0), positionImage=wx.RIGHT)
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))
        
        self.__set_properties()
        self.__do_layout()
                
        self.Bind(wx.EVT_BUTTON, self.Onbouton_emis, self.bouton_emis)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_retour, self.bouton_retour)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_suite, self.bouton_suite)
        
        self.bouton_retour.Enable(False)
        self.nbrePages = len(self.listePages)    
        self.pageVisible = 1
                        
        # Création des pages
        self.Creation_Pages()        

    def Creation_Pages(self):
        """ Creation des pages """
        for numPage in range(1, self.nbrePages+1) :
            setattr(self, "page%d" % numPage,
                    eval(self.listePages[numPage - 1] + "(self)"))
            self.sizer_pages.Add(getattr(self, "page%d" % numPage), 1,
                                 wx.EXPAND, 0)
            self.sizer_pages.Layout()
            getattr(self, "page%d" % numPage).Show(False)
        self.page1.Show(True)
        self.sizer_pages.Layout()

    def __set_properties(self):
        self.bouton_emis.SetToolTip(_("Cliquez ici pour consulter les cerfas précédemment émis sur cette période"))
        self.bouton_retour.SetToolTip(_("Cliquez ici pour revenir à la page précédente"))
        self.bouton_suite.SetToolTip(_("Cliquez ici pour passer à l'étape suivante"))
        self.bouton_annuler.SetToolTip(_("Cliquez pour fermer"))
        self.SetMinSize((1300, 760))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        # Bandeau
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        
        # Contenu
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_pages = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base.Add(sizer_pages, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_base.Add(self.static_line, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_emis, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_retour, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_suite, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, wx.LEFT, 10)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen()
        
        self.sizer_pages = sizer_pages

    def Onbouton_emis(self, event):
        # Rend invisible la page affichée
        self.oldPage = self.pageVisible
        page = eval("self.page"+str(self.pageVisible))
        page.Show(False)
        # Fait apparaître la dernière page
        self.pageVisible = self.nbrePages
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.MAJ()
        pageCible.Show(True)
        self.sizer_pages.Layout()
        self.bouton_retour.Enable(True)
        self.bouton_suite.Enable(False)
        event.Skip()
        pageCible.ctrl_attestations.OnCerfasEmis()

    def Onbouton_retour(self, event):
        # rend invisible la page affichée
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(False)
        # Fait apparaître la page précédente
        if self.oldPage:
            self.pageVisible = self.oldPage
            self.oldPage = None
        else:
            self.pageVisible -= 1
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()

        # On active tous les boutons
        self.bouton_retour.Enable(True)
        self.bouton_annuler.Enable(True)
        self.bouton_suite.Enable(True)

        # Si on quitte l'avant-dernière page, on active le bouton Suivant
        if self.pageVisible == self.nbrePages :
            self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/32x32/Fermer.png"))
        else:
            self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/32x32/Fleche_droite.png"))
            self.bouton_suite.SetTexte(_("Suite"))
        # Si on revient à la première page, on désactive le bouton Retour
        if self.pageVisible == 1 :
            self.bouton_retour.Enable(False)
        if self.pageVisible == 2 :
            self.bouton_suite.Enable(False)
        # On réinitialise
        ctrlOlv = self.page1.ctrl_listview
        ctrlOlv.MAJ()

    def Onbouton_suite(self, event):
        # Vérifie que les données de la page en cours sont valides
        validation = self.ValidationPages()
        if validation == False : return
        # Si on est déjà sur la dernière page : on termine
        if self.pageVisible == self.nbrePages :
            self.Terminer()
            return
        # Rend invisible la page affichée
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(False)
        # Fait apparaître nouvelle page
        self.pageVisible += 1
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.MAJ() 
        pageCible.Show(True)
        self.sizer_pages.Layout()
        # Si on arrive à la dernière page, on désactive le bouton Suivant
        if self.pageVisible == self.nbrePages :
            self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/32x32/Fermer.png"))
            self.bouton_suite.SetTexte(_("Fermer"))
            self.bouton_suite.Enable(True)
            self.bouton_annuler.Enable(False)
        # Si on quitte la première page, on active le bouton Retour
        if self.pageVisible > 1 :
            self.bouton_retour.Enable(True)
        if self.pageVisible == 2 :
            self.bouton_suite.Enable(False)

    def ValidationPages(self) :
        """ Validation des données avant changement de pages """
        validation = getattr(self, "page%d" % self.pageVisible).Validation()
        return validation

    def Terminer(self):
        # Fermeture
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    IDactivite = 1
    frame_1 = Dialog(None) 

    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()
