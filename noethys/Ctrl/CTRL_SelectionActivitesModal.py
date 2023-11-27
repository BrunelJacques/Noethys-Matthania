#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    évolutions Matthania, selection des activités en vue de listes
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import Chemins
import datetime
from Ctrl import CTRL_Bouton_image
import wx.lib.agw.pybusyinfo as PBI
import GestionDB
from Ctrl import CTRL_Saisie_date
from Dlg import DLG_calendrier_simple
import wx.lib.agw.hyperlink as Hyperlink
import UTILS_Dates as ut

# Afaptation possible pour le Panel CTRL

class Adapt(object):
    def __init__(self, parent,periode):
        self.parent = parent
        self.periode = periode
        self.lstIDactivitesPossibles = []
        self.lstIDgroupes = []
        self.lstIDactivites = []

    def GetTitleBox(self):
        return "Activités dans la période"

    def SetPeriode(self,periode):
        self.periode = periode
        
    def SetPossibles(self,lstIDactivitesPossibles):
        self.lstIDactivitesPossibles = lstIDactivitesPossibles

    def SetGroupes(self, lstIDgroupes):
        self.lstIDgroupes = lstIDgroupes

    # Activites possibles selon les dates
    def GetIDactivitePossibles(self):
        # appel des activités filtrées sur les dates
        req = """
                SELECT IDactivite
                FROM prestations
                WHERE date BETWEEN '%s' AND '%s'
                GROUP BY IDactivite
                ORDER BY IDactivite;
                """ % (self.periode[0],self.periode[1])
        DB = GestionDB.DB()
        DB.ExecuterReq(req, MsgBox="CTRL_SelectionActivitesModal.GetIDactivitePossible")
        recordset = DB.ResultatReq()
        DB.Close()
        self.lstIDactivitesPossibles = []
        self.lstIDactivitesPossibles = [ x[0] for x in recordset if x[0] and (x[0]>0)]

    # Groupes à afficher selon période
    def GetGroupes(self):
        if len(self.lstIDactivitesPossibles) > 0:
            lstAct = str(self.lstIDactivitesPossibles)[1:-1]
            # filtres sur les seuls possibles
            conditionWhere = "WHERE activites.IDactivite In ( %s )" % lstAct
        else:
            conditionWhere = "WHERE FALSE"
        # appel des groupes d'activites représentés dans la liste d'activités
        DB = GestionDB.DB()
        req = """
                SELECT types_groupes_activites.IDtype_groupe_activite, types_groupes_activites.nom
                FROM (activites
                      INNER JOIN groupes_activites ON activites.IDactivite = groupes_activites.IDactivite)
                INNER JOIN types_groupes_activites ON groupes_activites.IDtype_groupe_activite = types_groupes_activites.IDtype_groupe_activite
                %s
                GROUP BY types_groupes_activites.IDtype_groupe_activite, types_groupes_activites.nom
                ORDER BY types_groupes_activites.nom;
                """ % conditionWhere
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        DB.Close()
        lstDonnees, lstID = [], []
        for (IDgroupe, nomGroupe) in recordset:
            lstDonnees.append(nomGroupe)
            lstID.append(IDgroupe)
        return lstDonnees, lstID

    # Activités à afficher selon des groupes retenus
    def GetActivites(self, lstGroupesChecked):
        recordset = ()
        if len(lstGroupesChecked) > 0:
            req = """
                    SELECT activites.IDactivite, activites.nom
                    FROM (groupes_activites
                          INNER JOIN activites ON groupes_activites.IDactivite = activites.IDactivite)
                    WHERE (groupes_activites.IDtype_groupe_activite IN ( %s ))
                    AND (activites.IDactivite IN ( %s))
                    ORDER BY IDactivite;
                    """ % (str(lstGroupesChecked)[1:-1],str(self.lstIDactivitesPossibles)[1:-1])
            DB = GestionDB.DB()
            DB.ExecuterReq(req, MsgBox="CTRL_SelectionActivitesModal.GetIDactivitePossible")
            recordset = DB.ResultatReq()
            DB.Close()
        lstDonnees, lstID = [], []
        for (ID, nom) in recordset:
            lstDonnees.append(nom)
            lstID.append(ID)
        return lstDonnees, lstID

