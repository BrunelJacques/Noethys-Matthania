#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------
from Utils.UTILS_Traduction import _
import wx
import GestionDB
import wx.lib.agw.customtreectrl as CT
from datetime import date
from UTILS_Dates import DateDDEnDateEng, DateEngEnDateDD

def WhereDates(periode):
    deb_per, fin_per = periode
    filtre = ""
    if deb_per:
        deb_per = DateDDEnDateEng(deb_per)
        filtre += " ((activites.date_fin >= '%s') or (activites.date_debut >= '%s'))" % (deb_per, deb_per)
    if fin_per:
        if filtre != "":
            filtre += " AND "
        fin_per = DateDDEnDateEng(fin_per)
        filtre += " ((activites.date_fin <= '%s') or (activites.date_debut <= '%s'))" % (fin_per, fin_per)
    if filtre != "":
        filtre = "WHERE ( %s )"%filtre
    return filtre

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Groupes_activites(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.dictDonnees = {}
        self.dictIndex = {}
        self.periode = (None,None)
        self.lstDonnees = self.Importation()
        if self.lstDonnees == None : 
            self.lstDonnees = []
        self.MAJ()
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)
        
    def MAJ(self):
        lstIDcoches = self.GetIDcoches()
        self.lstDonnees = self.Importation()
        self.Clear()
        self.dictIndex = {}
        if self.lstDonnees == [] : return
        self.lstDonnees.sort()
        index = 0
        for nomGrpAct, IDtype_groupe_activite in self.lstDonnees :
            if nomGrpAct == None :
                nomGrpAct = _("Groupe inconnu !")
            self.Append(nomGrpAct) 
            self.dictIndex[index] = IDtype_groupe_activite
            index += 1
        self.SetIDcoches(lstIDcoches)

    def Importation(self):
        if self.periode == (None,None):
            return []
        whereDate = WhereDates(self.periode)
        DB = GestionDB.DB()
        req = """
        SELECT IDgroupe_activite, groupes_activites.IDactivite, activites.nom, 
            types_groupes_activites.nom, groupes_activites.IDtype_groupe_activite            
        FROM (groupes_activites
        LEFT JOIN types_groupes_activites ON types_groupes_activites.IDtype_groupe_activite = groupes_activites.IDtype_groupe_activite)
        LEFT JOIN activites ON activites.IDactivite = groupes_activites.IDactivite
        %s
        ORDER BY types_groupes_activites.nom;"""%whereDate
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        lstGrpAct = DB.ResultatReq()
        DB.Close()
        if len(lstGrpAct) == 0 : return []
        lstDonnees = []
        self.dictDonnees = {}
        for IDgroupe_activite, IDactivite, nomActivite, nomGrpAct, IDGrpAct in lstGrpAct :
            listeTemp = (nomGrpAct, IDGrpAct)
            if listeTemp not in lstDonnees : 
                lstDonnees.append(listeTemp)
            if (IDGrpAct in self.dictDonnees) == False :
                self.dictDonnees[IDGrpAct] = []
            self.dictDonnees[IDGrpAct].append(IDactivite)    
        return lstDonnees

    def ImportePeriode(self,lstIDact):
        DB = GestionDB.DB()
        req = """
            SELECT activites.date_debut,activites.date_fin
            FROM activites
            WHERE activites.ID in ( %s )
            ;"""%",".join(lstIDact)
        DB.ExecuterReq(req,MsgBox="ImporterPeriode")
        recordset = DB.ResultatReq()
        DB.Close()
        if len(recordset) == 0 : return (date.today(),date.today())
        debut = "9999-99-99"
        fin = "0000-00-00"
        for actdebut, actfin in recordset:
            if actdebut < debut:
                debut = actdebut
            if actfin > fin:
                fin = actfin
        return (DateEngEnDateDD(debut),DateDDEnDateEng(fin))

    def GetIDcoches(self):
        lstIDcoches = []
        NbreItems = len(self.lstDonnees)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                IDtype_groupe_activite = self.dictIndex[index]
                lstIDcoches.append(IDtype_groupe_activite)
        lstIDcoches.sort() 
        return lstIDcoches

    def SetIDcoches(self, lstIDcoches=[]):
        for index in range(0, len(self.lstDonnees)):
            ID = self.dictIndex[index]
            if ID in lstIDcoches :
                self.Check(index)
            index += 1
        self.OnCheck()

    def CocheTout(self):
        index = 0
        for index in range(0, len(self.lstDonnees)):
            self.Check(index)
            index += 1

    def SetPeriode(self,periode):
        if self.periode != periode:
            self.periode = periode
            self.MAJ()

    def SetPeriodeByActivites(self, lstIDact):
        self.periode = self.ImportePeriode(lstIDact)
        self.MAJ()

    def OnCheck(self, event=None):
        self.parent.OnCheckGrpAct()
    
    def GetLabelsGroupes(self):
        """ Renvoie les labels des groupes d'activités sélectionnés """
        listeLabels = []
        index = 0
        for nomGroupe, IDtype_groupe_activite in self.lstDonnees :
            if self.IsChecked(index):
                listeLabels.append(nomGroupe)
            index += 1
        return listeLabels

