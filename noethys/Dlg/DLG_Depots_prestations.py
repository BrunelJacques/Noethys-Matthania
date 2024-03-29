#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import wx.lib.agw.hyperlink as hl
import wx.html as html
import GestionDB
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Depot_prestations
from Utils import UTILS_Dates
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")



class CTRL_Infos(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=32, couleurFond=(255, 255, 255), style=0):
        html.HtmlWindow.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.texte = ""
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(3)
        self.SetMinSize((-1, hauteur))
        self.couleurFond = couleurFond
        font = self.parent.GetFont()
        self.SetFont(font)
        self.SetLabel(texte)

    def SetLabel(self, texte=""):
        if texte == "":
            texte = _("S�lectionnez un d�p�t pour commencer...")
        self.texte = texte
        self.SetPage(u"""<BODY><FONT SIZE=2 COLOR='#000000'>%s</FONT></BODY>""" % texte)
        self.SetBackgroundColour(self.couleurFond)

    def GetLabel(self):
        return self.texte

# --------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        # Bandeau
        intro = _("S�lectionnez un d�p�t pour afficher le d�tail des prestations ventil�es avec les r�glements inclus dans ce d�p�t. Il est ensuite possible d'exporter les r�sultats sous forme de PDF ou sous Ms Excel.")
        titre = _("D�tail des prestations d'un d�p�t")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Diagramme.png")
        self.SetTitle(titre)

        # S�lection du d�p�t
        self.staticbox_depot = wx.StaticBox(self, -1, _("S�lection du d�p�t"))
        self.ctrl_infos = CTRL_Infos(self, hauteur=32, couleurFond="#F0FBED", style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.SUNKEN_BORDER)
        self.ctrl_infos.SetLabel("")
        self.bouton_rechercher = CTRL_Bouton_image.CTRL(self, texte=_("S�lectionner un d�p�t"), cheminImage="Images/32x32/Loupe.png")

        # R�sultats
        self.staticbox_resultats = wx.StaticBox(self, -1, _("R�sultats"))
        self.ctrl_resultats = CTRL_Depot_prestations.CTRL(self, IDdepot=None)
        
        # Commandes de liste
        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        self.check_details = wx.CheckBox(self, -1, _("Afficher d�tail par tarif unitaire"))
        self.check_details.SetValue(True) 

        self.hyper_developper = self.Build_Hyperlink_developper()
        self.label_barre = wx.StaticText(self, -1, "|")
        self.hyper_reduire = self.Build_Hyperlink_reduire()
        
        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.Bind(wx.EVT_BUTTON, self.OnSelectionDepot, self.bouton_rechercher)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExcel, self.bouton_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckDetails, self.check_details)

        self.__set_properties()
        self.__do_layout()
                
        # Initialisation des contr�les
        self.ctrl_resultats.MAJ()

    def __set_properties(self):
        self.bouton_rechercher.SetToolTip(wx.ToolTip(_("Cliquez ici pour rechercher un d�p�t")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.bouton_apercu.SetToolTip(wx.ToolTip(_("Cliquez ici pour cr�er un aper�u avant impression des r�sultats (PDF)")))
        self.bouton_excel.SetToolTip(wx.ToolTip(_("Cliquez ici pour exporter les r�sultats au format MS Excel")))
        self.check_details.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher le d�tail par tarif unitaire")))
        self.SetMinSize((700, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticbox_depot = wx.StaticBoxSizer(self.staticbox_depot, wx.VERTICAL)
        grid_sizer_depot = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_depot.Add(self.ctrl_infos, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        grid_sizer_depot.Add(self.bouton_rechercher, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_depot.AddGrowableCol(0)
        staticbox_depot.Add(grid_sizer_depot, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_depot, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        staticbox_resultats = wx.StaticBoxSizer(self.staticbox_resultats, wx.VERTICAL)

        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        grid_sizer_contenu.Add(self.ctrl_resultats, 1, wx.EXPAND, 0)

        grid_sizer_commandes = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_commandes.Add(self.bouton_apercu, 0, wx.EXPAND, 0)
        grid_sizer_commandes.Add(self.bouton_excel, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)
        
        # Commandes de liste
        grid_sizer_commandes2 = wx.FlexGridSizer(rows=1, cols=9, vgap=5, hgap=5)
        grid_sizer_commandes2.Add( (30, 5), 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.check_details, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes2.Add( (30, 5), 0, wx.EXPAND, 0)
        grid_sizer_commandes2.Add(self.hyper_developper, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes2.Add(self.label_barre, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes2.Add(self.hyper_reduire, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes2.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_commandes2, 1, wx.EXPAND, 0)
        
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)

        staticbox_resultats.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_resultats, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
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

    def OnSelectionDepot(self, event=None):
        # Importation de la liste des d�p�ts
        DB = GestionDB.DB()
        req = """SELECT depots.IDdepot, depots.date, depots.nom, SUM(reglements.montant), COUNT(reglements.IDreglement)
        FROM depots
        LEFT JOIN reglements ON reglements.IDdepot = depots.IDdepot
        GROUP BY depots.IDdepot
        ORDER BY depots.date;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDepots = DB.ResultatReq()
        DB.Close()
        listeDonnees = []
        listeLabels = []
        for IDdepot, date, nom, total, quantite in listeDepots:
            if not total:
                total = 0.0
            nom = "%s (%s - %.2f %s - %d r�glements)" % (nom, UTILS_Dates.DateEngFr(date), total, SYMBOLE, quantite)
            listeDonnees.append({"IDdepot": IDdepot, "nom": nom})
            listeLabels.append(nom)

        dlg = wx.SingleChoiceDialog(None, _("S�lectionnez un d�p�t dans la liste :"), _("S�lection d'un d�p�t"), listeLabels, wx.CHOICEDLG_STYLE)
        dlg.SetSize((700, 700))
        dlg.CenterOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            dictDepot = listeDonnees[dlg.GetSelection()]
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False

        self.ctrl_resultats.SetIDdepot(dictDepot["IDdepot"])
        self.ctrl_infos.SetLabel(dictDepot["nom"])

    def Build_Hyperlink_developper(self) :
        """ Construit un hyperlien """
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        hyper = hl.HyperLinkCtrl(self, -1, _("Tout d�velopper"), URL="")
        hyper.Bind(hl.EVT_HYPERLINK_LEFT, self.OnLeftLink_developper)
        hyper.AutoBrowse(False)
        hyper.SetColours("BLUE", "BLUE", "BLUE")
        hyper.EnableRollover(True)
        hyper.SetUnderlines(False, False, True)
        hyper.SetBold(False)
        hyper.SetToolTip(wx.ToolTip(_("Tout d�velopper")))
        hyper.UpdateLink()
        hyper.DoPopup(False)
        return hyper
        
    def OnLeftLink_developper(self, event):
        self.ctrl_resultats.DevelopperTout()

    def Build_Hyperlink_reduire(self) :
        """ Construit un hyperlien """
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        hyper = hl.HyperLinkCtrl(self, -1, _("Tout r�duire"), URL="")
        hyper.Bind(hl.EVT_HYPERLINK_LEFT, self.OnLeftLink_reduire)
        hyper.AutoBrowse(False)
        hyper.SetColours("BLUE", "BLUE", "BLUE")
        hyper.EnableRollover(True)
        hyper.SetUnderlines(False, False, True)
        hyper.SetBold(False)
        hyper.SetToolTip(wx.ToolTip(_("Tout r�duire")))
        hyper.UpdateLink()
        hyper.DoPopup(False)
        return hyper
        
    def OnLeftLink_reduire(self, event):
        self.ctrl_resultats.ReduireTout()

    def OnCheckDetails(self, event):
        etat = self.check_details.GetValue()
        self.ctrl_resultats.afficher_detail = etat
        self.ctrl_resultats.MAJ()

    def OnBoutonImprimer(self, event):
        self.ctrl_resultats.Imprimer()

    def OnBoutonExcel(self, event):
        self.ctrl_resultats.ExportExcel()
        
    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Detaildesprestationsdundepot")



# -------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
