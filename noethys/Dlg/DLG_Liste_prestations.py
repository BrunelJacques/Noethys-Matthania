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
import CTRL_Saisie_date

# ------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Activite(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.debutPeriode = None
        self.finPeriode = None

    def SetListeDonnees(self):
        self.listeLabels = ["Toutes",]
        self.listeID = ['toutes',]
        if self.debutPeriode != None and self.finPeriode != None:
            where = "(prestations.date >= '%s') AND (prestations.date <= '%s') "%(self.debutPeriode,self.finPeriode)
            DB = GestionDB.DB()
            req = """
                SELECT activites.IDactivite, activites.nom, prestations.categorie
                FROM prestations 
                LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
                WHERE (%s)
                GROUP BY activites.IDactivite, activites.nom, prestations.categorie
                ORDER BY activites.nom ASC
            ;""" % where
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) == 0 : return
            for IDactivite, nom, categorie in listeDonnees :
                if IDactivite != None and IDactivite > 0:
                    self.listeLabels.append(nom)
                    self.listeID.append(IDactivite)
                elif 'conso' in categorie:
                    self.listeLabels.append('_Niveau famille')
                    self.listeID.append('conso')
                else:
                    self.listeLabels.append(categorie)
                    self.listeID.append(categorie)
        self.SetItems(self.listeLabels)
        self.SetSelection(0)

    def GetID(self):
        index = self.GetSelection()
        if index < 1 : return 0
        return self.listeID[index]

    def GetIndexID(self,ID):
        return self.listeID.index(ID)


# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.periode = (None, None)
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

        self.label_lignes = wx.StaticText(self, -1, _("Détail/Total :"))
        self.ctrl_lignes = wx.Choice(self, -1, 
                                     choices = ("Détail lignes", "Total prestations",
                                                "Les deux", "Prest.HorsConsos",
                                                "Toutes prestations"))
        self.ctrl_lignes.Select(0) 
                
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
        
        self.Bind(wx.EVT_BUTTON, self.OuvrirFiche, self.bouton_ouvrir_fiche)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)
        
        self.Bind(wx.EVT_CHOICE, self.MAJactivite, self.ctrl_activite)
        self.Bind(wx.EVT_CHOICE, self.MAJlignes, self.ctrl_lignes)
        
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
        grid_sizer_options.Add(self.label_periode, 0, wx.TOP, 13)
        grid_sizer_options.Add(self.ctrl_periode, 0, 0, 0)
        grid_sizer_options.Add( (25, 5), 1,wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_activite, 0, wx.TOP, 13)
        grid_sizer_options.Add(self.ctrl_activite, 1, wx.EXPAND|wx.TOP, 10)
        grid_sizer_options.Add( (25, 5), 1,wx.EXPAND,0)
        grid_sizer_options.Add(self.label_lignes, 0, wx.TOP, 13)
        grid_sizer_options.Add(self.ctrl_lignes, 0, wx.TOP, 10)
        grid_sizer_options.Add( (25, 5), 1, wx.EXPAND,0)
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
        self.MAJperiode()
        self.MAJactivite()
        self.MAJlignes()
        self.MAJ()

    def MAJperiode(self, event=None):
        # Filtre Période
        (debut,fin) = self.ctrl_periode.GetPeriode()
        if debut and fin:
            self.ctrl_listview.dictFiltres['periode'] = (debut,fin)
            self.ctrl_activite.debutPeriode = debut
            self.ctrl_activite.finPeriode = fin
            # reprend le choix antérieur malgré le changement de liste
            ID = self.ctrl_activite.GetID()
            self.ctrl_activite.SetListeDonnees()
            try:
                index = self.ctrl_activite.GetIndexID(ID)                
                self.ctrl_activite.SetSelection(index)
            except Exception as err:
                self.ctrl_activite.SetSelection(0)                
        else :
            self.ctrl_listview.dictFiltres['periode'] = None
        if event != None:
            if "whereActivite" in self.ctrl_listview.dictFiltres :
                del self.ctrl_listview.dictFiltres["whereActivite"]
            self.MAJ()
            
    def MAJactivite(self, event=None):
        # Filtre Activité
        IDactivite = self.ctrl_activite.GetID()
        if isinstance(IDactivite,int):
            self.ctrl_listview.dictFiltres["whereActivite"] = "( pieIDactivite = %d )" %IDactivite
        elif IDactivite == 'toutes':
            self.ctrl_listview.dictFiltres["whereActivite"] = "TRUE"
        elif isinstance(IDactivite,str):
            self.ctrl_listview.dictFiltres["whereActivite"] = "( prestations.categorie = '%s' )" %IDactivite
        else:
            raise ValueError('Non attendu')
        if event != None:
            self.MAJ()

    def MAJlignes(self, event=None):
        self.ctrl_listview.periode = self.ctrl_periode.GetPeriode()
        # Filtre type de lignes
        lignes = self.ctrl_lignes.GetSelection()
        self.MAJactivite()
        if lignes == 0 :
            self.ctrl_listview.dictFiltres["lignes"] = ["detail",]
        if lignes == 1 :
            self.ctrl_listview.dictFiltres["lignes"] = ["total",]
        if lignes == 2 :
            self.ctrl_listview.dictFiltres["lignes"] = ["detail","total"]
        if lignes == 3 :
            self.ctrl_listview.dictFiltres["lignes"] = ["noConsos",]
        if lignes == 4:
            self.ctrl_listview.dictFiltres["lignes"] = ["noConsos","total"]
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

    def OnChoixDate(self):
        self.MAJperiode()

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
