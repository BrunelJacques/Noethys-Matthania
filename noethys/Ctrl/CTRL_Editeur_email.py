#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Module : Propositions de mots clés modifiées selon UTILS_Facturation
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import wx.richtext as rt
import io
import copy
import datetime
import os
import wx.lib.agw.hyperlink as Hyperlink
import GestionDB
from Utils import UTILS_Identification

CATEGORIES = [
    ("saisie_libre", _("Saisie libre")),
    ("releve_prestations", _("Relevé des prestations")),
    ("reglement", _("Règlement")),
    ("recu_reglement", _("Reçu de règlement")),
    ("recu_don_oeuvres", _("Reçu de don aux oeuvres")),
    ("facture", _("Facture")),
    ("rappel", _("Rappel")),
    ("attestation_presence", _("Attestation de présence")),
    ("attestation_fiscale", _("Attestation fiscale")),
    ("reservations", _("Liste des réservations")),
    ("cotisation", _("Cotisation")),
    ("rappel_pieces_manquantes", _("Rappel pièces manquantes")),
    ("portail", _("Rappel des données du compte internet")),
    ("portail_demande_inscription", _("Portail - Demande d'une inscription")),
    ("portail_demande_reservation", _("Portail - Demande d'une réservation")),
    ("portail_demande_renseignement", _("Portail - Demande de modification d'un renseignement")),
    ("portail_demande_facture", _("Portail - Demande d'une facture")),
    ("portail_demande_recu_reglement", _("Portail - Demande d'un reçu de règlement")),
    ("portail_demande_location", _("Portail - Demande d'une location")),
    ("portail_demande_piece", _("Portail - Demande de saisie d'une pièce")),
    ("location", _("Location")),
    ("location_demande", _("Demande de location")),
    ("commande_repas", _("Commande de repas")),
    ("inscription", _("Inscription")),
    ("devis", _("Devis")),
]

MOTSCLES_STANDARDS = [
                ( "{UTILISATEUR_NOM_COMPLET}", _("Nom complet de l'utilisateur") ),
                ( "{UTILISATEUR_NOM}", _("Nom de famille de l'utilisateur") ),
                ( "{UTILISATEUR_PRENOM}", _("Prénom de l'utilisateur") ),
                ( "{DATE_COURTE}", _("Date du jour courte") ),
                ( "{DATE_LONGUE}", _("Date du jour longue") ),
                ]
    