class ACheckListBox(wx.CheckListBox):
    def __init__(self, parent, *args, **kwargs):
        wx.CheckListBox.__init__(self, parent, -1, size = (50,50))
        self.parent = parent
        self.__initDonnees()
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def __initDonnees(self):
        self.listeDonnees = []
        self.listeID = []

    def Importation(self):
        ValueError("méthode Importation obligatoire dans l'instance")
        #self.listeDonnees, self.listeID = ([],[])

    def MAJ_CheckListBox(self,oldIDcheck, oldID):
        # Affiche les lignes et Coche selon l'historique 
        self.Clear()
        for item in self.listeDonnees :
            self.Append(item)
        #reprise des check
        for index in range(0, len(self.listeDonnees)):
            ID = self.listeID[index]
            if (ID in oldID) and (ID in oldIDcheck):
                self.Check(index, check=True)
            elif (ID in oldID) and not(ID in oldIDcheck):
                self.Check(index,check = False)
            else:
                self.Check(index,check = False)

    def MAJ(self):
        oldIDcheck = [self.listeID[ix] for ix in self.GetCheckedItems()]
        oldID = [x for x in self.listeID]
        self.Importation()
        self.MAJ_CheckListBox(oldIDcheck, oldID)

    def CocheTout(self,coche):
        for index in range(0, len(self.listeDonnees)):
            self.Check(index,check = coche)
            index += 1
        if coche:
            self.listeChecked = []
        else:
            self.listeUnChecked = []
        self.OnCheck(coche)

    def CocheIDliste(self,liste):
        for index in range(0, len(self.listeID)):
            item = self.listeID[index]
            if item in liste:
                check = True
            else : check = False
            self.Check(index,check = check)
            index += 1
        self.listeChecked, self.listeUnChecked = self.GetNewChecked(self.listeChecked,self.listeUnChecked)

    def CocheListe(self,liste):
        for index in range(0, len(liste)):
            item = liste[index]
            if item in self.listeDonnees:
                check = True
            else : check = False
            self.Check(index,check = check)
            index += 1
        self.OnCheck(liste)

    def OnCheck(self, event):
        pass

    def GetListeChecked(self):
        return self.GetCheckedStrings()

    def GetListeIDchecked(self):
        return [ self.listeID[ix] for ix in self.GetCheckedItems()]

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
        if self.URL == "tout": self.parent.CocheTout(True)
        if self.URL == "rien": self.parent.CocheTout(False)
        self.UpdateLink()

class CocheToutRien(wx.Panel):
    def __init__(self, parent,IDparent):
        self.parent = parent
        self.IDparent = IDparent
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.hyper_tout = Hyperlien(self, label="Cocher", infobulle="Cliquez ici pour tout cocher",
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label="Décocher", infobulle="Cliquez ici pour tout décocher",
                                    URL="rien")
        fgSizer_cocher = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        fgSizer_cocher.Add(self.hyper_tout, 0, wx.TOP, 10)
        fgSizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        self.SetSizer(fgSizer_cocher)
        fgSizer_cocher.Fit(self)

    def CocheTout(self,bool):
        self.parent.CocheTout(bool,self.IDparent)

# -------------------------------------------------------------------------------------

class CTRL_GroupesActivite(ACheckListBox):
    def __init__(self, parent,periode):
        ACheckListBox.__init__(self, parent, -1)
        self.periode = periode
        self.nomCtrl = "Grp d'activité"
        self.Adapt = self.parent.Adapt

    def Importation(self):
        self.listeDonnees, self.listeID =self.Adapt.GetGroupes()

    def OnCheck(self, event):
        self.parent.OnCheckGroupe()

    def GetGroupes(self):
        return self.GetListeIDchecked()

class CTRL_Activites(ACheckListBox):
    def __init__(self, parent,periode):
        ACheckListBox.__init__(self, parent, -1)
        self.periode = periode
        self.lstGroupes = []
        self.nomCtrl = "Activité"
        self.Adapt = parent.Adapt

    def Importation(self):
        self.listeDonnees, self.listeID = self.Adapt.GetActivites(self.lstGroupes)

    def SetGroupes(self, lstGroupes):
        self.lstGroupes = lstGroupes

    def GetActivites(self):
        return self.GetListeChecked()

