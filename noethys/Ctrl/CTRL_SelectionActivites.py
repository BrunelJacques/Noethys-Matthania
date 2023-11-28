#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    évolutions Matthania, selection des activités en vue de listes
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

# Version à factoriser avec CTRL_SelectionActivitesModal conçu adaptable par classe ADAPT

import wx
import Chemins
import datetime
from Ctrl import CTRL_Bouton_image
import wx.lib.agw.pybusyinfo as PBI
import GestionDB
from Ctrl import CTRL_Saisie_date
from Dlg import DLG_calendrier_simple
import wx.lib.agw.hyperlink as Hyperlink

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateEngSQL(textDate):
    text = str(textDate[6:10]) + "-" + str(textDate[3:5]) + "-" +str(textDate[0:2])
    return text

def ConditionDateSql(self):
    # toutes les activités de la période du parent seront appelées
    condDates = ""
    if hasattr(self,"parent"):
        if hasattr(self.parent,"ctrl_date_debut"):
            dateDeb = DateEngSQL(self.parent.ctrl_date_debut.Value)
            dateFin = DateEngSQL(self.parent.ctrl_date_fin.Value)
        condDates = " activites.date_fin >= '%s' And activites.date_fin <= '%s' " % (
                    dateDeb, dateFin)
    return condDates

def GetStaticBox(self):
    return wx.StaticBox(self, -1, "Activités se terminant dans la période")

class ACheckListBox(wx.CheckListBox):
    def __init__(self, parent, *args, **kwargs):
        wx.CheckListBox.__init__(self, parent, -1, size = (50,50))
        self.parent = parent
        self.dictDonnees = {}
        self.listeDonnees = []
        self.listeChecked = []
        self.listeUnChecked = []
        self.listeID = []
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def MajCheck(self):
        # Coche les lignes selon l'historique actualisé par Modified
        self.Clear()
        for item in self.listeDonnees :
            self.Append(item)
        #reprise des check
        for index in range(0, len(self.listeDonnees)):
            item = self.listeDonnees[index]
            if item in self.listeChecked:
                self.Check(index, check=True)
            elif item in self.listeUnChecked:
                self.Check(index,check = False)
            else:
                self.Check(index,check = True)

    def MAJ(self):
        self.Importation()
        self.MajCheck()

    def StockDonnees(self,recordset,nomlien="lstIDlien"):
        # Met à jour le dictionnaire de données après une requête d'importation
        self.dictDonnees = {}
        self.listeDonnees = []
        for ID, nom, IDlien in recordset:
            if ID != None :
                if nom not in self.dictDonnees: self.dictDonnees[nom] = {}
                if "lstID" not in self.dictDonnees[nom]:
                    self.dictDonnees[nom]["lstID"] = [ID]
                else:
                    if not ID in self.dictDonnees[nom]["lstID"]:
                       self.dictDonnees[nom]["lstID"].append(ID)
                if nomlien not in self.dictDonnees[nom]:
                    self.dictDonnees[nom][nomlien] = []
                if IDlien !=None:
                    self.dictDonnees[nom][nomlien].append(IDlien)
                if nom and not nom in self.listeDonnees:
                    self.listeDonnees.append(nom)

    def GetListeIDlienChecked(self,nomlien="lstIDlien"):
        # Harmonise les coches entre des boites liées, suite à une modification dans une liée.
        listeIDchecked = []
        for nom  in self.GetListeChecked():
            if nom in self.dictDonnees:
                if nomlien in self.dictDonnees[nom]:
                    lstIDitem = self.dictDonnees[nom][nomlien]
                    for ID in lstIDitem:
                        if not ID in listeIDchecked:
                            listeIDchecked.append(ID)
        listeIDchecked.sort()
        return listeIDchecked

    def CocheTout(self,coche):
        for index in range(0, len(self.listeDonnees)):
            self.Check(index,check = coche)
            index += 1
        if coche:
            self.listeChecked = []
        else:
            self.listeUnChecked = []
        self.Modified()

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
        for index in range(0, len(self.listeDonnees)):
            item = self.dictDonnees[index]
            if item in liste:
                check = True
            else : check = False
            self.Check(index,check = check)
            index += 1
        self.Modified()

    def OnCheck(self, event):
        selection = event.String
        self.Modified()
        if selection in self.listeChecked:
            self.listeChecked.remove(selection)
            self.listeUnChecked.append(selection)
        else:
            self.listeUnChecked.remove(selection)
            self.listeChecked.append(selection)

    def GetListeChecked(self):
        newListeChecked = []
        for item in self.GetCheckedStrings():
            newListeChecked.append(item)
        return newListeChecked

    def GetNewChecked(self, oldListeChecked, oldListeUnChecked):
        # Met à jour les anciennes listes de coches suite à une modification
        newListeChecked = self.GetCheckedStrings()
        listeStrings = self.GetStrings()
        listNewChecked = []
        listNewUnChecked = []
        for item in listeStrings :
            if item in oldListeChecked:
                listNewChecked.append(item)
            elif item in oldListeUnChecked:
                listNewUnChecked.append(item)
            else:
                if item in newListeChecked:
                    listNewChecked.append(item)
                else:
                    listNewUnChecked.append(item)
        return listNewChecked,listNewUnChecked

    def GetListeIDchecked(self):
        listeIDchecked = []
        for nom  in self.GetListeChecked():
            if nom in self.dictDonnees:
                if "lstID" in self.dictDonnees[nom]:
                    for ID in self.dictDonnees[nom]["lstID"]:
                        listeIDchecked.append(ID)
        listeIDchecked.sort()
        return listeIDchecked

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
        grid_sizer_cocher = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.TOP, 10)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        self.SetSizer(grid_sizer_cocher)
        grid_sizer_cocher.Fit(self)

    def CocheTout(self,bool):
        self.parent.CocheTout(bool,self.IDparent)

