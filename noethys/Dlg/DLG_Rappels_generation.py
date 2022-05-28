#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania pour des relances globales et non par prestations
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau

from Dlg.DLG_Rappels_generation_parametres import Panel as Page1
from Dlg.DLG_Rappels_generation_selection import Panel as Page2
from Dlg.DLG_Rappels_generation_actions import Panel as Page3


class Dialog(wx.Dialog):
    def __init__(self, parent,IDfamille=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Rappels_generation", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDfamille = IDfamille
        intro = _("Génération des lettres de rappel. Page 1 : Filtrez les rappels ciblés. / Page 2 : Choix du document, génération. / Page 3 Action d'édition")
        titre = _("DLG_Rappels_generation : Génération de lettres de rappel")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=20, nomImage="Images/22x22/Smiley_nul.png")
        
        self.listePages = ("Page1","Page2", "Page3")

        self.static_line = wx.StaticLine(self, -1)
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_retour = CTRL_Bouton_image.CTRL(self, texte=_("Retour"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fleche_gauche.png"))
        self.bouton_suite = CTRL_Bouton_image.CTRL(self, texte=_("Suite"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fleche_droite.png"), margesImage=(0, 0, 4, 0), positionImage=wx.RIGHT)
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))
        
        self.__set_properties()
        self.__do_layout()
                
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_retour, self.bouton_retour)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_suite, self.bouton_suite)
        
        self.bouton_retour.Enable(False)
        self.nbrePages = len(self.listePages)    

        self.pageVisible = 1
        if self.IDfamille != None : self.pageVisible = 2
                        
        # Création des pages
        self.Creation_Pages()

    def Creation_Pages(self):
        """ Creation des pages """
        for numPage in range(1, self.nbrePages + 1):
            setattr(self, "page%d" % numPage,
                    eval(self.listePages[numPage - 1] + "(self)"))
            self.sizer_pages.Add(getattr(self, "page%d" % numPage), 1,
                                 wx.EXPAND, 0)
            self.sizer_pages.Layout()
            getattr(self, "page%d" % numPage).Show(False)
        self.page1.Show(True)
        self.sizer_pages.Layout()

    def __set_properties(self):
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_retour.SetToolTip(_("Cliquez ici pour revenir à la page précédente"))
        self.bouton_suite.SetToolTip(_("Cliquez ici pour passer à l'étape suivante"))
        self.bouton_annuler.SetToolTip(_("Cliquez pour annuler"))
        self.SetMinSize((1000, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        # Bandeau
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        
        # Contenu
        sizer_pages = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base.Add(sizer_pages, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_base.Add(self.static_line, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_retour, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_suite, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, wx.LEFT, 10)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen()
        
        self.sizer_pages = sizer_pages
    
    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Gnration1")

    def Onbouton_retour(self, event):
        # rend invisible la page affichée
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(False)
        # Fait apparaître nouvelle page
        self.pageVisible -= 1
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()
        # Si on quitte l'avant-dernière page, on active le bouton Suivant
        if self.pageVisible == self.nbrePages :
            self.bouton_suite.Enable(True)
            self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/32x32/Fermer.png"))
        else:
            self.bouton_suite.Enable(True)
            self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/32x32/Fleche_droite.png"))
        # Si on revient à la première page, on désactive le bouton Retour
        if self.pageVisible == 1 :
            self.bouton_retour.Enable(False)
        # On active le bouton annuler
        self.bouton_annuler.Enable(True)

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
            self.bouton_annuler.Enable(False)
        # Si on quitte la première page, on active le bouton Retour
        if self.pageVisible > 1 :
            self.bouton_retour.Enable(True)
        
        # Désactivation du bouton Retour si dernière page > SPECIAL FACTURATION !!!
        if self.pageVisible == self.nbrePages :            
            self.bouton_retour.Enable(False)

    def ValidationPages(self) :
        """ Validation des données avant changement de pages """
        validation = getattr(self, "page%d" % self.pageVisible).Validation()
        return validation

    def Terminer(self):
        # Fermeture
        self.EndModal(wx.ID_OK)

    def SetFamille(self, IDfamille=None):
        self.page2.SetFamille(IDfamille)
        self.page2.MAJ()

        
        
if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    IDactivite = 1
    frame_1 = Dialog(None,None)
    # TESTS
    #frame_1.page1.ctrl_date_reference.SetDate(datetime.date.today())

    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()