# Panel Pilote pour le choix des  activités par les groupes d'activité -------------------
class CTRL_SelectionActivites(wx.Panel):
    def __init__(self, parent, periode):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_SelectionActivites", style=wx.TAB_TRAVERSAL)
        if not periode:
            self.periode = [datetime.date.today() - datetime.timedelta(29),
                            datetime.date.today()]
        else: self.periode = periode
        self.lstIDactivitePossibles = []
        self.Adapt = Adapt(self,self.periode)
        self.__init_layout()
        self.parent = parent
        self.Init(self.periode)

    def __init_layout(self):
        self.baseStaticBox = wx.StaticBox(self, -1, self.Adapt.GetTitleBox())
        # Période
        self.ctrl_periode = CTRL_Saisie_date.Periode(self,self.periode,flexGridParams=(1,4,2,10))
        # Groupes d'activités
        self.box_groupes_activites_staticbox = wx.StaticBox(self, -1, "Groupes d'activités")
        self.ctrl_groupesActivite = CTRL_GroupesActivite(self, self.periode)
        self.ctrl_groupesActivite.SetMinSize((50, 50))
        self.ctrl_coche_grpAct = CocheToutRien(self, "grpAct")
        self.ctrl_coche_act = CocheToutRien(self, "act")
        # Activités
        self.box_activites_staticbox = wx.StaticBox(self, -1, "Activités")
        self.ctrl_activites = CTRL_Activites(self,self.periode)
        self.ctrl_activites.SetMinSize((50, 50))

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.ctrl_groupesActivite.SetToolTip("Cochez des groupes pour présélectionner les activités")
        self.ctrl_activites.SetToolTip("Cochez les activités des groupes d'activités")
        self.ctrl_periode.ctrl_date_debut.bouton_calendrier.SetToolTip("Cliquez ici pour saisir une date de début")
        self.ctrl_periode.ctrl_date_fin.bouton_calendrier.SetToolTip("Cliquez ici pour saisir une date de fin")
        self.ctrl_groupesActivite.MAJ()
        self.ctrl_activites.MAJ()

    def __do_layout(self):
        fgSizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=5)
        box_base = wx.StaticBoxSizer(self.baseStaticBox, wx.VERTICAL)

                     # Période
        box_base.Add(self.ctrl_periode, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        # Groupes d'activité
        box_grpactiv = wx.StaticBoxSizer(self.box_groupes_activites_staticbox, wx.HORIZONTAL)
        box_grpactiv.Add(self.ctrl_groupesActivite, 1, wx.ALL | wx.EXPAND, 5)
        box_grpactiv.Add(self.ctrl_coche_grpAct, 0, wx.ALL, 0)
        box_base.Add(box_grpactiv, 1, wx.LEFT | wx.EXPAND, 15)

        # Activité
        box_activite = wx.StaticBoxSizer(self.box_activites_staticbox, wx.HORIZONTAL)
        box_activite.Add(self.ctrl_activites, 1, wx.ALL | wx.EXPAND, 5)
        box_activite.Add(self.ctrl_coche_act, 0, wx.ALL, 0)
        box_base.Add(box_activite, 2, wx.LEFT | wx.EXPAND, 15)

        fgSizer_base.Add((10,20), 1,0,0)
        fgSizer_base.Add(box_base, 1, wx.TOP| wx.LEFT| wx.RIGHT | wx.EXPAND, 5)
        fgSizer_base.AddGrowableRow(1)
        fgSizer_base.AddGrowableCol(0)

        self.SetSizer(fgSizer_base)
        #fgSizer_base.Fit(self)

    def Init(self,periode):
        self.Adapt.SetPeriode(periode)
        self.Adapt.GetIDactivitePossibles()

        self.ctrl_groupesActivite.MAJ()
        self.ctrl_activites.SetGroupes(self.ctrl_groupesActivite.GetGroupes())
        self.ctrl_activites.MAJ()

    def CocheTout(self, bool, ID):
        if ID == "grpAct":
            self.ctrl_groupesActivite.CocheTout(bool)
        if ID == "act":
            self.ctrl_activites.CocheTout(bool)

    # fonctions appelées par un enfant
    def OnChoixDate(self):
        if self.periode != self.ctrl_periode.GetPeriode():
            self.Init(self.ctrl_periode.GetPeriode())
            if hasattr(self.parent,'OnChoixDate'):
                self.parent.OnChoixDate()

    def OnCheckGroupe(self):
        groupes = self.ctrl_groupesActivite.GetGroupes()
        self.ctrl_activites.SetGroupes(groupes)
        self.ctrl_activites.MAJ()
        
    # fonctions appelées par le parent
    def Validation(self):
        """ Vérifie que des données ont été sélectionnées """
        if  len(self.GetActivites()) == 0:
            dlg = wx.MessageDialog(self, "Vous n'avez sélectionné aucune activité !", "Erreur de saisie",
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True

    def GetActivites(self):
        return self.ctrl_activites.GetListeIDchecked()

    def GetPeriode(self):
        return (self.ctrl_date_debut.GetDate(),self.ctrl_date_fin.GetDate())
    # fin CTRL

# Dialog complet avec boutons de confirmation ------------------------------------------
class DLG_SelectionActivites(wx.Dialog):
    def __init__(self, parent, periode=None, minSize=(100, 600),**kwd):
        self.parent = parent
        style = kwd.pop('style',
                    wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, parent, -1, style=style)
        title = kwd.pop('title', "MultiChoix d'activité")
        self.periode = periode
        if not self.periode:
            self.periode = [datetime.date.today()-datetime.timedelta(29),
                            datetime.date.today()]
        self.SetTitle(title)
        self.SetMinSize(minSize)

        # Panel période, groupes d'activités, activités
        self.ctrl = CTRL_SelectionActivites(self,self.periode)
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider",
                                                cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.bouton_ok.SetToolTip("Cliquez ici pour valider le choix de la liste")
        self.SetMinSize((300, 570))

    def __do_layout(self):
        fgSizer_ = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=10)
        fgSizer_.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 0)
        fgSizer_.Add(self.bouton_ok, 1, wx.RIGHT | wx.BOTTOM| wx.ALIGN_RIGHT, 5)
        fgSizer_.AddGrowableRow(0)
        fgSizer_.AddGrowableCol(0)

        self.SetSizer(fgSizer_)
        fgSizer_.Fit(self)
        self.Layout()
        self.CenterOnScreen()
        # fin Dialog

    def OnBoutonOk(self, evt):
        if self.ctrl.Validation() == False:
            return
        self.EndModal(wx.ID_OK)

    def GetActivites(self):
        return self.ctrl.GetActivites()

    def GetPeriode(self):
        return self.ctrl.GetPeriode()

