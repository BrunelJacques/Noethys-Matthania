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
import wx.lib.agw.hyperlink as Hyperlink
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Selection_depots
from Ctrl import CTRL_Selection_activites
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Synthese_ventilation



class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "developper":
            self.parent.ctrl_resultats.DevelopperTout()
        if self.URL == "reduire":
            self.parent.ctrl_resultats.ReduireTout()


        self.UpdateLink()


class Page_depots(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.ctrl_depots = CTRL_Selection_depots.CTRL(self)
        self.ctrl_depots.MAJ() 

        self.__set_properties()
        self.__do_layout()
        

    def __set_properties(self):
        pass

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_depots, 0, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def Validation(self):
        return True

# -------------------------------------------------------------------------------------------------------

class Page_prestations(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.label_date_debut = wx.StaticText(self, -1, _("P�riode du"))
        self.ctrl_date_debut = CTRL_Saisie_date.Date(self)
        self.label_date_fin = wx.StaticText(self, -1, " au")
        self.ctrl_date_fin = CTRL_Saisie_date.Date(self)

        self.check_activites = wx.CheckBox(self, -1, _("Uniquement rattach�es aux activit�s :"))
        self.ctrl_activites = CTRL_Selection_activites.CTRL(self)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheckActiveActivites, self.check_activites)
        self.OnCheckActiveActivites()

    def __set_properties(self):
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_("Saisissez la date de d�but")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_("Saisissez la date de fin")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)

        # P�riode
        grid_sizer_periode = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_periode.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, 0, 0)
        grid_sizer_periode.Add(self.label_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, 0, 0)
        grid_sizer_base.Add(grid_sizer_periode, 1, wx.EXPAND | wx.TOP, 10)

        grid_sizer_base.Add(self.check_activites, 0, wx.EXPAND | wx.TOP, 8)
        grid_sizer_base.Add(self.ctrl_activites, 1, wx.EXPAND | wx.LEFT, 15)

        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def OnCheckActiveActivites(self, event=None):
        self.ctrl_activites.Enable(self.check_activites.GetValue())

    def OnCheckActivites(self):
        pass

    def GetActivites(self):
        return self.ctrl_activites.GetActivites()

    def Validation(self):
        date_debut = self.ctrl_date_debut.GetDate()
        if self.ctrl_date_debut.FonctionValiderDate() == False or date_debut == None:
            dlg = wx.MessageDialog(self, _("La date de d�but de p�riode ne semble pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_debut.SetFocus()
            return False

        date_fin = self.ctrl_date_fin.GetDate()
        if self.ctrl_date_fin.FonctionValiderDate() == False or date_fin == None:
            dlg = wx.MessageDialog(self, _("La date de fin de p�riode ne semble pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_fin.SetFocus()
            return False

        if self.check_activites.GetValue() == True:
            listeActivites = self.GetActivites()
            if len(listeActivites) == 0:
                dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune activit� !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return True

    def GetDonnees(self):
        date_debut = self.ctrl_date_debut.GetDate()
        date_fin = self.ctrl_date_fin.GetDate()
        if self.check_activites.GetValue() == True:
            listeActivites = self.GetActivites()
        else :
            listeActivites = []
        return {"date_debut" : date_debut, "date_fin" : date_fin, "activites" : listeActivites}

# ------------------------------------------------------------------------------------------------------------

class CTRL_Parametres(wx.Choicebook):
    def __init__(self, parent):
        wx.Choicebook.__init__(self, parent, id=-1)
        self.parent = parent

        self.listePanels = [
            ("DEPOTS", _("Affiche les d�p�ts s�lectionn�s"), Page_depots(self)),
            ("PRESTATIONS", _("Affiche les prestations ventil�es sur une p�riode"), Page_prestations(self)),
        ]

        for code, label, ctrl in self.listePanels:
            self.AddPage(ctrl, label)

        # S�lection par d�faut
        self.SetSelection(0)

    def GetCodePage(self):
        index = self.GetSelection()
        return self.listePanels[index][0]

    def GetPanel(self):
        index = self.GetSelection()
        return self.listePanels[index][2]

# --------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        # Bandeau
        intro = _("Ceci est un tableau d'analyse crois�e Ventilation/D�p�ts qui vous permet d'afficher deux types de donn�es : 1) Les prestations, regroup�es par p�riode, que les r�glements des d�p�ts s�lectionn�s ont servi � payer, et 2) les d�p�ts dont les r�glements ont servi � payer les prestations d'une p�riode donn�e. Ces r�sultats vous permettront donc de mettre en corr�lation les d�p�ts et les prestations � la fin d'un exercice comptable.")
        titre = _("Tableau d'analyse crois�e ventilation/d�p�ts")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Diagramme.png")
        self.SetTitle(titre)
        
        # Panel Param�tres
        self.staticbox_parametres = wx.StaticBox(self, -1, _("Param�tres"))
        self.ctrl_parametres = CTRL_Parametres(self)
        self.ctrl_parametres.SetMinSize((280, -1))
        self.bouton_actualiser = CTRL_Bouton_image.CTRL(self, texte=_("Rafra�chir la liste"), cheminImage="Images/32x32/Actualiser.png")
        self.bouton_actualiser.SetMinSize((-1, 50))

        # CTRL R�sultats
        self.staticbox_resultats_staticbox = wx.StaticBox(self, -1, _("R�sultats"))
        self.ctrl_resultats = CTRL_Synthese_ventilation.CTRL(self)
        
        # Commandes de liste
        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        # Commandes de r�sultats
        self.label_mode_affichage = wx.StaticText(self, -1, _("Mode d'affichage :"))
        self.radio_mois = wx.RadioButton(self, -1, _("Mois"), style=wx.RB_GROUP)
        self.radio_annee = wx.RadioButton(self, -1, _("Ann�e"))
        
        self.check_details = wx.CheckBox(self, -1, _("Afficher d�tails"))
        self.check_details.SetValue(True) 
        
        self.hyper_developper = Hyperlien(self, label=_("D�velopper"), infobulle=_("Cliquez ici pour d�velopper l'arborescence"), URL="developper")
        self.label_barre = wx.StaticText(self, -1, "|")
        self.hyper_reduire = Hyperlien(self, label=_("R�duire"), infobulle=_("Cliquez ici pour r�duire l'arborescence"), URL="reduire")
        
        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExcel, self.bouton_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMois, self.radio_mois)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioAnnee, self.radio_annee)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckDetails, self.check_details)
        self.Bind(wx.EVT_BUTTON, self.MAJ, self.bouton_actualiser)

        self.__set_properties()
        self.__do_layout()
                
        # Initialisation des contr�les
        self.MAJ()

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.bouton_apercu.SetToolTip(wx.ToolTip(_("Cliquez ici pour cr�er un aper�u avant impression des r�sultats (PDF)")))
        self.bouton_excel.SetToolTip(wx.ToolTip(_("Cliquez ici pour exporter les r�sultats au format MS Excel")))
        self.radio_mois.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher les r�sultats par mois")))
        self.radio_annee.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher les r�sultats par ann�es")))
        self.check_details.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher les d�tails dans les r�sultats")))
        self.bouton_actualiser.SetToolTip(wx.ToolTip(_("Cliquez ici pour actualiser les r�sultats")))
        self.SetMinSize((1100, 750))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)

        # Param�tres
        staticbox_param = wx.StaticBoxSizer(self.staticbox_parametres, wx.VERTICAL)
        staticbox_param.Add(self.ctrl_parametres, 1, wx.ALL|wx.EXPAND, 5)
        staticbox_param.Add(self.bouton_actualiser, 0, wx.ALL | wx.EXPAND, 5)
        grid_sizer_contenu.Add(staticbox_param, 1, wx.EXPAND, 0)

        # R�sultats
        staticbox_resultats= wx.StaticBoxSizer(self.staticbox_resultats_staticbox, wx.VERTICAL)
        grid_sizer_resultats = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        grid_sizer_resultats.Add(self.ctrl_resultats, 1, wx.EXPAND, 0)
        
        # Boutons de liste
        grid_sizer_commandes = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_commandes.Add(self.bouton_apercu, 0, wx.EXPAND, 0)
        grid_sizer_commandes.Add(self.bouton_excel, 0, wx.EXPAND, 0)
        grid_sizer_resultats.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)
        
        # Commandes de liste
        grid_sizer_commandes2 = wx.FlexGridSizer(rows=1, cols=9, vgap=5, hgap=5)
        grid_sizer_commandes2.Add(self.label_mode_affichage, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.radio_mois, 0, wx.EXPAND, 0) 
        grid_sizer_commandes2.Add(self.radio_annee, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add( (30, 5), 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.check_details, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.hyper_developper, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.label_barre, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.hyper_reduire, 0, wx.EXPAND, 0)
        grid_sizer_commandes2.AddGrowableCol(5)
        grid_sizer_resultats.Add(grid_sizer_commandes2, 1, wx.EXPAND, 0)
        
        grid_sizer_resultats.AddGrowableRow(0)
        grid_sizer_resultats.AddGrowableCol(0)
        
        staticbox_resultats.Add(grid_sizer_resultats, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_contenu.Add(staticbox_resultats, 1, wx.RIGHT|wx.EXPAND, 5)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
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
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnRadioMois(self, event):
        self.ctrl_resultats.SetModeAffichage("mois")
        self.MAJ() 
    
    def OnRadioAnnee(self, event):
        self.ctrl_resultats.SetModeAffichage("annee")
        self.MAJ() 
    
    def OnCheckDetails(self, event):
        etat = self.check_details.GetValue()
        self.ctrl_resultats.SetAffichageDetails(etat)
        self.MAJ() 
        self.hyper_developper.Enable(-etat)
        self.label_barre.Enable(-etat)
        self.hyper_reduire.Enable(-etat)

    def MAJ(self, event=None):
        codePage = self.ctrl_parametres.GetCodePage()
        page = self.ctrl_parametres.GetPanel()
        if page.Validation() == False:
            self.ctrl_resultats.SetTypeVide()

        else :

            # Page d�p�ts
            if codePage == "DEPOTS" :
                listeDepots = page.ctrl_depots.GetDepots()
                self.ctrl_resultats.SetTypeDepots(listeDepots)

                # Page Prestations
            if codePage == "PRESTATIONS":
                dictDonnees = page.GetDonnees()
                self.ctrl_resultats.SetTypePrestations(dictDonnees["date_debut"], dictDonnees["date_fin"], dictDonnees["activites"])

        self.ctrl_resultats.MAJ() 
        
    def OnBoutonImprimer(self, event):
        self.ctrl_resultats.Imprimer() 

    def OnBoutonExcel(self, event):
        self.ctrl_resultats.ExportExcel() 
        
    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Tableaudanalysecroiseventilation")



# -------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