class CTRL_Activites(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SIMPLE_BORDER):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.root = self.AddRoot(_("Racine"))
        self.SetBackgroundColour(wx.WHITE)
        self.SetAGWWindowStyleFlag(
            wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT)  # CT.TR_AUTO_CHECK_CHILD
        self.EnableSelectionVista(True)
        self.dictItems = {}
        self.lstDonnees = []
        self.lstGrpAct = []
        self.works = False
        self.oldActivites = []
        self.lstActivites = []
        self.dictActivites={}
        self.dictGroupes={}
        self.periode = (None,None)

        # Binds
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnCheck)

    def MAJ(self):
        oldActivites = [x for x in self.lstDonnees]
        self.lstDonnees = self.Importation()
        if oldActivites == [x for x in self.lstDonnees]:
            return
        oldCoches = self.GetGroupes()
        self.DeleteAllItems()
        self.root = self.AddRoot(_("Données"))
        self.dictItems = {}
        # Préparation des données
        dictDonnees = {}
        for IDgroupe, nomGroupe, ordreGroupe, IDactivite, nomActivite, dateFinActivite in self.lstDonnees:
            if (IDactivite in dictDonnees) == False:
                dictDonnees[IDactivite] = {"nom": nomActivite, "IDactivite": IDactivite,
                                           "dateFinActivite": dateFinActivite,
                                           "groupes": []}
            dictDonnees[IDactivite]["groupes"].append((ordreGroupe, IDgroupe, nomGroupe))
            self.dictActivites[IDactivite] = nomActivite
            self.dictGroupes[IDgroupe] = {"nom":nomGroupe,"IDactivite":IDactivite}

        # Tri des noms des activités par ordre alpha
        lstActivites = []
        for IDactivite, dictActivite in dictDonnees.items():
            lstActivites.append((dictActivite["dateFinActivite"], IDactivite))
        lstActivites.sort(reverse=True)

        # Remplissage
        for dateFinActivite, IDactivite in lstActivites:
            # Branche activité
            dictActivite = dictDonnees[IDactivite]
            nomActivite = dictActivite["nom"]
            if nomActivite == None: nomActivite = "Activité inconnue"
            brancheActivite = self.AppendItem(self.root, nomActivite, ct_type=1)
            dictData = {"type": "activite", "IDactivite": IDactivite, "nom": nomActivite}
            self.SetPyData(brancheActivite, dictData)
            ##            self.SetItemBold(brancheActivite)
            self.dictItems[brancheActivite] = dictData

            # Branches groupes
            listeGroupes = dictActivite["groupes"]
            listeGroupes.sort()

            for ordregroupe, IDgroupe, nomgroupe in listeGroupes:
                branchegroupe = self.AppendItem(brancheActivite, nomgroupe, ct_type=1)
                dictData = {"type": "groupe", "IDgroupe": IDgroupe, "nom": nomgroupe}
                self.SetPyData(branchegroupe, dictData)
                self.dictItems[branchegroupe] = dictData

            self.EnableChildren(brancheActivite, False)

        self.EnableChildren(self.root, True)
        self.SetCochesGroupes(oldCoches)
        self.lstActivites = [y for (x,y) in lstActivites]
        self.parent.OnChangeActivites()

    def Importation(self):
        if self.lstGrpAct == []:
            return []
        if self.periode != (None,None):
            whereDate = WhereDates(self.periode)
            whereDate += " AND "
        else: whereDate = "WHERE "
        where = whereDate + "(groupes_activites.IDtype_groupe_activite IN (%s))"%str(self.lstGrpAct)[1:-1]
        DB = GestionDB.DB()
        req = """
            SELECT groupes.IDgroupe, groupes.nom, groupes.ordre, activites.IDactivite, 
                    activites.nom, activites.date_fin
            FROM (activites 
            LEFT JOIN groupes_activites ON activites.IDactivite = groupes_activites.IDactivite) 
            INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite
            %s
            GROUP BY groupes.IDgroupe, groupes.nom, groupes.ordre, activites.IDactivite, 
                    activites.nom, activites.date_fin
            ORDER BY activites.date_fin DESC;"""%where
        ret = DB.ExecuterReq(req)
        listeGroupes = []
        if ret == 'ok':
            listeGroupes = DB.ResultatReq()
        DB.Close()
        return listeGroupes

    def SetGrpAct(self,lstGrpAct):
        if lstGrpAct == self.lstGrpAct:
            return
        self.lstGrpAct = lstGrpAct
        self.MAJ()
        self.OnCheck()

    def GetDictActivites(self):
        return self.dictActivites

    def GetDictGroupes(self):
        return self.dictGroupes

    def SetPeriode(self,periode):
        if self.periode != periode:
            self.periode = periode
            self.MAJ()

    def OnCheck(self, event=None):
        if self.works == True:
            return
        if event:
            item = event.GetItem()
            self.Coche(item=item)
        self.parent.OnCheckActivite()

    def Coche(self, item=None, etat=None):
        self.works = True
        """ Coche ou décoche un item """
        dictData = self.GetItemPyData(item)
        itemParent = self.GetItemParent(item)

        if etat != None:
            self.CheckItem(item, etat)

        if dictData["type"] == "activite":
            if self.IsItemChecked(item):
                self.EnableChildren(item, True)
                if self.works == False:
                    self.CheckChilds(item, True)
            else:
                self.EnableChildren(item, False)
                self.CheckChilds(item, False)

        if dictData["type"] == "groupe":
            if self.IsItemChecked(item):
                self.CheckItem(itemParent, True)
            else:
                listeCoches = self.GetCochesItem(itemParent)
                if len(listeCoches) == 0:
                    self.CheckItem(itemParent, False)
        self.works = False
        self.OnCheck()

    def GetCochesItem(self, item=None):
        """ Renvoie la liste des sous items cochés d'un item parent """
        listeItems = []
        itemTemp, cookie = self.GetFirstChild(item)
        for index in range(0, self.GetChildrenCount(item, recursively=False)):
            if self.IsItemChecked(itemTemp):
                dictData = self.GetPyData(itemTemp)
                listeItems.append(dictData)
            itemTemp, cookie = self.GetNextChild(item, cookie)
        return listeItems

    def GetToutesActivites(self):
        """ Renvoie la liste des activites affichées """
        return self.lstActivites

    def GetActivites(self):
        """ Renvoie la liste des activites cochés """
        lstActivites = []
        for item, dictData in self.dictItems.items():
            if self.IsItemEnabled(item) and self.IsItemChecked(item) and dictData[
                "type"] == "activite":
                lstActivites.append(dictData["IDactivite"])
        lstActivites.sort()
        return lstActivites

    def GetGroupes(self):
        """ Renvoie la liste des groupes cochés """
        listeGroupes = []
        for item, dictData in self.dictItems.items():
            if self.IsItemEnabled(item) and self.IsItemChecked(item) and dictData[
                "type"] == "groupe":
                listeGroupes.append(dictData["IDgroupe"])
        if len(listeGroupes) == 0:
            # pas de choix == tous
            for item, dictData in self.dictItems.items():
                if dictData["type"] == "groupe":
                    listeGroupes.append(dictData["IDgroupe"])
        listeGroupes.sort()
        return listeGroupes

    def SetCochesGroupes(self, listeGroupes=[]):
        if listeGroupes == []:
            return
        """ Coche les groupes donnés """
        self.works = True
        for item, dictData in self.dictItems.items():
            if dictData["type"] == "groupe":
                if dictData["IDgroupe"] in listeGroupes:
                    self.Coche(item, etat=True)
                else:
                    self.Coche(item, etat=False)
        self.works = False

    def SetCochesActivites(self, lstActivites=[]):
        """ Coche les activités """
        for item, dictData in self.dictItems.items():
            if dictData["type"] == "activite":
                if dictData["IDactivite"] in lstActivites:
                    self.Coche(item, etat=True)
                else:
                    self.Coche(item, etat=False)

