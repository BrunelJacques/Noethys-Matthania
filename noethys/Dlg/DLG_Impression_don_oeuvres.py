#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import os
import FonctionsPerso

from Utils import UTILS_Parametres
from Utils import UTILS_Conversion

from Ctrl import CTRL_Saisie_date

import GestionDB

from Data import DATA_Civilites as Civilites
LISTE_CIVILITES = Civilites.LISTE_CIVILITES

def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))




class Choix_donateur(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.dictAdresses = {}
        self.dictDonnees = {}
    
    def SetListeDonnees(self, IDcompte_payeur=None):
        self.listeNoms = []
        self.dictAdresses = {}
        self.dictDonnees = {}
                    
        # Si on vient d'une fiche familiale : On affiche uniquement la famille en cours
        DB = GestionDB.DB()
        req = """SELECT IDrattachement, rattachements.IDindividu, rattachements.IDfamille, IDcategorie, titulaire, nom, prenom, IDcivilite,
        adresse_auto, rue_resid, cp_resid, ville_resid
        FROM rattachements 
        LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = rattachements.IDfamille
        WHERE comptes_payeurs.IDcompte_payeur=%d and titulaire=1 and IDcategorie=1
        ORDER BY IDrattachement;""" % IDcompte_payeur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeTitulaires = []
        for IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire, nom, prenom, IDcivilite, adresse_auto, rue_resid, cp_resid, ville_resid in listeDonnees :
            
            # Recherche du nom des titulaires
            civilite = self.GetCivilite(IDcivilite)
            nomIndividu = "%s%s %s" % (civilite, nom, prenom)
            listeTitulaires.append( (IDindividu, nomIndividu) )
            
            # Recherche de l'adresse
            adresseComplete = ""
            if rue_resid != None : adresseComplete += rue_resid
            if cp_resid != None : adresseComplete += " " + cp_resid
            if ville_resid != None : adresseComplete += " " + ville_resid
            self.dictAdresses[IDindividu] =  { "adresse_auto" : adresse_auto, "adresseComplete" : adresseComplete }
            
        nbreTitulaires = len(listeTitulaires)
        if nbreTitulaires == 0 : 
            nomTitulaires = _("Pas de titulaires !")
        if nbreTitulaires == 1 : 
            nomTitulaires = listeTitulaires[0][1]
        if nbreTitulaires == 2 : 
            nomTitulaires = _("%s et %s") % (listeTitulaires[0][1], listeTitulaires[1][1])
        if nbreTitulaires > 2 :
            nomTitulaires = ""
            for IDindividu, nomTitulaire in listeTitulaires[:-2] :
                nomTitulaires += "%s, " % nomTitulaire
            nomTitulaires += listeTitulaires[-1][1]
        self.listeNoms.append(nomTitulaires)
        self.dictDonnees[0] = IDindividu
        
        index = 1
        for IDindividu, nomTitulaire in listeTitulaires :
            if nomTitulaire != nomTitulaires :
                self.listeNoms.append(nomTitulaire)
                self.dictDonnees[index] = IDindividu
                index += 1
                
        # Remplissage du contr�le
        self.SetItems(self.listeNoms)
        
        if len(self.listeNoms) > 0 :
            self.Select(0)
    
    def GetAdresse(self):
        """ Permet d'obtenir l'adresse de l'item s�lectionn� dans la liste """
        index = self.GetSelection()
        if index == -1 : return ""
        if (index in self.dictDonnees) == False : return ""
        IDindividu = self.dictDonnees[index]
        adresse_auto = self.dictAdresses[IDindividu]["adresse_auto"]
        adresseComplete = self.dictAdresses[IDindividu]["adresseComplete"]
        
        if adresse_auto != None :
            # Recherche une adresse li�e
            for IDindividuTmp, dictAdresse in self.dictAdresses.items() :
                if IDindividuTmp == adresse_auto :
                    return dictAdresse["adresseComplete"]
        else:
            return adresseComplete
        
    
    def GetCivilite(self, IDcivilite=None):
        for groupe, civilites in LISTE_CIVILITES :
            for civilite in civilites :
                if civilite[0] == IDcivilite : 
                    return civilite[2] + " "
        return ""
    
    def GetNom(self):
        index = self.GetSelection()
        if index == -1 : return ""
        return self.GetStringSelection() 

# ------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Mode(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDmode, label, numero_piece, nbre_chiffres, 
        frais_gestion, frais_montant, frais_pourcentage, frais_arrondi, frais_label
        FROM modes_reglements
        ORDER BY label;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = []
        self.dictDonnees = {}
        index = 0
        for IDmode, label, numero_piece, nbre_chiffres, frais_gestion, frais_montant, frais_pourcentage, frais_arrondi, frais_label in listeDonnees :
            self.dictDonnees[index] = { 
                "ID" : IDmode, "label" : label, "numero_piece" : numero_piece, "nbre_chiffres" : nbre_chiffres,
                "frais_gestion" : frais_gestion, "frais_montant" : frais_montant, "frais_pourcentage" : frais_pourcentage, 
                "frais_arrondi" : frais_arrondi, "frais_label" : frais_label, 
                }
            listeItems.append(label)
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
    
    def GetInfosMode(self):
        """ R�cup�re les infos sur le mode s�lectionn� """
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]
    
    def GetNomMode(self):
        index = self.GetSelection()
        if index == -1 : return ""
        return self.GetStringSelection() 
        
