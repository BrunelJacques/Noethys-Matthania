#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, redirige OL_Prestations vers OL_Liste_prestations pour détailler les lignes de facturation
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
from Ctrl import CTRL_Bandeau
from Ol import OL_Liste_prestations
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_SelectionActivitesModal as sam

# ------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Activite(sam.CTRL_BoutonSelectionActivites):
    def __init__(self, parent):
        sam.CTRL_BoutonSelectionActivites.__init__(self, parent, -1,parent.periode) 
        self.parent = parent
        self.listeID = []
        self.debutPeriode = None
        self.finPeriode = None

    def SetListeDonnees(self):
        self.SetPeriode(self.parent.periode)

    def GetWhere(self):
        if len(self.GetIDactivites()) > 1:
            return "( pieIDactivite in (%s))"%str(self.GetIDactivites())[1:-1]
        elif len(self.GetIDactivites()) > 0:
            return "( pieIDactivite = %d )" %self.GetIDactivites()[0]
        else: return "FALSE"
# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.periode = CTRL_Saisie_date.PeriodeMois()
        intro = _("Vous trouvez ici la liste des prestations avec leur total et leur détail dans deux colonnes différentes. <br />Une ligne pour le total de la prestation est précédée du détail trouvé dans les lignes de la pièce correspondante")
        titre = _("Liste des prestations - Lignes de Pièces")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")

        # Paramètres
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Filtres"))

        self.label_periode = wx.StaticText(self, -1, _("Période"))
        self.ctrl_periode = CTRL_Saisie_date.Periode(self,flexGridParams=(1,5,0,4))
        self.ctrl_periode.SetMinSize((330, -1))

        self.label_activite = wx.StaticText(self, -1, _("Activité :"))
        self.ctrl_activite = CTRL_Activite(self)
        self.ctrl_activite.SetMinSize((200, -1))

        self.ctrl_avecDetail = wx.CheckBox(self, -1, "AvecDétail")
        self.ctrl_niveauFamille = wx.CheckBox(self, -1, "NiveauFamille")
        self.ctrl_horsConsos = wx.CheckBox(self, -1, "HorsConsos")
        self.ctrl_avecDetail.SetValue(False)
        self.ctrl_horsConsos.SetValue(True)
        self.ctrl_niveauFamille.SetValue(False)
                
        # Liste
        self.listviewAvecFooter = OL_Liste_prestations.ListviewAvecFooter(self, kwargs={}) 
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Liste_prestations.CTRL_Outils(self, listview=self.ctrl_listview)


        self.bouton_ouvrir_fiche = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_liste_export_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_liste_export_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CHECKBOX, self.OnOptions, self.ctrl_avecDetail)
        self.Bind(wx.EVT_CHECKBOX, self.OnOptions, self.ctrl_niveauFamille)
        self.Bind(wx.EVT_CHECKBOX, self.OnOptions, self.ctrl_horsConsos)

        self.Bind(wx.EVT_BUTTON, self.OuvrirFiche, self.bouton_ouvrir_fiche)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)

        # Init contrôles
        wx.CallAfter(self.MAJinit)

    def __set_properties(self):
        self.SetTitle(_("Liste des prestations"))
        self.bouton_ouvrir_fiche.SetToolTip(_("Cliquez ici pour ouvrir la fiche famille de la prestation sélectionnée dans la liste"))
        self.bouton_apercu.SetToolTip(_("Cliquez ici pour créer un aperçu avant impression de la liste"))
        self.bouton_imprimer.SetToolTip(_("Cliquez ici pour imprimer directement la liste"))
        self.bouton_liste_export_texte.SetToolTip(_("Cliquez ici pour exporter cette liste au format Texte"))
        self.bouton_liste_export_excel.SetToolTip(_("Cliquez ici pour exporter cette liste au format Excel"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_fermer.SetToolTip(_("Cliquez ici pour fermer"))
        self.SetMinSize((1000, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        # Paramètres
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=16, vgap=0, hgap=5)
        grid_sizer_options.Add(self.ctrl_periode, 0, 0, 0)
        grid_sizer_options.Add( (5, 5), 1,wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_activite, 0, wx.TOP, 13)
        grid_sizer_options.Add(self.ctrl_activite, 1, wx.EXPAND|wx.TOP, 10)
        grid_sizer_options.Add( (5, 5), 1,wx.EXPAND,0)
        grid_sizer_options.Add(self.ctrl_avecDetail, 0, wx.TOP, 10)
        grid_sizer_options.Add(self.ctrl_niveauFamille, 0, wx.TOP, 10)
        grid_sizer_options.Add(self.ctrl_horsConsos, 0, wx.TOP, 10)
        grid_sizer_options.Add( (5, 5), 1, wx.EXPAND,0)
        #grid_sizer_options.AddGrowableCol(4)
        staticbox_options.Add(grid_sizer_options, 0, wx.EXPAND,0)
        grid_sizer_base.Add(staticbox_options, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Contenu
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_gauche.Add(self.listviewAvecFooter, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        
        grid_sizer_droit = wx.FlexGridSizer(rows=11, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add( (10, 10), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_ouvrir_fiche, 0, 0, 0)
        grid_sizer_droit.Add( (10, 10), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_droit.Add( (10, 10), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_liste_export_texte, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_liste_export_excel, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def MAJinit(self):
        self.OnChoixDate()
        self.OnActivites(wx.ID_OK,None)
        self.OnOptions()
        self.MAJ()

    def OnChoixDate(self, event=None):
        # Filtre Période
        periode = self.ctrl_periode.GetPeriode()
        self.ctrl_listview.dictFiltres['periode'] = periode
        self.ctrl_activite.SetPeriode(periode)
        if event:
            self.MAJ()
 
    def OnActivites(self, retour=None,periode=None):
        # Filtre Activité
        if retour == wx.ID_OK:
            oldPeriode = self.ctrl_periode.GetPeriode()
            if periode and oldPeriode != periode:
                self.ctrl_periode.SetPeriode(periode)
                self.ctrl_listview.dictFiltres['periode'] = periode
            if self.ctrl_listview.dictFiltres["whereActivites"] != self.ctrl_activite.GetWhere():
                self.ctrl_listview.dictFiltres["whereActivites"] = self.ctrl_activite.GetWhere()
                self.MAJ()

    def OnOptions(self,event=None):
        options =  {'avecDetail': self.ctrl_avecDetail.GetValue(),
                    'niveauFamille': self.ctrl_niveauFamille.GetValue(),
                    'horsConsos': self.ctrl_horsConsos.GetValue()}
        self.ctrl_listview.dictFiltres["options"] = options
        if self.ctrl_avecDetail.GetValue() and self.ctrl_activite.nbActivites == 0:
            mess = "Choississez des activités\n\nLe détail ne s'applique qu'aux lignes d'activité"
            wx.MessageBox(mess,"Remarque",wx.ICON_INFORMATION)
        self.MAJ()

    def MAJ(self, event=None):
        # MAJ de la liste
        attente = wx.BusyInfo(_("Recherche des données..."), self)
        self.ctrl_listview.MAJ() 
        del attente
        
    def OuvrirFiche(self, event):
        self.ctrl_listview.OuvrirFicheFamille(None)

    def Imprimer(self, event):
        self.ctrl_listview.Imprimer(None)

    def Apercu(self, event):
        self.ctrl_listview.Apercu(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_listview.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_listview.ExportExcel(None)


    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Listedesprestations")



if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