MOTSCLES = {
    
    "saisie_libre" : [
                ],
    
    "releve_prestations" : [
                ( "{DATE_EDITION_RELEVE}", _("Date de l'édition du relevé") ),
                ( "{RESTE_DU}", _("Reste dû indiqué par le relevé") ),
                ],

    "reglement" : [
                ( "{ID_REGLEMENT}", _("ID du règlement") ),
                ( "{DATE_REGLEMENT}", _("Date du règlement") ),
                ( "{MODE_REGLEMENT}", _("Mode de règlement") ),
                ( "{NOM_EMETTEUR}", _("Nom de l'émetteur") ),
                ( "{NUM_PIECE}", _("Numéro de la pièce") ),
                ( "{MONTANT_REGLEMENT}", _("Montant du règlement") ),
                ( "{NOM_PAYEUR}", _("Nom du payeur") ),
                ( "{NUM_QUITTANCIER}", _("Numéro de quittancier") ),
                ( "{DATE_SAISIE}", _("Date de saisie du règlement") ),
                ( "{DATE_DIFFERE}", _("Date d'encaissement différé") ),
                ],

    "recu_reglement" : [
                ( "{DATE_EDITION_RECU}", _("Date d'édition du reçu") ),
                ( "{NUMERO_RECU}", _("Numéro du reçu") ),
                ( "{ID_REGLEMENT}", _("ID du règlement") ),
                ( "{DATE_REGLEMENT}", _("Date du règlement") ),
                ( "{MODE_REGLEMENT}", _("Mode de règlement") ),
                ( "{NOM_EMETTEUR}", _("Nom de l'émetteur") ),
                ( "{NUM_PIECE}", _("Numéro de la pièce") ),
                ( "{MONTANT_REGLEMENT}", _("Montant du règlement") ),
                ( "{NOM_PAYEUR}", _("Nom du payeur") ),
                ( "{NUM_QUITTANCIER}", _("Numéro de quittancier") ),
                ( "{DATE_SAISIE}", _("Date de saisie du règlement") ),
                ("{DATE_DIFFERE}", _("Date d'encaissement différé")),
                ],

    "recu_don_oeuvres" : [
                ( "{DATE_EDITION}", _("Date d'édition du reçu") ),
                ( "{NUMERO_RECU}", _("Numéro du reçu") ),
                ( "{NOM_DONATEUR}", _("Nom du donateur") ),
                ( "{ADRESSE_DONATEUR}", _("Adresse du donateur") ),
                ( "{DATE_REGLEMENT}", _("Date du règlement") ),
                ( "{MODE_REGLEMENT}", _("Mode du règlement") ),
                ( "{MONTANT_CHIFFRES}", _("Montant en chiffres") ),
                ( "{MONTANT_LETTRES}", _("Montant en lettres") ),
                ],

    "facture" : [
                ( "{NATURE}", _("Nature de la pièce(s)") ),
                ( "{NUM_FACTURE}", _("Numéro si pièce FAC,AVO") ),
                ( "{TEXTE_NUMERO}", _("Numéro pièce avec préfixe") ),
                ( "{DATE_EDITION}", _("Date FACTURE de la facture") ),
                ( "{DATE_EDITION_LONG}", _("Date FACTURE, le mois en lettre") ),
                ( "{DATE_DEBUT}", _("Date de début de facturation") ),
                ( "{DATE_FIN}", _("Date de fin de facturation") ),
                ( "{DATE_ECHEANCE}", _("Date d'échance") ),
                ( "{LIB_MONTANT}", _("Libellé pour qualifier le montant") ),
                ( "{MONTANT}", _("Montant de la facture") ),
                ( "{VENTILATION}", _("Règlements affectés à la facture") ),
                ( "{LIB_SOLDE}", _("Libellé pour qualifier le solde") ),
                ( "{SOLDE}", _("Reste dû sur la facture") ),
                ],

    "rappel" : [
                ( "{DATE_EDITION_RAPPEL}", _("Date d'édition de la lettre de rappel") ),
                ( "{NUMERO_RAPPEL}", _("Numéro de le lattre de rappel") ),
                ( "{DATE_MIN}", _("Date de début des impayés") ),
                ( "{DATE_MAX}", _("Date de fin des impayés") ),
                ( "{DATE_REFERENCE}", _("Date de référence") ),
                ( "{SOLDE_CHIFFRES}", _("Solde du rappel en chiffres") ),
                ( "{SOLDE_LETTRES}", _("Solde du rappel en lettres") ),
                ],

    "attestation_presence" : [
                ( "{DATE_EDITION_ATTESTATION}", _("Date d'édition de l'attestation") ),
                ( "{NUMERO_ATTESTATION}", _("Numéro de l'attestation") ),
                ( "{DATE_DEBUT}", _("Date de début de la période") ),
                ( "{DATE_FIN}", _("Date de fin de la période") ),
                ( "{INDIVIDUS_CONCERNES}", _("Liste des individus concernés") ),
                ( "{SOLDE}", _("Solde de l'attestation") ),
                ],

    "reservations" : [
                ( "{SOLDE}", _("Solde du document") ),
                ],

    "mandat_sepa" : [
                ( "{REFERENCE_UNIQUE_MANDAT}", _("RUM (Référence Unique du Mandat)") ),
                ( "{DATE_SIGNATURE}", _("Date de signature du mandat") ),
                ],

    "cotisation" : [
                ( "{NUMERO_CARTE}", _("Numéro de la carte") ),
                ( "{DATE_DEBUT}", _("Date de début de validité de la cotisation") ),
                ( "{DATE_FIN}", _("Date de fin de validité de la cotisation") ),
                ( "{NOM_TYPE_COTISATION}", _("Nom du type de cotisation") ),
                ( "{NOM_UNITE_COTISATION}", _("Nom de l'unité de cotisation") ),
                ( "{NOM_COTISATION}", _("Nom de la cotisation (type + unité)") ),
                ( "{DATE_CREATION_CARTE}", _("Date de création de la carte") ),
                ( "{MONTANT_FACTURE}", _("Montant facturé") ),
                ( "{MONTANT_REGLE}", _("Montant réglé") ),
                ( "{SOLDE_ACTUEL}", _("Solde actuel") ),
                ( "{ACTIVITES}", _("Activités associées") ),
                ( "{NOTES}", _("Notes") ),
                ],

    "attestation_fiscale" : [
                ("{DATE_EDITION_COURT}", _("Date d'édition court")),
                ("{DATE_EDITION_LONG}", _("Date d'édition long")),
                ("{DATE_DEBUT}", _("Date de début de la période")),
                ("{DATE_FIN}", _("Date de fin de la période")),
                ("{MONTANT_FACTURE}", _("Montant total facturé")),
                ("{MONTANT_REGLE}", _("Montant réglé")),
                ("{MONTANT_IMPAYE}", _("Montant impayé")),
                ("{MONTANT_FACTURE_LETTRES}", _("Montant total facturé en lettres")),
                ("{MONTANT_REGLE_LETTRES}", _("Montant réglé en lettres")),
                ("{MONTANT_IMPAYE_LETTRES}", _("Montant impayé en lettres")),
                ],

    "rappel_pieces_manquantes" : [
                ("{NOM_FAMILLE}", _("Nom de la famille")),
                ("{LISTE_PIECES_MANQUANTES}", _("Liste des pièces manquantes")),
                ],

    "portail" : [
                ( "{NOM_FAMILLE}", _("Nom de la famille")),
                ( "{IDENTIFIANT_INTERNET}", _("Identifiant du compte internet") ),
                ( "{MOTDEPASSE_INTERNET}", _("Mot de passe du compte internet") ),
                ],

    "portail_demande_inscription" : [
                ( "{DEMANDE_HORODATAGE}", _("Date et heure de la demande") ),
                ( "{DEMANDE_DESCRIPTION}", _("Description de la demande") ),
                ( "{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande") ),
                ( "{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement") ),
                ( "{DEMANDE_REPONSE}", _("Réponse à la demande") ),
                ],

    "portail_demande_renseignement": [
        ("{DEMANDE_HORODATAGE}", _("Date et heure de la demande")),
        ("{DEMANDE_DESCRIPTION}", _("Description de la demande")),
        ("{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande")),
        ("{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement")),
        ("{DEMANDE_REPONSE}", _("Réponse à la demande")),
    ],

    "portail_demande_location": [
        ("{DEMANDE_HORODATAGE}", _("Date et heure de la demande")),
        ("{DEMANDE_DESCRIPTION}", _("Description de la demande")),
        ("{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande")),
        ("{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement")),
        ("{DEMANDE_REPONSE}", _("Réponse à la demande")),
    ],

    "portail_demande_piece": [
        ("{DEMANDE_HORODATAGE}", _("Date et heure de la demande")),
        ("{DEMANDE_DESCRIPTION}", _("Description de la demande")),
        ("{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande")),
        ("{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement")),
        ("{DEMANDE_REPONSE}", _("Réponse à la demande")),
    ],

    "portail_demande_reservation" : [
                ( "{DEMANDE_HORODATAGE}", _("Date et heure de la demande") ),
                ( "{DEMANDE_DESCRIPTION}", _("Description de la demande") ),
                ( "{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande") ),
                ( "{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement") ),
                ( "{DEMANDE_REPONSE}", _("Réponse à la demande") ),
                ( "{PERIODE_NOM}", _("Nom de la période") ),
                ( "{PERIODE_DATE_DEBUT}", _("Date de début de la période") ),
                ( "{PERIODE_DATE_FIN}", _("Date de fin de la période") ),
                ( "{TOTAL}", _("Total des prestations de la période") ),
                ( "{REGLE}", _("Total déjà réglé pour la période") ),
                ( "{SOLDE}", _("Solde de la période") ),
                ],

    "portail_demande_facture" : [
                ( "{DEMANDE_HORODATAGE}", _("Date et heure de la demande") ),
                ( "{DEMANDE_DESCRIPTION}", _("Description de la demande") ),
                ( "{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande") ),
                ( "{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement") ),
                ( "{DEMANDE_REPONSE}", _("Réponse à la demande") ),
                ],

    "portail_demande_recu_reglement" : [
                ( "{DEMANDE_HORODATAGE}", _("Date et heure de la demande") ),
                ( "{DEMANDE_DESCRIPTION}", _("Description de la demande") ),
                ( "{DEMANDE_COMMENTAIRE}", _("Commentaire de la demande") ),
                ( "{DEMANDE_TRAITEMENT_DATE}", _("Date de traitement") ),
                ( "{DEMANDE_REPONSE}", _("Réponse à la demande") ),
                ],

    "location": [
                ("{IDLOCATION}", _("ID de la location")),
                ("{IDPRODUIT}", _("ID du produit")),
                ("{DATE_DEBUT}", _("Date de début")),
                ("{DATE_FIN}", _("Date de fin")),
                ("{HEURE_DEBUT}", _("Heure de début")),
                ("{HEURE_FIN}", _("Heure de fin")),
                ("{NOM_PRODUIT}", _("Nom du produit")),
                ("{NOM_CATEGORIE}", _("Nom de la catégorie")),
                ("{NOTES}", _("Observations")),
                ],

    "location_demande": [
                ("{IDDEMANDE}", _("ID de la demande")),
                ("{DATE}", _("Date de la demande")),
                ("{HEURE}", _("Heure de la demande")),
                ("{CATEGORIES}", _("Catégories demandées")),
                ("{PRODUITS}", _("Produits demandés")),
                ("{NOTES}", _("Observations")),
                ],

    "commande_repas": [
                ("{NOM_COMMANDE}", _("Nom de la commande")),
                ("{DATE_DEBUT}", _("Date de début de la période")),
                ("{DATE_FIN}", _("Date de fin de la période")),
                ],

    "inscription": [
                ("{IDINSCRIPTION}", _("ID de l'inscription")),
                ("{DATE_INSCRIPTION}", _("Date de l'inscription")),
                ("{EST_PARTI}", _("L'individu est parti")),
                ("{ACTIVITE_NOM_LONG}", _("Nom de l'activité long")),
                ("{ACTIVITE_NOM_COURT}", _("Nom de l'activité abrégé")),
                ("{GROUPE_NOM_LONG}", _("Nom du groupe long")),
                ("{GROUPE_NOM_COURT}", _("Nom du groupe abrégé")),
                ("{NOM_CATEGORIE_TARIF}", _("Nom de la catégorie de tarif")),
                ("{INDIVIDU_NOM}", _("Nom de famille de l'individu")),
                ("{INDIVIDU_PRENOM}", _("Prénom de l'individu")),
                ("{INDIVIDU_DATE_NAISS}", _("Date de naissance de l'individu")),
                ],

    "devis": [
        ("{DATE_EDITION_DEVIS}", _("Date d'édition du devis")),
        ("{NUMERO_DEVIS}", _("Numéro du devis")),
        ("{DATE_DEBUT}", _("Date de début de la période")),
        ("{DATE_FIN}", _("Date de fin de la période")),
        ("{INDIVIDUS_CONCERNES}", _("Liste des individus concernés")),
        ("{SOLDE}", _("Solde du devis")),
        ],

}

