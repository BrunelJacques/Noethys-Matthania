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
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
import GestionDB
from Dlg.DLG_Saisie_contrat import CTRL_Tarif




class CTRL_Etiquette(wx.Choice):
    def __init__(self, parent, IDactivite=None):
        wx.Choice.__init__(self, parent, -1, size=(-1, -1))
        self.parent = parent
        self.IDactivite = IDactivite
        self.MAJ()

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        listeItems = []
        self.dictDonnees = {}

        DB = GestionDB.DB()
        req = """SELECT IDetiquette, label, parent, ordre, couleur, active
        FROM etiquettes
        WHERE etiquettes.IDactivite=%d AND active=1
        ORDER BY parent, ordre;""" % self.IDactivite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()

        index = 0
        for IDetiquette, label, parent, ordre, couleur, active in listeDonnees :
            # M�morisation de l'�tiquette
            dictTemp = {
                "IDetiquette" : IDetiquette, "label" : label, "parent" : parent,
                "ordre" : ordre, "couleur" : couleur, "active" : active,
                }
            listeItems.append(label)
            self.dictDonnees[index] = dictTemp
            index += 1

        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["IDetiquette"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["IDetiquette"]


# --------------------------------------------------------------------------------------------------------------
class CTRL_Unite(wx.Choice):
    def __init__(self, parent, IDactivite=None):
        wx.Choice.__init__(self, parent, -1, size=(-1, -1))
        self.parent = parent
        self.IDactivite = IDactivite
        self.MAJ()

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        listeItems = []
        if self.IDactivite == None :
            return listeItems
        db = GestionDB.DB()
        req = """SELECT IDunite, nom, type
        FROM unites
        WHERE IDactivite=%d
        ORDER BY ordre;""" % self.IDactivite
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        self.dictDonnees = {}
        index = 0
        for IDunite, nom, type in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDunite, "nom " : nom}
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


