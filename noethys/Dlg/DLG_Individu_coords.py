#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
import FonctionsPerso as fp
from Ctrl import CTRL_Saisie_tel
from Ctrl import CTRL_Saisie_mail

from Utils import UTILS_Utilisateurs
from Utils import UTILS_SaisieAdresse as usa
from Dlg import DLG_SaisieAdresse
from Data import DATA_Civilites as Civilites

DICT_CIVILITES = Civilites.GetDictCivilites()

class Adresse_auto(wx.Choice):
    def __init__(self, parent,IDindividu=None, IDfamille=None):
        # si famille renseignée les choix seront limité à cette famille, sinon à toutes les familles de l'individu
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.lstIndividusAffiches = []
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.dictAdresses = {}
        if IDfamille and IDfamille >0 :
            self.cat = "famille"
            self.SetToolTip(_("Sélectionnez celui qui a l'adresse de cette famille.\n(Les individus sans adresse propre n'apparaissent pas)"))
        else:
            self.cat = "individu"
            self.SetToolTip(_("Sélectionnez un membre de la famille à la même adresse.\n(Les individus sans adresse propre n'apparaissent pas)"))

    def MAJ(self, DB=None):
        self.Clear()
        self.GetListeDonnees(DB)

    def GetNbreItems(self):
        return self.GetCount()

    def AjouteItem(self,IDindividu, nom, prenom, auto, rue, cp, ville,force=False):
        # ajoute un item à choice et aux listes associées seulement s'il a une adresse en propre
        nomComplet = "%s %s" % (nom, prenom)
        if (ville and len(ville)>0) or force:
            index = len(self.dictAdresses)
            self.Insert(nomComplet,index)
            self.dictAdresses[index] = {"ID": IDindividu, "rue": rue, "cp": cp, "ville": ville}
            self.lstIndividusAffiches.append(IDindividu)

    def GetListeDonnees(self, DB=None):
        if not DB:
            DB = GestionDB.DB()
        # liste des familles pouvant proposer une adresse pour l'individu
        adresse_auto = None
        if self.cat=="famille":
            listeFamilles = [self.IDfamille,]
        elif self.cat=="individu" :
            # Recherche des familles de rattachements de l'individu
            req = """SELECT IDfamille
            FROM rattachements
            WHERE IDindividu=%d
            GROUP BY IDfamille;""" %(self.IDindividu)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            listeFamilles = []
            for (IDfamille,) in listeDonnees :
                listeFamilles.append(IDfamille)

            # recherche adresse_auto de l'individu
            req = """SELECT adresse_auto
            FROM individus
            WHERE IDindividu=%d
            ;""" %(self.IDindividu)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            for (ID,) in listeDonnees:
                adresse_auto = ID


        # determination de l'adresse actuelle de ccorrespondance de la famille
        if self.cat=="famille":
            IDcorresp = None
            req = """
                    SELECT adresse_individu
                    FROM familles
                    WHERE IDfamille=%d
                    ;""" %(self.IDfamille)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            for (value,) in listeDonnees :
                IDcorresp = value

        # liminaire pour recherche des adresses à proposer
        if len(listeFamilles) == 0:
            self.dictAdresses = {}
            return []
        elif len(listeFamilles) == 1 :
            condition = "(%s)" % listeFamilles[0]
        else :
            condition = str(tuple(listeFamilles))
        if adresse_auto:
            condition += " OR individus.IDindividu = %d"%adresse_auto

        # Recherche des individus des familles rattachées ou de la famille, mais aussi éventuellement l'adresse pointée
        req = """SELECT individus.IDindividu, individus.nom, individus.prenom, adresse_auto, rue_resid, cp_resid, 
                        ville_resid, rattachements.titulaire
        FROM individus
        LEFT JOIN rattachements ON individus.IDindividu = rattachements.IDindividu
        WHERE IDfamille IN %s;""" % condition # J'ai enlevé ici "IDcategorie=1 AND " pour afficher également les contacts
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dictAdresses = {}
        self.lstIndividus = []
        self.lstPrenomsTitulaires = []
        self.lstIndividusAffiches = []
        self.lstNomsIndividus = []
        self.AjouteItem(0,"","",None,"","","",force=True)
        for IDindividu, nom, prenom, auto, rue, cp, ville, titulaire in listeDonnees :
            # stockage collatéral de tous les individus de la famille pour les listes de diffusion
            if self.cat=="individu" and self.IDindividu == IDindividu:
                # Je ne peux pointer ma propre adresse en auto (boucle dans la recherche)
                continue
            nomComplet = "%s %s" % (nom, prenom)
            self.lstIndividus.append(IDindividu)
            self.lstNomsIndividus.append(nomComplet)
            if titulaire == 1:
                self.lstPrenomsTitulaires.append(prenom)
            force = (ville and len(ville)>0)
            self.AjouteItem(IDindividu, nom, prenom, auto, rue, cp, ville, force)

        # pointeur du correspondant actuel
        if self.cat=="famille":
            self.SetID(ID=IDcorresp)
        return

    def SetID(self, ID=0):
        if not ID or ID == 0:
            self.SetSelection(0)
        else:
            for index, values in self.dictAdresses.items():
                if values["ID"] == ID :
                     self.SetSelection(index)
            self.parent.oldID = ID

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictAdresses[index]["ID"]

    def GetDonnee(self):
        """ return l'IDindividu sélectionné SI adresse_auto est TRUE sinon renvoie None """
        if isinstance(self.parent.radio_adresse_auto,wx.StaticText):
            return self.GetID()
        elif self.parent.radio_adresse_auto.GetValue() == True :
            return self.GetID()
        else:
            return None