class CTRL_Tarifs(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.dict_tarifs_groupes = {}
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)
        self.lstDonnees = []
        self.works = False
        self.periode = (None,None)
        self.lstActivites = []

    def MAJ(self):
        # génère self.dict_tarifs_groupes
        lstIDcoches = self.GetIDcoches()
        self.lstDonnees = self.Importation()
        self.Clear()
        self.dictIndex = {}
        if self.lstDonnees == [] : return
        self.lstDonnees.sort()
        index = 0
        for nomTarif,IDtarif in self.lstDonnees :
            if nomTarif == None or len(nomTarif)==0 :
                nomTarif = _("Tarif inconnu !")
            self.Append(nomTarif)
            self.dictIndex[index] = IDtarif
            index += 1
        if len(lstIDcoches) > 0:
            self.SetIDcoches(lstIDcoches)
        else:
            self.CocheTout()

    def Importation(self):
        if self.lstActivites == []:
            return []
        if self.periode != (None,None):
            whereDate = WhereDates(self.periode)
        else:
            whereDate = ""
        if whereDate == "":
            whereDate += "WHERE 1=1 "
        where = whereDate + "AND (activites.IDactivite IN (%s))"%str(self.lstActivites)[1:-1]

        DB = GestionDB.DB()
        # Récupère tous les ID groupes associés à un nom de catégorie tarif sur période
        req = """
            SELECT categories_tarifs.nom, matTarifs.trfIDcategorie_tarif, matTarifs.trfIDgroupe
            FROM (activites 
            LEFT JOIN matTarifs ON activites.IDactivite = matTarifs.trfIDactivite) 
            LEFT JOIN categories_tarifs ON matTarifs.trfIDcategorie_tarif = categories_tarifs.IDcategorie_tarif
            %s
            GROUP BY categories_tarifs.nom, matTarifs.trfIDcategorie_tarif, matTarifs.trfIDgroupe;
            ;"""% where
        DB.ExecuterReq(req, MsgBox="CTRL_Tarifs.Importation")
        recordset = DB.ResultatReq()
        DB.Close()
        self.dict_tarifs_groupes = {}
        lstDonnees = []
        for nomTarif, IDtarif, IDgroupe in recordset:
            if not IDtarif in self.dict_tarifs_groupes:
                self.dict_tarifs_groupes[IDtarif]=[]
                if not (nomTarif,IDtarif) in lstDonnees:
                    lstDonnees.append((nomTarif, IDtarif))
            self.dict_tarifs_groupes[IDtarif].append(IDgroupe)
        return lstDonnees

    def GetIDcoches(self):
        lstIDcoches = []
        NbreItems = len(self.lstDonnees)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                IDtype_groupe_activite = self.dictIndex[index]
                lstIDcoches.append(IDtype_groupe_activite)
        lstIDcoches.sort()
        return lstIDcoches

    def SetIDcoches(self, lstIDcoches=[]):
        self.works = True
        for index in range(0, len(self.lstDonnees)):
            ID = self.dictIndex[index]
            if ID in lstIDcoches :
                self.Check(index)
            index += 1
        self.works = False
        self.OnCheck()

    def CocheTout(self):
        self.works = True
        for index in range(0, len(self.lstDonnees)):
            self.Check(index)
            index += 1
        self.works = False

    def SetPeriode(self,periode):
        if self.periode != periode:
            self.periode = periode
            self.MAJ()

    def OnCheck(self, event=None):
        if self.works:
            return
        self.parent.OnCheckTarif()

    def SetActivites(self, lstActivites=[]):
        self.lstActivites = lstActivites
        self.MAJ()

    def GetGroupes(self):
        lstGroupes = []
        tarifsCoches = self.GetIDcoches()
        for ID in tarifsCoches:
            lstGroupes += self.dict_tarifs_groupes[ID]
        return lstGroupes

