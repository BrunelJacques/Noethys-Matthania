#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import time

from Ctrl import CTRL_Bandeau
from Ol import OL_Depots
from Ol import OL_Reglements_depots

import GestionDB

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")



def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))


class Track(object):
    def __init__(self, parent, donnees):
        self.parent = parent
        self.IDreglement = donnees[0]
        self.compte_payeur = donnees[1]
        self.date = DateEngEnDateDD(donnees[2])
        self.IDmode = donnees[3]
        self.nom_mode = donnees[4]
        self.IDemetteur = donnees[5]
        self.nom_emetteur = donnees[6]
        self.numero_piece = donnees[7]
        self.montant = donnees[8]
        self.IDpayeur = donnees[9]
        self.nom_payeur = donnees[10]
        self.observations = donnees[11]
        self.numero_quittancier = donnees[12]
        self.IDprestation_frais = donnees[13]
        self.IDcompte = donnees[14]
        self.date_differe = donnees[15]
        if self.date_differe != None :
            self.date_differe = DateEngEnDateDD(self.date_differe)
        self.encaissement_attente = donnees[16]
        self.IDdepot = donnees[17]
        self.date_depot = donnees[18]
        if self.date_depot != None :
            self.date_depot = DateEngEnDateDD(self.date_depot)
        self.nom_depot = donnees[19]
        self.verrouillage_depot = donnees[20]
        self.date_saisie = donnees[21]
        if self.date_saisie != None :
            self.date_saisie = DateEngEnDateDD(self.date_saisie)
        self.IDutilisateur = donnees[22]
        self.nom_compte = donnees[23]
        self.IDfamille = donnees[24]
        self.email_depots = ""
        self.adresse_intitule = donnees[25]
        self.avis_depot = donnees[26]

        # Etat
        if self.IDdepot == None or self.IDdepot == 0 :
            self.inclus = False
        else:
            self.inclus = True

        # R�cup�ration du nom des titulaires
        self.nomTitulaires = _(" ")
        try :
            self.nomTitulaires = self.parent.dict_titulaires[self.IDfamille]["titulairesSansCivilite"]
        except :
            pass