class Categorie(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.SetToolTip(_("Sélectionnez la catégorie socio-professionnelle de l'individu"))
    
    def MAJ(self, DB=None):
        choices = self.GetListeDonnees(DB)
        self.SetItems(choices)
        
    def GetListeDonnees(self, DB=None):
        req = """SELECT IDcategorie, nom FROM categories_travail ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dictDonnees = {}
        listeNoms = []
        index = 0
        for IDcategorie, nom in listeDonnees :
            listeNoms.append(nom)
            self.dictDonnees[index] = (IDcategorie, nom)
            index += 1
        return listeNoms

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values[0] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index][0]

# -------------------------------------------------------------------------------------------------------------------------

class CTRL_diff(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.SetToolTip(_("Cochez les listes de diffusion souhaitées"))
        self.listeDiff = []
        self.dictDiff = {}
        
    def MAJ(self, DB=None):
        self.listeDiff, self.dictDiff = self.Importation(DB)
        self.SetListeChoix()
    
    def Importation(self, DB=None):
        listeDiff = []
        dictDiff = {}
        # Recherche les listes de diffusion
        req = """SELECT IDliste, nom
        FROM listes_diffusion
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeListes = DB.ResultatReq()   
        for IDliste, nom in listeListes :
            dictDiff[IDliste] = nom
            listeDiff.append((nom, IDliste))
        listeDiff.sort()
        
        return listeDiff, dictDiff

    def SetListeChoix(self):
        self.Clear()
        listeItems = []
        index = 0
        for nom, IDliste in self.listeDiff :
            self.Append(nom)
            index += 1
                            
    def GetIDcoches(self):
        listeIDcoches = []
        NbreItems = len(self.listeDiff)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                listeIDcoches.append(self.listeDiff[index][1])
        return listeIDcoches
    
    def CocheTout(self):
        index = 0
        for index in range(0, len(self.listeDiff)):
            self.Check(index)
            index += 1

    def SetIDcoches(self, listeIDcoches=[]):
        for index in range(0, len(self.listeDiff)):
            ID = self.listeDiff[index][1]
            if ID in listeIDcoches :
                self.Check(index)

    def GetDictDiff(self):
        return self.dictDiff

class Panel_3StateCheckBoxes(wx.Panel):
    # gestion d'une liste de checkbox à trois états 
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_checkBoxes",style=wx.TRANSPARENT_WINDOW|wx.BORDER_SIMPLE)
        self.parent = parent
        self.listeDiff, self.dictDiff = self.Importation()
        self.lstBoxes = []
        # composition des ctrl checkbox
        for label,IDliste in self.listeDiff:
            self.lstBoxes.append(wx.CheckBox(self, -1,label,style=wx.CHK_3STATE))
            self.lstBoxes[-1].SetToolTip(_("Cochez les listes de diffusion souhaitées"))
            self.lstBoxes[-1].index=len(self.lstBoxes)-1
            self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.lstBoxes[-1])
        self.__do_layout()

    def __do_layout(self):
        grid_sizer = wx.FlexGridSizer(rows=len(self.listeDiff), cols=1, vgap=2, hgap=5)
        for i in range(len(self.listeDiff)):
            grid_sizer.Add(self.lstBoxes[i], 0, wx.EXPAND, 0)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        grid_sizer.Fit(self)

    def Importation(self):
        DB = GestionDB.DB()
        listeDiff = []
        dictDiff = {}
        # Recherche les listes de diffusion
        req = """SELECT IDliste, nom
        FROM listes_diffusion
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeListes = DB.ResultatReq()
        for IDliste, nom in listeListes:
            dictDiff[IDliste] = nom
            listeDiff.append((nom, IDliste))
        listeDiff.sort()
        DB.Close()
        return listeDiff, dictDiff

    def Get3States(self):
        listeIDcoches = []
        NbreItems = len(self.listeDiff)
        for index in range(0, NbreItems):
            listeIDcoches.append(self.lstBoxes[index].Get3StateValue())
        return listeIDcoches

    def Set3States(self, lstStates=[]):
        for index in range(0, len(self.listeDiff)):
            self.lstBoxes[index].Set3StateValue(lstStates[index])

    def OnCheck(self,event):
        # récupération de la liste checkée
        IDliste = self.listeDiff[event.EventObject.index]
        checked = event.EventObject.Get3StateValue()
        if checked == 1:
            # on coche pour tous
            if IDliste not in self.parent.dictDiffusionNew:
                self.parent.dictDiffusionNew[IDliste] = {"individus": [], "abonnements": []}
            self.parent.dictDiffusionNew[IDliste]["individus"] = self.parent.ctrl_adresse_auto.lstIndividus
            self.parent.dictDiffusionNew[IDliste]["abonnements"] = []
        elif checked == 0:
            # on décoche pour tous
            if IDliste in self.parent.dictDiffusionNew:
                self.parent.dictDiffusionNew[IDliste]["individus"] = []
                self.parent.dictDiffusionNew[IDliste]["abonnements"] = []

# ----------------------------------------------------------------------------------------------------------------------

class Panel_contact(wx.Panel):
    def __init__(self, parent, IDindividu=None,IDfamille=None,cat="individu"):
        wx.Panel.__init__(self, parent, id=-1, name="panel_coords",style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDindividu = IDindividu
        if not self.IDindividu and hasattr(self.parent,"IDindividu"):
            self.IDindividu = self.parent.IDindividu
        self.IDcorrespondant = None
        self.correspondant = None
        self.IDfamille = IDfamille

        self.nomPrenom = ""
        self.oldID = 0
        self.oldLstAdresse = None
        self.lstAdresse = []
        self.cat = cat
        self.intitule = ""
        if cat == "individu":
            titre = "Coordonnées individu"
            self.radio_adresse_auto = wx.RadioButton(self, -1, "adresse de :", style=wx.RB_GROUP)
            self.ctrl_adresse_auto = Adresse_auto(self,IDindividu=IDindividu)
            self.radio_adresse_manuelle = wx.RadioButton(self, -1, "adresse propre à l'individu")
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioAdresseAuto, self.radio_adresse_auto)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioAdresseManu, self.radio_adresse_manuelle)
            self.designationB = wx.TextCtrl(self, -1,"")
            # Listes de diffusion
            self.label_listesdiff = wx.StaticText(self, -1, _("Listes de diffusion :"))
            self.ctrl_listesdiff = CTRL_diff(self)
            self.ctrl_refus_pub = wx.CheckBox(self, -1, "refus pub papier")
            self.ctrl_refus_mel = wx.CheckBox(self, -1, "refus mails de com")
        elif cat == "famille":
            titre = "Coordonnées de la famille %d"%self.IDfamille
            self.radio_adresse_auto = wx.StaticText(self, -1, "utiliser l'adresse de :", style=wx.RB_GROUP)
            self.ctrl_adresse_auto = Adresse_auto(self,IDindividu=IDindividu,IDfamille = IDfamille)
            self.radio_adresse_manuelle = wx.StaticText(self, -1, "Correspondance à : ")
            self.designationB = wx.TextCtrl(self, -1,"")
            self.designationB.SetMaxLength(38)
            self.designationB.Bind(wx.EVT_KILL_FOCUS, self.OnKillDesignationB)
            # Listes de diffusion
            self.label_listesdiff = wx.StaticText(self, -1, _("Diffusions à tous les membres:"))
            self.ctrl_listesdiff = Panel_3StateCheckBoxes(self)
            self.ctrl_refus_pub = wx.CheckBox(self, -1, "refus pub famille",style=wx.CHK_3STATE)
            self.ctrl_refus_pub.Set3StateValue(wx.CHK_UNCHECKED)
            self.ctrl_refus_mel = wx.CheckBox(self, -1, "refus mails famille",style=wx.CHK_3STATE)
            self.ctrl_refus_mel.Set3StateValue(wx.CHK_UNCHECKED)
            self.Bind(wx.EVT_CHECKBOX, self.OnRefusPub, self.ctrl_refus_pub)
            self.Bind(wx.EVT_CHECKBOX, self.OnRefusMel, self.ctrl_refus_mel)
            self.Bind(wx.EVT_KILL_FOCUS,self.OnKillDesignationB,self.designationB)

        self.majEffectuee = False
                
        # Adresse
        self.staticbox_adresse = wx.StaticBox(self, -1, titre)
        self.staticbox_contacts = wx.StaticBox(self, -1, "Gestion des contacts %s"%cat)
        self.bouton_adresse = wx.Button(self, -1, "...", size=(20, 20))
        self.ctrl_adresse = wx.TextCtrl(self, -1, "",size=(60,100), style=wx.TE_MULTILINE|wx.TE_READONLY)
        # Contacts
        self.label_tel_domicile = wx.StaticText(self, -1, _("Tel fixe :"))
        self.ctrl_tel_domicile = CTRL_Saisie_tel.Tel(self, intitule=_("tel fixe"))
        self.label_tel_mobile = wx.StaticText(self, -1, _("Mobile :"))
        self.ctrl_tel_mobile = CTRL_Saisie_tel.Tel(self, intitule=_("mobile"))
        self.label_tel_mob2 = wx.StaticText(self, -1, _("Mob 2 :"))
        self.ctrl_tel_mob2 = CTRL_Saisie_tel.Tel(self, intitule=_("mobile2"))
        self.label_mail = wx.StaticText(self, -1, _("Mail1 :"))
        self.ctrl_mail = CTRL_Saisie_mail.Mail(self)
        self.bouton_mail_perso = wx.BitmapButton(self, 900, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))

        # Activité professionnelle
        self.label_categorie = wx.StaticText(self, -1, _("CSP :"))
        self.ctrl_categorie = Categorie(self)
        self.label_travail_tel = wx.StaticText(self, -1, _("TélProf:"))
        self.ctrl_travail_tel = CTRL_Saisie_tel.Tel(self, intitule=_("travail"))
        self.label_profession = wx.StaticText(self, -1, _("Métier :"))
        self.ctrl_profession = wx.TextCtrl(self, -1, "")

        self.label_travail_mail = wx.StaticText(self, -1, _("Mail2 :"))
        self.ctrl_travail_mail = CTRL_Saisie_mail.Mail(self)
        self.bouton_mail_travail = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))
                

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnEnvoiEmail, self.bouton_mail_travail)
        self.Bind(wx.EVT_BUTTON, self.OnEnvoiEmail, self.bouton_mail_perso)
        self.ctrl_adresse_auto.Bind(wx.EVT_CHOICE, self.OnAuto)

        self.bouton_adresse.Bind(wx.EVT_BUTTON, self.OnAdresse)

    def __set_properties(self):
        self.radio_adresse_auto.SetToolTip(_("Cliquez ici pour utiliser l'adresse d'un autre membre de la famille"))
        self.radio_adresse_manuelle.SetToolTip(_("Cliquez ici pour saisir manuellement une adresse"))
        self.ctrl_adresse.SetToolTip(_("Cliquez sur le bouton '...' à gauche, pour gérer l'adresse"))
        self.bouton_adresse.SetToolTip(_("Cliquez sur ce bouton pour gérer l'adresse"))
        self.ctrl_profession.SetToolTip(_("Saisissez la profession de l'individu"))
        self.bouton_mail_travail.SetToolTip(_("Cliquez ici pour envoyer un email à cette adresse internet"))
        self.bouton_mail_perso.SetToolTip(_("Cliquez ici pour envoyer un email à cette adresse internet"))
        if self.cat == "individu":
            self.ctrl_refus_pub.SetToolTip(_("Saisissez le refus de publicité papier de l'individu"))
            self.ctrl_refus_mel.SetToolTip(_("Saisissez le refus de publicité par mail de l'individu"))
        else:
            self.ctrl_refus_pub.SetToolTip(_("Saisissez le refus de publicité papier pour toute la famille"))
            self.ctrl_refus_mel.SetToolTip(_("Saisissez le refus de publicité par mail pour toute la famille"))

    def __do_layout(self):
        grid_sizer_base0 = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        staticbox_adresse = wx.StaticBoxSizer(self.staticbox_adresse, wx.VERTICAL)
        grid_sizer_haut = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)

        grid_sizer_auto = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=5)
        grid_sizer_auto.Add(self.radio_adresse_auto, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_auto.Add(self.ctrl_adresse_auto, 0, wx.EXPAND, 0)
        grid_sizer_auto.AddGrowableCol(1)
        grid_sizer_haut.Add(grid_sizer_auto, 1, wx.EXPAND, 0)

        grid_sizer_designation = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=5)
        grid_sizer_designation.Add(self.radio_adresse_manuelle, 0, 0, 0)
        grid_sizer_designation.Add(self.designationB, 0, wx.EXPAND, 0)
        grid_sizer_designation.AddGrowableCol(1)
        grid_sizer_haut.Add(grid_sizer_designation, 1, wx.EXPAND, 0)

        grid_sizer_adresse = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=5)
        grid_sizer_adresse.Add((10,10), 0, 0, 0)
        grid_sizer_adresse.Add(self.bouton_adresse, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_adresse.Add(self.ctrl_adresse, 0, wx.EXPAND, 0)
        grid_sizer_adresse.AddGrowableRow(0)
        grid_sizer_adresse.AddGrowableCol(2)
        grid_sizer_haut.Add(grid_sizer_adresse, 1, wx.EXPAND, 0)
        grid_sizer_haut.AddGrowableRow(2)
        grid_sizer_haut.AddGrowableCol(0)

        staticbox_adresse.Add(grid_sizer_haut, 1, wx.ALL | wx.EXPAND, 0)
        grid_sizer_base0.Add(staticbox_adresse,0,wx.EXPAND,0)

        grid_sizer_bas = wx.FlexGridSizer(rows=1, cols=2, vgap=2, hgap=10)
        grid_sizer_gauche = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)

        staticbox_contacts = wx.StaticBoxSizer(self.staticbox_contacts, wx.VERTICAL)

        grid_sizer_contact = wx.FlexGridSizer(rows=12, cols=2, vgap=5, hgap=5)
        grid_sizer_contact.Add((20,20), 0, 0, 0)
        grid_sizer_contact.Add(self.ctrl_refus_pub, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add((20,20), 0, 0, 0)
        grid_sizer_contact.Add(self.ctrl_refus_mel, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_tel_domicile, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_tel_domicile, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_tel_mobile, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_tel_mobile, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_tel_mob2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_tel_mob2, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_travail_tel, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_travail_tel, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_categorie, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_categorie, 0, wx.EXPAND, 0)
        grid_sizer_contact.Add(self.label_profession, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contact.Add(self.ctrl_profession, 0, wx.EXPAND, 0)
        
        grid_sizer_contact.Add(self.label_mail, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_mails = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=5)
        grid_sizer_mails.Add(self.ctrl_mail, 0, wx.EXPAND, 0)
        grid_sizer_mails.Add(self.bouton_mail_perso, 0, wx.EXPAND, 0)

        grid_sizer_mails.AddGrowableCol(1)
        grid_sizer_contact.Add(grid_sizer_mails, 0, wx.EXPAND, 0)

        grid_sizer_contact.Add(self.label_travail_mail, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_mails2 = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=5)
        grid_sizer_mails2.Add(self.ctrl_travail_mail, 0, wx.EXPAND, 0)
        grid_sizer_mails2.Add(self.bouton_mail_travail, 0, wx.EXPAND, 0)

        grid_sizer_mails2.AddGrowableCol(1)
        grid_sizer_contact.Add(grid_sizer_mails2, 0, wx.EXPAND, 0)

        grid_sizer_contact.AddGrowableCol(0)
        grid_sizer_gauche.Add(grid_sizer_contact, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_bas.Add(grid_sizer_gauche, 0, 0, 0)

        grid_sizer_droite = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=10)

        grid_sizer_droite.Add(self.label_listesdiff, 0, 0, 0)
        grid_sizer_droite.Add(self.ctrl_listesdiff, 1,wx.ALIGN_LEFT| wx.EXPAND, 0)
        grid_sizer_droite.AddGrowableRow(1)
        grid_sizer_droite.AddGrowableCol(0)

        grid_sizer_bas.Add(grid_sizer_droite, 0, wx.EXPAND, 0)
        grid_sizer_bas.AddGrowableRow(0)
        grid_sizer_bas.AddGrowableCol(1)

        staticbox_contacts.Add(grid_sizer_bas, 1, wx.ALL | wx.EXPAND, 0)
        grid_sizer_base0.Add(staticbox_contacts,1,wx.EXPAND,0)


        grid_sizer_base0.AddGrowableRow(1)
        grid_sizer_base0.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base0)
        grid_sizer_base0.Fit(self)

    def OnRadioAdresseAuto(self, event):
        # uniquement pour l'individu, pas pour famille
        self.ctrl_adresse_auto.Enable(True)
        self.bouton_adresse.Enable(False)
        self.ctrl_adresse.Enable(False)
        self.ctrl_adresse_auto.SetID(self.oldID)
        self.noAdresse = True
        self.OnTextAdresse(None)

    def OnRadioAdresseManu(self, event):
        # uniquement pour l'individu, pas pour famille
        self.oldID = self.ctrl_adresse_auto.GetID()
        self.ctrl_adresse_auto.Enable(False)
        self.bouton_adresse.Enable(True)
        self.ctrl_adresse.Enable(True)
        self.lstAdresse = self.oldLstAdresse
        self.ctrl_adresse_auto.SetID(0)
        self.noAdresse = False
        self.OnTextAdresse(None)
        self.ctrl_adresse_auto.Enable(True)

    def OnAdresse(self,event):
        dlg = DLG_SaisieAdresse.DlgSaisieAdresse(self.IDindividu)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            self.lstAdresse = dlg.lstAdresse
            self.strAdresse = usa.CompacteAdresse(lstAdresse=self.lstAdresse)
            self.ctrl_adresse.SetValue(self.strAdresse)
        event.Skip()

    def OnAuto(self,event):
        if self.cat == "individu":
            self.radio_adresse_auto.SetValue(True)
        self.OnTextAdresse(None)
        event.Skip()

    def OnTextAdresse(self,event):
        # actualise l'affichage de l'adresse
        if self.cat == "individu":
            self.OnTextAdresseIndividu()
        else: self.OnTextAdresseFamille()
        if event != None :
            event.Skip()

    def OnTextAdresseIndividu(self):
        # actualise l'affichage de l'adresse y compris dans le header
        self.strAdresse = ""

        # si on est en présence d'un ajout d'individu à nouvelleFiche
        if self.noAdresse and (len(self.ctrl_adresse_auto.lstIndividusAffiches)>0):
            self.radio_adresse_auto.SetValue(True)
            self.ctrl_adresse_auto.SetSelection(1)
            self.noAdresse = False

        if self.radio_adresse_auto.Value == True :
            # Adresse auto
            indexSelection = self.ctrl_adresse_auto.GetSelection()
            if indexSelection > 0 and indexSelection in self.ctrl_adresse_auto.dictAdresses :
                rue = self.ctrl_adresse_auto.dictAdresses[indexSelection]["rue"]
                cp = self.ctrl_adresse_auto.dictAdresses[indexSelection]["cp"]
                ville = self.ctrl_adresse_auto.dictAdresses[indexSelection]["ville"]
                if rue == "" and cp == None and ville == None :
                    self.strAdresse = _("Adresse inconnue")
                else:
                    self.lstAdresse = usa.ChampsToLstAdresse(rue,cp,ville)
                    self.strAdresse = usa.CompacteAdresse(self.lstAdresse)
            self.designationB.SetLabel("")
        if self.radio_adresse_manuelle.Value == True:
            # Adresse manuelle
            self.strAdresse = usa.CompacteAdresse(self.lstAdresse)
            self.designationB.SetLabel(self.nomPrenom)
            self.bouton_adresse.Enable(True)
            self.ctrl_adresse.Enable(True)
        self.ctrl_adresse.SetValue(self.strAdresse)

        # Envoie les infos vers l'Header
        self.Set_Header(nomLigne="adresse", texte=self.strAdresse.replace("\n",", "))

    def OnTextAdresseFamille(self):
        # actualise l'affichage de l'adresse
        self.strAdresse = ""
        # Adresse auto n'a pas le même sens que pour individu car pas de choix radio, mais affichage auto et adresse
        indexSelection = self.ctrl_adresse_auto.GetSelection()
        if indexSelection > 0 and indexSelection in self.ctrl_adresse_auto.dictAdresses :
            rue = self.ctrl_adresse_auto.dictAdresses[indexSelection]["rue"]
            cp = self.ctrl_adresse_auto.dictAdresses[indexSelection]["cp"]
            ville = self.ctrl_adresse_auto.dictAdresses[indexSelection]["ville"]
            if rue == "" and cp == None and ville == None :
                self.strAdresse = _("Adresse inconnue")
            else:
                self.lstAdresse = usa.ChampsToLstAdresse(rue,cp,ville)
                self.strAdresse = usa.CompacteAdresse(self.lstAdresse)
        # choix représentant à blanc
        else:
            self.strAdresse = _("Adresse famille à choisir chez l'un des membres")
            if not self.intitule or self.intitule == "":
                self.intitule = "%s"%self.parent.lstContacts[0].nomPrenom
        if not self.intitule:
            self.intitule="%s"%self.nomPrenom
        self.designationB.SetLabel(self.intitule)
        self.ctrl_adresse.SetValue(self.strAdresse)
        if self.IDcorrespondant == self.parent.IDindividu:
            # c'est le même individu des deux côtés, il faut éviter les conflits de champs modifiés
            for ctrl in (self.bouton_adresse,self.bouton_mail_perso,self.ctrl_adresse,self.ctrl_mail,self.ctrl_tel_domicile,
                         self.ctrl_tel_mob2,self.ctrl_tel_mobile,self.label_mail,self.label_tel_domicile,
                         self.label_tel_mob2,self.label_tel_mobile,self.ctrl_categorie,self.ctrl_profession,
                         self.ctrl_travail_tel,self.label_categorie,self.label_profession,self.label_travail_tel,
                         self.bouton_mail_travail,self.ctrl_travail_mail,self.label_travail_mail):
                ctrl.Enable(False)

    def OnEnvoiEmail(self, event):
        # Création du menu contextuel
        menuPop = wx.Menu()
        
        item = wx.MenuItem(menuPop, event.GetId()+1, _("Depuis l'éditeur d'Emails de Noethys"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Editeur_email.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=event.GetId()+1)
        
        item = wx.MenuItem(menuPop, event.GetId()+2, _("Depuis le client de messagerie par défaut"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Terminal.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=event.GetId()+2)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def OnRefusPub(self,event):
        # mise à jour des refus de l'individu pour visualiser ce que se passera à la sauvegarde (tous seront modifiés)
        if self.cat == "famille":
            self.parent.lstContacts[0].ctrl_refus_pub.SetValue(self.ctrl_refus_pub.GetValue())
            self.parent.lstContacts[0].ctrl_refus_pub.Enable(False)
        event.Skip()

    def OnKillDesignationB(self,event):
        # controle des caractères spéciaux
        ret = fp.NoPunctuation(self.designationB.GetValue())
        self.designationB.SetLabel(ret)
        event.Skip()

    def OnRefusMel(self,event):
        if self.cat == "famille":
            self.parent.lstContacts[0].ctrl_refus_mel.SetValue(self.ctrl_refus_mel.GetValue())
            self.parent.lstContacts[0].ctrl_refus_mel.Enable(False)
        event.Skip()

    def Set_Header(self, nomLigne, texte):
        try :
            self.ficheIndividu = self.GrandParent.GetParent()
            if self.ficheIndividu.GetName() != "fiche_individu" :
                self.ficheIndividu = None
        except :
            self.ficheIndividu = None
        if self.ficheIndividu != None :
            self.ficheIndividu.Set_Header(nomLigne, texte)

    def EnvoyerEmail(self, event):
        # Récupère l'adresse
        if event.GetId() in (801, 802) :
            ctrl = self.ctrl_travail_mail
        if event.GetId() in (901, 902) :
            ctrl = self.ctrl_mail
        adresse = ctrl.GetValue()
        valide, erreur = ctrl.Validation()

        # Vérifie l'adresse
        if adresse == "" or  valide == False :
            dlg = wx.MessageDialog(self, _("Vous devez d'abord saisir une adresse internet valide !"), "Information", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            ctrl.SetFocus()
            return
        
        # Depuis l'éditeur d'Emails de Noethys
        if event.GetId() in (801, 901) :
            from Dlg import DLG_Mailer
            dlg = DLG_Mailer.Dialog(self)
            listeDonnees = [{"adresse" : adresse, "pieces" : [], "champs" : {},},]
            dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
            dlg.ShowModal() 
            dlg.Destroy()
        
        # Depuis le client de messagerie par défaut
        if event.GetId() in (802, 902) :
            fp.EnvoyerMail(adresses=[adresse,], sujet="", message="")

    def MAJ(self):
        # Importation des données
        if self.majEffectuee == True:
            return
        self.nouvelleFiche = False
        gp = self.GetGrandParent()
        if hasattr(gp,'nouvelleFiche'):
            self.nouvelleFiche = gp.nouvelleFiche
        elif gp.Parent and  hasattr(gp.Parent,'nouvelleFiche'):
            self.nouvelleFiche = gp.Parent.nouvelleFiche

        if self.cat == "individu": self.MAJindividu()
        else: self.MAJfamille()

        # Verrouillage utilisateurs
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_coordonnees","modifier",afficheMessage=False)==False:
            for ctrl in self.GetChildren():
                ctrl.Enable(False)
        self.majEffectuee = True
        self.OnTextAdresse(None)

    def MAJindividu(self):
        # MAJ intiale des contrôles
        DB = GestionDB.DB()
        # infos complémentaires de l'individu
        req = """SELECT IDcivilite, nom, prenom, IDcategorie_travail, profession, travail_tel, travail_mail, tel_domicile, 
                        tel_mobile, tel_fax, mail, refus_pub, refus_mel, cp_resid, adresse_auto
                FROM individus WHERE IDindividu=%d;""" % self.IDindividu
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        IDcivilite, nom, prenom, IDcategorie, profession, travail_tel, travail_mail, tel_domicile, \
        tel_mobile, tel_fax, mail, refus_pub, refus_mel, cp_resid, adresse_auto = listeDonnees[0]

        if not prenom : prenom = ""
        if not nom : nom = ""
        # gestion d'une adresse par défaut dans ctrl_adresse_auto
        if not (cp_resid or adresse_auto):
            self.noAdresse = True
        else: self.noAdresse = False

        self.nomPrenom = nom + " " + prenom
        if IDcivilite :
            self.nomPrenom = (DICT_CIVILITES[IDcivilite]["civiliteAbrege"] + " " + self.nomPrenom).strip()
        self.ctrl_adresse_auto.MAJ(DB=DB)

        self.ctrl_categorie.MAJ(DB=DB)
        self.refusInitiaux = (0,0)
        self.listesDiffusionInitiale = []
        self.dictDiffusionInitiale = {}
        self.ctrl_listesdiff.MAJ(DB=DB)

        if self.ctrl_adresse_auto.GetNbreItems() == 0:
            self.radio_adresse_manuelle.SetValue(True)
            self.radio_adresse_auto.Enable(False)
            self.ctrl_adresse_auto.Enable(False)
        else:
            self.radio_adresse_manuelle.SetValue(False)
            self.bouton_adresse.Enable(False)
            self.designationB.Enable(False)
            self.ctrl_adresse.Enable(False)

        # Si pas nouvelle fiche -> Importation des données
        if self.nouvelleFiche == False:
            # Listes de diffusion
            req = """SELECT IDabonnement, IDliste
            FROM abonnements WHERE IDindividu=%d;""" % self.IDindividu
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            listeIDliste = []
            for IDabonnement, IDliste in listeDonnees:
                listeIDliste.append(IDliste)
                self.listesDiffusionInitiale.append(IDliste)
                self.dictDiffusionInitiale[IDliste] = IDabonnement
            self.ctrl_listesdiff.SetIDcoches(listeIDliste)

            # Adresse de référence
            self.lstAdresse, self.IDcorrespondant, nomprenom = usa.GetDBadresse(self.IDindividu,retNom=True)
            (nom,prenom)=nomprenom
            if not self.IDcorrespondant in self.ctrl_adresse_auto.lstIndividusAffiches:
                # l'adresse de référence n'est pas dans la famille : on l'ajoute si pas lui-même
                if self.IDindividu != self.IDcorrespondant:
                    rue,cp,ville = usa.LstAdresseToChamps(self.lstAdresse)
                    self.ctrl_adresse_auto.AjouteItem(self.IDcorrespondant,nom,prenom,None,rue,cp,ville)
            # adresse forcément automatique
            self.ctrl_adresse_auto.SetID(self.IDcorrespondant)
            self.strAdresse = usa.CompacteAdresse(self.lstAdresse)
            if self.IDcorrespondant != self.IDindividu:
                # adresse automatique
                self.radio_adresse_auto.SetValue(True)
                self.bouton_adresse.Enable(False)
                self.ctrl_adresse.Enable(False)
                self.ctrl_adresse_auto.SetID(self.IDcorrespondant)

            else:
                # l'individu a son adresse en propre
                self.oldLstAdresse = self.lstAdresse
                self.radio_adresse_auto.SetValue(False)
                self.radio_adresse_manuelle.SetValue(True)
                self.ctrl_adresse_auto.SetID(None)
                self.bouton_adresse.Enable(True)
                self.ctrl_adresse.Enable(True)
                self.ctrl_adresse_auto.Enable(False)
                #self.designationB.SetLabel(self.nomPrenom)
            self.OnTextAdresse(None)
            self.designationB.Enable(False)

            # Activité professionnelle
            self.ctrl_categorie.SetID(IDcategorie)
            if not profession: profession = ""
            self.ctrl_profession.SetValue(profession)
            self.ctrl_travail_tel.SetNumero(travail_tel)
            self.ctrl_travail_mail.SetMail(travail_mail)

            # Coords
            self.ctrl_tel_domicile.SetNumero(tel_domicile)
            self.ctrl_tel_mobile.SetNumero(tel_mobile)
            self.ctrl_tel_mob2.SetNumero(tel_fax)
            self.ctrl_mail.SetMail(mail)
            if not refus_pub: refus_pub = 0
            if not refus_mel: refus_mel = 0
            self.ctrl_refus_pub.SetValue(refus_pub)
            self.ctrl_refus_mel.SetValue(refus_mel)
        DB.Close()

    def MAJfamille(self):
        # MAJ intiale des contrôles
        DB = GestionDB.DB()
        self.ctrl_adresse_auto.MAJ(DB=DB)
        self.ctrl_categorie.MAJ(DB=DB)
        # recherche du représantant famille et de la désignation
        self.dictDiffusionOriginale = {}
        self.dictDiffusionNew = {}
        self.intitule = None
        self.correspondant = None
        req = """SELECT familles.adresse_intitule, familles.adresse_individu, refus_pub,refus_mel
                FROM familles
                WHERE (familles.IDfamille= %d );""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        refus_pub, refus_mel = 0,0
        for intitule,correspondant, refus_pub,refus_mel in listeDonnees:
            self.intitule = intitule
            self.correspondant = correspondant
            if not refus_pub: refus_pub = 0
            if not refus_mel: refus_mel = 0
            self.ctrl_refus_pub.SetValue(refus_pub)
            self.ctrl_refus_mel.SetValue(refus_mel)

        if not (self.intitule and self.correspondant):
            # On prend le premier titulaire pour adresse et désignation famille
            req = """
                    SELECT individus.IDindividu, individus.IDcivilite, individus.nom, individus.prenom
                    FROM rattachements INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
                    WHERE ((rattachements.IDfamille = %d ) AND ((rattachements.titulaire)=1));
                    ;""" % self.IDfamille
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            if len(recordset) >0:
                IDindividu, IDcivilite, nom, prenom  = recordset[0]
                if IDcivilite:
                    self.nomPrenom = (DICT_CIVILITES[IDcivilite]["civiliteAbrege"] + " " + nom + " " + prenom).strip()
                else:
                    self.nomPrenom = (nom + " " + prenom).strip()
                self.intitule = self.nomPrenom

                if not self.correspondant:
                    self.correspondant = IDindividu
        self.refusInitiaux = (refus_pub,refus_mel)

        # Listes de diffusion de la famille
        req = """SELECT rattachements.IDindividu, abonnements.IDabonnement, abonnements.IDliste
                FROM rattachements LEFT JOIN abonnements ON rattachements.IDindividu = abonnements.IDindividu
                WHERE (((rattachements.IDfamille)=%d));""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        for IDindividu,IDabonnement, IDliste in listeDonnees:
            if IDliste not in self.dictDiffusionOriginale:
                self.dictDiffusionOriginale[IDliste] = {"individus":[IDindividu,],"abonnements":[IDabonnement,]}
                self.dictDiffusionNew[IDliste] = {"individus": [IDindividu, ], "abonnements": [IDabonnement, ]}
            else:
                self.dictDiffusionOriginale[IDliste]["individus"].append(IDindividu)
                self.dictDiffusionOriginale[IDliste]["abonnements"].append(IDabonnement)
                self.dictDiffusionNew[IDliste]["individus"].append(IDindividu)
                self.dictDiffusionNew[IDliste]["abonnements"].append(IDabonnement)

        # préparation des trois états possibles pour les coches diffusion famille
        nbIndividus = len(self.ctrl_adresse_auto.lstIndividus)
        lstStates = []
        for nomliste, IDliste in self.ctrl_listesdiff.listeDiff:
            if IDliste not in self.dictDiffusionNew:
                lstStates.append(wx.CHK_UNCHECKED)
            elif len(self.dictDiffusionNew[IDliste]["individus"])>= nbIndividus:
                lstStates.append(wx.CHK_CHECKED)
            elif len(self.dictDiffusionNew[IDliste]["individus"]) == 0:
                lstStates.append(wx.CHK_UNCHECKED)
            else:
                lstStates.append(wx.CHK_UNDETERMINED)
        self.ctrl_listesdiff.Set3States(lstStates)

        # Adresse de référence pour la famille
        self.lstAdresse, self.IDcorrespondant = usa.GetDBadresse(IDfamille = self.IDfamille)
        self.strAdresse = usa.CompacteAdresse(self.lstAdresse)
        if self.IDcorrespondant:
            # infos complémentaires de l'individu
            req = """SELECT nom, prenom, IDcategorie_travail, profession, travail_tel, travail_mail, tel_domicile, 
                            tel_mobile, tel_fax, mail, refus_pub, refus_mel
                    FROM individus WHERE IDindividu=%d;""" % self.IDcorrespondant
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            if len(listeDonnees) > 0:
                nom, prenom, IDcategorie, profession, travail_tel, travail_mail, tel_domicile,\
                tel_mobile, tel_fax, mail, refus_pub, refus_mel = listeDonnees[0]

                if not self.IDcorrespondant in self.ctrl_adresse_auto.lstIndividusAffiches:
                    # l'adresse de référence n'est pas dans la famille : on l'ajoute
                    rue,cp,ville = usa.LstAdresseToChamps(self.lstAdresse)
                    self.ctrl_adresse_auto.AjouteItem(self.IDcorrespondant,nom,prenom,None,rue,cp,ville)

                # adresse forcément automatique
                self.ctrl_adresse_auto.SetID(self.IDcorrespondant)

                # Activité professionnelle
                self.ctrl_categorie.SetID(IDcategorie)
                if not profession: profession = ""
                self.ctrl_profession.SetValue(profession)
                self.ctrl_travail_tel.SetNumero(travail_tel)
                self.ctrl_travail_mail.SetMail(travail_mail)

                # Coords
                self.ctrl_tel_domicile.SetNumero(tel_domicile)
                self.ctrl_tel_mobile.SetNumero(tel_mobile)
                self.ctrl_tel_mob2.SetNumero(tel_fax)
                self.ctrl_mail.SetMail(mail)

        if self.intitule:
            self.designationB.SetLabel(self.intitule)

        if self.IDcorrespondant in self.ctrl_adresse_auto.lstIndividus:
            self.bouton_adresse.Enable(True)
            self.ctrl_adresse.Enable(True)
        else:
            self.bouton_adresse.Enable(False)
            self.ctrl_adresse.Enable(False)
        #self.OnTextAdresse(None)
        DB.Close()

    def ValidationData(self):
        """ Validation des données avant Sauvegarde """
        valide, messageErreur = self.ctrl_mail.Validation()
        if valide == False :
            dlg = wx.MessageDialog(self, _("L'adresse email personnelle n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        valide, messageErreur = self.ctrl_travail_mail.Validation()
        if valide == False :
            dlg = wx.MessageDialog(self, _("L'adresse email professionnelle n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if self.cat == "famille":
            adresse_intitule = self.designationB.GetValue().lower()
            mess = ""
            if not "famille" in adresse_intitule.lower():
                for prenom in self.ctrl_adresse_auto.lstPrenomsTitulaires:
                    if not prenom.lower() in adresse_intitule:
                        mess += prenom+", "
            if len(mess) > 0:
                dlg = wx.MessageDialog(self,
                        "Confirmez-vous?\n\nPrénom titulaire '%s' absent dans la désignation.\nFamille adressée à : '%s'"
                                       %(mess,adresse_intitule),_("Vérification"), wx.YES_NO | wx.ICON_EXCLAMATION)
                ret = dlg.ShowModal()
                dlg.Destroy()
                if ret == wx.ID_YES:
                    pass
                else:
                    return False
        return True

    def GetData(self):
        dictDonnees = {
            "adresse_auto" : self.ctrl_adresse_auto.GetDonnee(),

            "travail_categorie" : self.ctrl_categorie.GetID(),
            "profession" : self.ctrl_profession.GetValue(),
            "travail_tel" : self.ctrl_travail_tel.GetNumero(),
            "travail_mail" : self.ctrl_travail_mail.GetMail(),

            "tel_domicile" : self.ctrl_tel_domicile.GetNumero(),
            "tel_mobile" : self.ctrl_tel_mobile.GetNumero(),
            "tel_fax" : self.ctrl_tel_mob2.GetNumero(),
            "mail" : self.ctrl_mail.GetMail(),
            "refus_pub" : self.ctrl_refus_pub.Value,
            "refus_mel" : self.ctrl_refus_mel.Value,
            }

        return dictDonnees

    def Sauvegarde(self):
        """ Sauvegarde des données dans la base """
        dictDonnees = self.GetData()
        DB = GestionDB.DB()

        # modification de champs de l'individu pointé et représentant la famille
        listeDonnees = []
        if self.cat=="individu":
            if dictDonnees["adresse_auto"]:
                listeDonnees = [("rue_resid", ""),
                                ("cp_resid", ""),
                                ("ville_resid", ""),
                                ]
            listeDonnees.append(("adresse_auto", dictDonnees["adresse_auto"])),
        listeDonnees += [
                            ("IDcategorie_travail", dictDonnees["travail_categorie"]),
                            ("profession", dictDonnees["profession"]),
                            ("travail_tel", dictDonnees["travail_tel"]),
                            ("travail_mail",  dictDonnees["travail_mail"]),
                            ("tel_domicile", dictDonnees["tel_domicile"]),
                            ("tel_mobile", dictDonnees["tel_mobile"]),
                            ("tel_fax", dictDonnees["tel_fax"]),
                            ("mail", dictDonnees["mail"]),
                            ("refus_pub", dictDonnees["refus_pub"]),
                            ("refus_mel", dictDonnees["refus_mel"]),
                        ]
        ok = True
        if self.cat == "famille":
            if self.IDcorrespondant:
                self.IDindividu = self.IDcorrespondant
            if self.IDindividu == self.parent.IDindividu:
                ok = False
        if ok:
            DB.ReqMAJ("individus", listeDonnees, "IDindividu", self.IDindividu)

        # Listes de diffusion et autres ------------
        if self.cat=="individu":
            nouvellesListes = self.ctrl_listesdiff.GetIDcoches()
            # Ajout
            for IDliste in nouvellesListes :
                if IDliste not in self.listesDiffusionInitiale :
                    listeDonnees = [ ("IDliste", IDliste), ("IDindividu", self.IDindividu) ]
                    IDlisteNew = DB.ReqInsert("abonnements", listeDonnees)
            # Suppression
            for IDliste in self.listesDiffusionInitiale :
                if IDliste not in nouvellesListes :
                    IDabonnement = self.dictDiffusionInitiale[IDliste]
                    DB.ReqDEL("abonnements", "IDabonnement", IDabonnement)

        elif self.cat == "famille":
            # application des refus famille à l'ensemble des membres, seront ensuite portés dans table familles plus loin
            strMembres = str(self.ctrl_adresse_auto.lstIndividus)[1:-1]
            refusnow = (self.ctrl_refus_pub.GetValue(), self.ctrl_refus_mel.GetValue())
            for ix in range(2):
                refus = refusnow[ix]
                if hasattr(self,"refusInitiaux") and self.refusInitiaux[ix] != int(refus) :
                    # le refus famille a été modifié on l'applique
                    champ = ("refus_pub","refus_mel")[ix]
                    req = """   UPDATE individus 
                                SET %s = %d 
                                WHERE IDindividu IN (%s);"""%(champ,refus,strMembres)
                    ret = DB.ExecuterReq(req,MsgBox="UPDATE individus.refus_")

            # Ajout abonnements -------------------
            lstAjouts = []
            for IDliste, dict in self.dictDiffusionNew.items():
                if IDliste in self.dictDiffusionOriginale:
                    for IDindividu in dict["individus"]:
                        if not IDindividu in self.dictDiffusionOriginale[IDliste]["individus"]:
                            lstAjouts.append([("IDliste", IDliste[1]), ("IDindividu", IDindividu)])
                else:
                    for IDindividu in dict["individus"]:
                        lstAjouts.append([("IDliste", IDliste[1]), ("IDindividu", IDindividu)])
            for listeDonnees in lstAjouts:
                DB.ReqInsert("abonnements", listeDonnees,MsgBox="%s Individu Sauvegarde.Insert "%str(listeDonnees))
            # suppression abonnements
            lstSuppr = []
            for IDliste, dict in self.dictDiffusionOriginale.items():
                for IDindividu in dict["individus"]:
                    if not IDindividu in self.dictDiffusionNew[IDliste]["individus"]:
                        lstSuppr.append(dict["abonnements"][dict["individus"].index(IDindividu)])
            for IDabonnement in lstSuppr:
                DB.ReqDEL("abonnements", "IDabonnement", IDabonnement)

            # zones de famille -------
            adresse_individu = self.ctrl_adresse_auto.GetID()
            # cas d'une nouvelle famille
            if not adresse_individu:
                adresse_individu = self.correspondant
            if not adresse_individu:
                wx.MessageBox("Corrigé: L'adresse de correspondance famille sera sa propre adresse ","Correction automatique")
                adresse_individu = self.IDindividu

            listeDonnees = [
                                ("adresse_intitule", self.designationB.GetValue()),
                                ("adresse_individu", adresse_individu ),
                                ("refus_pub",self.ctrl_refus_pub.GetValue()),
                                ("refus_mel",self.ctrl_refus_mel.GetValue()),
                            ]
            DB.ReqMAJ("familles", listeDonnees, "IDfamille", self.IDfamille,MsgBox="Sauvegarde.familles")

        DB.Close()

class Panel_coords(wx.Panel):
    def __init__(self, parent, IDindividu=None,IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_coords",style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.majEffectuee = True
        # Deux panels contacts l'un pour l'individu, et l'éventuel deuxième pour la famille
        contactInd = Panel_contact(self, IDindividu=IDindividu, cat="individu")
        self.lstContacts = [contactInd,]
        if IDfamille:
            contactFam = Panel_contact(self,IDfamille=IDfamille,cat="famille")
            self.lstContacts.append(contactFam)
        self.__do_layout()

    def __do_layout(self):
        sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        for contact in self.lstContacts:
            sizer.Add(contact,1,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def MAJ(self):
        for contact in self.lstContacts:
            contact.MAJ()
        return

    def ValidationData(self):
        # la validation se fait dans chaque partie de l'écran
        for contact in self.lstContacts:
            ret = contact.ValidationData()
            if not ret : return False
        return True

    def Sauvegarde(self):
        for contact in self.lstContacts:
            contact.Sauvegarde()

# Pour tests -----------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, size=(800,700))
        self.IDindividu = 1724
        IDfamille = 1724
        self.nouvelleFiche = False
        #IDfamille = None
        if IDfamille : size = (700,1780)
        else: size = (1350,1000)
        #self.ctrl = Panel_3StateCheckBoxes(self,)
        self.ctrl = Panel_coords(self, IDindividu=self.IDindividu, IDfamille=IDfamille)
        self.ctrl.MAJ()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()