# -------------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, IDactivite=None, clsParametres=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.IDactivite = IDactivite
        self.parent = parent
        self.clsParametres = clsParametres

        # Bandeau
        titre = _("Param�tres P.S.U.")
        intro = _("Vous pouvez ici renseigner les param�tres P.S.U. de l'activit�.")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Contrat.png")
        
        # Activation
        self.box_activation_staticbox = wx.StaticBox(self, -1, _("Activation"))
        self.label_activation = wx.StaticText(self, -1, _("Mode P.S.U. activ� :"))
        self.radio_activation_oui = wx.RadioButton(self, -1, _("Oui"), style=wx.RB_GROUP)
        self.radio_activation_non = wx.RadioButton(self, -1, _("Non"))
                
        # Param�tres
        self.box_parametres_staticbox = wx.StaticBox(self, -1, _("Param�tres P.S.U."))
        self.label_unite_prevision = wx.StaticText(self, -1, _("Unit� pr�vision :"))
        self.ctrl_unite_prevision = CTRL_Unite(self, self.IDactivite)
        self.ctrl_unite_prevision.SetMinSize((350, -1))
        self.label_unite_presence = wx.StaticText(self, -1, _("Unit� pr�sence :"))
        self.ctrl_unite_presence = CTRL_Unite(self, self.IDactivite)
        self.label_tarif_forfait = wx.StaticText(self, -1, _("Tarif forfait :"))
        self.ctrl_tarif_forfait = CTRL_Tarif(self, IDactivite=self.IDactivite)
        self.label_etiquette_rtt = wx.StaticText(self, -1, _("Etiquette RTT :"))
        self.ctrl_etiquette_rtt = CTRL_Etiquette(self, self.IDactivite)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init contr�les
        self.Importation()

    def __set_properties(self):
        self.radio_activation_oui.SetToolTip(wx.ToolTip(_("Cliquez ici pour activer le mode P.S.U. pour cette activit�")))
        self.radio_activation_non.SetToolTip(wx.ToolTip(_("Cliquez ici pour d�sactiver le mode P.S.U. pour cette activit�")))
        self.ctrl_unite_prevision.SetToolTip(wx.ToolTip(_("S�lectionnez l'unit� de consommation qui doit �tre utilis�e comme unit� de pr�vision")))
        self.ctrl_unite_presence.SetToolTip(wx.ToolTip(_("S�lectionnez l'unit� de consommation qui doit �tre utilis�e comme unit� de pr�sence")))
        self.ctrl_tarif_forfait.SetToolTip(wx.ToolTip(_("S�lectionnez le tarif qui doit �tre utilis� comme forfait-cr�dit pour les mensualit�s")))
        self.ctrl_etiquette_rtt.SetToolTip(wx.ToolTip(_("S�lectionnez l'�tiquette qui repr�sente les absences RTT")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        # Activation
        box_activation = wx.StaticBoxSizer(self.box_activation_staticbox, wx.VERTICAL)
        grid_sizer_activation = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_activation.Add(self.label_activation, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_activation.Add(self.radio_activation_oui, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_activation.Add(self.radio_activation_non, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        box_activation.Add(grid_sizer_activation, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_base.Add(box_activation, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
                
        # Param�tres
        box_parametres = wx.StaticBoxSizer(self.box_parametres_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=10)

        grid_sizer_parametres.Add(self.label_unite_prevision, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_parametres.Add(self.ctrl_unite_prevision, 0, wx.EXPAND, 0)
        grid_sizer_parametres.Add(self.label_unite_presence, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_parametres.Add(self.ctrl_unite_presence, 0, wx.EXPAND, 0)
        grid_sizer_parametres.Add(self.label_tarif_forfait, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_parametres.Add(self.ctrl_tarif_forfait, 0, wx.EXPAND, 0)
        grid_sizer_parametres.Add(self.label_etiquette_rtt, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_parametres.Add(self.ctrl_etiquette_rtt, 0, wx.EXPAND, 0)

        grid_sizer_parametres.AddGrowableCol(1)
        box_parametres.Add(grid_sizer_parametres, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_base.Add(box_parametres, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
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
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Factures1")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def Importation(self):
        if self.clsParametres != None :
            if self.clsParametres.GetValeur("psu_activation", 0) == 1 :
                self.radio_activation_oui.SetValue(True)
            else :
                self.radio_activation_non.SetValue(True)
            self.ctrl_unite_prevision.SetID(self.clsParametres.GetValeur("psu_unite_prevision", None))
            self.ctrl_unite_presence.SetID(self.clsParametres.GetValeur("psu_unite_presence", None))
            self.ctrl_tarif_forfait.SetID(self.clsParametres.GetValeur("psu_tarif_forfait", None))
            self.ctrl_etiquette_rtt.SetID(self.clsParametres.GetValeur("psu_etiquette_rtt", None))

    def OnBoutonOk(self, event):
        # R�cup�ration des donn�es
        psu_activation = int(self.radio_activation_oui.GetValue())
        psu_unite_prevision = self.ctrl_unite_prevision.GetID()
        psu_unite_presence = self.ctrl_unite_presence.GetID()
        psu_tarif_forfait = self.ctrl_tarif_forfait.GetID()
        psu_etiquette_rtt = self.ctrl_etiquette_rtt.GetID()

        if psu_activation == 1 :
            if psu_unite_prevision == None :
                dlg = wx.MessageDialog(self.parent, _("Vous avez activ� le mode P.S.U. mais sans s�lectionner d'unit� de pr�vision !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if psu_unite_presence == None :
                dlg = wx.MessageDialog(self.parent, _("Vous avez activ� le mode P.S.U. mais sans s�lectionner d'unit� de pr�sence !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if psu_tarif_forfait == None :
                dlg = wx.MessageDialog(self.parent, _("Vous avez activ� le mode P.S.U. mais sans s�lectionner de tarif forfait-cr�dit !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        self.clsParametres.SetValeur("psu_activation", psu_activation)
        self.clsParametres.SetValeur("psu_unite_prevision", psu_unite_prevision)
        self.clsParametres.SetValeur("psu_unite_presence", psu_unite_presence)
        self.clsParametres.SetValeur("psu_tarif_forfait", psu_tarif_forfait)
        self.clsParametres.SetValeur("psu_etiquette_rtt", psu_etiquette_rtt)

        # Fermeture
        self.EndModal(wx.ID_OK)




if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDactivite=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