# ---------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Depots", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.limit = 100

        # Bandeau
        intro = _("Vous pouvez ici saisir, modifier ou supprimer des d�p�ts bancaires. ")
        titre = _("Gestion des d�p�ts")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Banque.png")
        
        # Reglements disponibles
        self.staticbox_reglements = wx.StaticBox(self, -1, _("R�glements disponibles"))
        kw = {"inclus" : False, "selectionPossible" : False, "size" : (-1, 180) }
        self.listviewAvecFooter1 = OL_Reglements_depots.ListviewAvecFooter(self,kwargs=kw)
        self.ctrl_reglements = self.listviewAvecFooter1.GetListview()
        self.ctrl_reglements.SetMinSize((600, 150))

        # D�p�ts
        self.staticbox_depots = wx.StaticBox(self, -1, _("D�p�ts"))
        self.listviewAvecFooter2 = OL_Depots.ListviewAvecFooter(self, kwargs={}) 
        self.ctrl_depots = self.listviewAvecFooter2.GetListview()
        self.ctrl_recherche = OL_Depots.CTRL_Outils(self, listview=self.ctrl_depots)

        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        
        # Options
        self.check_images = wx.CheckBox(self, -1, _("Afficher les images des modes et �metteurs"))
        self.check_images.SetValue(UTILS_Config.GetParametre("depots_afficher_images", defaut=True))

        self.label_limit = wx.StaticText(self, -1, _("D�pots affich�s limit�s � :"))
        self.ctrl_limit = wx.TextCtrl(self, -1, "200", style=wx.TE_PROCESS_ENTER)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckImages, self.check_images)
        self.ctrl_limit.Bind(wx.EVT_KILL_FOCUS, self.OnLimit) # to perform in a textctrl
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

        # Init
        self.OnLimit(None)
        self.MAJreglements()
        self.ctrl_depots.MAJ()

    def __set_properties(self):
        self.SetTitle(_("Gestion des d�p�ts"))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter un d�p�t")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_("Cliquez ici pour modifier le d�p�t s�lectionn� dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer le d�p�t s�lectionn� dans la liste")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour imprimer la liste des d�p�ts affich�s")))
        self.check_images.SetToolTip(wx.ToolTip(_("Cochez cette case pour afficher les images des modes et �metteurs dans chaque fen�tre du gestionnaire de d�p�ts")))
        self.ctrl_limit.SetToolTip(wx.ToolTip("Modifiez le nombre de lignes de d�p�t souhait� dans l'affichage"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.ctrl_limit.SetMaxSize((60,20))
        self.SetMinSize((1050, 850))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        
        # Bandeau
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        # R�glements
        staticbox_reglements = wx.StaticBoxSizer(self.staticbox_reglements, wx.VERTICAL)
        grid_sizer_reglements = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_reglements.Add(self.listviewAvecFooter1, 1, wx.EXPAND | wx.ALL, 0)
        
        grid_sizer_reglements.AddGrowableRow(0)
        grid_sizer_reglements.AddGrowableCol(0)
        staticbox_reglements.Add(grid_sizer_reglements, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_reglements, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # D�p�ts
        staticbox_depots = wx.StaticBoxSizer(self.staticbox_depots, wx.VERTICAL)
        grid_sizer_depots = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=10)
        grid_sizer_gauche.Add(self.listviewAvecFooter2, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_depots.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        
        grid_sizer_droit = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_droit.Add( (10, 10), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_depots.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        
        grid_sizer_depots.AddGrowableRow(0)
        grid_sizer_depots.AddGrowableCol(0)
        staticbox_depots.Add(grid_sizer_depots, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_depots, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Options
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=3)
        grid_sizer_options.Add(self.check_images, 1, wx.LEFT|wx.RIGHT, 10)
        grid_sizer_options.Add(self.label_limit, 1, wx.LEFT|wx.RIGHT, 10)
        grid_sizer_options.Add(self.ctrl_limit, 1, wx.LEFT|wx.RIGHT, 10)
        grid_sizer_base.Add(grid_sizer_options, 1, wx.LEFT|wx.LEFT|wx.BOTTOM, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()
    
    def OnCheckImages(self, event):
        UTILS_Config.SetParametre("depots_afficher_images", self.check_images.GetValue())
        self.MAJreglements() 

    def OnLimit(self,event):
        self.ctrl_depots.limit = self.ctrl_limit.GetValue()
        self.ctrl_depots.MAJ()
        if event:
            event.Skip()

    def MAJreglements(self):
        tracks = self.GetTracks()
        self.ctrl_reglements.MAJ(tracks)
        # Label de staticbox
        self.staticbox_reglements.SetLabel(self.ctrl_reglements.GetLabelListe(_("r�glements disponibles")))

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        db = GestionDB.DB()
        req = """SELECT 
        reglements.IDreglement, reglements.IDcompte_payeur, reglements.date, 
        reglements.IDmode, modes_reglements.label, 
        reglements.IDemetteur, emetteurs.nom, 
        reglements.numero_piece, reglements.montant, 
        payeurs.IDpayeur, payeurs.nom, 
        reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe, 
        encaissement_attente, 
        reglements.IDdepot, depots.date, depots.nom, depots.verrouillage, 
        date_saisie, IDutilisateur,
        comptes_bancaires.nom,
        familles.IDfamille, 
        familles.adresse_intitule,
        reglements.avis_depot
        FROM reglements
        LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
        LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
        LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
        LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
        LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte=reglements.IDcompte
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
        LEFT JOIN familles ON familles.IDfamille = comptes_payeurs.IDfamille
        WHERE reglements.IDdepot IS NULL
        GROUP BY reglements.IDreglement
        ORDER BY reglements.date;
        """
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeListeView = []
        for item in listeDonnees :
            track = Track(self.ctrl_reglements, item)
            listeListeView.append(track)
        return listeListeView

    def Ajouter(self, event):
        self.ctrl_depots.Ajouter(None)
        
    def Modifier(self, event):
        self.ctrl_depots.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_depots.Supprimer(None)
        
    def OnBoutonImprimer(self, event):               
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=20)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=30)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.ctrl_depots.Apercu(None)

    def Imprimer(self, event):
        self.ctrl_depots.Imprimer(None)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Gestiondesdpts")



if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    heure_debut = time.time()
    dialog_1 = Dialog(None)
    print("Temps de chargement =", time.time() - heure_debut)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
