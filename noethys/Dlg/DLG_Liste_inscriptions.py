#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :   Selection d'inscriptions pour liste et pour action
# Site internet :  www.noethys.com Matthania
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image
from Ol import OL_Liste_inscriptions
from Ctrl import CTRL_ParamListeInscriptions

# --------------------------------------------------------------------------------------------------------------------------------------------------
class Notebook(wx.Notebook):
    def __init__(self, parent, id=-1):
        wx.Notebook.__init__(self, parent, id, style= wx.BK_DEFAULT)
        self.parent = parent

        self.dictPages = {}
        #      codePage,       labelPage,         ctrlPage,              imgPage
        self.listePages = [
            ("selection", _("Selection_filtres"), "PanelSelection(self)", "Composition.png"),
            ("liste", _("Liste_résultat"), "PanelListe(self)", "Cocher.png"),
            ]
        # ImageList pour le NoteBook
        il = wx.ImageList(16, 16)
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            exec("self.img%d = il.Add(wx.Bitmap(Chemins.GetStaticPath('Images/16x16/%s'), wx.BITMAP_TYPE_PNG))" % (index, imgPage))
            index += 1
        self.AssignImageList(il)

        # Création des pages
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            exec("self.page%d = %s" % (index, ctrlPage))
            exec("self.AddPage(self.page%d, u'%s')" % (index, labelPage))
            exec("self.SetPageImage(%d, self.img%d)" % (index, index))
            exec("self.dictPages['%s'] = {'ctrl' : self.page%d, 'index' : %d}" % (codePage, index, index))
            index += 1
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]["ctrl"]

    def AffichePage(self, codePage=""):
        indexPage = self.dictPages[codePage]["index"]
        self.SetSelection(indexPage)

    def OnPageChanged(self, event):
        """ Quand une page du notebook est sélectionnée """
        indexAnciennePage = event.GetOldSelection()
        indexPage = event.GetSelection()
        codePage = self.listePages[indexAnciennePage][0]
        # Sauvegarde ancienne page si besoin
        if indexAnciennePage!=wx.NOT_FOUND:
            anciennePage = self.GetPage(indexAnciennePage)
        indexPage = event.GetSelection()
        page = self.GetPage(indexPage)
        self.Freeze()
        #wx.CallLater(1, page.MAJ)
        self.Thaw()
        event.Skip()

    def MAJpageActive(self):
        """ MAJ la page active du notebook """
        indexPage = self.GetSelection()
        page = self.GetPage(indexPage)
        wx.CallLater(1, page.MAJ)

    def MAJpage(self, codePage=""):
        page = self.dictPages[codePage]["ctrl"]
        wx.CallLater(1, page.MAJ)
    #fin Notebook

class PanelSelection(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_selection", style=wx.TAB_TRAVERSAL)
        self.name = "panelSelection"
        self.notebook = parent
        self.ctrl_parametres = CTRL_ParamListeInscriptions.Parametres(self)
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetMinSize((200, 200))

    def __do_layout(self):

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)

        # Panel des paramètres
        grid_sizer_contenu.Add(self.ctrl_parametres, 1, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)

        self.SetSizer(grid_sizer_contenu)
        grid_sizer_contenu.Fit(self)
        self.Layout()

    def MAJ(self):
        pass
        self.ctrl_listview.MAJ()
    #fin PanelSelection

class PanelListe(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_liste", style=wx.TAB_TRAVERSAL)
        self.notebook = parent

        self.listviewAvecFooter = OL_Liste_inscriptions.ListviewAvecFooter(self, kwargs={})
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Liste_inscriptions.CTRL_Outils(self, listview=self.ctrl_listview)

        self.bouton_ouvrir_fiche = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OuvrirFiche, self.bouton_ouvrir_fiche)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.ExportTexte, self.bouton_texte)
        self.Bind(wx.EVT_BUTTON, self.ExportExcel, self.bouton_excel)

    def __set_properties(self):
        self.bouton_ouvrir_fiche.SetToolTip(_("Cliquez ici pour ouvrir la fiche de la famille sélectionnée dans la liste"))
        self.bouton_apercu.SetToolTip(_("Cliquez ici pour créer un aperçu de la liste"))
        self.bouton_imprimer.SetToolTip(_("Cliquez ici pour imprimer la liste"))
        self.bouton_texte.SetToolTip(_("Cliquez ici pour exporter la liste au format Texte"))
        self.bouton_excel.SetToolTip(_("Cliquez ici pour exporter la liste au format Excel"))
        self.SetMinSize((200, 200))

    def __do_layout(self):

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)

        # Panel des listes
        # Liste + Barre de recherche
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_gauche.Add(self.listviewAvecFooter, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND | wx.LEFT, 5)

        # Commandes
        grid_sizer_droit = wx.FlexGridSizer(rows=7, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add(self.bouton_ouvrir_fiche, 0, 0, 0)
        grid_sizer_droit.Add( (5, 5), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_droit.Add( (5, 5), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_texte, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_excel, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)

        self.SetSizer(grid_sizer_contenu)
        grid_sizer_contenu.Fit(self)
        self.Layout()

    def OuvrirFiche(self, event):
        self.ctrl_listview.OuvrirFicheFamille(None)

    def Apercu(self, event):
        self.ctrl_listview.Apercu(None)

    def Imprimer(self, event):
        self.ctrl_listview.Imprimer(None)

    def ExportTexte(self, event):
        self.ctrl_listview.ExportTexte(None)

    def ExportExcel(self, event):
        self.ctrl_listview.ExportExcel(None)

    def MAJ(self):
        pass
        #self.notebook.page1.ctrl_listview.MAJ()
    #fin PanelListe

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        intro = _("Vous pouvez ici consulter et imprimer la liste des inscriptions. Commencez par sélectionner des activités avant de cliquer sur le bouton 'Valider' pour afficher les résultats. Vous pouvez également regrouper les données par type d'informations et sélectionner les colonnes à afficher. Les données peuvent être ensuite imprimées ou exportées au format Texte ou Excel.")
        titre = _("Liste paramétrable des inscriptions")
        self.SetTitle("DLG_Liste_inscriptions")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")

        self.notebook = Notebook(self)
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        self.notebook.SetFocus()

    def __set_properties(self):
        self.bouton_fermer.SetToolTip(_("Cliquez ici pour fermer"))
        self.SetMinSize((1080, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)

        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        grid_sizer_base.Add(self.notebook, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_pied = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_pied.Add((40,20), 0, 0, 0)
        grid_sizer_pied.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_pied.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_pied.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_pied, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