def GetMotscles(categorie=""):
    listeTemp = copy.deepcopy(MOTSCLES_STANDARDS)
    if categorie in MOTSCLES :
        listeTemp.extend(MOTSCLES[categorie])
    return listeTemp

def GetChampsStandards(dictUtilisateur=None):
    dictTemp  = {}
    
    # Utilisateur en cours
    if not dictUtilisateur:
        dictUtilisateur = UTILS_Identification.GetDictUtilisateur()
    if dictUtilisateur != None :
        dictTemp["{UTILISATEUR_NOM_COMPLET}"] = "%s %s" % (dictUtilisateur["nom"], dictUtilisateur["prenom"])
        dictTemp["{UTILISATEUR_NOM}"] = dictUtilisateur["nom"]
        dictTemp["{UTILISATEUR_PRENOM}"] = dictUtilisateur["prenom"]
    else:
        dictTemp["{UTILISATEUR_NOM_COMPLET}"] ="Bénévole de l'ASSOCIATION"
        dictTemp["{UTILISATEUR_NOM}"] = "ASSOCIATION"
        dictTemp["{UTILISATEUR_PRENOM}"] = "Bénévole"

    # Dates
    dictTemp["{DATE_COURTE}"] = DateEngFr(str(datetime.date.today()))
    dictTemp["{DATE_LONGUE}"] = DateComplete(datetime.date.today())

    return dictTemp

# ------------------------------------------------------------------------------------------------------------------------------

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, label="", infobulle=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id=-1, label=label, URL="")
        self.parent = parent
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
        
    def OnLeftLink(self, event):
        self.UpdateLink()
        

class Hyperlien_inserer_motcle(Hyperlien):
    def __init__(self, parent, label="", infobulle="", listeMotscles=[], editeur=None):
        Hyperlien.__init__(self, parent, label=label, infobulle=infobulle)
        self.parent = parent
        self.listeMotscles = listeMotscles
        self.editeur = editeur

    def OnLeftLink(self, event):
        menuPop = wx.Menu()
        id = 10000
        for motcle in self.listeMotscles :
            menuPop.Append(wx.MenuItem(menuPop, id, motcle))
            self.Bind(wx.EVT_MENU, self.InsererMotcle, id=id)
            id += 1
        self.PopupMenu(menuPop)
        menuPop.Destroy()
        self.UpdateLink()
        
    def InsererMotcle(self, event):
        motcle = self.listeMotscles[10000 - event.GetId() ]
        self.editeur.EcritTexte(motcle)