# -----------------------------------------------------------------------------------------------------------------------


class Dialog(wx.Dialog):
    def __init__(self, parent, IDcotisation=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDcotisation = IDcotisation
        self.IDfamille = None
        
        self.numero = ""
        self.montant = 0.00
        self.totalVentilation = 0.00
        
        # B�n�ficiaire
        self.staticbox_beneficiaire_staticbox = wx.StaticBox(self, -1, _("B�n�ficiaire"))
        self.label_nom_beneficiaire = wx.StaticText(self, -1, _("Nom :"))
        self.ctrl_nom_beneficiaire = wx.TextCtrl(self, -1, "")
        self.label_adresse_beneficiaire = wx.StaticText(self, -1, _("Adresse :"))
        self.ctrl_adresse_beneficiaire = wx.TextCtrl(self, -1, "")
        self.label_objet = wx.StaticText(self, -1, _("Objet :"))
        self.ctrl_objet = wx.TextCtrl(self, -1, "")
        self.label_type = wx.StaticText(self, -1, _("Type :"))
        self.ctrl_type = wx.TextCtrl(self, -1, "")
        
        # Donateur
        self.staticbox_donateur_staticbox = wx.StaticBox(self, -1, _("Donateur"))
        self.label_nom_donateur = wx.StaticText(self, -1, _("Nom :"))
        self.radio_nom_auto = wx.RadioButton(self, -1, "", style=wx.RB_GROUP)
        self.ctrl_nom_auto = Choix_donateur(self)
        self.radio_nom_autre = wx.RadioButton(self, -1, _("Autre :"))
        self.ctrl_nom_autre = wx.TextCtrl(self, -1, "")
        self.label_adresse_donateur = wx.StaticText(self, -1, _("Adresse :"))
        self.ctr_adresse_donateur = wx.TextCtrl(self, -1, "")
        
        # Versement
        self.staticbox_versement_staticbox = wx.StaticBox(self, -1, _("Versement"))
        self.label_date_versement = wx.StaticText(self, -1, _("Date :"))
        self.ctrl_date_versement = CTRL_Saisie_date.Date2(self)
        self.label_mode_versement = wx.StaticText(self, -1, _("Mode :"))
        self.radio_mode_auto = wx.RadioButton(self, -1, "", style=wx.RB_GROUP)
        self.ctrl_mode_auto = CTRL_Mode(self)
        self.radio_mode_autre = wx.RadioButton(self, -1, _("Autre :"))
        self.ctrl_mode_autre = wx.TextCtrl(self, -1, "")
        
        # M�morisation des param�tres de l'organisme b�n�ficiaire
        self.ctrl_memoriser_organisme = wx.CheckBox(self, -1, _("M�moriser l'organisme b�n�ficiaire"))
        font = self.GetFont() 
        font.SetPointSize(7)
        self.ctrl_memoriser_organisme.SetFont(font)
        self.ctrl_memoriser_organisme.SetValue(True) 
        
        # Date �dition
        self.label_date_edition = wx.StaticText(self, -1, _("Date d'�dition :"))
        self.ctrl_date_edition = CTRL_Saisie_date.Date2(self)
        self.ctrl_date_edition.SetDate(datetime.date.today())
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer par Email"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aper�u"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioNom, self.radio_nom_auto)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioNom, self.radio_nom_autre)
        self.Bind(wx.EVT_CHOICE, self.OnChoixNom, self.ctrl_nom_auto)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_mode_auto)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_mode_autre)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        
        # Init Contr�les
        if self.IDcotisation != None :
            self.Importation() 
        self.OnRadioNom(None)
        self.OnRadioMode(None)

    def __set_properties(self):
        self.SetTitle(_("Edition d'un re�u Dons aux Oeuvres"))
        self.ctrl_memoriser_organisme.SetToolTip(wx.ToolTip(_("Cochez cette case pour ne pas avoir � re-saisir les donn�es sur l'organisme la prochaine fois !")))
        self.ctrl_nom_beneficiaire.SetToolTip(wx.ToolTip(_("Saisissez ici le nom de l'organisme")))
        self.ctrl_adresse_beneficiaire.SetToolTip(wx.ToolTip(_("Saisissez ici l'adresse de l'organisme")))
        self.ctrl_objet.SetToolTip(wx.ToolTip(_("Saisissez ici l'objet de l'organisme")))
        self.ctrl_type.SetToolTip(wx.ToolTip(_("Saisissez ici le type d'oeuvre dont il s'agit")))
        self.ctrl_nom_auto.SetToolTip(wx.ToolTip(_("S�lectionnez un destinataire")))
        self.ctrl_nom_autre.SetToolTip(wx.ToolTip(_("Saisissez un nom de destinataire")))
        self.ctr_adresse_donateur.SetToolTip(wx.ToolTip(_("Saisissez ici l'adresse du destinataire")))
        self.ctrl_date_versement.SetToolTip(wx.ToolTip(_("Saisissez ici la date du versement")))
        self.ctrl_mode_auto.SetToolTip(wx.ToolTip(_("S�lectionnez ici le mode de versement")))
        self.ctrl_mode_autre.SetToolTip(wx.ToolTip(_("Saisissez ici un autre mode de versement")))
        self.ctrl_date_edition.SetToolTip(wx.ToolTip(_("Saisissez ici la date d'�dition du document")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_email.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer ce document par Email")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((550, 400))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_date_edition = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        staticbox_versement = wx.StaticBoxSizer(self.staticbox_versement_staticbox, wx.VERTICAL)
        grid_sizer_versement = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_mode = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_mode_autre = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_mode_auto = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        staticbox_donateur = wx.StaticBoxSizer(self.staticbox_donateur_staticbox, wx.VERTICAL)
        grid_sizer_donateur = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_nom_donateur = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_nom_donateur_autre = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_nom_donateur_auto = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        staticbox_beneficiaire = wx.StaticBoxSizer(self.staticbox_beneficiaire_staticbox, wx.VERTICAL)
        grid_sizer_beneficiaire = wx.FlexGridSizer(rows=4, cols=2, vgap=5, hgap=5)
        grid_sizer_beneficiaire.Add(self.label_nom_beneficiaire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_beneficiaire.Add(self.ctrl_nom_beneficiaire, 0, wx.EXPAND, 0)
        grid_sizer_beneficiaire.Add(self.label_adresse_beneficiaire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_beneficiaire.Add(self.ctrl_adresse_beneficiaire, 0, wx.EXPAND, 0)
        grid_sizer_beneficiaire.Add(self.label_objet, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_beneficiaire.Add(self.ctrl_objet, 0, wx.EXPAND, 0)
        grid_sizer_beneficiaire.Add(self.label_type, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_beneficiaire.Add(self.ctrl_type, 0, wx.EXPAND, 0)
        grid_sizer_beneficiaire.AddGrowableCol(1)
        staticbox_beneficiaire.Add(grid_sizer_beneficiaire, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_beneficiaire, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        grid_sizer_donateur.Add(self.label_nom_donateur, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_nom_donateur_auto.Add(self.radio_nom_auto, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_nom_donateur_auto.Add(self.ctrl_nom_auto, 0, wx.EXPAND, 0)
        grid_sizer_nom_donateur_auto.AddGrowableCol(1)
        grid_sizer_nom_donateur.Add(grid_sizer_nom_donateur_auto, 1, wx.EXPAND, 0)
        grid_sizer_nom_donateur_autre.Add(self.radio_nom_autre, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_nom_donateur_autre.Add(self.ctrl_nom_autre, 0, wx.EXPAND, 0)
        grid_sizer_nom_donateur_autre.AddGrowableCol(1)
        grid_sizer_nom_donateur.Add(grid_sizer_nom_donateur_autre, 1, wx.EXPAND, 0)
        grid_sizer_nom_donateur.AddGrowableCol(0)
        grid_sizer_donateur.Add(grid_sizer_nom_donateur, 1, wx.EXPAND, 0)
        grid_sizer_donateur.Add(self.label_adresse_donateur, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_donateur.Add(self.ctr_adresse_donateur, 0, wx.EXPAND, 0)
        grid_sizer_donateur.AddGrowableCol(1)
        staticbox_donateur.Add(grid_sizer_donateur, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_donateur, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_versement.Add(self.label_date_versement, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_versement.Add(self.ctrl_date_versement, 0, 0, 0)
        grid_sizer_versement.Add(self.label_mode_versement, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_mode_auto.Add(self.radio_mode_auto, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_mode_auto.Add(self.ctrl_mode_auto, 0, wx.EXPAND, 0)
        grid_sizer_mode_auto.AddGrowableCol(1)
        grid_sizer_mode.Add(grid_sizer_mode_auto, 1, wx.EXPAND, 0)
        grid_sizer_mode_autre.Add(self.radio_mode_autre, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_mode_autre.Add(self.ctrl_mode_autre, 0, wx.EXPAND, 0)
        grid_sizer_mode_autre.AddGrowableCol(1)
        grid_sizer_mode.Add(grid_sizer_mode_autre, 1, wx.EXPAND, 0)
        grid_sizer_mode.AddGrowableCol(0)
        grid_sizer_versement.Add(grid_sizer_mode, 1, wx.EXPAND, 0)
        grid_sizer_versement.AddGrowableCol(1)
        staticbox_versement.Add(grid_sizer_versement, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_versement, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_date_edition.Add(self.ctrl_memoriser_organisme, 0, 0, 0)
        grid_sizer_date_edition.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_date_edition.Add(self.label_date_edition, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_date_edition.Add(self.ctrl_date_edition, 0, 0, 0)
        grid_sizer_date_edition.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_date_edition, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_email, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
    
    def OnChoixNom(self, event):
        adresse = self.ctrl_nom_auto.GetAdresse() 
        self.ctr_adresse_donateur.SetValue(adresse)

    def OnRadioNom(self, event): 
        if self.radio_nom_auto.GetValue() == True :
            self.ctrl_nom_auto.Enable(True)
            self.ctrl_nom_autre.Enable(False)
        else:
            self.ctrl_nom_auto.Enable(False)
            self.ctrl_nom_autre.Enable(True)
            self.ctrl_nom_autre.SetFocus()

    def OnRadioMode(self, event): 
        if self.radio_mode_auto.GetValue() == True :
            self.ctrl_mode_auto.Enable(True)
            self.ctrl_mode_autre.Enable(False)
        else:
            self.ctrl_mode_auto.Enable(False)
            self.ctrl_mode_autre.Enable(True)
            self.ctrl_mode_autre.SetFocus()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Cotisations1")

    def OnBoutonEmail(self, event): 
        """ Envoi par mail """
        from Utils import UTILS_Envoi_email
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=self.IDfamille, nomDoc=FonctionsPerso.GenerationNomDoc("RECUDONAUXOEUVRES", "pdf") , categorie="recu_don_oeuvres")

    def OnBoutonOk(self, event): 
        self.CreationPDF() 

    def CreationPDF(self, nomDoc=FonctionsPerso.GenerationNomDoc("RECUDONAUXOEUVRES", "pdf"), afficherDoc=True):
        dictChampsFusion = {}

        # V�rifie que la cotisation a �t� pay�e
        if self.totalVentilation < self.montant :
            dlg = wx.MessageDialog(self, _("Cette cotisation n'a pas �t� r�gl�e en int�gralit�.\n\nSouhaitez-vous quand m�me l'�diter ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
        
        # R�cup�ration des donn�es sur l'organisme
        nom_organisme = self.ctrl_nom_beneficiaire.GetValue() 
        adresse_organisme = self.ctrl_adresse_beneficiaire.GetValue()
        objet_organisme = self.ctrl_objet.GetValue() 
        type_organisme = self.ctrl_type.GetValue() 
        
        # M�morisation des donn�es ORGANISME
        if self.ctrl_memoriser_organisme.GetValue() == True :
            UTILS_Parametres.Parametres(mode="set", categorie="don_oeuvres", nom="nom_organisme", valeur=nom_organisme)
            UTILS_Parametres.Parametres(mode="set", categorie="don_oeuvres", nom="adresse_organisme", valeur=adresse_organisme)
            UTILS_Parametres.Parametres(mode="set", categorie="don_oeuvres", nom="objet_organisme", valeur=objet_organisme)
            UTILS_Parametres.Parametres(mode="set", categorie="don_oeuvres", nom="type_organisme", valeur=type_organisme)

        # Donateur
        if self.radio_nom_auto.GetValue() == True :
            nom_donateur = self.ctrl_nom_auto.GetNom() 
        else:
            nom_donateur = self.ctrl_nom_autre.GetValue() 
        adresse_donateur = self.ctr_adresse_donateur.GetValue() 
        
        # Versement
        date_versement = self.ctrl_date_versement.GetDate(FR=True)
        if date_versement == "  /  /    " or date_versement == None :
            date_versement = ""
        if self.radio_mode_auto.GetValue() == True :
            mode = self.ctrl_mode_auto.GetNomMode() 
        else:
            mode = self.ctrl_mode_autre.GetValue() 
        
        # Date �dition
        date_edition = self.ctrl_date_edition.GetDate(FR=True) 
        if date_edition == "  /  /    " or date_edition ==  None :
            date_edition = ""
        
        # Montant
        montant_chiffres = "%.2f �" % self.montant
        montant_lettres = UTILS_Conversion.trad(self.montant)
        
        dictDonnees = {
            "numero" : self.numero,
            "nom_organisme" : nom_organisme,
            "adresse_organisme" : adresse_organisme,
            "objet_organisme" : objet_organisme,
            "type_organisme" : type_organisme,
            "nom_donateur" : nom_donateur,
            "adresse_donateur" : adresse_donateur,
            "date_versement" : date_versement,
            "montant_chiffres" : montant_chiffres,
            "montant_lettres" : montant_lettres,
            "mode" : mode,
            "date_edition" : date_edition,
            }

        dictChampsFusion["{DATE_EDITION}"] = date_edition
        dictChampsFusion["{NUMERO_RECU}"] = self.numero
        dictChampsFusion["{NOM_DONATEUR}"] = nom_donateur
        dictChampsFusion["{ADRESSE_DONATEUR}"] = adresse_donateur
        dictChampsFusion["{DATE_REGLEMENT}"] = date_versement
        dictChampsFusion["{MODE_REGLEMENT}"] = mode
        dictChampsFusion["{MONTANT_CHIFFRES}"] = montant_chiffres
        dictChampsFusion["{MONTANT_LETTRES}"] = montant_lettres

        # Lancement de l'�dition du PDF
        Impression(dictDonnees, nomDoc=nomDoc, afficherDoc=afficherDoc)
        
        return dictChampsFusion



    def Importation(self):
        """ Importation des donnees de la base """
        # R�cup�ration des param�tres ORGANISME
        nom_organisme = UTILS_Parametres.Parametres(mode="get", categorie="don_oeuvres", nom="nom_organisme", valeur=u"")
        adresse_organisme = UTILS_Parametres.Parametres(mode="get", categorie="don_oeuvres", nom="adresse_organisme", valeur=u"")
        objet_organisme = UTILS_Parametres.Parametres(mode="get", categorie="don_oeuvres", nom="objet_organisme", valeur=u"")
        type_organisme = UTILS_Parametres.Parametres(mode="get", categorie="don_oeuvres", nom="type_organisme", valeur=u"")
        
        self.ctrl_nom_beneficiaire.SetValue(nom_organisme)
        self.ctrl_adresse_beneficiaire.SetValue(adresse_organisme)
        self.ctrl_objet.SetValue(objet_organisme)
        self.ctrl_type.SetValue(type_organisme)
        
        # Importation de la cotisation
        DB = GestionDB.DB()
        req = """SELECT
        IDfamille, IDindividu, cotisations.IDtype_cotisation, IDunite_cotisation,
        date_saisie, date_creation_carte, numero,
        date_debut, date_fin, IDprestation, types_cotisations.type, cotisations.observations
        FROM cotisations 
        LEFT JOIN types_cotisations ON types_cotisations.IDtype_cotisation = cotisations.IDtype_cotisation
        WHERE IDcotisation=%d;""" % self.IDcotisation
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) == 0 : 
            DB.Close() 
            return
        
        IDfamille, IDindividu, IDtype_cotisation, IDunite_cotisation, date_saisie, date_creation_carte, numero, date_debut, date_fin, IDprestation, typeCotisation, observations = listeDonnees[0]
        
        self.numero = numero
        if self.numero == None :
            self.numero = ""
            
        self.IDfamille = IDfamille
        
        # Prestation
        if IDprestation == None :
            self.montant = 0.00
        else:
            
            # Importation des donn�es de la prestation
            req = """SELECT
            IDcompte_payeur, label, montant
            FROM prestations 
            WHERE IDprestation=%d;""" % IDprestation
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listePrestations = DB.ResultatReq()
            if len(listePrestations) == 0 :
                DB.Close() 
                return
            
            IDcompte_payeur, label, montant = listePrestations[0]
            
            # Remplit les noms des payeurs
            self.ctrl_nom_auto.SetListeDonnees(IDcompte_payeur)
            self.OnChoixNom(None)
        
            if montant != None :
                self.montant = float(montant)
            
            # Importation des donn�es sur le (ou les) r�glement
            req = """SELECT
            reglements.IDreglement, reglements.date, reglements.IDmode, reglements.montant,
            ventilation.montant
            FROM reglements
            LEFT JOIN ventilation ON ventilation.IDreglement = reglements.IDreglement 
            WHERE ventilation.IDprestation=%d;""" % IDprestation
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeReglements = DB.ResultatReq()
            
            listeDates = []
            listeModes = []
            totalVentilation = 0.0
            for IDreglement, date, IDmode, montant_reglement, montant_ventilation in listeReglements :
                listeDates.append(date)
                listeModes.append((montant_reglement, IDmode))
                totalVentilation += montant_ventilation
            listeDates.sort() 
            listeModes.sort() 
            
            if len(listeDates) > 0 : self.ctrl_date_versement.SetDate(listeDates[-1])
            if len(listeModes) > 0 : 
                IDmode = listeModes[-1][1]
                self.ctrl_mode_auto.SetID(IDmode)
            
            self.totalVentilation = totalVentilation
        
        DB.Close()

# -----------------------------------------------------------------------------------------------------------------

class Impression():
    def __init__(self, dictDonnees={}, nomDoc=FonctionsPerso.GenerationNomDoc("RECUDONAUXOEUVRES", "pdf") , afficherDoc=True):
        """ Imprime un re�u Dons aux Oeuvres """
        
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.rl_config import defaultPageSize
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        styleSheet = getSampleStyleSheet()
        self.hauteur_page = defaultPageSize[1]
        self.largeur_page = defaultPageSize[0]
        self.inch = inch
        
        # Initialisation du PDF
        PAGE_HEIGHT=defaultPageSize[1]
        PAGE_WIDTH=defaultPageSize[0]
        doc = SimpleDocTemplate(nomDoc)
        story = []

        # ---------------- Titre du document ----------------------------------------------------------------
        
        largeursColonnes = ( (300,150) )
        
        txt1 = Paragraph(u"""
        <para align=center fontSize=16><b>Re�u Dons Aux Oeuvres</b></para>
        """, styleSheet['BodyText'])
        
        txt2 = Paragraph(u"""
        <para align=center fontSize=8>Num�ro d'ordre du re�u</para>
        """, styleSheet['BodyText'])
        
        txt3 = Paragraph(u"""
        <para align=center fontSize=9>(Article 200-5 du Code G�n�ral des Imp�ts)</para>
        """, styleSheet['BodyText'])
        
        txt4 = Paragraph(u"""
        <para align=center fontsize=16>%s</para>
        """ % dictDonnees["numero"], styleSheet['BodyText'])
        
        # Valeurs du tableau
        dataTableau = [
        [ "" , txt2 ],
        [ [ txt1, txt3] , txt4 ],
        ]
        
        # Style du tableau
        style = TableStyle([
                            ('GRID', (1,1), (1,1), 0.25, colors.black), 
                            ('VALIGN', (0,0), (-1,-1), "MIDDLE"), 
                            ])
        tableau = Table(dataTableau, largeursColonnes)
        tableau.setStyle(style)
        story.append(tableau)
        story.append(Spacer(0,20)) 


        # ------------ Corps du document -----------------------------------------------------
        largeursColonnes = ( (450,) )
        
        # Texte du tableau
        txt10 = Paragraph(u"""
        <para align=center><b>B�n�ficiaire des versements</b></para>
        """, styleSheet['BodyText'])
        
        txt20 = Paragraph(u"""
        <br/>
        Nom ou d�nomination : %s<br/>
        <br/>
        Adresse : %s<br/>
        <br/>
        Objet : %s<br/>
        <br/>
        %s<br/>   
        <br/>     
        """ % (dictDonnees["nom_organisme"], dictDonnees["adresse_organisme"], dictDonnees["objet_organisme"], dictDonnees["type_organisme"]), styleSheet['BodyText'])
        
        # Donateur
        txt30 = Paragraph(u"""
        <para align=center><b>Donateur</b></para>
        """, styleSheet['BodyText'])
        
        txt40 = Paragraph(u"""
        <br/>
        Nom : %s<br/>
        <br/>
        Adresse : %s
        <br/>
        <br/>
        """ % (dictDonnees["nom_donateur"] , dictDonnees["adresse_donateur"]) , styleSheet['BodyText'])
        
        # Montant
        txt50 = Paragraph(u"""
        <para align=center><b>Versement</b></para>
        """, styleSheet['BodyText'])
        
        txt60 = Paragraph(u"""
        <br/>
        Le b�n�ficiaire reconna�t avoir re�u au titre des versements ouvrant droit � r�duction d'imp�t la somme de : <br/>
        <br/>
        """, styleSheet['BodyText'])
        
        txt70 = Paragraph(u"""
        <para align=center fontSize=12>
        <b>%s</b><br/>
        <br/>
        <b>Soit %s</b>
        </para>
        """ % (dictDonnees["montant_chiffres"], dictDonnees["montant_lettres"]) , styleSheet['BodyText'])
        
        txt80 = Paragraph(u"""
        <br/>
        Date du paiement : %s<br/>
        <br/>
        Mode de versement : %s
        <br/>
        <br/>
        """ % (dictDonnees["date_versement"], dictDonnees["mode"]), styleSheet['BodyText'])
        
        txt100 = Paragraph(u"""
        Fait en double exemplaire<br/>
        (Un pour le donateur - un pour l'association)<br/>
        <br/>
        """, styleSheet['BodyText'])
        
        if dictDonnees["date_edition"] != "" :
            date_edition = _("Le %s") % dictDonnees["date_edition"]
        else:
            dictDonnees["date_edition"] = ""
        
        txt110 = Paragraph(u"""
        <para align=right rightIndent=50>
        Date et signature
        <br/>
        <br/>
        %s
        <br/>
        <br/>
        <br/>
        <br/>
        <br/>
        <br/>
        </para>
        """ % date_edition, styleSheet['BodyText'])
        
        # Valeurs du tableau
        dataTableau = [
        [ txt10 ,],
        [ txt20 ,],
        [ "",],
        [ txt30 ,],
        [ txt40 ,],
        [ "",],
        [ txt50 ,],
        [ [txt60, txt70, txt80, txt100, txt110] ,],
        ]
        
        
        # Style du tableau
        style = TableStyle([
                            ('GRID', (0,0), (0,1), 0.25, colors.black), 
                            ('GRID', (0,3), (0,4), 0.25, colors.black), 
                            ('GRID', (0,6), (0,7), 0.25, colors.black), 
                            ])
        tableau = Table(dataTableau, largeursColonnes)
        tableau.setStyle(style)
        story.append(tableau)
        story.append(Spacer(0,20))       
                    
        # Enregistrement du PDF
        try :
            doc.build(story)
        except Exception as err :
            print("Erreur dans ouverture PDF :", err)
            if "Permission denied" in err :
                dlg = wx.MessageDialog(None, _("Noethys ne peut pas cr�er le PDF.\n\nVeuillez v�rifier qu'un autre PDF n'est pas d�j� ouvert en arri�re-plan..."), _("Erreur d'�dition"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return
        
        # Affichage du PDF
        if afficherDoc == True :
            FonctionsPerso.LanceFichierExterne(nomDoc)




if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDcotisation=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
