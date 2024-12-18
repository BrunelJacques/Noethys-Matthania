#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
from Ctrl import CTRL_Bandeau
from Ol import OL_Contratspsu_validation
from Ctrl.CTRL_ObjectListView import CTRL_Outils
import GestionDB

LISTE_MOIS = [_("Janvier"), _("F�vrier"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Ao�t"), _("Septembre"), _("Octobre"), _("Novembre"), _("D�cembre")]


class CTRL_Activite(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.MAJ()

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        self.SetItems(listeItems)
        if len(listeItems) > 0 :
            self.Select(0)

    def GetListeDonnees(self):
        DB = GestionDB.DB()
        req = """SELECT IDactivite, nom, abrege
        FROM activites
        WHERE psu_activation=1
        ORDER BY date_fin DESC;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeItems = []
        self.dictDonnees = {}
        index = 0
        for IDactivite, nom, abrege in listeDonnees :
            if nom == None : nom = "Activit� inconnue"
            self.dictDonnees[index] = {"ID" : IDactivite, "nom" : nom, "abrege" : abrege}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]

    def GetInfos(self):
        """ R�cup�re les infos sur le compte s�lectionn� """
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]



class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        intro = _("Avant de g�n�rer les factures d'une activit� de type P.S.U., vous devez commencer par g�n�rer ici les mensualit�s pour le mois souhait�. Notez qu'il est est possible de saisir manuellement un nombre d'heures de r�gularisation avant de valider la g�n�ration.")
        titre = _("Validation des contrats P.S.U.")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Contrat.png")
        
        # Param�tres
        self.box_parametres_staticbox = wx.StaticBox(self, -1, _("Param�tres"))
        self.label_mois = wx.StaticText(self, -1, _("Mois :"))
        self.ctrl_mois = wx.Choice(self, -1, choices=LISTE_MOIS)
        self.spin_mois = wx.SpinButton(self, -1, size=(18, 20),  style=wx.SP_VERTICAL)
        self.spin_mois.SetRange(-1, 1)
        self.ctrl_annee = wx.SpinCtrl(self, -1, size=(60, -1), min=2000, max=2999)
        self.label_activite = wx.StaticText(self, -1, _("Activit� :"))
        self.ctrl_activite = CTRL_Activite(self)

        # Contrats
        self.box_contrats_staticbox = wx.StaticBox(self, -1, _("Mensualit�s"))
        self.listviewAvecFooter = OL_Contratspsu_validation.ListviewAvecFooter(self)
        self.ctrl_contrats = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = CTRL_Outils(self, listview=self.ctrl_contrats, afficherCocher=True)

        self.bouton_detail = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Zoom_plus.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        self.label_info = wx.StaticText(self, -1, _("Remarque : Vous pouvez double-cliquer dans la colonne 'H. r�gular.' pour saisir un nombre positif ou n�gatif d'heures de r�gularisation."))
        self.label_info.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.label_info.SetForegroundColour(wx.Colour(180, 180, 180))

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=-1, texte=_("Valider"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=-1, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHOICE, self.OnChangeParametres, self.ctrl_mois)
        self.Bind(wx.EVT_SPIN, self.OnSpinMois, self.spin_mois)
        self.Bind(wx.EVT_SPINCTRL, self.OnChangeParametres, self.ctrl_annee)
        self.Bind(wx.EVT_CHOICE, self.OnChangeParametres, self.ctrl_activite)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Detail, self.bouton_detail)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Apercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.Imprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.ExportTexte, self.bouton_texte)
        self.Bind(wx.EVT_BUTTON, self.ctrl_contrats.ExportExcel, self.bouton_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)

        # Init
        date = datetime.date.today()
        self.SetMois(mois=date.month, annee=date.year)
        self.OnChangeParametres()


    def __set_properties(self):
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_detail.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher un aper�u du d�tail de la mensualit� s�lectionn�e")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer les prestations existantes des lignes s�lectionn�es ou coch�es")))
        self.bouton_apercu.SetToolTip(wx.ToolTip(_("Cliquez ici pour cr�er un aper�u de la liste")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour imprimer la liste")))
        self.bouton_texte.SetToolTip(wx.ToolTip(_("Cliquez ici pour exporter la liste au format Texte")))
        self.bouton_excel.SetToolTip(wx.ToolTip(_("Cliquez ici pour exporter la liste au format Excel")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.SetMinSize((900, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Parametres
        box_parametres = wx.StaticBoxSizer(self.box_parametres_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_parametres.Add(self.label_mois, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_mois = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        grid_sizer_mois.Add(self.ctrl_mois, 0, wx.EXPAND, 0)
        grid_sizer_mois.Add(self.spin_mois, 0, wx.EXPAND, 0)
        grid_sizer_mois.Add(self.ctrl_annee, 0, wx.EXPAND, 0)
        grid_sizer_parametres.Add(grid_sizer_mois, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_parametres.Add( (5, 5), 0, wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_parametres.Add(self.label_activite, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_parametres.Add(self.ctrl_activite, 1, wx.EXPAND, 0)

        grid_sizer_parametres.AddGrowableCol(4)
        box_parametres.Add(grid_sizer_parametres, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_parametres, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Contrats
        box_contrats = wx.StaticBoxSizer(self.box_contrats_staticbox, wx.VERTICAL)

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_gauche.Add(self.listviewAvecFooter, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)

        grid_sizer_gauche.Add(self.label_info, 0, wx.EXPAND, 0)

        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        
        grid_sizer_droit = wx.FlexGridSizer(rows=9, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add(self.bouton_detail, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_droit.Add( (5, 5), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_droit.Add( (5, 5), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_texte, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_excel, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)

        box_contrats.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_contrats, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

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
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def SetMois(self, mois=1, annee=2000):
        self.ctrl_mois.SetSelection(mois-1)
        self.ctrl_annee.SetValue(annee)

    def OnSpinMois(self, event):
        x = event.GetPosition()
        mois = self.ctrl_mois.GetSelection()+x
        if mois != -1 and mois < 12 :
            self.ctrl_mois.SetSelection(mois)
            self.OnChangeParametres()
        self.spin_mois.SetValue(0)

    def OnChangeParametres(self, event=None):
        mois = self.ctrl_mois.GetSelection() + 1
        annee = int(self.ctrl_annee.GetValue())
        IDactivite = self.ctrl_activite.GetID()
        nomActivite = self.ctrl_activite.GetStringSelection()
        self.ctrl_contrats.SetParametres(mois=mois, annee=annee, IDactivite=IDactivite, nomActivite=nomActivite)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("ValidationdescontratsPSU")

    def OnBoutonAnnuler(self, event=None):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        if self.ctrl_contrats.Valider() == False :
            return False









if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