class Hyperlien_inserer_modele(Hyperlien):
    def __init__(self, parent, label="", infobulle="", categorie="", editeur=None):
        Hyperlien.__init__(self, parent, label=label, infobulle=infobulle)
        self.parent = parent
        self.categorie = categorie
        self.editeur = editeur

    def OnLeftLink(self, event):
        # Récupération des modèles
        DB = GestionDB.DB()
        req = """SELECT IDmodele, categorie, nom, description, objet, texte_xml, IDadresse, defaut
        FROM modeles_emails
        WHERE categorie='%s'
        ORDER BY nom;""" % self.categorie
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        # Création du menu contextuel
        menuPop = UTILS_Adaptations.Menu()
        id = 10000
        for IDmodele, categorie, nom, description, objet, texte_xml, IDadresse, defaut in self.listeMotscles :
            menuPop.Append(wx.MenuItem(menuPop, id, nom))
            self.Bind(wx.EVT_MENU, self.InsererMotcle, id=id)
            id += 1
        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def InsererMotcle(self, event):
        motcle = self.listeMotscles[10000 - event.GetId() ]
        self.editeur.EcritTexte(motcle)



def FormateCouleur(texte):
    pos1 = texte.index(",")
    pos2 = texte.index(",", pos1+1)
    r = int(texte[1:pos1])
    v = int(texte[pos1+2:pos2])
    b = int(texte[pos2+2:-1])
    return (r, v, b)

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete


class CTRL_Expediteur(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
                                        
    def MAJ(self):
        selectionActuelle = self.GetID() 
        self.listeAdresses = []
        self.dictAdresses = {}
        # Récupération des données
        DB = GestionDB.DB()        
        req = """SELECT IDadresse, adresse, nom_adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, moteur, parametres
        FROM adresses_mail ORDER BY adresse; """
        DB.ExecuterReq(req,MsgBox="CTRL_Editeur_email")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        sel = None
        index = 0
        for IDadresse, adresse, nom_adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, moteur, parametres in listeDonnees :
            self.listeAdresses.append(adresse)
            self.dictAdresses[index] = {"IDadresse" : IDadresse, "moteur": moteur, "adresse": adresse, "nom_adresse": nom_adresse,
                                        "smtp" : smtp, "port" : port, "defaut" : defaut, "auth" : connexionAuthentifiee, "startTLS":startTLS,
                                        "motdepasse" : motdepasse, "utilisateur" : utilisateur, "parametres": parametres}
            if defaut == 1 : 
                sel = index
            index += 1
        self.SetItems(self.listeAdresses)
        if sel != None : 
            self.SetSelection(sel)
        if selectionActuelle != None :
            self.SetSelection(selectionActuelle)
        if len(self.listeAdresses) == 0 :
            self.Enable(False)
        else :
            self.Enable(True)

    def SetID(self, ID=0):
        for index, values in self.dictAdresses.items():
            if values["IDadresse"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictAdresses[index]["IDadresse"]
    
    def GetDonnees(self):
        IDadresse = self.GetID()
        if self.GetID() == None :
            return None
        else :
            test = self.GetSelection()
            return self.dictAdresses[self.GetSelection()]


class Panel_Expediteur(wx.Panel):
    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, id=-1, size=size, style=wx.TAB_TRAVERSAL)
        
        # Contrôles
        self.ctrl_exp = CTRL_Expediteur(self)
        self.bouton_exp = self.bouton_exp = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        # Propriétés
        self.ctrl_exp.SetToolTip(wx.ToolTip(_("Sélectionnez l'adresse d'expéditeur")))
        self.bouton_exp.SetToolTip(wx.ToolTip(_("Cliquez ici pour accéder à la gestion des adresses d'expédition")))
        
        # Layout
        grid_sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer.Add(self.ctrl_exp, 0, wx.EXPAND, 0)
        grid_sizer.Add(self.bouton_exp, 0, wx.EXPAND, 0)
        grid_sizer.AddGrowableRow(0)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        #grid_sizer.Fit(self)
        self.Layout()
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExp, self.bouton_exp)
        
    def OnBoutonExp(self, event):
        ID = self.GetID()
        from Dlg import DLG_Emails_exp
        dlg = DLG_Emails_exp.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_exp.MAJ()
        self.SetID(ID)
    
    def MAJ(self):
        self.ctrl_exp.MAJ() 
        
    def SetID(self, ID=0):
        self.ctrl_exp.SetID(ID)

    def GetID(self):
        return self.ctrl_exp.GetID()
    
    def GetDonnees(self):
        return self.ctrl_exp.GetDonnees()


# --------------------------------------------------------------------------------------------------------------------------------------------------------

def AddTool(barre=None, ID=None, chemin_image=None, kind=wx.ITEM_NORMAL, label="", handler=None, updateUI=None):
    if 'phoenix' in wx.PlatformInfo:
        item = barre.AddTool(toolId=ID, label=label, bitmap=wx.Bitmap(Chemins.GetStaticPath(chemin_image), wx.BITMAP_TYPE_ANY), shortHelp=label, kind=kind)
    else :
        if kind == wx.ITEM_CHECK :
            isToggle = True
        else :
            isToggle = False
        item = barre.AddTool(id=ID, bitmap=wx.Bitmap(Chemins.GetStaticPath(chemin_image), wx.BITMAP_TYPE_ANY), shortHelpString=label, isToggle=isToggle)
    barre.Bind(wx.EVT_TOOL, handler, item)
    if updateUI is not None:
        barre.Bind(wx.EVT_UPDATE_UI, updateUI, item)


