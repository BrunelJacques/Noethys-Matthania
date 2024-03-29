#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import os


from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Choix_modele
import FonctionsPerso

import GestionDB
from Data import DATA_Civilites as Civilites
from Utils import UTILS_Historique
from Utils import UTILS_Identification
from Utils import UTILS_Titulaires
from Utils import UTILS_Questionnaires
from Utils import UTILS_Parametres
from Utils import UTILS_Infos_individus

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal


DICT_CIVILITES = Civilites.GetDictCivilites()

LISTE_DONNEES = [
    { "nom" : _("Re�u"), "champs" : [
        { "code" : "numero", "label" : "Num�ro"}, 
        { "code" : "date", "label" : "Date d'�dition"}, 
        { "code" : "lieu", "label" : "Lieu d'�dition"},
        ] },
    { "nom" : _("Destinataire"), "champs" : [
        { "code" : "nom", "label" : "Nom"}, 
        { "code" : "rue", "label" : "Rue"}, 
        { "code" : "ville", "label" : "CP + Ville"},
        ] },
    { "nom" : _("Organisme"), "champs" : [
        { "code" : "siret", "label" : "Num�ro SIRET"}, 
        { "code" : "ape", "label" : "Code APE"}, 
        ] },
    ]

TEXTE_INTRO = _("Je soussign�{SIGNATAIRE_GENRE} {SIGNATAIRE_NOM}, {SIGNATAIRE_FONCTION}, atteste avoir inscrit pour la famille de {FAMILLE_NOM} l'enfant {INDIVIDU_PRENOM} � l'activit� {ACTIVITE_NOM_LONG}.")

DICT_DONNEES = {}


def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    if dateDD == None or dateDD == "" : return ""
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    if dateEng == None or dateEng == "" : return ""
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    if textDate == None or textDate == "" : return ""
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateFrEng(textDate):
    if textDate == None or textDate == "" : return ""
    text = str(textDate[6:10]) + "-" + str(textDate[3:5]) + "-" + str(textDate[:2])
    return text

def FormateStr(valeur=u""):
    try :
        if valeur == None : return ""
        elif type(valeur) == int : return str(valeur)
        elif type(valeur) == float : return str(valeur)
        else : return valeur
    except : 
        return ""

def FormateDate(dateStr):
    if dateStr == "" or dateStr == None : return ""
    date = str(datetime.date(year=int(dateStr[:4]), month=int(dateStr[5:7]), day=int(dateStr[8:10])))
    text = str(date[8:10]) + "/" + str(date[5:7]) + "/" + str(date[:4])
    return text

def FormateBool(valeur):
    if valeur == 1 or valeur == "1" :
        return "Oui"
    else :
        return "Non"


class CTRL_Signataires(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
        if len(self.dictDonnees) > 0 :
            self.SetSelection(0)
    
    def MAJ(self, listeActivites=[] ):
        listeItems, indexDefaut = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
        if indexDefaut != None :
            self.Select(indexDefaut)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDresponsable, IDactivite, nom, fonction, defaut, sexe
        FROM responsables_activite
        ORDER BY nom;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = []
        self.dictDonnees = {}
        indexDefaut = None
        index = 0
        for IDresponsable, IDactivite, nom, fonction, defaut, sexe in listeDonnees :
            if indexDefaut == None and defaut == 1 : indexDefaut = index
            self.dictDonnees[index] = { 
                "ID" : IDresponsable, "IDactivite" : IDactivite,
                "nom" : nom, "fonction" : fonction,
                "defaut" : defaut, "sexe" : sexe, 
                }
            listeItems.append(nom)
            index += 1
        return listeItems, indexDefaut

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]
    
    def GetInfos(self):
        """ R�cup�re les infos sur le signataire s�lectionn� """
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]
        


