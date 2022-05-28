#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-15 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import datetime
import GestionDB
from Utils import UTILS_Identification

CATEGORIES = {
    0 : _("Action Inconnue"),
    1 : _("Ouverture d'un fichier"),
    2 : _("Fermeture d'un fichier"),
    3 : _("Nouvel utilisateur"),
    4 : _("Cr�ation d'une famille"),
    5 : _("Suppression d'une famille"),
    6 : _("Saisie d'un r�glement"),
    7 : _("Modification d'un r�glement"),
    8 : _("Suppression d'un r�glement"),
    9 : _("Saisie de consommations"),
    10 : _("Suppression de consommations"),
    11 : _("Cr�ation d'un individu"),
    12 : _("Suppression d'un individu"),
    13 : _("Rattachement d'un individu"),
    14 : _("D�tachement d'un individu"),
    15 : _("Saisie d'une pi�ce"),
    16 : _("Modification d'une pi�ce"),
    17 : _("Suppression d'une pi�ce"),
    18 : _("Inscription � une activit�"),
    19 : _("D�sinscription d'une activit�"),
    20 : _("Modification de l'inscription � une activit�"),
    21 : _("Saisie d'une cotisation"),
    22 : _("Modification d'une cotisation"),
    23 : _("Suppression d'une cotisation"),
    24 : _("Saisie d'un message"),
    25 : _("Modification d'un message"),
    26 : _("Suppression d'un message"),
    27 : _("Edition d'une attestation de pr�sence"),
    28 : _("Edition d'un re�u de r�glement"),
    29 : _("Modification de consommations"),
    30 : _("Inscription scolaire"),
    31 : _("Modification d'une inscription scolaire"),
    32 : _("Suppression d'une inscription scolaire"),
    33 : _("Envoi d'un Email"),
    34 : _("Edition d'une confirmation d'inscription"),
    35 : _("G�n�ration d'un fichier XML SEPA"),
    72 : _("Transfert en compta"),
    73 : _("Coh�rence automatique"),
    74 : _("Suppression Facturation"),
    75 : _("Modification Facturation"),
    76 : _("Facturation"),
    77 : _("Suppression Inscription"),
    78 : _("Modification Inscription"),
    79 : _("Inscription"),
    80 : _("Diagnostic coh�rence")
    }

DICT_COULEURS = {
    (166, 245, 156) : (4, 5),
    (236, 245, 156) : (6, 7, 8),
    (245, 208, 156) : (9, 10, 29),
    (245, 164, 156) : (11, 12, 13, 14),
    (156, 245, 160) : (15, 16, 17),
    (156, 245, 223) : (18, 19, 20),
    (156, 193, 245) : (21, 22, 23),
    (170, 156, 245) : (24, 25, 26),
    (231, 156, 245) : (27, 28),
    }


def InsertActions(listeActions=[], DB=None):
    """ dictAction = { IDutilisateur : None, IDfamille : None, IDindividu : None, IDcategorie : None, action : "", IDdonnee: None } """
    date = str(datetime.date.today())
    heure = "%02d:%02d:%02d" % (datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)
    
    # Traitement des actions
    listeAjouts = []
    for dictAction in listeActions :
        if "IDutilisateur" in dictAction :
            IDutilisateur = dictAction["IDutilisateur"]
        else :
            IDutilisateur = UTILS_Identification.GetIDutilisateur()
        if "IDfamille" in dictAction :
            IDfamille = dictAction["IDfamille"]
        else :
            IDfamille = None
        if "IDindividu" in dictAction :
            IDindividu = dictAction["IDindividu"]
        else :
            IDindividu = None
        if "IDcategorie" in dictAction :
            IDcategorie = dictAction["IDcategorie"]
        else :
            IDcategorie = None
        if "action" in dictAction :
            action = dictAction["action"]
        else :
            action = ""
        if len(action) >= 500 :
            action = action[:495] + "..." # Texte limit� � 499 caract�res

        listeAjouts.append((date, heure, IDutilisateur, IDfamille, IDindividu, IDcategorie, action))
    
    # Enregistrement dans la base
    if len(listeAjouts) > 0 :
        req = "INSERT INTO historique (date, heure, IDutilisateur, IDfamille, IDindividu, IDcategorie, action) VALUES (?, ?, ?, ?, ?, ?, ?)"
        if DB == None :
            DB = GestionDB.DB()
            try:
                DB.Executermany(req, listeAjouts, commit=False)
            except:
                req = "INSERT INTO historique (date, heure, IDutilisateur, IDfamille, IDindividu, IDcategorie, action) VALUES (?, ?, ?, ?, ?, ?, ?)"
                DB.Executermany(req, listeAjouts[:-1], commit=False)
            DB.Commit()
            DB.Close()
        else :
            DB.Executermany(req, listeAjouts, commit=False)
            DB.Commit()
