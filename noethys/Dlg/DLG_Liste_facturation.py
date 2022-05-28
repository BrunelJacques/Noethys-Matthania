#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, suivi de facturation des pièces
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2019-10
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
from Ctrl import CTRL_Bandeau
from Ol import OL_Liste_facturation
import datetime


def DateDDenSQL(dateDD):
    if not isinstance(dateDD,datetime.date): return ""
    return dateDD.strftime("%Y-%m-%d")

def DateSQLenFR(dateSQL):
    if len(dateSQL) < 10: return ""
    aa = dateSQL[:4]
    mm = dateSQL[5:7]
    jj = dateSQL[8:10]
    return "%s/%s/%s"%(jj,mm,aa)

def DateSQLenDD(dateSQL):
    if len(dateSQL) < 10: return ""
    aa = int(dateSQL[:4])
    mm = int(dateSQL[5:7])
    jj = int(dateSQL[8:10])
    return datetime.date(aa,mm,jj)

class CTRL_Cloture(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeClotures = []
        self.SetListeDonnees()

    def SetListeDonnees(self):
        DB = GestionDB.DB()
        listeDonnees = DB.GetClotures()
        for cloture in listeDonnees :
            self.listeNoms.append(DateSQLenFR(cloture))
            self.listeClotures.append(cloture)
        self.SetItems(self.listeNoms)
        self.SetSelection(len(self.listeNoms)-1)
        DB.Close()


    def GetCloture(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeClotures[index]
   
# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        intro = _("Vous trouvez ici le contrôle des facturations de pièces faites ou à faire, avec choix possible du détail par ligne")
        titre = _("Liste des facturations - Lignes de Pièces")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")

        # Paramètres
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Filtres"))

        self.label_annee = wx.StaticText(self, -1, _("Exercice se clôturant au :"))
        self.ctrl_cloture = CTRL_Cloture(self)
        self.ctrl_cloture.SetMinSize((90, -1))


        self.label_facture = wx.StaticText(self, -1, _("Détail/Total :"))
        self.ctrl_facture = wx.Choice(self, -1, choices = (_("Détail lignes"), _("Total prestations"), _("Prest.HorsConsos")))
        self.ctrl_facture.Select(1)
                
        self.label_compta = wx.StaticText(self, -1, _("Transféré en compta :"))
        self.ctrl_compta = wx.CheckBox(self)

        # Liste
        self.listviewAvecFooter = OL_Liste_facturation.ListviewAvecFooter(self, kwargs={})
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Liste_facturation.CTRL_Outils(self, listview=self.ctrl_listview, afficherCocher=True)
        self.ctrl_listview.ctrl_recherche = self.ctrl_recherche
        self.bouton_ouvrir_fiche = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_liste_export_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_liste_export_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OuvrirFiche, self.bouton_ouvrir_fiche)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)
        
        self.Bind(wx.EVT_CHOICE, self.MAJcloture, self.ctrl_cloture)
        self.Bind(wx.EVT_CHOICE, self.MAJfacture, self.ctrl_facture)
        self.Bind(wx.EVT_CHECKBOX, self.MAJcompta, self.ctrl_compta)

        # Init contrôles
        wx.CallAfter(self.MAJinit)

    def __set_properties(self):
        self.SetTitle(_("Liste facturations"))
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
        grid_sizer_options.Add(self.label_annee, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.ctrl_cloture, 0, 0, 0)
        grid_sizer_options.Add( (50, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_facture, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_facture, 0, 0, 0)
        grid_sizer_options.Add((50, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_compta, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_compta, 0, 0, 0)
##        grid_sizer_options.AddGrowableCol(4)
        staticbox_options.Add(grid_sizer_options, 0, wx.EXPAND|wx.ALL, 0)
        grid_sizer_base.Add(staticbox_options, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

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
        self.MAJcloture()
        self.MAJfacture()
        self.MAJcompta()
        self.MAJ()

    def MAJcloture(self, event=None):
        # Filtre Année
        cloture = self.ctrl_cloture.GetCloture()
        ddcloture = DateSQLenDD(cloture)
        DB = GestionDB.DB()
        (deb, fin) = DB.GetExercice(ddcloture,alertes=False, approche=True)
        self.debSQL = DateDDenSQL(deb)
        self.finSQL = DateDDenSQL(fin)
        if len(cloture) > 0 :
            self.ctrl_listview.periode = (self.debSQL, self.finSQL)
        else :
            self.ctrl_listview.periode = None
        if event != None:
            self.MAJ()

    def MAJfacture(self, event=None):
        # Filtre Facturé
        facture = self.ctrl_facture.GetSelection()
        if facture == 0 :
            self.ctrl_listview.dictFiltres["COMPLEXE"] = "detail"
        if facture == 1 :
            self.ctrl_listview.dictFiltres["COMPLEXE"] = "total"
        if facture == 2 :
            self.ctrl_listview.dictFiltres["COMPLEXE"] = "noconso"
        if event != None:
            self.MAJ()

    def MAJcompta(self,event=None):
        # Filtre transfert compta
        compta = self.ctrl_compta.GetValue()
        self.ctrl_listview.transfert = compta
        if event != None:
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
        return


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
