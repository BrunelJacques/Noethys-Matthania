#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import wx.grid as gridlib
import six
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Choix_modele
import FonctionsPerso

import GestionDB
from Data import DATA_Civilites as Civilites
from Utils import UTILS_Historique
from Utils import UTILS_Identification
from Utils import UTILS_Titulaires
from Utils import UTILS_Questionnaires
from Utils import UTILS_Infos_individus
from Utils import UTILS_Parametres
from Ctrl import CTRL_Editeur_email

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal


DICT_CIVILITES = Civilites.GetDictCivilites()

LISTE_DONNEES = [
    { "nom" : _("Reçu"), "champs" : [
        { "code" : "numero", "label" : _("Numéro")},
        { "code" : "date", "label" : _("Date d'édition")},
        { "code" : "lieu", "label" : _("Lieu d'édition")},
        ] },
    { "nom" : _("Destinataire"), "champs" : [
        { "code" : "nom", "label" : "Nom"}, 
        { "code" : "rue", "label" : "Rue"}, 
        { "code" : "ville", "label" : "CP + Ville"},
        ] },
    { "nom" : _("Organisme"), "champs" : [
        { "code" : "siret", "label" : _("Numéro SIRET")},
        { "code" : "ape", "label" : "Code APE"}, 
        ] },
    ]

TEXTE_INTRO = "Je soussigné{GENRE} {NOM}, {FONCTION}, certifie avoir reçu pour la famille de {FAMILLE} la somme de {MONTANT}."

DICT_DONNEES = {}


def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    if dateDD == None or dateDD == "" : return ""
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
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