class BarreOutils1(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.parent = parent

        ID_SAUVEGARDER = wx.Window.NewControlId()
        ID_OUVRIR = wx.Window.NewControlId()
        ID_IMPRIMER = wx.Window.NewControlId()
        ID_APERCU = wx.Window.NewControlId()
        ID_GRAS = wx.Window.NewControlId()
        ID_ITALIQUE = wx.Window.NewControlId()
        ID_SOULIGNE = wx.Window.NewControlId()
        ID_COULEUR_POLICE = wx.Window.NewControlId()
        ID_ALIGNER_GAUCHE = wx.Window.NewControlId()
        ID_ALIGNER_CENTRE = wx.Window.NewControlId()
        ID_ALIGNER_DROIT = wx.Window.NewControlId()
        ID_GOMME = wx.Window.NewControlId()

        AddTool(self, ID_SAUVEGARDER, "Images/Teamword/sauvegarder.png", label=_("Sauvegarder le texte"), handler=self.parent.OnFileSave)
        AddTool(self, ID_OUVRIR, "Images/Teamword/ouvrir.png", label=_("Ouvrir un texte sauvegardé"), handler=self.parent.OnFileOpen)
        self.AddSeparator()
        AddTool(self, ID_IMPRIMER, "Images/Teamword/imprimer.png", label=_("Imprimer ce texte"), handler=self.parent.OnPrint)
        AddTool(self, ID_APERCU, "Images/Teamword/Apercu.png", label=_("Aperçu avant impression de ce texte"), handler=self.parent.OnPreview)
        self.AddSeparator()
        AddTool(self, ID_ALIGNER_GAUCHE, "Images/Teamword/aligner_gauche.png", kind=wx.ITEM_CHECK, label=_("Aligner à gauche"), handler=self.parent.OnAlignLeft, updateUI=self.parent.OnUpdateAlignLeft)
        AddTool(self, ID_ALIGNER_CENTRE, "Images/Teamword/aligner_centre.png", kind=wx.ITEM_CHECK, label=_("Centrer"), handler=self.parent.OnAlignCenter, updateUI=self.parent.OnUpdateAlignCenter)
        AddTool(self, ID_ALIGNER_DROIT, "Images/Teamword/aligner_droit.png", kind=wx.ITEM_CHECK, label=_("Aligner à droite"), handler=self.parent.OnAlignRight, updateUI=self.parent.OnUpdateAlignRight)
        self.AddSeparator()
        AddTool(self, ID_GRAS, "Images/Teamword/gras.png", kind=wx.ITEM_CHECK, label=_("Gras"), handler=self.parent.OnBold, updateUI=self.parent.OnUpdateBold)
        AddTool(self, ID_ITALIQUE, "Images/Teamword/italique.png", kind=wx.ITEM_CHECK, label=_("Italique"), handler=self.parent.OnItalic, updateUI=self.parent.OnUpdateItalic)
        AddTool(self, ID_SOULIGNE, "Images/Teamword/souligne.png", kind=wx.ITEM_CHECK, label=_("Souligné"), handler=self.parent.OnUnderline, updateUI=self.parent.OnUpdateUnderline)
        self.AddSeparator()
        AddTool(self, ID_COULEUR_POLICE, "Images/Teamword/police_couleur.png", label=_("Couleur de la police"), handler=self.parent.OnColour)
        self.AddSeparator()
        AddTool(self, wx.ID_UNDO, "Images/Teamword/annuler.png", label=_("Annuler"), handler=self.parent.ForwardEvent, updateUI=self.parent.ForwardEvent)
        AddTool(self, wx.ID_REDO, "Images/Teamword/repeter.png", label=_("Répéter"), handler=self.parent.ForwardEvent, updateUI=self.parent.ForwardEvent)
        self.AddSeparator()
        AddTool(self, ID_GOMME, "Images/16x16/Gomme.png", label=_("Effacer tout le texte"), handler=self.parent.OnGomme)

        self.SetToolBitmapSize((16, 16))
        self.Realize()


class BarreOutils2(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.parent = parent

        ID_RETRAIT_GAUCHE = wx.Window.NewControlId()
        ID_RETRAIT_DROIT = wx.Window.NewControlId()
        ID_PARA_MOINS = wx.Window.NewControlId()
        ID_PARA_PLUS = wx.Window.NewControlId()
        ID_INTER_SIMPLE = wx.Window.NewControlId()
        ID_INTER_DEMI = wx.Window.NewControlId()
        ID_INTER_DOUBLE = wx.Window.NewControlId()
        ID_URL = wx.Window.NewControlId()
        ID_IMAGE = wx.Window.NewControlId()

        AddTool(self, wx.ID_CUT, "Images/Teamword/couper.png", label=_("Couper"), handler=self.parent.ForwardEvent, updateUI=self.parent.ForwardEvent)
        AddTool(self, wx.ID_COPY, "Images/Teamword/copier.png", label=_("Copier"), handler=self.parent.ForwardEvent, updateUI=self.parent.ForwardEvent)
        AddTool(self, wx.ID_PASTE, "Images/Teamword/coller.png", label=_("Coller"), handler=self.parent.ForwardEvent, updateUI=self.parent.ForwardEvent)
        self.AddSeparator()
        AddTool(self, ID_RETRAIT_GAUCHE, "Images/Teamword/retrait_gauche.png", label=_("Diminuer le retrait"), handler=self.parent.OnIndentLess)
        AddTool(self, ID_RETRAIT_DROIT, "Images/Teamword/retrait_droit.png", label=_("Augmenter le retrait"), handler=self.parent.OnIndentMore)
        self.AddSeparator()
        AddTool(self, ID_PARA_MOINS, "Images/Teamword/espaceParagrapheMoins.png", label=_("Diminuer l'espacement des paragraphes"), handler=self.parent.OnParagraphSpacingLess)
        AddTool(self, ID_PARA_PLUS, "Images/Teamword/espaceParagraphePlus.png", label=_("Augmenter l'espacement des paragraphes"), handler=self.parent.OnParagraphSpacingMore)
        self.AddSeparator()
        AddTool(self, ID_INTER_SIMPLE, "Images/Teamword/interligne_simple.png", label=_("Interligne simple"), handler=self.parent.OnLineSpacingSingle)
        AddTool(self, ID_INTER_DEMI, "Images/Teamword/interligne_demi.png", label=_("Interligne 1.5"), handler=self.parent.OnLineSpacingHalf)
        AddTool(self, ID_INTER_DOUBLE, "Images/Teamword/interligne_double.png", label=_("Interligne double"), handler=self.parent.OnLineSpacingDouble)
        
        self.AddSeparator()
        AddTool(self, ID_URL, "Images/Teamword/url.png", label=_("Insérer une url"), handler=self.parent.OnInsererURL)
        AddTool(self, ID_IMAGE, "Images/Teamword/importer_image.png", label=_("Insérer une image"), handler=self.parent.OnImporterImage)

        self.SetToolBitmapSize((16, 16))
        self.Realize()

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


class Editeur(rt.RichTextCtrl):
    def __init__(self, parent, id=-1, style=wx.VSCROLL|wx.HSCROLL|wx.WANTS_CHARS ):
        rt.RichTextCtrl.__init__(self, parent, id=id, style=style)

    def GetXML(self):
        out = io.BytesIO()
        handler = wx.richtext.RichTextXMLHandler()
        buffer = self.GetBuffer()
        handler.SaveFile(buffer, out)
        out.seek(0)
        content = out.read()
        return content
    
    def SetXML(self, texteXml=""):
        out = io.BytesIO()
        handler = wx.richtext.RichTextXMLHandler()
        buf = self.GetBuffer()
        buf.AddHandler(handler)
        if isinstance(texteXml, str):
            texteXml = texteXml.encode("utf8")
        out.write(texteXml)
        out.seek(0)
        handler.LoadFile(buf, out)
        self.Refresh()


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, id=-1,size=size,style=wx.TAB_TRAVERSAL,
                          name="CTRL_Editeur_email.CTRL")
        
        # Contrôles
        self.barre_outils1 = BarreOutils1(self)
        self.barre_outils2 = BarreOutils2(self)
        self.AddRTCHandlers()
        self.ctrl_editeur = Editeur(self)

        # Layout
        grid_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        grid_sizer.Add(self.barre_outils1, 0, wx.EXPAND, 0)
        grid_sizer.Add(self.barre_outils2, 0, wx.EXPAND, 0)
        grid_sizer.Add(self.ctrl_editeur, 0, wx.EXPAND, 0)
        grid_sizer.AddGrowableRow(2)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        #grid_sizer.Fit(self)
        self.Layout()

    def OnFileOpen(self, evt):
        """ Ouvrir un texte """
        wildcard, types = rt.RichTextBuffer.GetExtWildcard(save=False)
        dlg = wx.FileDialog(self, _("Choisissez un fichier à ouvrir"), wildcard=wildcard, style=wx.FD_OPEN)
        dlg.SetFilterIndex(2)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path:
                fileType = types[dlg.GetFilterIndex()]
                self.ctrl_editeur.LoadFile(path, type=wx.richtext.RICHTEXT_TYPE_ANY)
                wx.CallAfter(self.ctrl_editeur.SetFocus)
        dlg.Destroy()

    def OnFileSave(self, evt):
        """ Sauvegarder dans un fichier """
        wildcard, types = rt.RichTextBuffer.GetExtWildcard(save=True)
        dlg = wx.FileDialog(self, _("Sauvegardez le texte"), wildcard=wildcard, style=wx.FD_SAVE)
        dlg.SetFilterIndex(3)
        if dlg.ShowModal() == wx.ID_OK:
            cheminFichier = dlg.GetPath()
            if cheminFichier :
                fileType = types[dlg.GetFilterIndex()]
                ext = rt.RichTextBuffer.FindHandlerByType(fileType).GetExtension()
                if not cheminFichier.endswith(ext):
                    cheminFichier += '.' + ext
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False            
        self.ctrl_editeur.SaveFile(cheminFichier, wx.richtext.RICHTEXT_TYPE_ANY)

    def OnBold(self, evt):
        self.ctrl_editeur.ApplyBoldToSelection()
        
    def OnItalic(self, evt): 
        self.ctrl_editeur.ApplyItalicToSelection()
        
    def OnUnderline(self, evt):
        self.ctrl_editeur.ApplyUnderlineToSelection()
        
    def OnAlignLeft(self, evt):
        self.ctrl_editeur.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_LEFT)
        
    def OnAlignRight(self, evt):
        self.ctrl_editeur.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_RIGHT)
        
    def OnAlignCenter(self, evt):
        self.ctrl_editeur.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_CENTRE)
        
    def OnIndentMore(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            attr.SetLeftIndent(attr.GetLeftIndent() + 100)
            attr.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
            self.ctrl_editeur.SetStyle(r, attr)
        
    def OnIndentLess(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

        if attr.GetLeftIndent() >= 100:
            attr.SetLeftIndent(attr.GetLeftIndent() - 100)
            attr.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
            self.ctrl_editeur.SetStyle(r, attr)
        
    def OnParagraphSpacingMore(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_PARA_SPACING_AFTER)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            attr.SetParagraphSpacingAfter(attr.GetParagraphSpacingAfter() + 20);
            attr.SetFlags(wx.TEXT_ATTR_PARA_SPACING_AFTER)
            self.ctrl_editeur.SetStyle(r, attr)
        
    def OnParagraphSpacingLess(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_PARA_SPACING_AFTER)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            if attr.GetParagraphSpacingAfter() >= 20:
                attr.SetParagraphSpacingAfter(attr.GetParagraphSpacingAfter() - 20);
                attr.SetFlags(wx.TEXT_ATTR_PARA_SPACING_AFTER)
                self.ctrl_editeur.SetStyle(r, attr)
        
    def OnLineSpacingSingle(self, evt): 
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(10)
            self.ctrl_editeur.SetStyle(r, attr)
                
    def OnLineSpacingHalf(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(15)
            self.ctrl_editeur.SetStyle(r, attr)
        
    def OnLineSpacingDouble(self, evt):
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
        ip = self.ctrl_editeur.GetInsertionPoint()
        if self.ctrl_editeur.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.ctrl_editeur.HasSelection():
                r = self.ctrl_editeur.GetSelectionRange()

            attr.SetFlags(wx.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(20)
            self.ctrl_editeur.SetStyle(r, attr)

    def OnFont(self, evt):
        if not self.ctrl_editeur.HasSelection():
            dlg = wx.MessageDialog(self, _("Vous devez d'abord sélectionner un texte."), _("Police"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        r = self.ctrl_editeur.GetSelectionRange()
        fontData = wx.FontData()
        fontData.EnableEffects(False)
        attr = rt.RichTextAttr()
        attr.SetFlags(wx.TEXT_ATTR_FONT)
        if self.ctrl_editeur.GetStyle(self.ctrl_editeur.GetInsertionPoint(), attr):
            fontData.SetInitialFont(attr.GetFont())

        dlg = wx.FontDialog(self, fontData)
        if dlg.ShowModal() == wx.ID_OK:
            fontData = dlg.GetFontData()
            font = fontData.GetChosenFont()
            if font:
                attr.SetFlags(wx.TEXT_ATTR_FONT)
                attr.SetFont(font)
                self.ctrl_editeur.SetStyle(r, attr)
        dlg.Destroy()

    def OnColour(self, evt):
        colourData = wx.ColourData()
        attr = rt.RichTextAttr() #wx.TextAttr()
        attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
        if self.ctrl_editeur.GetStyle(self.ctrl_editeur.GetInsertionPoint(), attr):
            colourData.SetColour(attr.GetTextColour())

        dlg = wx.ColourDialog(self, colourData)
        if dlg.ShowModal() == wx.ID_OK:
            colourData = dlg.GetColourData()
            colour = colourData.GetColour()
            if colour:
                if not self.ctrl_editeur.HasSelection():
                    self.ctrl_editeur.BeginTextColour(colour)
                else:
                    r = self.ctrl_editeur.GetSelectionRange()
                    attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
                    attr.SetTextColour(colour)
                    self.ctrl_editeur.SetStyle(r, attr)
        dlg.Destroy()

    def OnUpdateBold(self, evt):
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionBold())
    
    def OnUpdateItalic(self, evt):
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionItalics())
    
    def OnUpdateUnderline(self, evt): 
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionUnderlined())
    
    def OnUpdateAlignLeft(self, evt):
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionAligned(wx.TEXT_ALIGNMENT_LEFT))
        
    def OnUpdateAlignCenter(self, evt):
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionAligned(wx.TEXT_ALIGNMENT_CENTRE))
        
    def OnUpdateAlignRight(self, evt):
        if self.ctrl_editeur == None : return
        evt.Check(self.ctrl_editeur.IsSelectionAligned(wx.TEXT_ALIGNMENT_RIGHT))
    
    def ForwardEvent(self, evt):
        if self.ctrl_editeur == None : return
        self.ctrl_editeur.ProcessEvent(evt)
    
    def OnGomme(self, event):
        self.ctrl_editeur.Clear()
        self.ctrl_editeur.SetFocus()
        
    def OnInsererURL(self, event):
        from Dlg import DLG_Saisie_url
        dlg = DLG_Saisie_url.MyDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            label = dlg.GetLabel()
            URL = dlg.GetURL()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        urlStyle = rt.RichTextAttr()
        urlStyle.SetTextColour(wx.BLUE)
        urlStyle.SetFontUnderlined(True)
        self.ctrl_editeur.BeginStyle(urlStyle)
        self.ctrl_editeur.BeginURL(URL)
        self.ctrl_editeur.WriteText(label)
        self.ctrl_editeur.EndURL()
        self.ctrl_editeur.EndStyle()

    def OnImporterImage(self, event):
        # Sélection d'une image
        self.repCourant = os.getcwd()
        wildcard = "Toutes les images|*.jpg;*.png;*.gif|" \
                        "Images JPEG (*.jpg)|*.jpg|"     \
                        "Images PNG (*.png)|*.png|"     \
                        "Images GIF (*.gif)|*.gif|"     \
                        "Tous les fichiers (*.*)|*.*"
        # Récupération du chemin des documents
        sp = wx.StandardPaths.Get()
        cheminDefaut = sp.GetDocumentsDir()
        # Ouverture de la fenêtre de dialogue
        dlg = wx.FileDialog(
            self, message=_("Choisissez une image"),
            defaultDir=cheminDefaut, 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            nomFichierCourt = dlg.GetFilename()
            nomFichierLong = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        # Recadre la photo
        bmp = wx.Bitmap(Chemins.GetStaticPath(nomFichierLong), wx.BITMAP_TYPE_ANY)
##        from Dlg import DLG_Editeur_photo_2
##        dlg = DLG_Editeur_photo_2.MyDialog(self, image=nomFichierLong, titre=_("Redimensionnez l'image si vous le souhaitez"))
##        if dlg.ShowModal() == wx.ID_OK:
##            bmp = dlg.GetBmp()
##            dlg.Destroy()
##        else:
##            dlg.Destroy()
##            return 
        # Insère l'image dans l'éditeur
        if nomFichierLong.lower().endswith(".jpg") : typeBMP = wx.BITMAP_TYPE_JPEG
        elif nomFichierLong.lower().endswith(".png") : typeBMP = wx.BITMAP_TYPE_PNG
        elif nomFichierLong.lower().endswith(".gif") : typeBMP = wx.BITMAP_TYPE_GIF
        elif nomFichierLong.lower().endswith(".bmp"): typeBMP = wx.BITMAP_TYPE_BMP
        else: typeBMP = wx.BITMAP_TYPE_ANY
        self.ctrl_editeur.WriteImage(bmp, bitmapType=typeBMP)

    def AddRTCHandlers(self):
        # make sure we haven't already added them.
        if rt.RichTextBuffer.FindHandlerByType(rt.RICHTEXT_TYPE_HTML) is not None:
            return
        # This would normally go in your app's OnInit method.  I'm
        # not sure why these file handlers are not loaded by
        # default by the C++ richtext code, I guess it's so you
        # can change the name or extension if you wanted...
        rt.RichTextBuffer.AddHandler(rt.RichTextHTMLHandler())
        rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler())
        # ...like this
        rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler(name="Noetext", ext="ntx", type=99))
        # This is needed for the view as HTML option since we tell it
        # to store the images in the memory file system.
        wx.FileSystem.AddHandler(wx.MemoryFSHandler())

    def oldGetBuffer(self):
        buffer = self.ctrl_editeur.GetBuffer()
        text = buffer.Text
        if "{" in text and hasattr(self.Parent, "TransposeMotsCle"):
            text = self.Parent.TransposeMotsCle(text)
        #self.ctrl_editeur.ChangeValue(text)
        editeurTemp = Editeur(self)
        editeurTemp.WriteText(text)
        buffer = editeurTemp.GetBuffer()
        return buffer

    # fourni une nouvelle version du buffer façon MAJ_Apercu()
    def GetBuffer(self):
        textXml = self.GetXML()
        text = textXml.decode('UTF-8')
        if "{" in text and hasattr(self.Parent, "TransposeMotsCle"):
            text = self.Parent.TransposeMotsCle(text)
        editeurTemp = Editeur(self) # Double pour ne pas modifier l'original'
        editeurTemp.SetXML(text)
        buffer = editeurTemp.GetBuffer()
        return buffer

    def OnPreview(self, event):
        printout1 = rt.RichTextPrintout()
        printout1.SetRichTextBuffer(self.GetBuffer())

        printout2 = rt.RichTextPrintout()
        printout2.SetRichTextBuffer(self.GetBuffer())

        data = wx.PrintDialogData()
        data.SetCollate(True)
        datapr = wx.PrintData()
        data.SetPrintData(datapr)
        preview = wx.PrintPreview(printout1, printout2, data)
        if not preview.IsOk():
            print("Probleme dans le preview du richTextCtrl.")
            return

        from Utils import UTILS_Printer
        pfrm = UTILS_Printer.FramePreview(self, "Aperçu avant impression", preview)
        pfrm.SetPosition(self.GetPosition())
        pfrm.SetSize(self.GetSize())
        pfrm.Show(True)

    def OnFileViewHTML(self):
        handler = rt.RichTextHTMLHandler()
        handler.SetFlags(rt.RICHTEXT_HANDLER_SAVE_IMAGES_TO_MEMORY)
        handler.SetFontSizeMapping([7, 9, 11, 12, 14, 22, 100])

        stream = io.BytesIO()
        buffer = self.ctrl_editeur.GetBuffer()

        if not handler.SaveFile(self.GetBuffer(), stream):
            return

        head = b"""
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /> 
</head>
        """
        stream.seek(0)
        html_bytes = stream.read()
        html_bytes = html_bytes.replace(b"<head></head>", head)
        html_text = html_bytes.decode("utf-8")

        # Display HTML in a wx.HtmlWindow or dialog
        dlg = wx.Dialog(self, title="HTML Preview", size=(600, 400))
        html_win = wx.html.HtmlWindow(dlg)
        html_win.SetPage(html_text)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html_win, 1, wx.EXPAND | wx.ALL, 10)
        dlg.SetSizer(sizer)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPrint(self, event):
        printout1 = wx.richtext.RichTextPrintout()
        printout1.SetRichTextBuffer(self.GetBuffer())

        printout2 = wx.richtext.RichTextPrintout()
        printout2.SetRichTextBuffer(self.GetBuffer())

        preview = wx.PrintPreview(printout1, printout2, wx.PrintDialogData())
        if preview.IsOk():
            frame = wx.PreviewFrame(preview, self, "Aperçu avant impression")
            frame.Initialize()
            frame.Show()
        else:
            wx.MessageBox("Impossible d'afficher l'aperçu", "Erreur", wx.ICON_ERROR)

    def GetHTML(self, imagesIncluses=True, base64=False):
        # Récupération de la source HTML
        handler = rt.RichTextHTMLHandler()
        if imagesIncluses == True :
            if base64 == True :
                handler.SetFlags(rt.RICHTEXT_HANDLER_SAVE_IMAGES_TO_BASE64)
            else :
                handler.SetFlags(rt.RICHTEXT_HANDLER_SAVE_IMAGES_TO_FILES)
        else:
            handler.SetFlags(rt.RICHTEXT_HANDLER_SAVE_IMAGES_TO_MEMORY)
        handler.SetFontSizeMapping([7,9,11,12,14,22,100])
        stream = io.BytesIO()
        if not handler.SaveFile(self.ctrl_editeur.GetBuffer(), stream):
            return False

        source = stream.getvalue()
        source = source.decode("utf-8")
        listeImages = handler.GetTemporaryImageLocations()
        return source, listeImages, handler

    def GetHTML_base64(self):
        # Récupération de la source HTML
        handler = rt.RichTextHTMLHandler()
        handler.SetFlags(rt.RICHTEXT_HANDLER_SAVE_IMAGES_TO_BASE64)
        handler.SetFontSizeMapping([7, 9, 11, 12, 14, 22, 100])
        stream = io.BytesIO()

        if not handler.SaveFile(self.ctrl_editeur.GetBuffer(), stream):
            return False

        source = stream.getvalue()
        source = source.decode("utf-8")
        for balise in ("<html>", "</html>", "<head>", "</head>", "<body>", "</body>"):
            if isinstance(balise, str):
                balise = balise.encode("utf-8")
                source = source.replace(balise, b"")
            else:
                source = source.replace(balise, "")
        return source

    def GetValue(self):
        return self.ctrl_editeur.GetValue() 
    
    def GetXML(self):
        return self.ctrl_editeur.GetXML()
    
    def SetXML(self, texteXml=""):
        self.ctrl_editeur.SetXML(texteXml)
        
    def EcritTexte(self, texte=""):
        """ Ecrit un texte à l'emplacement du focus """
        self.ctrl_editeur.WriteText(texte)
        self.ctrl_editeur.SetFocus()



# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL(panel)
        self.bouton_test = wx.Button(panel, -1, "Test fileView")
        self.bouton_2 = wx.Button(panel, -1, "Test preview html")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.bouton_test, 0, wx.ALL | wx.EXPAND, 4)
        sizer_2.Add(self.bouton_2, 0, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.bouton_test)
        self.Bind(wx.EVT_BUTTON, self.OnBouton2, self.bouton_2)

    def OnBoutonTest(self, event):
        print(self.ctrl.GetHTML(base64=True)[0])
        self.ctrl.OnFileViewHTML()

    def OnBouton2(self, event):
        self.ctrl.OnPreview(event)


if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "CTRL_Editeur_email",size = (500,600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