# -------------------------------------------------------------------------------------

class CTRL_Groupes_activites(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Grp d'activité"
        #self.Importation()

    def Importation(self):
        condDates = ConditionDateSql(self)
        table = "activites"
        # appel des activités filtrées sur les dates
        req = """
                SELECT IDactivite
                FROM %s
                WHERE (%s)
                ORDER BY IDactivite;
                """ %(table, condDates)
        DB = GestionDB.DB()
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        self.listeActivites = []
        for record in recordset:
            self.listeActivites.append(record[0])

        if len(self.listeActivites) >0:
                lstAct= str(self.listeActivites)[1:-1]
                conditionWhere = "WHERE activites.IDactivite In ( %s )"%lstAct
        else: conditionWhere = ""
        # appel des groupes d'activites représentés dans la liste d'activités
        req= """
                SELECT types_groupes_activites.IDtype_groupe_activite, types_groupes_activites.nom, groupes_activites.IDactivite
                FROM (activites
                      INNER JOIN groupes_activites ON activites.IDactivite = groupes_activites.IDactivite)
                INNER JOIN types_groupes_activites ON groupes_activites.IDtype_groupe_activite = types_groupes_activites.IDtype_groupe_activite
                %s
                ORDER BY types_groupes_activites.nom;
                """ % conditionWhere
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        DB.Close()
        self.StockDonnees(recordset,nomlien="lstIDchild")
        return

    def Modified(self):
        self.listeChecked, self.listeUnChecked = self.GetNewChecked(self.listeChecked,self.listeUnChecked)
        self.parent.ctrl_activites.MAJ()
        self.parent.ctrl_activites.Modified()

    def CocheActivites(self,liste):
        # Coche les groupes d'activités dont une activité au moins est cochée
        for key,donnee in self.dictDonnees.items():
            index = self.listeDonnees.index(key)
            check = False
            for activite in liste:
                if "lstIDchild" in donnee:
                    if activite in donnee["lstIDchild"]:
                        check = True
            self.Check(index,check = check)
            index += 1

class CTRL_Activites(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Activité"

    def Importation(self):
        DB = GestionDB.DB()
        # Appel des activités correspondant aux groupes d'activités cochés
        self.listeID = self.parent.ctrl_groupes_activites.GetListeIDlienChecked(nomlien="lstIDchild")
        if len(self.listeID) == 0:
            condDates = ConditionDateSql(self)
        else:
            lstIDact = str(self.listeID)[1:-1]
            condDates = "activites.IDactivite IN ( %s )"%lstIDact

        # appel des activites représentés dans la liste des groupes d'activités
        req= """
                SELECT activites.IDactivite, activites.nom, groupes.IDgroupe
                FROM activites 
                LEFT JOIN groupes ON activites.IDactivite = groupes.IDactivite
                WHERE %s
                ORDER BY activites.nom;
                """ % condDates
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        DB.Close()
        self.StockDonnees(recordset)
        return

    def Modified(self):
        self.listeChecked, self.listeUnChecked = self.GetNewChecked(self.listeChecked,self.listeUnChecked)

# Panel pour le choix des groupes et activités------------------------------------------
class CTRL(wx.Panel):
    # Panel gérant les dates de limite des activités et leur sélection par les groupes d'activité
    def __init__(self, parent, listview=None):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_SelectionActivites", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.listview = listview
        self.box_selection_staticbox = GetStaticBox(self)

        # Période
        self.label_date_debut = wx.StaticText(self, -1, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date(self)
        self.bouton_date_debut = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.label_date_fin = wx.StaticText(self, -1, "Au")
        self.ctrl_date_fin = CTRL_Saisie_date.Date(self)
        self.bouton_date_fin = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.dateDebut, self.dateFin = self.GetExercice()
        if self.dateDebut:
            self.ctrl_date_debut.SetValue(self.dateDebut)
        if self.dateFin:
            self.ctrl_date_fin.SetValue(self.dateFin)

        # Groupes d'activités
        self.box_groupes_activites_staticbox = wx.StaticBox(self, -1, "Groupes d'activités")
        self.ctrl_groupes_activites = CTRL_Groupes_activites(self)
        self.ctrl_groupes_activites.SetMinSize((50, 50))
        self.ctrl_coche_grpAct = CocheToutRien(self, "grpAct")
        self.ctrl_coche_act = CocheToutRien(self, "act")

        # Activités
        self.box_activites_staticbox = wx.StaticBox(self, -1, "Activités")
        self.ctrl_activites = CTRL_Activites(self)
        self.ctrl_activites.SetMinSize((50, 50))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonDateDebut, self.bouton_date_debut)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDateFin, self.bouton_date_fin)

    def __set_properties(self):
        self.ctrl_groupes_activites.SetToolTip("Cochez des groupes pour présélectionner les activités")
        self.ctrl_activites.SetToolTip("Cochez les activités des groupes d'activités")
        self.ctrl_date_debut.SetToolTip("Saisissez ici une date de début")
        self.bouton_date_debut.SetToolTip("Cliquez ici pour saisir une date de début")
        self.ctrl_date_fin.SetToolTip("Saisissez ici une date de fin")
        self.bouton_date_fin.SetToolTip("Cliquez ici pour saisir une date de fin")
        self.ctrl_groupes_activites.MAJ()
        self.ctrl_activites.MAJ()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=5)
        # Gauche - sélection des lignes
        box_selection = wx.StaticBoxSizer(self.box_selection_staticbox, wx.VERTICAL)
        grid_sizer_gauche = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)

        # Période
        grid_sizer_dates = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        grid_sizer_dates.Add(self.label_date_debut, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrl_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.bouton_date_debut, 0, 0, 0)
        grid_sizer_dates.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrl_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.bouton_date_fin, 0, 0, 0)
        grid_sizer_gauche.Add(grid_sizer_dates, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)

        # Groupes d'activité
        box_grpactiv = wx.StaticBoxSizer(self.box_groupes_activites_staticbox, wx.HORIZONTAL)
        box_grpactiv.Add(self.ctrl_groupes_activites, 1, wx.ALL | wx.EXPAND, 5)
        box_grpactiv.Add(self.ctrl_coche_grpAct, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_grpactiv, 1, wx.LEFT | wx.EXPAND, 25)

        # Activité
        box_activite = wx.StaticBoxSizer(self.box_activites_staticbox, wx.HORIZONTAL)
        box_activite.Add(self.ctrl_activites, 1, wx.ALL | wx.EXPAND, 5)
        box_activite.Add(self.ctrl_coche_act, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_activite, 1, wx.LEFT | wx.EXPAND, 25)

        grid_sizer_gauche.AddGrowableRow(1)
        grid_sizer_gauche.AddGrowableRow(2)
        grid_sizer_gauche.AddGrowableCol(0)
        box_selection.Add(grid_sizer_gauche, 1, wx.LEFT | wx.EXPAND, 5)
        grid_sizer_base.Add(box_selection, 1, wx.LEFT | wx.EXPAND, 5)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def CocheTout(self, bool, ID):
        if ID == "grpAct":
            self.ctrl_groupes_activites.CocheTout(bool)
        if ID == "act":
            self.ctrl_activites.CocheTout(bool)

    def OnBoutonDateDebut(self, event):
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            date = dlg.GetDate()
            self.ctrl_date_debut.SetDate(date)
        self.ctrl_groupes_activites.MAJ()
        dlg.Destroy()

    def OnBoutonDateFin(self, event):
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            date = dlg.GetDate()
            self.ctrl_date_fin.SetDate(date)
        dlg.Destroy()
        self.ctrl_groupes_activites.MAJ()

    def GetExercice(self):
        DB = GestionDB.DB()
        deb,fin =  DB.GetExercice(datetime.date.today(),approche=True)
        debfr = DateEngFr(deb)
        finfr = DateEngFr(fin)
        DB.Close()
        return debfr,finfr

    def SetDates(self,dates="",lstIDactivites=[]):
        if len(dates) > 20:
            self.dateDebut,self.dateFin = dates.split(";")
        else:
            # appel des dates des activités de la liste
            if not lstIDactivites or lstIDactivites == []:
                return self.GetExercice()
            req = """
                     SELECT MIN(date_fin),MAX(date_fin)
                     FROM activites
                     WHERE IDactivite in (%s);
                     """ % (str(lstIDactivites)[1:-1])
            DB = GestionDB.DB()
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            self.dateDebut = DateEngFr(recordset[0][0])
            self.dateFin = DateEngFr(recordset[0][1])
            DB.Close()
        self.ctrl_date_debut.SetValue(self.dateDebut)
        self.ctrl_date_fin.SetValue(self.dateFin)

    def OnChoixDate(self):
        if (self.dateDebut != self.ctrl_date_debut.Value) or (self.dateFin != self.ctrl_date_fin.Value):
            self.dateDebut = self.ctrl_date_debut.Value
            self.dateFin = self.ctrl_date_fin.Value
            self.ctrl_groupes_activites.MAJ()
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

    def GetDates(self):
        return (self.ctrl_date_debut.GetDate(),self.ctrl_date_fin.GetDate())

    def SetValeurs(self, lstIDactivites=[]):
        # Initialisation lancée après reprise de valeurs enregistrées
        self.ctrl_groupes_activites.MAJ()
        self.ctrl_groupes_activites.CocheActivites(lstIDactivites)
        self.ctrl_activites.MAJ()
        self.ctrl_activites.CocheIDliste(lstIDactivites)
        self.ctrl_groupes_activites.Modified()
        self.ctrl_activites.Modified()
    # fin CTRL

