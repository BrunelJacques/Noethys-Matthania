#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# Types de prestations dans champ catégorie des prestations

import wx
import GestionDB

TYPES_PRESTATIONS = [
        # ( IDtypePrestation, label ),
        ("","_____ Saisir le type ou flécher _____"),
        ("don", "Don à l'association"),
        ("donsscerfa", "Don sans Cerfa"),
        ("debour", "Frais ou débour dû par client"),
        ("autre", "Paiement autre client (ou autres cas)"),
        ("consommation", "Prestation issue de pièce liée à une inscription"),
        ("consoavoir", "Prestation de pièce annulée par un avoir"),
        ]

TYPES_COMPTES = [
        # (IDtypecompte, label,                             motCle,  prefix-piece
        ("vente",       "Vente|Avoir service|accessoire ",  "70",    "vt"),
        ("reduc",       "Réduction commerciale ",           "RED",   "vt"),
        ("don",         "Don à l'association",              "DON",   "dn"),
        ("rbt",         "Remboursement avance bénevole"     "RBT"    "rb"),
        ("debour",      "Frais ou débour dû par client",    "6",     "db"),
        ("debour58",    "Frais ou débour ",                 "58",    "db"),
        ("autre",       "Cas à gérer en compta ",           "",      "xx"),
        ]

def GetLstTypesPrest(consos=True, dons=True, autres=True):
    # retourne deux listes pour un choix à l'écran
    lstIDtypes, lstLibTypes = [], []
    for IDtypePrestation, libTypePrestation, prefix in TYPES_PRESTATIONS :
        if not consos and IDtypePrestation.startswith("conso"):
            continue
        if not dons and IDtypePrestation.startswith("don"):
            continue
        if not autres and not (IDtypePrestation.startswith("don")
                               or IDtypePrestation.startswith("conso")):
            continue
        lstIDtypes.append(IDtypePrestation)
        lstLibTypes.append(libTypePrestation)
    return lstIDtypes, lstLibTypes

def GetLstComptes(DB):
    req = """
        SELECT pctCodeComptable, pctLibelle, pctCompte
        FROM matPlanComptable; 
    """
    DB.ExecuterReq(req,MsgBox="DATA_Types_prestations.GetMatPlanCpte")
    lstDonnees = [x for x in sorted(DB.ResultatReq(), key=lambda item: item[1])]
    # retourne la liste triée sur le libellé
    return lstDonnees

def GetLstCptesTypes(DB):
    lstResult = []
    lstcptes = GetLstComptes(DB)
    for code,lib,cpt in lstcptes:
        for ID, lab,mot,prefix in TYPES_COMPTES:
            try:
                i = int(mot)
            except:
                i = None
            lstResult.append((code,lib,cpt,prefix))
            break