# --------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDinscription=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Impression_inscription", style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent
        self.IDinscription = IDinscription
        self.dictSave = {}
        self.listeAdresses = []
        
        # Importation des donn�es
        self.dictInscription = self.Importation()
        self.IDfamille = self.dictInscription["IDFAMILLE"]
                
        # Bandeau
        intro = _("Vous pouvez ici �diter une confirmation d'inscription. S�lectionnez un mod�le de document puis cliquez tout simplement sur 'Aper�u' ou sur 'Envoyer Par Email'.")
        titre = _("Edition d'une confirmation d'inscription")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Imprimante.png")

        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options"))
        self.label_modele = wx.StaticText(self, -1, _("Mod�le :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="inscription")
        self.bouton_gestion_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        self.label_signataire = wx.StaticText(self, -1, _("Signataire :"))
        self.ctrl_signataire = CTRL_Signataires(self)
        
        self.label_intro = wx.StaticText(self, -1, _("Intro :"))
        self.ctrl_intro = wx.CheckBox(self, -1, "")
        self.ctrl_intro.SetValue(True)
        self.ctrl_texte_intro = wx.TextCtrl(self, -1, TEXTE_INTRO, style=wx.TE_MULTILINE)
        self.ctrl_texte_intro.SetMinSize((400, 120))
        self.label_tableau = wx.StaticText(self, -1, _("Tableau :"))
        self.ctrl_tableau = wx.CheckBox(self, -1, _("Afficher un tableau comportant les caract�ristiques de l'inscription"))

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer par Email"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aper�u"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_gestion_modeles)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckIntro, self.ctrl_intro)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        
        # Init contr�les
        self.OnCheckIntro(None) 
        self.ctrl_texte_intro.SetValue(UTILS_Parametres.Parametres(mode="get", categorie="edition_confirmation_inscription", nom="intro", valeur=TEXTE_INTRO))
        self.ctrl_intro.SetValue(UTILS_Parametres.Parametres(mode="get", categorie="edition_confirmation_inscription", nom="check_intro", valeur=True))
        self.ctrl_tableau.SetValue(UTILS_Parametres.Parametres(mode="get", categorie="edition_confirmation_inscription", nom="check_tableau", valeur=True))
        self.OnCheckIntro(None)
        wx.CallLater(0, self.Layout)

    def __set_properties(self):
        self.ctrl_modele.SetToolTip(wx.ToolTip(_("Selectionnez un mod�le de documents")))
        self.ctrl_signataire.SetToolTip(wx.ToolTip(_("S�lectionnez ici le signataire du document")))
        self.ctrl_intro.SetToolTip(wx.ToolTip(_("Cochez cette case pour inclure le texte d'introduction : 'Je soussign�... atteste...' ")))
        listeMotsCles = []
        for mot in list(self.dictInscription.keys()) :
            listeMotsCles.append(u"{%s}" % mot)
        self.ctrl_texte_intro.SetToolTip(wx.ToolTip(_("Vous pouvez modifier ici le texte d'introduction. \n\nVous pouvez utiliser les mots-cl�s suivants : %s") % ", ".join(listeMotsCles)))
        self.ctrl_tableau.SetToolTip(wx.ToolTip(_("Afficher un tableau comportant les caract�ristiques de l'inscription")))
        self.bouton_gestion_modeles.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la gestion des mod�les de documents")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_email.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer ce document par Email")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher le PDF")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((570, 500))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=10)
        
        # Mod�le
        grid_sizer_options.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_modele = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_modele.Add(self.ctrl_modele, 0, wx.EXPAND, 0)
        grid_sizer_modele.Add(self.bouton_gestion_modeles, 0, 0, 0)
        grid_sizer_modele.AddGrowableCol(0)
        grid_sizer_options.Add(grid_sizer_modele, 1, wx.EXPAND, 0)
        
        # Signataire
        grid_sizer_options.Add(self.label_signataire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_signataire, 1, wx.EXPAND, 0)
        
        # Intro
        grid_sizer_options.Add(self.label_intro, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_intro = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_intro.Add(self.ctrl_intro, 0, 0, 0)
        grid_sizer_intro.Add(self.ctrl_texte_intro, 1,wx.EXPAND, 0)
        grid_sizer_intro.AddGrowableCol(1)
        grid_sizer_options.Add(grid_sizer_intro, 1, wx.EXPAND, 0)
        
        grid_sizer_options.AddGrowableCol(1)
        staticbox_options.Add(grid_sizer_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_options, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # Prestations
        grid_sizer_options.Add(self.label_tableau, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_tableau, 1, wx.EXPAND, 0)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_email, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
        
    def OnCheckIntro(self, event):
        if self.ctrl_intro.GetValue() == True :
            self.ctrl_texte_intro.Enable(True)
        else:
            self.ctrl_texte_intro.Enable(False)

    def OnBoutonModeles(self, event): 
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="inscription")
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_modele.MAJ() 
    
    def Importation(self):
        # R�cup�ration des informations sur l'inscription
        dictChamps = {
            "inscriptions.IDinscription" : "IDINSCRIPTION",
            "inscriptions.date_inscription" : "DATE_INSCRIPTION",
            "inscriptions.date_desinscription" : "EST_PARTI",
            
            "activites.IDactivite" : "IDACTIVITE",
            "activites.nom" : "ACTIVITE_NOM_LONG",
            "activites.abrege" : "ACTIVITE_NOM_COURT", 
            
            "groupes.IDgroupe" : "IDGROUPE",
            "groupes.nom" : "GROUPE_NOM_LONG",
            "groupes.abrege" : "GROUPE_NOM_COURT", 
            
            "categories_tarifs.IDcategorie_tarif" : "IDCATEGORIETARIF",
            "categories_tarifs.nom" : "NOM_CATEGORIE_TARIF",
            
            "individus.IDindividu" : "IDINDIVIDU",
            "individus.IDcivilite" : "IDCIVILITE",
            "individus.nom" : "INDIVIDU_NOM",
            "individus.prenom" : "INDIVIDU_PRENOM",
            "individus.date_naiss" : "INDIVIDU_DATE_NAISS",
            "individus.cp_naiss" : "INDIVIDU_CP_NAISS",
            "individus.ville_naiss" : "INDIVIDU_VILLE_NAISS",
            "individus.adresse_auto" : "INDIVIDU_ADRESSE_AUTO",
            "individus.rue_resid" : "INDIVIDU_RUE",
            "individus.cp_resid" : "INDIVIDU_CP",
            "individus.ville_resid" : "INDIVIDU_VILLE",
            "individus.profession" : "INDIVIDU_PROFESSION",
            "individus.employeur" : "INDIVIDU_EMPLOYEUR",
            "individus.tel_domicile" : "INDIVIDU_TEL_DOMICILE",
            "individus.tel_mobile" : "INDIVIDU_TEL_MOBILE",
            "individus.tel_fax" : "INDIVIDU_FAX",
            "individus.mail" : "INDIVIDU_EMAIL",
            "individus.travail_tel" : "INDIVIDU_TEL_PRO",
            "individus.travail_fax" : "INDIVIDU_FAX_PRO",
            "individus.travail_mail" : "INDIVIDU_EMAIL_PRO",
            
            "familles.IDfamille" : "IDFAMILLE",
            "caisses.nom" : "FAMILLE_CAISSE",
            "regimes.nom" : "FAMILLE_REGIME",
            "familles.num_allocataire" : "FAMILLE_NUMALLOC",
            }
        
        listeChamps = list(dictChamps.keys())
        
        DB = GestionDB.DB()
        req = """SELECT %s
        FROM inscriptions
        LEFT JOIN activites ON activites.IDactivite = inscriptions.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = inscriptions.IDgroupe
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
        LEFT JOIN individus ON individus.IDindividu = inscriptions.IDindividu
        LEFT JOIN familles ON familles.IDfamille = inscriptions.IDfamille
        LEFT JOIN caisses ON caisses.IDcaisse = familles.IDcaisse
        LEFT JOIN regimes ON regimes.IDregime = caisses.IDregime
        WHERE IDinscription=%d
        """ % (", ".join(listeChamps), self.IDinscription)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()  
        if len(listeDonnees) == 0 : return None
        
        dictInscription = {}
        index = 0
        for nomChamp in listeChamps :
            code = dictChamps[nomChamp]
            valeur = listeDonnees[0][index]
            dictInscription[code] = valeur
            index += 1

        return dictInscription

    def OnBoutonAnnuler(self, event):
        # Historique
        self.Sauvegarder() 
        # Parametres
        UTILS_Parametres.Parametres(mode="set", categorie="edition_confirmation_inscription", nom="intro", valeur=self.ctrl_texte_intro.GetValue())
        UTILS_Parametres.Parametres(mode="set", categorie="edition_confirmation_inscription", nom="check_intro", valeur=self.ctrl_intro.GetValue())
        UTILS_Parametres.Parametres(mode="set", categorie="edition_confirmation_inscription", nom="check_tableau", valeur=self.ctrl_tableau.GetValue())
        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide()

    def Sauvegarder(self, demander=True):
        """ Sauvegarder la trace du re�u """
        if len(self.dictSave) == 0 : 
            return
        
        # Demande la confirmation de sauvegarde
        if demander == True :
            dlg = wx.MessageDialog(self, _("Souhaitez-vous m�moriser dans l'historique le document �dit� ?\n\n(Cliquez NON si c'�tait juste un test sinon cliquez OUI)"), _("Sauvegarde"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
                
        # M�morisation de l'action dans l'historique
        UTILS_Historique.InsertActions([{
                "IDfamille" : self.IDfamille,
                "IDindividu" : self.IDindividu,
                "IDcategorie" : 34, 
                "action" : _("Edition d'une confirmation d'inscription pour l'activit� '%s'") % self.dictSave["activite"],
                },])

    def OnBoutonOk(self, event): 
        self.CreationPDF() 

    def OnBoutonEmail(self, event): 
        """ Envoi par mail """
        from Utils import UTILS_Envoi_email
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=self.IDfamille, nomDoc=FonctionsPerso.GenerationNomDoc("INSCRIPTION", "pdf"), categorie="inscription", listeAdresses=self.listeAdresses)
    
    def CreationPDF(self, nomDoc=FonctionsPerso.GenerationNomDoc("INSCRIPTION", "pdf"), afficherDoc=True):
        dictChampsFusion = {}
        
        # R�cup�ration des valeurs de base
        dictDonnees = DICT_DONNEES
        
        # R�cup�ration des infos sur l'organisme
        DB = GestionDB.DB()
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()      
        dictOrganisme = {}
        for nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape in listeDonnees :
            dictOrganisme["nom"] = nom
            dictOrganisme["rue"] = rue
            dictOrganisme["cp"] = cp
            if ville != None : ville = ville.capitalize()
            dictOrganisme["ville"] = ville
            dictOrganisme["tel"] = tel
            dictOrganisme["fax"] = fax
            dictOrganisme["mail"] = mail
            dictOrganisme["site"] = site
            dictOrganisme["num_agrement"] = num_agrement
            dictOrganisme["num_siret"] = num_siret
            dictOrganisme["code_ape"] = code_ape
        DB.Close() 
        
        date_editionDD = datetime.date.today() 
        
        # Adresse
        self.IDindividu = self.dictInscription["IDINDIVIDU"]
        individus = UTILS_Titulaires.GetIndividus() 
        self.dictInscription["INDIVIDU_RUE"] = individus[self.IDindividu]["rue"]
        self.dictInscription["INDIVIDU_CP"] = individus[self.IDindividu]["cp"]
        self.dictInscription["INDIVIDU_VILLE"] = individus[self.IDindividu]["ville"]
        
        # Nom Titulaires
        dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=[self.IDfamille,])
        self.dictInscription["FAMILLE_NOM"] = dictTitulaires[self.IDfamille]["titulairesSansCivilite"]
        
        # Civilit�
        dictCivilites = Civilites.GetDictCivilites()
        if self.dictInscription["IDCIVILITE"] == None or self.dictInscription["IDCIVILITE"] == "" :
            IDcivilite = 1
        else :
            IDcivilite = self.dictInscription["IDCIVILITE"]
        self.dictInscription["INDIVIDU_GENRE"] = dictCivilites[IDcivilite]["sexe"]
        self.dictInscription["INDIVIDU_CIVILITE_LONG"]  = dictCivilites[IDcivilite]["civiliteLong"]
        self.dictInscription["INDIVIDU_CIVILITE_COURT"] = dictCivilites[IDcivilite]["civiliteAbrege"] 
        
        # Date de naissance
        if self.dictInscription["INDIVIDU_DATE_NAISS"] == None :
            self.dictInscription["INDIVIDU_AGE"] = None
        else:
            datenaissDD = datetime.date(year=int(self.dictInscription["INDIVIDU_DATE_NAISS"][:4]), month=int(self.dictInscription["INDIVIDU_DATE_NAISS"][5:7]), day=int(self.dictInscription["INDIVIDU_DATE_NAISS"][8:10]))
            datedujour = datetime.date.today()
            age = (datedujour.year - datenaissDD.year) - int((datedujour.month, datedujour.day) < (datenaissDD.month, datenaissDD.day))
            self.dictInscription["INDIVIDU_AGE"] = age

        # Insertion des donn�es de base dans le dictValeurs
        IDfamille = self.IDfamille
        dictValeurs = {
            "IDfamille" : self.IDfamille,
            "{IDFAMILLE}" : str(self.IDfamille),
            
            "{DATE_EDITION}" : DateEngFr(str(date_editionDD)),
            "{DATE_EDITION_LONG}" : DateComplete(date_editionDD),
            "{DATE_EDITION_COURT}" : DateEngFr(str(date_editionDD)),

            "{ORGANISATEUR_NOM}" : dictOrganisme["nom"],
            "{ORGANISATEUR_RUE}" : dictOrganisme["rue"],
            "{ORGANISATEUR_CP}" : dictOrganisme["cp"],
            "{ORGANISATEUR_VILLE}" : dictOrganisme["ville"],
            "{ORGANISATEUR_TEL}" : dictOrganisme["tel"],
            "{ORGANISATEUR_FAX}" : dictOrganisme["fax"],
            "{ORGANISATEUR_MAIL}" : dictOrganisme["mail"],
            "{ORGANISATEUR_SITE}" : dictOrganisme["site"],
            "{ORGANISATEUR_AGREMENT}" : dictOrganisme["num_agrement"],
            "{ORGANISATEUR_SIRET}" : dictOrganisme["num_siret"],
            "{ORGANISATEUR_APE}" : dictOrganisme["code_ape"],
            
            "{IDINSCRIPTION}" : FormateStr(self.dictInscription["IDINSCRIPTION"]),
            "{DATE_INSCRIPTION}" : FormateDate(self.dictInscription["DATE_INSCRIPTION"]),
            "{EST_PARTI}" : FormateBool(self.dictInscription["EST_PARTI"]),
            
            "{IDACTIVITE}" : FormateStr(self.dictInscription["IDACTIVITE"]),
            "{ACTIVITE_NOM_LONG}" : FormateStr(self.dictInscription["ACTIVITE_NOM_LONG"]),
            "{ACTIVITE_NOM_COURT}" : FormateStr(self.dictInscription["ACTIVITE_NOM_COURT"]),
            
            "{IDGROUPE}" : FormateStr(self.dictInscription["IDGROUPE"]),
            "{GROUPE_NOM_LONG}" : FormateStr(self.dictInscription["GROUPE_NOM_LONG"]),
            "{GROUPE_NOM_COURT}" : FormateStr(self.dictInscription["GROUPE_NOM_COURT"]),
            
            "{IDCATEGORIETARIF}" : FormateStr(self.dictInscription["IDCATEGORIETARIF"]),
            "{NOM_CATEGORIE_TARIF}" : FormateStr(self.dictInscription["NOM_CATEGORIE_TARIF"]),
            
            "{IDINDIVIDU}" : FormateStr(self.dictInscription["IDINDIVIDU"]),
            "{INDIVIDU_CIVILITE_LONG}" : FormateStr(self.dictInscription["INDIVIDU_CIVILITE_LONG"]),
            "{INDIVIDU_CIVILITE_COURT}" : FormateStr(self.dictInscription["INDIVIDU_CIVILITE_COURT"]),
            "{INDIVIDU_GENRE}" : FormateStr(self.dictInscription["INDIVIDU_GENRE"]),
            "{INDIVIDU_NOM}" : FormateStr(self.dictInscription["INDIVIDU_NOM"]),
            "{INDIVIDU_PRENOM}" : FormateStr(self.dictInscription["INDIVIDU_PRENOM"]),
            "{INDIVIDU_DATE_NAISS}" : FormateDate(self.dictInscription["INDIVIDU_DATE_NAISS"]),
            "{INDIVIDU_AGE}" : FormateStr(self.dictInscription["INDIVIDU_AGE"]),
            "{INDIVIDU_CP_NAISS}" : FormateStr(self.dictInscription["INDIVIDU_CP_NAISS"]),
            "{INDIVIDU_VILLE_NAISS}" : FormateStr(self.dictInscription["INDIVIDU_VILLE_NAISS"]),
            "{INDIVIDU_RUE}" : FormateStr(self.dictInscription["INDIVIDU_RUE"]),
            "{INDIVIDU_CP}" : FormateStr(self.dictInscription["INDIVIDU_CP"]),
            "{INDIVIDU_VILLE}" : FormateStr(self.dictInscription["INDIVIDU_VILLE"]),
            "{INDIVIDU_PROFESSION}" : FormateStr(self.dictInscription["INDIVIDU_PROFESSION"]),
            "{INDIVIDU_EMPLOYEUR}" : FormateStr(self.dictInscription["INDIVIDU_EMPLOYEUR"]),
            "{INDIVIDU_TEL_DOMICILE}" : FormateStr(self.dictInscription["INDIVIDU_TEL_DOMICILE"]),
            "{INDIVIDU_TEL_MOBILE}" : FormateStr(self.dictInscription["INDIVIDU_TEL_MOBILE"]),
            "{INDIVIDU_FAX}" : FormateStr(self.dictInscription["INDIVIDU_FAX"]),
            "{INDIVIDU_EMAIL}" : FormateStr(self.dictInscription["INDIVIDU_EMAIL"]),
            "{INDIVIDU_TEL_PRO}" : FormateStr(self.dictInscription["INDIVIDU_TEL_PRO"]),
            "{INDIVIDU_FAX_PRO}" : FormateStr(self.dictInscription["INDIVIDU_FAX_PRO"]),
            "{INDIVIDU_EMAIL_PRO}" : FormateStr(self.dictInscription["INDIVIDU_EMAIL_PRO"]),
            
            "{FAMILLE_NOM}" : FormateStr(self.dictInscription["FAMILLE_NOM"]),
            "{FAMILLE_CAISSE}" : FormateStr(self.dictInscription["FAMILLE_CAISSE"]),
            "{FAMILLE_REGIME}" : FormateStr(self.dictInscription["FAMILLE_REGIME"]),
            "{FAMILLE_NUMALLOC}" : FormateStr(self.dictInscription["FAMILLE_NUMALLOC"]),
            }

        # R�cup�ration des infos de base individus et familles
        self.infosIndividus = UTILS_Infos_individus.Informations() 
        dictValeurs.update(self.infosIndividus.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True))
        dictValeurs.update(self.infosIndividus.GetDictValeurs(mode="individu", ID=self.dictInscription["IDINDIVIDU"], formatChamp=True))

        # R�cup�ration des questionnaires
        Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille")
        for dictReponse in Questionnaires.GetDonnees(IDfamille) :
            dictValeurs[dictReponse["champ"]] = dictReponse["reponse"]
            if dictReponse["controle"] == "codebarres" :
                dictValeurs["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = dictReponse["reponse"]

        # R�cup�ration du signataire
        infosSignataire = self.ctrl_signataire.GetInfos()
        if infosSignataire == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun signataire !"), _("Annulation"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        nomSignataire = infosSignataire["nom"]
        fonctionSignataire = infosSignataire["fonction"]
        sexeSignataire = infosSignataire["sexe"]
        if sexeSignataire == "H" :
            genreSignataire = ""
        else:
            genreSignataire = "e"
        
        # R�cup�ration et transformation du texte d'intro
        if self.ctrl_intro.GetValue() == True :
            textIntro = self.ctrl_texte_intro.GetValue()         
            textIntro = textIntro.replace("{SIGNATAIRE_GENRE}", genreSignataire)
            textIntro = textIntro.replace("{SIGNATAIRE_NOM}", nomSignataire)
            textIntro = textIntro.replace("{SIGNATAIRE_FONCTION}", fonctionSignataire)
            for key, valeur in dictValeurs.items() :
                if key.startswith("{") :
                    if valeur == None : valeur = ""
                    if type(valeur) == int : valeur = str(valeur)
                    textIntro = textIntro.replace(key, valeur)
            dictValeurs["intro"] = textIntro
        else:
            dictValeurs["intro"] = None

        # Tableau
        dictValeurs["tableau"] = self.ctrl_tableau.GetValue()

        for key, valeur in dictValeurs.items() :
            if valeur == None : valeur = ""
            dictChampsFusion[key] = valeur
                        
        # Pr�paration des donn�es pour une sauvegarde dans l'historique
        self.dictSave = {}
        self.dictSave["activite"] = self.dictInscription["ACTIVITE_NOM_LONG"]
        self.dictSave["groupe"] = self.dictInscription["GROUPE_NOM_LONG"]
        
        # R�cup�ration du mod�le
        IDmodele = self.ctrl_modele.GetID() 
        if IDmodele == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un mod�le !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
                
        # Fabrication du PDF
        from Utils import UTILS_Impression_inscription
        UTILS_Impression_inscription.Impression(dictValeurs, IDmodele=IDmodele, nomDoc=nomDoc, afficherDoc=afficherDoc)
        
        return dictChampsFusion
    

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None, IDinscription=1)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