class CTRL_Signataires(wx.ComboBox):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ()

    def MAJ(self):
        listeItems, indexDefaut = self.GetListeSignataires()
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
        if indexDefaut != None :
            self.Select(indexDefaut)

    def GetListeSignataires(self):
        db = GestionDB.DB()
        req = """SELECT IDresponsable, IDactivite, nom, fonction, defaut, sexe
        FROM responsables_activite
        ORDER BY nom ASC, IDactivite DESC;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = []
        self.dictSignataires = {}
        indexDefaut = None
        index = 0
        for (IDresponsable, IDactivite, nom, fonction, defaut, sexe) in listeDonnees:
        #    ) in  sorted(listeDonnees, key=lambda index : f'{index[2]} {str(-index[1])}'):
            if nom not in listeItems :
                if not indexDefaut and defaut == 1 :
                    indexDefaut = index
                self.dictSignataires[index] = {
                    "ID" : IDresponsable,
                    "IDactivite" : IDactivite,
                    "nom" : nom,
                    "fonction" : fonction,
                    "defaut" : defaut,
                    "sexe" : sexe,
                    }
                listeItems.append(nom)
                index += 1
        return listeItems, indexDefaut

    def SetID(self, ID=0):
        for index, values in self.dictSignataires.items():
            if values["ID"] == ID :
                self.SetSelection(index)
                break

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictSignataires[index]["ID"]
    
    def GetInfos(self):
        """ Récupère les infos sur le signataire sélectionné """
        index = self.GetSelection()
        if index == -1 :
            txt = self.GetValue()
            if not txt:
                return None
            lstTxt = txt.split(',')
            if len(lstTxt)>1:
                dict = {"nom": lstTxt[0],"fonction":lstTxt[1],"sexe":"H"}
            else:
                dict = {"nom": txt,"fonction":"","sexe":"H"}
            return dict
        return self.dictSignataires[index]

# -----------------------------------------------------------------------------------------------------------------------


class CTRL_Donnees(gridlib.Grid): 
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1, size=(200, 200), style=wx.WANTS_CHARS)
        self.moveTo = None
        self.SetMinSize((100, 100))
        self.parent = parent
        self.dictCodes = {}
        
        self.MAJ_CTRL_Donnees() 
        
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
        # Calcul du nbre de lignes
        nbreLignes = 0
        for dictCategorie in LISTE_DONNEES :
            nbreLignes += 1
            for dictChamp in dictCategorie["champs"] :
                nbreLignes += 1
        
        # Création de la grille
        self.CreateGrid(nbreLignes, 2)
        self.SetColSize(0, 150)
        self.SetColSize(1, 330)
        self.SetColLabelValue(0, "")
        self.SetColLabelValue(1, "")
        self.SetRowLabelSize(1)
        self.SetColLabelSize(1)
        
        # Remplissage avec les données
        key = 0
        for dictCategorie in LISTE_DONNEES :
            nomCategorie = dictCategorie["nom"]
            
            # Création d'une ligne CATEGORIE
            self.SetRowLabelValue(key, "")
            self.SetCellFont(key, 0, wx.Font(8, wx.DEFAULT , wx.NORMAL, wx.BOLD))
            self.SetCellBackgroundColour(key, 0, "#C5DDFA")
            self.SetReadOnly(key, 0, True)
            self.SetCellValue(key, 0, nomCategorie)
            self.SetCellAlignment(key, 0, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
            self.SetCellValue(key, 1, "")
            self.SetCellBackgroundColour(key, 1, "#C5DDFA")
            self.SetReadOnly(key, 1, True)
            self.SetCellSize(key, 0, 1, 2)
            
            key += 1
            
            # Création d'une ligne de données
            for dictChamp in dictCategorie["champs"] :
                code = dictChamp["code"]
                label = dictChamp["label"]
                if code in DICT_DONNEES:
                    valeur = DICT_DONNEES[code]
                else:
                    valeur = ""
                
                # Entete de ligne
                self.SetRowLabelValue(key, "")
                
                # Création de la cellule LABEL
                self.SetCellValue(key, 0, label)
                self.SetCellBackgroundColour(key, 0, "#EEF4FB")
                self.SetReadOnly(key, 0, True)
                self.SetCellAlignment(key, 0, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                self.SetCellValue(key, 1, valeur)
            
                # Mémorisation dans le dictionnaire des données
                self.dictCodes[key] = code
                key += 1
            
        # test all the events
        self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.moveTo = (1, 1)

    def OnCellChange(self, evt):
        # Modification de la valeur dans le dict de données
        numRow = evt.GetRow()
        valeur = self.GetCellValue(numRow, 1)
        code = self.dictCodes[numRow]
        self.SetValeur(code, valeur)
        
    def OnIdle(self, evt):
        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None
        evt.Skip()

    def GetValeur(self, code=""):
        if code in DICT_DONNEES :
            return DICT_DONNEES[code]
        else:
            return None

    def SetValeur(self, code="", valeur = ""):
        global DICT_DONNEES
        DICT_DONNEES[code] = valeur

    def MAJ_CTRL_Donnees(self):
        """ Importe les valeurs de base dans le GRID Données """
        DB = GestionDB.DB()
        
        # Récupération des infos sur l'attestation
        dateDuJour = str(datetime.date.today())
        self.SetValeur("date", DateEngFr(dateDuJour))
        
        req = """SELECT MAX(numero)
        FROM recus
        ;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()     
        if len(listeDonnees) > 0 : 
            numero = listeDonnees[0][0]
            if numero == None :
                numero = 1
            else:
                numero += 1
        else:
            numero = 0
        self.SetValeur("numero", "%06d" % numero)
        
        # Récupération des infos sur l'organisme
        req = """SELECT nom, num_siret, code_ape, ville
        FROM organisateur
        WHERE IDorganisateur=1;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()      
        DB.Close() 
        for nom, num_siret, code_ape, ville in listeDonnees :
            if num_siret != None : 
                self.SetValeur("siret", num_siret)
            else :
                self.SetValeur("siret", "")
            if code_ape != None : 
                self.SetValeur("ape", code_ape)
            else :
                self.SetValeur("ape", "")
            if ville != None : 
                self.SetValeur("lieu", ville.capitalize() )
            else :
                self.SetValeur("lieu", "")
        
        # Récupération des données sur le destinataire
        dictNomsTitulaires = UTILS_Titulaires.GetTitulaires([self.parent.IDfamille,]) 
        dictInfosTitulaires = dictNomsTitulaires[self.parent.IDfamille]
        nomsTitulairesAvecCivilite = dictInfosTitulaires["titulairesAvecCivilite"]
        rue_resid = dictInfosTitulaires["adresse"]["rue"]
        cp_resid = dictInfosTitulaires["adresse"]["cp"]
        ville_resid = dictInfosTitulaires["adresse"]["ville"]
        
        if rue_resid == None : rue_resid = ""
        if cp_resid == None : cp_resid = ""
        if ville_resid == None : ville_resid = ""

        self.SetValeur("nom", nomsTitulairesAvecCivilite)
        self.SetValeur("rue", rue_resid)
        self.SetValeur("ville", cp_resid + " " + ville_resid)
        

# --------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDreglement=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Impression_recu", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDreglement = IDreglement
        self.dictSave = {}
        self.listeAdresses = []
        
        # Importation des données
        self.dictReglement = self.Importation()
        self.IDfamille = self.dictReglement["IDfamille"]
                
        # Bandeau
        intro = _("Vous pouvez ici éditer un reçu de règlement au format PDF. Pour un reçu standard, cliquez tout simplement sur 'Aperçu' ou sur 'Envoyer Par Email'.")
        titre = _("Edition d'un reçu de règlement")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Imprimante.png")
        
        # Données
        self.staticbox_donnees_staticbox = wx.StaticBox(self, -1, _("Données"))
        self.ctrl_donnees = CTRL_Donnees(self)

        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options"))

        self.label_email = wx.StaticText(self, -1, _("Modèle email:"))
        self.ctrl_email = CTRL_Choix_modele.CTRL_Choice(self,
                                                        categorie="recu_reglement",
                                                        table="modeles_emails")
        self.bouton_email_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))

        self.label_modele = wx.StaticText(self, -1, _("Modèle pdf:"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="reglement")
        self.bouton_gestion_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))

        self.label_signataire = wx.StaticText(self, -1, _("Signataire :"))
        self.ctrl_signataire = CTRL_Signataires(self)
        
        self.label_intro = wx.StaticText(self, -1, _("Intro pdf:"))
        self.ctrl_intro = wx.CheckBox(self, -1, "")
        self.ctrl_intro.SetValue(True)
        self.ctrl_texte_intro = wx.TextCtrl(self, -1, TEXTE_INTRO)
        self.label_prestations = wx.StaticText(self, -1, _("Prestations :"))
        self.ctrl_prestations = wx.CheckBox(self, -1, _("Afficher la liste des prestations payées avec ce règlement"))

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer par Email"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aperçu"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties(parent)
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_gestion_modeles)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmailModeles, self.bouton_email_modeles)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckIntro, self.ctrl_intro)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)

        # Importation des paramètres perso

        dictValeursDefaut = {
            "intro_activer" : True,
            "intro_texte" : TEXTE_INTRO,
            "prestations_afficher" : False,
            "signataire": 0
            }
        dictParametres = UTILS_Parametres.ParametresCategorie(mode="get",
                                                              categorie="impression_recu",
                                                              dictParametres=dictValeursDefaut)
        
        # Init contrôles
        self.ctrl_intro.SetValue(dictParametres["intro_activer"])
        if dictParametres["intro_texte"] != None :
            self.ctrl_texte_intro.SetValue(dictParametres["intro_texte"])
        self.ctrl_prestations.SetValue(dictParametres["prestations_afficher"])
        self.ctrl_signataire.SetID(dictParametres["signataire"])
        self.OnCheckIntro(None) 
    
    def MemorisationParametres(self):
        dictValeurs = {
            "intro_activer" : self.ctrl_intro.GetValue(),
            "intro_texte" : self.ctrl_texte_intro.GetValue(),
            "prestations_afficher" : self.ctrl_prestations.GetValue(),
            "signataire": self.ctrl_signataire.GetID()
            }
        UTILS_Parametres.ParametresCategorie(mode="set", categorie="impression_recu",
                                             dictParametres=dictValeurs)
        
    def __set_properties(self,parent):
        if parent and parent.Name:
            nomParent = parent.Name
        else: nomParent = "Test"
        self.SetTitle(f"{nomParent}-DLG_Impression_recu")
        self.ctrl_donnees.SetToolTip(wx.ToolTip(_("Vous pouvez modifier ici les données de base")))
        self.ctrl_email.SetToolTip(wx.ToolTip(_("Selectionnez un modèle de texte mail")))
        self.ctrl_modele.SetToolTip(wx.ToolTip(_("Selectionnez un modèle de documents")))
        self.ctrl_signataire.SetToolTip(wx.ToolTip(_("Sélectionnez ici le signataire du document")))
        self.ctrl_intro.SetToolTip(wx.ToolTip(_("Cochez cette case pour inclure le texte d'introduction : 'Je soussigné... atteste...' ")))
        self.ctrl_texte_intro.SetToolTip(wx.ToolTip(_("Vous pouvez modifier ici le texte d'introduction. \n\nUtilisez les mots-clés {GENRE}, {NOM}, {FONCTION}, {ENFANTS}, \n{DATE_DEBUT} et {DATE_FIN} pour inclure dynamiquement les \nvaleurs correspondantes.")))
        self.ctrl_prestations.SetToolTip(wx.ToolTip(_("Afficher la liste des prestations payées avec ce règlement")))
        self.bouton_gestion_modeles.SetToolTip(wx.ToolTip(_("Cliquez ici pour accéder à la gestion des modèles de documents PDF")))
        self.bouton_email_modeles.SetToolTip(wx.ToolTip(_("Cliquez ici pour accéder à la gestion des modèles de texte email")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_email.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer ce document par Email")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher le PDF")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((570, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Données
        staticbox_donnees = wx.StaticBoxSizer(self.staticbox_donnees_staticbox, wx.VERTICAL)
        staticbox_donnees.Add(self.ctrl_donnees, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_donnees, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        
        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=5, cols=2, vgap=5, hgap=10)
        
        # Modèle email
        grid_sizer_options.Add(self.label_email, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_email = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_email.Add(self.ctrl_email, 0, wx.EXPAND, 0)
        grid_sizer_email.Add(self.bouton_email_modeles, 0, 0, 0)
        grid_sizer_email.AddGrowableCol(0)
        grid_sizer_options.Add(grid_sizer_email, 1, wx.EXPAND, 0)

        # Modèle pdf
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
        grid_sizer_options.Add(self.label_intro, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_intro = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_intro.Add(self.ctrl_intro, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_intro.Add(self.ctrl_texte_intro, 1,wx.EXPAND, 0)
        grid_sizer_intro.AddGrowableCol(1)
        grid_sizer_options.Add(grid_sizer_intro, 1, wx.EXPAND, 0)
        
        grid_sizer_options.AddGrowableCol(1)
        staticbox_options.Add(grid_sizer_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_options, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # Prestations
        grid_sizer_options.Add(self.label_prestations, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_prestations, 1, wx.EXPAND, 0)

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

    def OnBoutonEmailModeles(self, event):
        from Dlg import DLG_Modeles_emails
        dlg = DLG_Modeles_emails.Dialog(self, categorie="recu_reglement")
        dlg.ShowModal()
        ID = dlg.GetIDmodele()
        dlg.Destroy()
        if ID:
            self.ctrl_email.SetID(ID)
        self.ctrl_email.MAJ()

    def OnBoutonModeles(self, event): 
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="reglement")
        dlg.ShowModal()
        ID = dlg.GetIDmodele()
        dlg.Destroy()
        if ID:
            self.ctrl_modele.SetID(ID)
        self.ctrl_modele.MAJ()
    
    def Importation(self):
        # Récupération des informations sur le règlement
        DB = GestionDB.DB()
        req = """SELECT 
        reglements.IDreglement, 
        reglements.IDcompte_payeur, comptes_payeurs.IDfamille,
        reglements.date, 
        reglements.IDmode, modes_reglements.label, 
        reglements.IDemetteur, emetteurs.nom, 
        reglements.numero_piece, reglements.montant, 
        payeurs.IDpayeur, payeurs.nom, 
        reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe, 
        encaissement_attente, 
        date_saisie, IDutilisateur
        FROM reglements
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
        LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
        LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
        LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
        WHERE IDreglement=%d
        """ % self.IDreglement
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeReglements = DB.ResultatReq()  
        DB.Close() 
        if len(listeReglements) == 0 : return None
        
        IDreglement, IDcompte_payeur, IDfamille, date,  IDmode, nomMode, IDemetteur, nomEmetteur, \
        numPiece, montant, IDpayeur, nomPayeur, observations, numQuittancier, \
        IDprestation_frais, IDcompteDepot, date_differe, encaissement_attente, \
        date_saisie, IDutilisateur = listeReglements[0]
        
        dictReglements = {}
        dictReglements["IDreglement"] = IDreglement
        dictReglements["IDcompte_payeur"] = IDcompte_payeur
        dictReglements["IDfamille"] = IDfamille
        dictReglements["dateReglement"] = date
        dictReglements["IDmode"] = IDmode
        dictReglements["nomMode"] = nomMode
        dictReglements["IDemetteur"] = IDemetteur
        dictReglements["nomEmetteur"] = nomEmetteur
        dictReglements["numPiece"] = numPiece
        dictReglements["montant"] = montant
        dictReglements["IDpayeur"] = IDpayeur
        dictReglements["nomPayeur"] = nomPayeur
        dictReglements["observations"] = observations
        dictReglements["numQuittancier"] = numQuittancier
        dictReglements["IDprestation_frais"] = IDprestation_frais
        dictReglements["IDcompteDepot"] = IDcompteDepot
        dictReglements["date_differe"] = date_differe
        dictReglements["encaissement_attente"] = encaissement_attente
        dictReglements["date_saisie"] = date_saisie
        dictReglements["IDutilisateur"] = IDutilisateur
        
        return dictReglements

    def OnBoutonAnnuler(self, event):
        # Mémoriser le reçu
        self.Sauvegarder() 

        # Mémorisation des paramètres perso
        self.MemorisationParametres() 

        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Rglements1")

    def Sauvegarder(self, demander=True):
        """ Sauvegarder la trace du reçu """
        if len(self.dictSave) == 0 : 
            return
        
        # Demande la confirmation de sauvegarde
        if demander == True :
            dlg = wx.MessageDialog(self, _("Souhaitez-vous mémoriser le reçu édité ?\n\n(Cliquez NON si c'était juste un test sinon cliquez OUI)"), _("Sauvegarde"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        # Sauvegarde de l'attestation
        DB = GestionDB.DB()
        listeDonnees = [ 
            ("numero", self.dictSave["numero"] ), 
            ("IDfamille", self.dictSave["IDfamille"] ), 
            ("date_edition", self.dictSave["date_edition"] ), 
            ("IDutilisateur", self.dictSave["IDutilisateur"] ), 
            ("IDreglement", self.dictSave["IDreglement"] ), 
            ]
        IDrecu = DB.ReqInsert("recus", listeDonnees)        
        DB.Close()
        
        # Mémorisation de l'action dans l'historique
        UTILS_Historique.InsertActions([{
                "IDfamille" : self.IDfamille,
                "IDcategorie" : 28, 
                "action" : _("Edition d'un reçu pour le règlement ID%d") % self.dictSave["IDreglement"],
                },])

    # Génération du pdf et son affichage
    def OnBoutonOk(self, event): 
        self.CreationPDF()

    # Lance envoi mail avec l'embarquement de CreationPDF ci-dessous
    def OnBoutonEmail(self, event):
        IDmodelEmail = self.ctrl_email.GetID()
        if IDmodelEmail == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un modèle de texte mail!"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        """ Envoi par mail """
        from Utils import UTILS_Envoi_email
        nomDoc = FonctionsPerso.GenerationNomDoc(f"RECU-{self.IDfamille}-", "pdf",unique=False)
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self,
                                            IDfamille=self.IDfamille,
                                            IDmodele=IDmodelEmail,
                                            nomDoc= nomDoc,
                                            CreationPDF=self.CreationPDF,
                                            categorie="recu_reglement",
                                            listeAdresses=self.listeAdresses)

    # appelé par UTILS_Envoi_email.EnvoiEmailFamille ou par self.OnBoutonOk
    def CreationPDF(self, nomDoc=None, afficherDoc=True, **kw):
        if not nomDoc:
            nomDoc = FonctionsPerso.GenerationNomDoc("RECU_REGLEMENT", "pdf")
        dictChampsFusion = {}

        # Récupération des valeurs de base
        dictDonnees = DICT_DONNEES

        # Récupération des infos sur l'organisme
        dictOrganisme = self.GetDictOrganisme()

        date_edition = dictDonnees["date"]
        try:
            date_editionDD = DateEngEnDateDD(DateFrEng(date_edition))
        except:
            date_editionDD = ""

        # Insertion des données de base dans le dictValeurs
        IDfamille = self.IDfamille
        dictValeurs = {
            "IDfamille": self.IDfamille,
            "{IDFAMILLE}": str(self.IDfamille),
            "num_recu": dictDonnees["numero"],
            "{LIEU_EDITION}": dictDonnees["lieu"],
            "{DESTINATAIRE_NOM}": dictDonnees["nom"],
            "{DESTINATAIRE_RUE}": dictDonnees["rue"],
            "{DESTINATAIRE_VILLE}": dictDonnees["ville"],

            "{NUM_RECU}": dictDonnees["numero"],
            "{DATE_EDITION}": date_edition,
            "{DATE_EDITION_LONG}": DateComplete(date_editionDD),
            "{DATE_EDITION_COURT}": date_edition,

            "{ORGANISATEUR_NOM}": dictOrganisme["nom"],
            "{ORGANISATEUR_RUE}": dictOrganisme["rue"],
            "{ORGANISATEUR_CP}": dictOrganisme["cp"],
            "{ORGANISATEUR_VILLE}": dictOrganisme["ville"],
            "{ORGANISATEUR_TEL}": dictOrganisme["tel"],
            "{ORGANISATEUR_FAX}": dictOrganisme["fax"],
            "{ORGANISATEUR_MAIL}": dictOrganisme["mail"],
            "{ORGANISATEUR_SITE}": dictOrganisme["site"],
            "{ORGANISATEUR_AGREMENT}": dictOrganisme["num_agrement"],
            "{ORGANISATEUR_SIRET}": dictOrganisme["num_siret"],
            "{ORGANISATEUR_APE}": dictOrganisme["code_ape"],
        }

        # Récupération des infos de base individus et familles
        self.infosIndividus = UTILS_Infos_individus.Informations(
            lstIDfamilles=[self.IDfamille, ])
        dictValeurs.update(self.infosIndividus.GetDictValeurs(mode="famille",
                                                              ID=IDfamille,
                                                              formatChamp=True))

        # Récupération des questionnaires
        Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille")
        for dictReponse in Questionnaires.GetDonnees(IDfamille):
            dictValeurs[dictReponse["champ"]] = dictReponse["reponse"]
            if dictReponse["controle"] == "codebarres":
                dictValeurs["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = \
                dictReponse["reponse"]

        # Récupération du texte d'intro
        if self.ctrl_intro.GetValue() == True:
            dictValeurs["intro"] = self.GetTexteIntro()
        else:
            dictValeurs["intro"] = None

        # Envoi des informations sur le règlement
        for key, valeur in self.dictReglement.items():
            dictValeurs[key] = valeur

        dictValeurs["{IDREGLEMENT}"] = str(dictValeurs["IDreglement"])
        dictValeurs["{DATE_REGLEMENT}"] = DateEngFr(dictValeurs["dateReglement"])
        dictValeurs["{MODE_REGLEMENT}"] = dictValeurs["nomMode"]
        if dictValeurs["nomEmetteur"] != None:
            dictValeurs["{NOM_EMETTEUR}"] = dictValeurs["nomEmetteur"]
        else:
            dictValeurs["{NOM_EMETTEUR}"] = ""
        dictValeurs["{NUM_PIECE}"] = dictValeurs["numPiece"]
        dictValeurs["{MONTANT_REGLEMENT}"] = "%.2f %s" % (dictValeurs["montant"], SYMBOLE)
        dictValeurs["{NOM_PAYEUR}"] = dictValeurs["nomPayeur"]
        dictValeurs["{NUM_QUITTANCIER}"] = six.text_type(dictValeurs["numQuittancier"])
        dictValeurs["{DATE_SAISIE}"] = DateEngFr(dictValeurs["date_saisie"])
        dictValeurs["{OBSERVATIONS}"] = "%s" % dictValeurs["observations"]

        if dictValeurs["date_differe"] != None:
            dictValeurs["{DATE_DIFFERE}"] = DateEngFr(dictValeurs["date_differe"])
        else:
            dictValeurs["{DATE_DIFFERE}"] = ""

        # Récupération liste des prestations
        if self.ctrl_prestations.GetValue() == True:
            dictValeurs["prestations"] = self.GetPrestations()
        else:
            dictValeurs["prestations"] = []

        # Préparation des données pour une sauvegarde de l'attestation
        self.dictSave = {}
        self.dictSave["numero"] = dictDonnees["numero"]
        self.dictSave["IDfamille"] = self.IDfamille
        self.dictSave["date_edition"] = DateFrEng(dictDonnees["date"])
        self.dictSave["IDutilisateur"] = dictValeurs['IDutilisateur']
        self.dictSave["IDreglement"] = self.IDreglement

        # Récupération du modèle
        IDmodele = self.ctrl_modele.GetID()
        if IDmodele == None:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement sélectionner un modèle !"),
                                   _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dictChampsFusion.update(self.GetDictUtilisateur())

        dictChampsFusion["{DATE_EDITION_RECU}"] = DateFrEng(dictDonnees["date"])
        dictChampsFusion["{NUMERO_RECU}"] = dictDonnees["numero"]
        dictChampsFusion["{ID_REGLEMENT}"] = str(dictValeurs["{IDREGLEMENT}"])
        dictChampsFusion["{DATE_REGLEMENT}"] = dictValeurs["{DATE_REGLEMENT}"]
        dictChampsFusion["{MODE_REGLEMENT}"] = dictValeurs["{MODE_REGLEMENT}"]
        dictChampsFusion["{NOM_EMETTEUR}"] = dictValeurs["{NOM_EMETTEUR}"]
        dictChampsFusion["{NUM_PIECE}"] = dictValeurs["{NUM_PIECE}"]
        dictChampsFusion["{MONTANT_REGLEMENT}"] = dictValeurs["{MONTANT_REGLEMENT}"]
        dictChampsFusion["{NOM_PAYEUR}"] = dictValeurs["{NOM_PAYEUR}"]
        dictChampsFusion["{NUM_QUITTANCIER}"] = dictValeurs["{NUM_QUITTANCIER}"]
        dictChampsFusion["{DATE_SAISIE}"] = dictValeurs["{DATE_SAISIE}"]
        dictChampsFusion["{DATE_DIFFERE}"] = dictValeurs["{DATE_DIFFERE}"]

        # Fabrication du PDF
        from Utils import UTILS_Impression_recu
        UTILS_Impression_recu.Impression(dictValeurs, IDmodele=IDmodele, nomDoc=nomDoc,
                                         afficherDoc=afficherDoc)
        return ({self.IDfamille: dictChampsFusion}, {0: nomDoc})

    def GetPrestations(self):
        DB = GestionDB.DB()

        # Recherche de la ventilation
        req = """SELECT IDprestation, SUM(ventilation.montant) AS total_ventilation
        FROM ventilation
        WHERE ventilation.IDreglement=%d
        GROUP BY IDprestation;""" % self.IDreglement
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        liste_prestations = []
        dict_ventilation = {}
        for IDprestation, total_ventilation in listeDonnees :
            liste_prestations.append(IDprestation)
            dict_ventilation[IDprestation] = total_ventilation

        # Recherche des prestations
        if len(liste_prestations) == 0 : condition_prestations = "()"
        elif len(liste_prestations) == 1 : condition_prestations = "(%d)" % liste_prestations[0]
        else : condition_prestations = str(tuple(liste_prestations))

        req = """SELECT IDprestation, date, categorie, label,
        activites.IDactivite, activites.nom, activites.abrege,
        individus.nom, individus.prenom,
        montant
        FROM prestations
        LEFT JOIN activites ON activites.IDactivite = prestations.IDactivite
        LEFT JOIN individus ON individus.IDindividu = prestations.IDindividu
        WHERE IDprestation IN %s
        GROUP BY IDprestation
        ORDER BY date;""" % condition_prestations

        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()      
        DB.Close()
        listePrestations = []
        for IDprestation, date, categorie, label, IDactivite, nomActivite, abregeActivite, nomIndividu, prenomIndividu, montant in listeDonnees :
            dateDD = DateEngEnDateDD(date)
            if nomActivite == None : nomActivite = ""
            if abregeActivite == None : abregeActivite = ""
            if prenomIndividu == None : prenomIndividu = ""
            montant = FloatToDecimal(montant)
            ventilation = FloatToDecimal(dict_ventilation[IDprestation])
            dictTemp = {
                "IDprestation" : IDprestation, "date" : dateDD, "categorie" : categorie, "label" : label, "IDactivite" : IDactivite, 
                "nomActivite" : nomActivite, "abregeActivite" : abregeActivite, "prenomIndividu" : prenomIndividu, "montant" : montant, "ventilation" : ventilation,
                }
            listePrestations.append(dictTemp)
        return listePrestations

    def GetTexteIntro(self):
        # Transpose les champs du texte Intro
        dictDonnees = DICT_DONNEES
        # Récupération du signataire
        infosSignataire = self.ctrl_signataire.GetInfos()
        if infosSignataire == None:
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun signataire !"),
                                   _("Annulation"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        nomSignataire = infosSignataire["nom"]
        fonctionSignataire = infosSignataire["fonction"]
        sexeSignataire = infosSignataire["sexe"]
        if sexeSignataire == "H":
            genreSignataire = ""
        else:
            genreSignataire = "e"

        # Récupération et transformation du texte d'intro
        textIntro = self.ctrl_texte_intro.GetValue()
        textIntro = textIntro.replace("{GENRE}", genreSignataire)
        textIntro = textIntro.replace("{NOM}", nomSignataire)
        textIntro = textIntro.replace("{FONCTION}", fonctionSignataire)
        textIntro = textIntro.replace("{FAMILLE}", dictDonnees["nom"])
        textIntro = textIntro.replace("{MONTANT}", "<b>%.2f %s</b>" % (
            self.dictReglement["montant"], SYMBOLE))

        return textIntro

    # Récupération des infos sur l'organisme
    def GetDictOrganisme(self):
        DB = GestionDB.DB()
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        dictOrganisme = {}
        for (nom, rue, cp, ville, tel, fax, mail, site, num_agrement,
             num_siret, code_ape) in listeDonnees :
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
        return dictOrganisme

    # Récup les infos de l'utilsateur courant
    def GetDictUtilisateur(self):
        dUser = UTILS_Identification.GetDictUtilisateur()
        if not dUser:
            dUser = UTILS_Identification.GetDictUtilSqueleton()
        return CTRL_Editeur_email.GetChampsStandards(dUser)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None, IDreglement=38658)
    app.SetTopWindow(dlg)
##    dlg.ctrl_prestations.SetValue(True)
    dlg.ShowModal()
    app.MainLoop()
