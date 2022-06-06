#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Branche Matthania
# Module :         Mise en place d'un fichier release contenant les patchs
# Auteur:          JB adaptation de DLG_Restauration
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import sys
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Fichiers
from Utils import UTILS_Cryptage_fichier

sys.modules['UTILS_Cryptage_fichier'] = UTILS_Cryptage_fichier

class CTRL_Donnees(wx.TextCtrl):
    def __init__(self, parent):
        label = "Info dernières versions"
        id = wx.ID_ANY
        pos = wx.DefaultPosition
        size = wx.DefaultSize
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_DONTWRAP
        wx.TextCtrl.__init__(self, parent, id, label, pos, size, style=style)
        self.parent = parent
        self.actuelle = self.GetVersionNow()
        invite = "%s Choisissez un fichier"%self.actuelle
        self.SetValue(invite)

    def MAJ(self):

        # --- Fonctions préliminaires à UTILS_Fichiers

        def GetNameReleaseZip():
            # Demande l'emplacement du fichier
            wildcard = "Release Noethys (*.zip; *.7z)|*.*"
            intro = "Veuillez sélectionner le fichier contenant la MISE A JOUR DE NOETHYS"
            return UTILS_Fichiers.SelectionFichier(intro, wildcard, verifZip=True)

        def GetVersionsFile(releaseZip):
            if not releaseZip: return
            lstFichiers = UTILS_Fichiers.GetListeFichiersZip(releaseZip)
            lstVersions = [x for x in lstFichiers if "versions" in x.lower()]
            if len(lstVersions) == 0:
                mess = "Le Zip %s ne contient pas de fichier 'Version.txt'"%self.nameRelease
                wx.MessageBox(mess, "Echec",style=wx.ICON_ERROR)
                return
            nameVersionsFile = lstVersions[0]
            return UTILS_Fichiers.GetOneFileInZip(releaseZip,nameVersionsFile)

        # action de mise à jour
        self.nameRelease = GetNameReleaseZip()
        if not self.nameRelease:
            return
        try:
            self.zipFile = UTILS_Fichiers.GetZipFile(self.nameRelease,"r")
            texte = GetVersionsFile(self.zipFile).decode()
            # afichage du contenu
            if texte:
                nouvelle = "Versions dans le fichier :\n\n%s"%texte
                self.SetValue("%s%s"%(self.actuelle,nouvelle))
                dc = wx.ClientDC(self)
                dc.SetFont(self.GetFont())
                self.parent.bouton_ok.Enable(True)
            
        except Exception as err:
            if isinstance(err,UnicodeDecodeError):
                mess = "Le fichier version importé n'est pas codé en UTF-8\n%s"%err
                wx.MessageBox(mess,"Abandon")
            print(type(err),err)

    def GetVersionNow(self):
        import codecs
        # ----
        import FonctionsPerso
        fichier = codecs.open(
            FonctionsPerso.GetRepertoireProjet("Versions.txt"),
            encoding='utf-8', mode='r')
        versionNow = fichier.readlines()[0]
        fichier.close()
        pos = versionNow.find(")") + 1
        return "Actuellement : %s\n\n"%versionNow[:pos]

# ------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        intro = _("Vous pouvez ici mettre à jour votre version Noethys, à partir d'un fichier ZIP contenant la release")
        titre = _("Release")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Restaurer.png")
                
        # Données
        self.box_donnees_staticbox = wx.StaticBox(self, -1, _("Description des versions :"))
        self.ctrl_donnees = CTRL_Donnees(self)
        self.ctrl_donnees.SetMinSize((250, -1))
        
        # Boutons
        self.bouton_fichier = CTRL_Bouton_image.CTRL(self, texte=_("Choisir le fichier"), cheminImage="Images/32x32/Desarchiver.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok pour release"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFichier, self.bouton_fichier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_fichier.SetToolTip(wx.ToolTip(_("Cliquez ici pour choisir le fichier release.zip")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer la restauration")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((600, 800))
        self.bouton_ok.Enable(False)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        box_donnees = wx.StaticBoxSizer(self.box_donnees_staticbox, wx.VERTICAL)
        box_donnees.Add(self.ctrl_donnees, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_donnees, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fichier, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonFichier(self, event):
        self.ctrl_donnees.MAJ()
        return

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        noethysPath = "%s"%Chemins.REP_PARENT
        self.ctrl_donnees.zipFile.extractall("%s/.."%noethysPath)

        # Fin du processus
        dlg = wx.MessageDialog(self, _("Le processus de mise à jour est terminé."), "Release", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Fermeture
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