# Large bouton appelant le dlg.showmodal(), son label affiche le nombre d'activités
class CTRL_BoutonSelectionActivites(wx.Panel):
    def __init__(self,parent,*args, **kwds):
        value = kwds.pop("value","")
        wx.Panel.__init__(self,parent, *args, **kwds)
        self.parent = parent
        self.periode = None
        self.ctrl = wx.TextCtrl(self,value=value)
        self.ctrl.SetMinSize((250,30))
        self.btn = CTRL_Bouton_image.CTRL(self,
                                          texte="Activites",
                                          cheminImage=Chemins.GetStaticPath("Images/16x16/Loupe_et_menu.png"),
                                          tailleImage=(25,16),
                                          margesImage=(0,0,0,0),
                                          positionImage=wx.RIGHT,
                                          margesTexte=(0,0),
                                          )
        self.btn.SetMinSize((85,30))
        self.btn.Bind(wx.EVT_BUTTON,self.OnActivate)
        sizer = wx.FlexGridSizer(1, 2, 1, 1)
        sizer.Add(self.ctrl, 1, wx.LEFT | wx.EXPAND, 10)
        sizer.Add(self.btn, 0,wx.RIGHT, 10)
        self.SetSizerAndFit(sizer)
        sizer.AddGrowableCol(0)
        self.Layout()

    def SetPeriode(self,periode):
        self.periode = periode

    def OnActivate(self,evt):
        dlgAttente = PBI.PyBusyInfo("Recherche des activités...",
                                    parent=None, title="Veuillez patienter...",
                                    icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        dlg = DLG_SelectionActivites(self, periode= self.periode)
        del dlgAttente
        retour = dlg.ShowModal()
        if retour == wx.ID_OK:
            self.ctrl.SetValue(str(dlg.GetActivites())[1:-1])
        dlg.Destroy()


# Pour test ----------------------------------------------------------------------------
class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.panel = panel

        self.panel.ctrl = CTRL_BoutonSelectionActivites(panel, value="ctrl")
        self.panel.ctrl2 = wx.TextCtrl(panel,value="ctrl2")
        self.panel.ctrl3 = wx.TextCtrl(panel,value="ctrl3")
        self.panel.ctrl.SetPeriode((datetime.date(2023,7,1),datetime.date(2023,10,11)))

        bxSizer_1 = wx.BoxSizer(wx.VERTICAL)
        bxSizer_1.Add(self.panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(bxSizer_1)

        bxSizer_2 = wx.BoxSizer(wx.VERTICAL)
        bxSizer_2.Add(self.panel.ctrl, 1,wx.ALL|wx.EXPAND)
        bxSizer_2.Add(self.panel.ctrl2,  )
        bxSizer_2.Add(self.panel.ctrl3, 1, wx.ALL|wx.EXPAND)
        panel.SetSizer(bxSizer_2)

        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = DLG_SelectionActivites(None)
    print(frame_1.ShowModal())
    #app.SetTopWindow(frame_1)
    #frame_1 = MyFrame(None, -1, "TEST", size=(500, 700))
    #print('retour frame',frame_1.Show())
    app.MainLoop()

