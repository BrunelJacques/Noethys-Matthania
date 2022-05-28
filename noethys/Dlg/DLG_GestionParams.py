#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques Brunel
# Licence:         Licence GNU GPL
# Permet le stockage et la reprise de paramètres
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn
from Ctrl import CTRL_Bandeau
import GestionDB
from Ctrl import CTRL_SaisieSimple
import wx.lib.agw.hyperlink as Hyperlink

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)

        # SetColours(1,2,3 )1'link':à l'ouverture, 2`visited`: survol avant clic, 3`rollover`: après le clic,
        self.SetColours("BLUE", "BLUE", "PURPLE")

        # SetUnderlines(1,2,3 ) 1'link':`True` underlined(à l'ouverture),2`visited`:'True` underlined(lors du survol avant clic), 3`rollover`:`True` (trace après le clic),
        self.SetUnderlines(False, True, False)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "ajout": self.parent.AjoutParam()
        if self.URL == "suppr": self.parent.SupprParam()
        if self.URL == "modif": self.parent.ModifParam()
        self.UpdateLink()

class Dialog(wx.Dialog):
    def __init__(self, parent, setGet="set", paramToSet="monParam à stocker",categorie="test",largeur = 80, minSize=(300, 350),colonne =_("Paramètres"),titre=_("Choisissez le paramètre !"), intro=_("Double Clic sur la réponse souhaitée...")):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle("DLG_GestionParams")
        if setGet == "set":
            self.paramToSet = paramToSet
            self.forSet = True
        else: self.forSet = False
        self.categorie = categorie
        self.wLib = largeur
        self.minSize = minSize
        self.nomColonne = colonne
        self.intro = intro
        self.titre = titre
        self.choix= None
        self.DB = GestionDB.DB()
        self.listeDonnees = []
        # import des params existants
        self.dictParams = self.Importation(self.categorie)
        for key in list(self.dictParams.keys()):
            self.listeDonnees.append((key,))
        self.init_DLG()

    def init_DLG(self):
        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=self.intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        # conteneur des données
        self.resultsOlv = FastObjectListView(self)
        # Boutons
        self.hyper_ajout = Hyperlien(self, label=_("Ajouter"), infobulle=_("Cliquez ici pour tout ajouter un nouveau nom"),
                                    URL="ajout")
        self.hyper_suppr = Hyperlien(self, label=_("Supprimer"), infobulle=_("Cliquez ici pour supprimer le paramètre sélectionné"),
                                    URL="suppr")
        self.hyper_modif = Hyperlien(self, label=_("Modifier"),
                                     infobulle=_("Cliquez ici pour modifier le paramètre sélectionné"),
                                     URL="modif")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Reprendre"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, self.bouton_fermer)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClicOk)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnClic)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.hyper_suppr.Enable(False)
        self.hyper_modif.Enable(False)
        if self.forSet:
            self.hyper_ajout.Enable(True)
            self.bouton_ok.Enable(False)
        else:
            self.hyper_ajout.Enable(False)

        self.bouton_fermer.SetToolTip(_("Cliquez ici pour fermer"))
        self.resultsOlv.SetToolTip(_("Double Cliquez pour choisir"))
        # Couleur en alternance des lignes
        self.resultsOlv.oddRowsBackColor = "#F0FBED"
        self.resultsOlv.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.resultsOlv.useExpansionColumn = True
        self.resultsOlv.SetColumns([
            ColumnDefn(self.nomColonne, "left", self.wLib, 0,isSpaceFilling = True),
            ])
        self.resultsOlv.SetSortColumn(self.resultsOlv.columns[0])
        self.resultsOlv.SetObjects(self.listeDonnees)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.resultsOlv, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        grid_sizer_cocher = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=10)
        grid_sizer_cocher.Add(self.hyper_ajout, 0, wx.LEFT, 10)
        grid_sizer_cocher.Add(self.hyper_suppr, 0, wx.LEFT, 10)
        grid_sizer_cocher.Add(self.hyper_modif, 0, wx.LEFT, 10)
        gridsizer_boutons.Add(grid_sizer_cocher, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((10, 10), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(1)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def Importation(self,categorie):
        # Recherche du parametre
        req = """SELECT IDparametre, nom, parametre FROM parametres WHERE categorie="%s";""" % categorie
        self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = self.DB.ResultatReq()
        dictParams = {}
        for ID, nom, parametre in recordset :
            dictParams[nom]= (ID,parametre)
        return dictParams

    def OnDblClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnDblClicOk(self, event):
        self.choix = self.resultsOlv.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, _("Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), _("Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if self.forSet:
                self.ModifParam()
            self.EndModal(wx.ID_OK)

    def OnClic(self, event):
        self.hyper_suppr.Enable(True)
        if self.forSet:
            self.hyper_modif.Enable(True)

    def GetParam(self):
        # retourne le paramètre correspondant au nom choisi
        choix = self.resultsOlv.GetSelectedObject()
        param = None
        if choix != None:
            (ID,param) = self.dictParams[choix[0]]
        return param

    def ModifParam(self):
        nom = None
        if len(self.resultsOlv.GetSelectedObject()[0]) > 0:
            nom = self.resultsOlv.GetSelectedObject()[0]
        if nom == None:
            dlg = wx.MessageDialog(self, _("Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"),
                                   _("Sppression Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            (ID,param)= self.dictParams[nom]
        ret = self.DB.ReqMAJ("parametres",[("parametre",self.paramToSet),],nomChampID="IDparametre",ID=ID,MsgBox = "DLG_GestionParam.ModifParam")
        self.EndModal(wx.ID_OK)

    def AjoutParam(self):
        dlg = CTRL_SaisieSimple.Dialog(self,title = _("Stockage d'un nouveau paramètre"),nomParam="Nom de stockage")
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            nom = dlg.saisie
            if (nom,) in self.listeDonnees:
                dlg1 = wx.MessageDialog(self, _("Nom existant !\nChoisissez le dans la liste pour le modifier,\nou ajoutez un nom différent "), _("Ajout impossible"), wx.OK | wx.ICON_EXCLAMATION)
                dlg1.ShowModal()
                dlg1.Destroy()
            else:
                ret = self.DB.ReqInsert("parametres",[("categorie",self.categorie),("nom",nom),("parametre",self.paramToSet)],MsgBox = "DLG_GestionParam.AjoutParam")
                self.listeDonnees.append((nom,))
                self.resultsOlv.SetObjects(self.listeDonnees)
        dlg.Destroy()
        self.EndModal(wx.ID_OK)

    def SupprParam(self):
        nom = None
        if len(self.resultsOlv.GetSelectedObject()[0]) > 0:
            nom = self.resultsOlv.GetSelectedObject()[0]
        if nom == None:
            dlg = wx.MessageDialog(self, _("Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"),
                                   _("Sppression Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            (ID,param)= self.dictParams[nom]
            ret = self.DB.ReqDEL("parametres",nomChampID="IDparametre",ID=ID,MsgBox = "DLG_GestionParam.SupprParam")
            self.listeDonnees.remove((nom,))
        self.resultsOlv.SetObjects(self.listeDonnees)
        self.resultsOlv.RefreshObjects(self.listeDonnees)

if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None,paramToSet= "mon paramètre",categorie="liste_inscriptions")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    reponse = dialog_1.GetParam()
    dialog_1.Destroy()
    print(reponse)
    app.MainLoop()