# Dialog complet avec boutons de confirmation ------------------------------------------
class DLG_SelectionActivites(wx.Dialog):
    def __init__(self, parent, minSize=(100, 600),**kwd):
        style = kwd.pop('style',wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX )
        wx.Dialog.__init__(self, parent, -1, style=style)
        self.parent = parent
        self.periode = kwd.pop('periode',None)
        title = kwd.pop('title', "MultiChoix d'activité")
        self.SetTitle(title)
        self.SetMinSize(minSize)

        # Panel période, groupes d'activités, activités
        self.ctrl = CTRL(self,)
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider",
                                                cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.bouton_ok.SetToolTip("Cliquez ici pour valider le choix de la liste")
        self.SetMinSize((300, 570))
        if self.periode:
            self.ctrl.SetDates(self.periode)

    def __do_layout(self):
        sizer_2 = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=10)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 0)
        sizer_2.Add(self.bouton_ok, 1, wx.RIGHT | wx.BOTTOM| wx.ALIGN_RIGHT, 5)


        sizer_2.AddGrowableRow(0)
        sizer_2.AddGrowableCol(0)

        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
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
        return self.ctrl.GetDates()

class CTRL_ChoixActivites(wx.Panel):
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



class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.panel = panel

        self.panel.ctrl = CTRL_ChoixActivites(panel,value="ctrl")
        self.panel.ctrl2 = wx.TextCtrl(panel,value="ctrl2")
        self.panel.ctrl3 = wx.TextCtrl(panel,value="ctrl3")
        self.panel.ctrl.SetPeriode((datetime.date(2023,7,1),datetime.date(2023,10,11)))

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.panel.ctrl, 1,wx.ALL|wx.EXPAND)
        sizer_2.Add(self.panel.ctrl2,  )
        sizer_2.Add(self.panel.ctrl3, 1, wx.ALL|wx.EXPAND)
        panel.SetSizer(sizer_2)

        self.Layout()
        self.CentreOnScreen()



if __name__ == '__main__':
    app = wx.App(0)
    #frame_1 = DLG_SelectionActivites(None)
    #print(frame_1.ShowModal())
    #app.SetTopWindow(frame_1)
    frame_1 = MyFrame(None, -1, "TEST", size=(500, 700))
    print('retour frame',frame_1.Show())
    app.MainLoop()