# ----------------------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, modeGroupes=True,
                 periode=(date.today(),date.today())):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        # Le mode groupe se limite à l'apparition ou non du filtre tarif
        self.parent = parent
        self.modeGroupes = modeGroupes
        self.periode = periode

        # Contrôles
        self.groupes_activites_staticbox = wx.StaticBox(self, -1, _("Types d'activités"))
        self.ctrl_groupes_activites = CTRL_Groupes_activites(self)
        self.ctrl_groupes_activites.SetMinSize((100, 30))

        self.activites_staticbox = wx.StaticBox(self, -1, _("Activités et groupes"))
        self.ctrl_activites = CTRL_Activites(self)
        self.ctrl_activites.SetMinSize((100, 60))

        self.tarifs_staticbox = wx.StaticBox(self, -1, _("Cocher les groupes par tarif"))
        self.ctrl_tarifs= CTRL_Tarifs(self)
        self.ctrl_tarifs.SetMinSize((100, 30))

        if self.modeGroupes == False:
            self.ctrl_tarifs.Show(False)
            self.tarifs_staticbox.Show(False)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=7, cols=1, vgap=3, hgap=5)

        box_grpactiv = wx.StaticBoxSizer(self.groupes_activites_staticbox,wx.VERTICAL)
        box_grpactiv.Add(self.ctrl_groupes_activites,proportion=1,flag=wx.LEFT|wx.EXPAND,border=6)
        grid_sizer_base.Add(box_grpactiv,proportion=1,flag=wx.LEFT|wx.TOP|wx.EXPAND,border=3)
        grid_sizer_base.Add((1, 1), 0, wx.LEFT|wx.EXPAND, 0)

        box_activ = wx.StaticBoxSizer(self.activites_staticbox,wx.VERTICAL)
        box_activ.Add(self.ctrl_activites, proportion=50,flag=wx.LEFT|wx.EXPAND,border=6)
        grid_sizer_base.Add(box_activ,proportion=50,flag=wx.LEFT|wx.EXPAND,border=3)
        grid_sizer_base.Add((1, 1), 0, wx.LEFT | wx.EXPAND, 0)

        box_tarifs = wx.StaticBoxSizer(self.tarifs_staticbox,wx.VERTICAL)
        box_tarifs.Add(self.ctrl_tarifs, 10, wx.LEFT|wx.EXPAND, 6)
        grid_sizer_base.Add(box_tarifs, 10, wx.LEFT|wx.EXPAND,3)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableRow(4)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

        # Init Contrôles
        self.SetPeriode(self.periode)

    def Validation(self):
        """ Vérifie que des données ont été sélectionnées """
        if len(self.GetActivites()) == 0 :
            dlg = wx.MessageDialog(self, "Vous n'avez sélectionné aucune activité !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True

    def SetPeriode(self, periode):
        self.periode = periode
        self.ctrl_tarifs.SetPeriode(periode)
        self.ctrl_activites.SetPeriode(periode)
        self.ctrl_groupes_activites.SetPeriode(periode)
        self.ctrl_groupes_activites.MAJ()

    def SetActivites(self, lstActivites=[]):
        self.ctrl_activites.SetActivites(lstActivites)
        if self.modeGroupes:
            self.ctrl_tarifs.SetActivites(lstActivites)

    def GetActivites(self):
        """ Retourne la liste des IDactivité sélectionnés """
        # Vérifie les activités sélectionnées
        lstActivites = self.ctrl_activites.GetActivites()
        return lstActivites

    def SetTarifs(self, listActivites):
        self.ctrl_tarifs.SetTarifs(listActivites)

    def SetGroupes(self, listeGroupes=[]):
        self.ctrl_tarifs.SetGroupes(listeGroupes)

    def GetGroupes(self):
        listeGroupes = self.ctrl_activites.GetGroupes()
        return listeGroupes
        
    def GetDictActivites(self):
        dictActivites = self.ctrl_activites.GetDictActivites()
        return dictActivites

    def GetDictGroupes(self):
        dictGroupes = self.ctrl_activites.GetDictGroupes()
        return dictGroupes

    def OnCheckGrpAct(self):
        # déclenche une MAJ en cascade
        self.ctrl_activites.SetGrpAct(self.ctrl_groupes_activites.GetIDcoches())

    def OnCheckActivite(self):
        try :
            self.parent.OnCheckActivites()
        except :
            pass

    def OnCheckTarif(self):
        self.ctrl_activites.SetCochesGroupes(self.ctrl_tarifs.GetGroupes())

    def OnChangeActivites(self):
        if self.modeGroupes:
            self.ctrl_tarifs.SetActivites(self.ctrl_activites.GetToutesActivites())
        
    def GetLabelActivites(self):
        """ Renvoie les labels des groupes ou activités sélectionnées """

        # Activités
        listeTemp = []
        dictActivites = self.GetDictActivites()
        for IDactivite in self.GetActivites()  :
            listeTemp.append(dictActivites[IDactivite])
        return listeTemp

    def GetValeurs(self):
        """ Retourne les valeurs sélectionnées """
        listeID = self.ctrl_activites.GetIDcoches()
        return "activites", listeID
    
    def SetValeurs(self, mode="", listeID=[]):
        self.ctrl_groupes_activites.SetPeriodeByActivites(listeID)

# ----------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        bouton_test = wx.Button(panel, -1, "Test")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL(panel, modeGroupes=True)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetMinSize((150, 200))
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton, bouton_test) 
        
    def OnBouton(self, event):
        print(self.ctrl.GetActivites())
        print(self.ctrl.GetGroupes())
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()