#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Ctrl import CTRL_Selection_activites
from Ctrl import CTRL_Saisie_date
from Utils import UTILS_Dates


class zzCTRL_Groupes(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.data = []
        self.date = None
        self.SetToolTip(wx.ToolTip(_("Cochez les groupes à afficher")))
        self.listeGroupes = []
        self.dictGroupes = {}
        self.SetMinSize((-1, 100))

    def SetActivites(self, listeActivites=[]):
        self.listeActivites = listeActivites
        self.MAJ()
        self.CocheTout()

    def MAJ(self):
        self.listeGroupes, self.dictGroupes = self.Importation()
        self.SetListeChoix()

    def Importation(self):
        listeGroupes = []
        dictGroupes = {}
        if len(self.listeActivites) == 0:
            return listeGroupes, dictGroupes
            # Récupération des groupes des activités sélectionnées
        if len(self.listeActivites) == 0:
            conditionActivites = "()"
        elif len(self.listeActivites) == 1:
            conditionActivites = "(%d)" % self.listeActivites[0]
        else:
            conditionActivites = str(tuple(self.listeActivites))
        DB = GestionDB.DB()
        req = """SELECT IDgroupe, groupes.IDactivite, groupes.nom, activites.nom
        FROM groupes
        LEFT JOIN activites ON activites.IDactivite = groupes.IDactivite
        WHERE groupes.IDactivite IN %s
        ORDER BY groupes.nom;""" % conditionActivites
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDgroupe, IDactivite, nom, nomActivite in listeDonnees:
            dictTemp = {"nom": nom, "IDactivite": IDactivite, "nomActivite": nomActivite}
            dictGroupes[IDgroupe] = dictTemp
            listeGroupes.append((nom, IDgroupe, nomActivite))
        listeGroupes.sort()
        return listeGroupes, dictGroupes

    def SetListeChoix(self):
        self.Clear()
        index = 0
        for nom, IDgroupe, nomActivite in self.listeGroupes:
            nom = "%s (%s)" % (nom, nomActivite)
            self.Append(nom)
            index += 1

    def GetIDcoches(self):
        listeIDcoches = []
        NbreItems = len(self.listeGroupes)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                listeIDcoches.append(self.listeGroupes[index][1])
        return listeIDcoches

    def CocheTout(self):
        index = 0
        for index in range(0, len(self.listeGroupes)):
            self.Check(index)
            index += 1

    def SetIDcoches(self, listeIDcoches=[]):
        index = 0
        for index in range(0, len(self.listeGroupes)):
            ID = self.listeGroupes[index][1]
            if ID in listeIDcoches:
                self.Check(index)
            index += 1

    def GetListeGroupes(self):
        return self.GetIDcoches()

    def GetDictGroupes(self):
        return self.dictGroupes

class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Mode
        self.staticbox_mode_staticbox = wx.StaticBox(self, -1, _("Mode de sélection sur la période"))
        self.radio_inscrits = wx.RadioButton(self, -1, _("Inscrits"), style=wx.RB_GROUP)
        self.radio_presents = wx.RadioButton(self, -1, _("Présents"))

        # Calendrier
        self.staticbox_date_staticbox = wx.StaticBox(self, -1, _("Période"))
        self.ctrl_periode = CTRL_Saisie_date.Periode(self)
        self.ctrl_periode.SetMinSize((200, 100))

        # Activités
        self.staticbox_activites_staticbox = wx.StaticBox(self, -1, _("Activités"))
        self.ctrl_activites = CTRL_Selection_activites.CTRL(self,modeGroupes=False)
        self.ctrl_activites.SetMinSize((100, 100))

        # Groupes
        #self.staticbox_groupes_staticbox = wx.StaticBox(self, -1, _("Groupes"))
        #self.ctrl_groupes = CTRL_Selection_activites.CTRL_Groupes(self)
        #self.ctrl_groupes.SetMinSize((10, 100))

        self.__Property()
        self.__Layout()

    def __Property(self):
        # Propriétés
        self.radio_inscrits.SetToolTip(wx.ToolTip(_("Sélectionnez le mode de sélection des individus")))
        self.radio_presents.SetToolTip(wx.ToolTip(_("Sélectionnez le mode de sélection des individus")))

        # Binds
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_inscrits)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_presents)

    def __Layout(self):
        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)

        # Sizer GAUCHE
        grid_sizer_gauche = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)

        # Mode
        staticbox_mode = wx.StaticBoxSizer(self.staticbox_mode_staticbox, wx.VERTICAL)
        grid_sizer_mode = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=10)
        grid_sizer_mode.Add(self.radio_inscrits, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_mode.Add(self.radio_presents, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox_mode.Add(grid_sizer_mode, 0, wx.ALL | wx.EXPAND, 10)
        grid_sizer_gauche.Add(staticbox_mode, 1, wx.EXPAND, 0)

        # Période
        staticbox_date = wx.StaticBoxSizer(self.staticbox_date_staticbox, wx.VERTICAL)
        staticbox_date.Add(self.ctrl_periode, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_gauche.Add(staticbox_date, 1, wx.EXPAND, 0)

        grid_sizer_gauche.AddGrowableRow(1)
        grid_sizer_base.Add(grid_sizer_gauche, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.BOTTOM, 10)

        # Sizer DROIT
        grid_sizer_droit = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)

        # Activités
        staticbox_activites = wx.StaticBoxSizer(self.staticbox_activites_staticbox, wx.VERTICAL)

        staticbox_activites.Add(self.ctrl_activites, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_droit.Add(staticbox_activites, 1, wx.EXPAND, 0)

        # Groupes
        #staticbox_groupes = wx.StaticBoxSizer(self.staticbox_groupes_staticbox, wx.VERTICAL)
        #staticbox_groupes.Add(self.ctrl_groupes, 1, wx.ALL | wx.EXPAND, 10)
        #grid_sizer_droit.Add(staticbox_groupes, 1, wx.EXPAND, 0)

        grid_sizer_droit.AddGrowableRow(0)
        grid_sizer_droit.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_droit, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM, 10)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(1)
        self.SetSizer(grid_sizer_base)
        #self.Layout()
        self.grid_sizer_base = grid_sizer_base

        # Init
        #self.OnRadioMode()

    def OnRadioMode(self, event=None):
        self.grid_sizer_base.Layout()

    def OnCheckActivites(self):
        pass

    def OnChoixDate(self,evt=None):
        self.ctrl_activites.SetPeriode(self.ctrl_periode.GetPeriode())

    def GetPeriode(self):
        return self.ctrl_periode.GetPeriode()

    def SetPeriode(self, periode):
        self.ctrl_periode.SetPeriode(periode)

    def SetListesPeriodes(self, listePeriodes=[]):
        self.ctrl_activites.SetPeriodes(listePeriodes)
        self.SetGroupes(self.ctrl_activites.GetListeActivites())

    #def SetGroupes(self, listeActivites=[]):
    #    self.ctrl_groupes.SetActivites(listeActivites)

    def SetModePresents(self, etat=True):
        self.radio_presents.SetValue(etat)
        self.OnRadioMode()

    def GetParametres(self):
        dictParametres = {}

        dictParametres["liste_periodes"] = [self.ctrl_periode.GetPeriode,]
        dictParametres["impression_infos_med_mode_presents"] = self.radio_presents.GetValue()

        dictParametres["mode"] = "inscrits"
        dictParametres["liste_activites"] = self.ctrl_activites.GetActivites()
        dictParametres["dict_activites"] = self.ctrl_activites.GetDictActivites()

        dictParametres["liste_groupes"] = self.ctrl_activites.GetGroupes()
        dictParametres["dict_groupes"] = self.ctrl_activites.GetDictGroupes()

        return dictParametres

    def SetParametres(self, dictParametres={}):
        pass


# ----------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        bouton_test = wx.Button(panel, -1, "Test")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetMinSize((600, 500))
        #self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton, bouton_test) 
        
    def OnBouton(self, event):
        print("ok")
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(600, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()