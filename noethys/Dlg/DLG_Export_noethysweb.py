#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-20 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Export_noethysweb
from Ctrl import CTRL_Editeur_email
import os, datetime



class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Export_noethysweb", style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent

        # Bandeau
        intro = _("Utilisez cette fonctionnalit� pour convertir votre base de donn�es au format Noethysweb. Saisissez un mot de passe deux fois et cliquez sur le bouton G�n�rer.")
        titre = _("Exporter les donn�es vers Noethysweb")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Document_export.png")

        # Fichier de destination
        self.box_destination_staticbox = wx.StaticBox(self, -1, _("Destination"))
        self.label_nom = wx.StaticText(self, -1, "Nom :")
        nom_fichier = _("Noethysweb_%s") % datetime.datetime.now().strftime("%Y%m%d_%H%M")
        self.ctrl_nom = wx.TextCtrl(self, -1, nom_fichier)

        self.label_repertoire = wx.StaticText(self, -1, "R�pertoire :")
        sp = wx.StandardPaths.Get()
        cheminDefaut = sp.GetDocumentsDir()
        self.ctrl_repertoire = wx.TextCtrl(self, -1, cheminDefaut)
        self.bouton_repertoire = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Repertoire.png"), wx.BITMAP_TYPE_ANY))

        # Mot de passe
        self.box_cryptage_staticbox = wx.StaticBox(self, -1, _("Cryptage"))
        self.label_mdp = wx.StaticText(self, -1, _("Mot de passe :"))
        self.ctrl_mdp = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        self.label_confirmation = wx.StaticText(self, -1, _("Confirmation :"))
        self.ctrl_confirmation = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)

        # CTRL Editeur d'Emails pour r�cup�rer la version HTML d'un texte XML
        self.ctrl_editeur = CTRL_Editeur_email.CTRL(self)
        self.ctrl_editeur.Show(False)

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_generer = CTRL_Bouton_image.CTRL(self, texte=_("G�n�rer"), cheminImage="Images/32x32/Sauvegarder.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonRepertoire, self.bouton_repertoire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGenerer, self.bouton_generer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

    def __set_properties(self):
        self.ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez ici le nom du fichier de sauvegarde")))
        self.ctrl_mdp.SetToolTip(wx.ToolTip(_("Saisissez le mot de passe qui sera utilis�e pour crypter la sauvegarde")))
        self.ctrl_confirmation.SetToolTip(wx.ToolTip(_("Confirmez le mot de passe")))
        self.ctrl_repertoire.SetMinSize((350, -1))
        self.ctrl_repertoire.SetToolTip(wx.ToolTip(_("Saisissez ici le r�pertoire de destination")))
        self.bouton_repertoire.SetToolTip(wx.ToolTip(_("Cliquez ici pour s�lectionner un r�pertoire de destination")))

        self.bouton_aide.SetToolTip(wx.ToolTip(_("Obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Annuler")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(self.ctrl_editeur, 0, wx.EXPAND, 0)

        # Contenu
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)

        # Destination
        box_destination = wx.StaticBoxSizer(self.box_destination_staticbox, wx.VERTICAL)
        grid_sizer_destination = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_destination.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_destination.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_destination.Add(self.label_repertoire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_repertoire = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_repertoire.Add(self.ctrl_repertoire, 0, wx.EXPAND, 0)
        grid_sizer_repertoire.Add(self.bouton_repertoire, 0, 0, 0)
        grid_sizer_repertoire.AddGrowableCol(0)

        grid_sizer_destination.Add(grid_sizer_repertoire, 1, wx.EXPAND, 0)

        grid_sizer_destination.AddGrowableCol(1)
        box_destination.Add(grid_sizer_destination, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_contenu.Add(box_destination, 1, wx.EXPAND, 0)

        # Cryptage
        box_cryptage = wx.StaticBoxSizer(self.box_cryptage_staticbox, wx.VERTICAL)
        grid_sizer_cryptage = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_cryptage.Add(self.label_mdp, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_cryptage.Add(self.ctrl_mdp, 0, wx.EXPAND, 0)
        grid_sizer_cryptage.Add(self.label_confirmation, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_cryptage.Add(self.ctrl_confirmation, 0, wx.EXPAND, 0)
        grid_sizer_cryptage.AddGrowableCol(1)
        box_cryptage.Add(grid_sizer_cryptage, 1, wx.ALL|wx.EXPAND, 10)

        grid_sizer_contenu.Add(box_cryptage, 1, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_generer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonRepertoire(self, event):
        if self.ctrl_repertoire.GetValue != "":
            cheminDefaut = self.ctrl_repertoire.GetValue()
            if os.path.isdir(cheminDefaut) == False :
                cheminDefaut = ""
        else:
            cheminDefaut = ""
        dlg = wx.DirDialog(self, _("Veuillez s�lectionner un r�pertoire de destination :"), defaultPath=cheminDefaut, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_repertoire.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnBoutonGenerer(self, event):
        # Nom
        nom = self.ctrl_nom.GetValue()
        if not nom:
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return False

        # Mot de passe
        motdepasse = self.ctrl_mdp.GetValue()
        confirmation = self.ctrl_confirmation.GetValue()
        if not motdepasse:
            dlg = wx.MessageDialog(self, _("Vous devez saisir un mot de passe !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_mdp.SetFocus()
            return False
        if motdepasse != confirmation:
            dlg = wx.MessageDialog(self, _("Le mot de passe n'a pas �t� confirm� � l'identique !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_confirmation.SetFocus()
            return False
        # if six.PY3:
        #     motdepasse = six.binary_type(motdepasse, "utf-8")
        # motdepasse = base64.b64encode(motdepasse)

        # R�pertoire
        repertoire = self.ctrl_repertoire.GetValue()
        if repertoire == "":
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un r�pertoire de destination !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_repertoire.SetFocus()
            return False
        # V�rifie que le r�pertoire existe
        if not os.path.isdir(repertoire):
            dlg = wx.MessageDialog(self, _("Le r�pertoire de destination que vous avez saisi n'existe pas !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_repertoire.SetFocus()
            return False

        # G�n�rer du fichier de donn�es
        dlgAttente = wx.BusyInfo(_("Cette op�ration peut prendre quelques minutes. Veuillez patienter..."), self)
        UTILS_Export_noethysweb.Export_all(dlg=self, nom_fichier=os.path.join(repertoire, nom + ".nweb"), mdp=motdepasse)
        del dlgAttente

        # Confirmation de r�ussite
        dlg = wx.MessageDialog(self, _("Le fichier a �t� g�n�r� avec succ�s."), _("Confirmation"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return True




if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
