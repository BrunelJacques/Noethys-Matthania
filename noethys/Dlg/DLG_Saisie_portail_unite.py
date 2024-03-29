#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB




class Liste_unites_conso(wx.CheckListBox):
    def __init__(self, parent, IDactivite=None):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.data = []
        self.IDactivite = IDactivite
        self.SetMinSize((290, 160))
    
    def MAJ(self):
        listeTmp = []
        DB = GestionDB.DB()
        req = """SELECT IDunite, nom
        FROM unites 
        WHERE IDactivite=%d
        ORDER BY ordre;""" % self.IDactivite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) > 0 : 
            for IDunite, nom in listeDonnees :
                listeTmp.append((IDunite, nom, False))
        self.SetData(listeTmp)    
            
    def SetData(self, listeValeurs=[]):
        """ items = (ID, label, checked) """
        self.Clear()
        self.data = []
        index = 0
        for ID, label, checked in listeValeurs:
            self.data.append((ID, label))
            self.Append(label)
            if checked == True :
                self.Check(index)
            index += 1
    
    def GetIDcoches(self):
        listeIDcoches = []
        NbreItems = len(self.data)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                listeIDcoches.append(self.data[index][0])
        return listeIDcoches

    def SetIDcoches(self, listeIDcoches=[]):
        index = 0
        for index in range(0, len(self.data)):
            ID = self.data[index][0]
            if ID in listeIDcoches :
                self.Check(index)
            index += 1
    
    def SetCochesStr(self, texte=""):
        if texte in (None, ""):
            return
        listeID = []
        for IDunite in texte.split(";") :
            listeID.append(int(IDunite))
        self.SetIDcoches(listeID)

    def GetCochesStr(self):
        listeID = self.GetIDcoches()
        texte = ";".join([str(IDunite) for IDunite in listeID])
        return texte

    def GetNomsUnites(self, listeID=[]):
        listeNoms = []
        for ID, label in self.data :
            if ID in listeID :
                listeNoms.append(label)
        return listeNoms

# ------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDunite=None, IDactivite=None, ordre=1):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDunite = IDunite
        self.IDactivite = IDactivite
        self.ordre = ordre

        # Nom
        self.staticbox_nom_staticbox = wx.StaticBox(self, -1, _("Nom de l'unit� de r�servation"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")

        # Caract�ristiques
        self.staticbox_caract_staticbox = wx.StaticBox(self, -1, _("Caract�ristiques"))

        self.label_unites_principales = wx.StaticText(self, -1, _("Unit�s de conso\nprincipales :"))
        self.ctrl_unites_principales = Liste_unites_conso(self, IDactivite=self.IDactivite)
        self.ctrl_unites_principales.MAJ()

        self.label_unites_secondaires = wx.StaticText(self, -1, _("Unit�s de conso\nsecondaires :"))
        self.ctrl_unites_secondaires = Liste_unites_conso(self, IDactivite=self.IDactivite)
        self.ctrl_unites_secondaires.MAJ()

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        if self.IDunite != None :
            self.Importation() 
        

    def __set_properties(self):
        if self.IDunite == None :
            self.SetTitle(_("Saisie d'une unit� de r�servation"))
        else :
            self.SetTitle(_("Modification d'une unit� de r�servation"))
        self.SetSize((650, -1))
        self.ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez ici le nom de l'unit� de r�servation")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))


    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)

        # Nom
        staticbox_nom = wx.StaticBoxSizer(self.staticbox_nom_staticbox, wx.VERTICAL)
        staticbox_nom.Add(self.ctrl_nom, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_nom, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)

        # Caract�ristiques
        staticbox_caract = wx.StaticBoxSizer(self.staticbox_caract_staticbox, wx.VERTICAL)
        grid_sizer_caract = wx.FlexGridSizer(rows=7, cols=2, vgap=15, hgap=5)

        grid_sizer_caract.Add(self.label_unites_principales, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_caract.Add(self.ctrl_unites_principales, 0, wx.EXPAND, 0)

        grid_sizer_caract.Add(self.label_unites_secondaires, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_caract.Add(self.ctrl_unites_secondaires, 0, wx.EXPAND, 0)

        grid_sizer_caract.AddGrowableCol(1)
        grid_sizer_caract.AddGrowableRow(0)
        grid_sizer_caract.AddGrowableRow(1)
        staticbox_caract.Add(grid_sizer_caract, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_caract, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen() 
        self.SetMinSize(self.GetSize())
        


    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Portail")

    def OnBoutonOk(self, event): 
        # Nom
        nom = self.ctrl_nom.GetValue() 
        if nom == "" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom pour cette unit� de r�servation !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Unit�s de conso principales
        listeCochesUnitesPrincipales = self.ctrl_unites_principales.GetIDcoches()
        texteCochesUnitesPrincipales = self.ctrl_unites_principales.GetCochesStr()
        if len(listeCochesUnitesPrincipales) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement cocher au moins une unit� de consommation principale !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Unit�s de conso secondaires
        listeCochesUnitesSecondaires = self.ctrl_unites_secondaires.GetIDcoches()
        texteCochesUnitesSecondaires = self.ctrl_unites_secondaires.GetCochesStr()

        listeUniteConflit = []
        for IDunite_secondaire in listeCochesUnitesSecondaires :
            for IDunite_principale in listeCochesUnitesPrincipales :
                if IDunite_secondaire == IDunite_principale :
                    listeUniteConflit.append(IDunite_secondaire)

        if len(listeUniteConflit) :
            listeNoms = self.ctrl_unites_principales.GetNomsUnites(listeUniteConflit)
            dlg = wx.MessageDialog(self, _("Les unit�s secondaires ne peuvent pas �tre identiques aux unit�s secondaires. Veuillez d�cocher les unit�s secondaires suivantes :\n\n > %s") % ", ".join(listeNoms), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Enregistrement
        DB = GestionDB.DB()
        listeDonnees = [ 
            ("IDactivite", self.IDactivite),
            ("nom", nom),
            ("unites_principales", texteCochesUnitesPrincipales),
            ("unites_secondaires", texteCochesUnitesSecondaires),
            ("ordre", self.ordre),
            ]

        if self.IDunite == None :
            self.IDunite = DB.ReqInsert("portail_unites", listeDonnees)
        else:
            DB.ReqMAJ("portail_unites", listeDonnees, "IDunite", self.IDunite)
        DB.Close()

        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)


    def Importation(self):
        """ Importation des valeurs """
        DB = GestionDB.DB()
        req = """SELECT IDactivite, nom, unites_principales, unites_secondaires, ordre
        FROM portail_unites WHERE IDunite=%d;""" % self.IDunite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeTemp = DB.ResultatReq()
        DB.Close()
        if len(listeTemp) == 0 : return
        listeTemp = listeTemp[0]
        
        self.IDactivite = listeTemp[0]
        nom = listeTemp[1]
        unites_principales = listeTemp[2]
        unites_secondaires = listeTemp[3]
        self.ordre = listeTemp[4]

        self.ctrl_nom.SetValue(nom)
        self.ctrl_unites_principales.SetCochesStr(unites_principales)
        self.ctrl_unites_secondaires.SetCochesStr(unites_secondaires)


    def GetIDunite(self):
        return self.IDunite

        


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDunite=1, IDactivite=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
