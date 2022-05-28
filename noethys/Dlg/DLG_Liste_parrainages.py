#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, suivi de contrôle des parrainages évolution de cerfa
# Auteur:          Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_date
from Ol import OL_Liste_parrainages
import datetime
import PIL.Image as Image

def dateDDenSQL(dateDD):
    if not isinstance(dateDD,datetime.date): return ""
    return dateDD.strftime("%Y-%m-%d")

# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX,
                           size=(1350,600))
        self.parent = parent
        self.annee = 0
        intro = _("Vous trouvez ici une liste de contrôle des inscriptions parrainées sur la période. Une ligne pour chaque famille filleule regroupe ses inscriptions parrainées")
        titre = _("Liste des parrainages")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")

        # Période
        self.periode_staticbox = wx.StaticBox(self, -1, _("Période de référence"))
        self.label_date_debut = wx.StaticText(self, -1, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_date_fin = wx.StaticText(self, -1, _("Au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)
        self.btn_plus = wx.Button(self,label="+1an",size=(40,25))
        self.btn_moins = wx.Button(self,label="-1an",size=(40,25))

        # Paramètres
        self.options_staticbox = wx.StaticBox(self, -1, _("Filtres"))
        self.ctrl_anterieur = wx.CheckBox(self,label=" Report des parrainages antérieurs")
        self.ctrl_anterieur.SetMinSize((200, -1))

        self.ctrl_post = wx.CheckBox(self,label=" Avec les réductions postérieures")
        self.ctrl_post.SetMinSize((200, -1))

        self.btnInfo1 = wx.StaticText(self,-1, " COULEURS : azur-Impayés,pbRatio; cyste-Réduc.orphelines; saumon-Réduc.perdues; rose-Pb parrain")

        # ListeView
        self.listviewAvecFooter = OL_Liste_parrainages.ListviewAvecFooter(self, kwargs={}) 
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Liste_parrainages.CTRL_Outils(self, listview=self.ctrl_listview)


        self.bouton_ouvrir_parrain = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Responsable_legal.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_ouvrir_filleul = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_liste_export_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_liste_export_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))
        
        # Actualiser
        self.bouton_actualiser = CTRL_Bouton_image.CTRL(self, texte=_("Rafraîchir la liste"), cheminImage=Chemins.GetStaticPath("Images/32x32/Actualiser.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()

        # Init contrôles
        wx.CallAfter(self.MAJ)

    def __set_properties(self):
        self.SetTitle(_("Liste des prestations"))

        self.Bind(wx.EVT_BUTTON, self.OuvrirParrain, self.bouton_ouvrir_parrain)
        self.Bind(wx.EVT_BUTTON, self.OuvrirFilleul, self.bouton_ouvrir_filleul)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.MAJ, self.bouton_actualiser)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBtnPlusMoins, self.btn_plus)
        self.Bind(wx.EVT_BUTTON, self.OnBtnPlusMoins, self.btn_moins)

        self.ctrl_date_debut.SetToolTip(_("Saisissez la date de début de période"))
        self.ctrl_date_fin.SetToolTip(_("Saisissez la date de fin de période"))
        self.btn_plus.SetToolTip("Cliquez pour avancer d'un an les dates")
        self.btn_moins.SetToolTip("Cliquez pour reculer d'un an les dates")
        self.btn_plus.Name = 'plus'
        self.btn_moins.Name = 'moins'

        self.ctrl_anterieur.SetToolTip(_("Il s'agit des parrainages qui étaient en attente au début de période et de leurs réductions ultérieures liées."))
        self.ctrl_post.SetToolTip(_("Il s'agit des réductions qui ont pu être attribuées postérieurement à la période étudiée."))
        self.bouton_ouvrir_parrain.SetToolTip(_("Cliquez ici pour ouvrir la fiche famille du parrain de la ligne sélectionnée"))
        self.bouton_ouvrir_filleul.SetToolTip(_("Cliquez ici pour ouvrir la fiche famille du filleul de la ligne sélectionnée"))
        self.bouton_apercu.SetToolTip(_("Cliquez ici pour créer un aperçu avant impression de la liste"))
        self.bouton_imprimer.SetToolTip(_("Cliquez ici pour imprimer directement la liste"))
        self.bouton_liste_export_texte.SetToolTip(_("Cliquez ici pour exporter cette liste au format Texte"))
        self.bouton_liste_export_excel.SetToolTip(_("Cliquez ici pour exporter cette liste au format Excel"))
        self.bouton_actualiser.SetToolTip(_("Cliquez ici pour actualiser la liste"))
        self.bouton_fermer.SetToolTip(_("Cliquez ici pour fermer"))
        self.SetMinSize((1000, 700))

        # Données par défaut
        anneeActuelle = datetime.date.today().year
        self.ctrl_date_debut.SetDate(datetime.date(anneeActuelle-1, 1, 1))
        self.ctrl_date_fin.SetDate(datetime.date(anneeActuelle-1, 12, 31))
        self.ctrl_anterieur.SetValue(True)
        self.ctrl_post.SetValue(True)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        # Paramètres
        grid_sizer_params = wx.FlexGridSizer(rows=1, cols=2, vgap=3, hgap=0)

        # Date de référence
        staticbox_periode = wx.StaticBoxSizer(self.periode_staticbox, wx.VERTICAL)
        grid_sizer_periode = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)
        grid_sizer_periode.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.btn_plus, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.btn_moins, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox_periode.Add(grid_sizer_periode, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_params.Add(staticbox_periode, 1, wx.RIGHT | wx.EXPAND, 5)

        # Autres paramètres
        staticbox_options = wx.StaticBoxSizer(self.options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_options.Add(self.ctrl_anterieur, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_post, 0, 0, 0)
        staticbox_options.Add(grid_sizer_options, 0, wx.EXPAND|wx.ALL, 10)
        staticbox_options.Add(self.btnInfo1, 0, 0, 0)

        grid_sizer_params.Add(staticbox_options, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_params.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_params, 1, wx.RIGHT | wx.EXPAND, 5)

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
        grid_sizer_droit.Add(self.bouton_ouvrir_parrain, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_ouvrir_filleul, 0, 0, 0)
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
        grid_sizer_boutons.Add(self.bouton_actualiser, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        #grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBtnPlusMoins(self,event):
        if event.EventObject.Name == "plus":
            sens = 1
        else: sens = -1
        dte = self.ctrl_date_debut.GetDate()
        self.ctrl_date_debut.SetDate(dte.replace(year=dte.year + sens))
        dte = self.ctrl_date_fin.GetDate()
        self.ctrl_date_fin.SetDate(dte.replace(year=dte.year + sens))
        self.MAJ(None)

    def MAJ(self, event=None):
        # MAJ de la liste
        attente = wx.BusyInfo(_("Recherche des données..."), self)
        self.ctrl_listview.MAJ() 
        del attente
        
    def OuvrirParrain(self, event):
        self.ctrl_listview.OuvrirFicheParrain(None)

    def OuvrirFilleul(self, event):
        self.ctrl_listview.OuvrirFicheFilleul(None)

    def Imprimer(self, event):
        self.ctrl_listview.Imprimer(None)

    def Apercu(self, event):
        self.ctrl_listview.Apercu(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_listview.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_listview.ExportExcel(None)


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
